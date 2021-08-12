import asyncio
import logging
import pathlib
import time
import traceback
from asyncio import Task
from math import floor
from typing import Dict, Optional, Set, List, Tuple, Callable
import json
from kafka import KafkaProducer
import redis

from blspy import AugSchemeMPL, G1Element
from chia.consensus.block_rewards import calculate_pool_reward
from chia.pools.pool_wallet_info import PoolState, PoolSingletonState
from chia.protocols.pool_protocol import (
    PoolErrorCode,
    PostPartialRequest,
    PostPartialResponse,
    PostFarmerRequest,
    PostFarmerResponse,
    PutFarmerRequest,
    PutFarmerResponse,
    POOL_PROTOCOL_VERSION,
)
from chia.rpc.wallet_rpc_client import WalletRpcClient
from chia.types.blockchain_format.coin import Coin
from chia.types.coin_record import CoinRecord
from chia.types.coin_spend import CoinSpend
from chia.util.bech32m import decode_puzzle_hash
from chia.consensus.constants import ConsensusConstants
from chia.util.ints import uint8, uint16, uint32, uint64, int64
from chia.util.byte_types import hexstr_to_bytes
from chia.util.default_root import DEFAULT_ROOT_PATH
from chia.rpc.full_node_rpc_client import FullNodeRpcClient
from chia.full_node.signage_point import SignagePoint
from chia.types.end_of_slot_bundle import EndOfSubSlotBundle
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.consensus.pot_iterations import calculate_iterations_quality
from chia.util.lru_cache import LRUCache
from chia.util.chia_logging import initialize_logging
from chia.wallet.transaction_record import TransactionRecord
from chia.pools.pool_puzzles import (
    get_delayed_puz_info_from_launcher_spend,
    launcher_id_to_p2_puzzle_hash,
)

from .difficulty_adjustment import get_new_difficulty
from .singleton import create_absorb_transaction, get_singleton_state, get_coin_spend, get_farmed_height
from .store.abstract import AbstractPoolStore
from .store.sqlite_store import SqlitePoolStore
from .record import FarmerRecord
from .util import error_dict, RequestMetadata
from .proto.chia_pb2 import FarmerMsg, ShareMsg


class Pool:
    def __init__(self, config: Dict, pool_config: Dict, constants: ConsensusConstants,
                 pool_store: Optional[AbstractPoolStore] = None,
                 difficulty_function: Callable = get_new_difficulty):
        self.follow_singleton_tasks: Dict[bytes32, asyncio.Task] = {}
        self.log = logging
        # If you want to log to a file: use filename='example.log', encoding='utf-8'
        self.log.basicConfig(level=logging.INFO)

        initialize_logging("pool", pool_config["logging"], pathlib.Path(pool_config["logging"]["log_path"]))

        # Set our pool info here
        self.info_default_res = pool_config["pool_info"]["default_res"]
        self.info_name = pool_config["pool_info"]["name"]
        self.info_logo_url = pool_config["pool_info"]["logo_url"]
        self.info_description = pool_config["pool_info"]["description"]
        self.welcome_message = pool_config["welcome_message"]

        self.config = config
        self.constants = constants

        self.store: AbstractPoolStore = pool_store or SqlitePoolStore()

        self.pool_fee = pool_config["pool_fee"]

        # This number should be held constant and be consistent for every pool in the network. DO NOT CHANGE
        self.iters_limit = self.constants.POOL_SUB_SLOT_ITERS // 64

        # This number should not be changed, since users will put this into their singletons
        self.relative_lock_height = uint32(pool_config["relative_lock_height"])

        # TODO(pool): potentially tweak these numbers for security and performance
        # This is what the user enters into the input field. This exact value will be stored on the blockchain
        self.pool_url = pool_config["pool_url"]
        self.min_difficulty = uint64(pool_config["min_difficulty"])  # 10 difficulty is about 1 proof a day per plot
        self.default_difficulty: uint64 = uint64(pool_config["default_difficulty"])
        self.difficulty_function: Callable = difficulty_function

        self.pending_point_partials: Optional[asyncio.Queue] = None
        self.recent_points_added: LRUCache = LRUCache(20000)

        # The time in minutes for an authentication token to be valid. See "Farmer authentication" in SPECIFICATION.md
        self.authentication_token_timeout: uint8 = pool_config["authentication_token_timeout"]

        # This is where the block rewards will get paid out to. The pool needs to support this address forever,
        # since the farmers will encode it into their singleton on the blockchain. WARNING: the default pool code
        # completely spends this wallet and distributes it to users, do don't put any additional funds in here
        # that you do not want to distribute. Even if the funds are in a different address than this one, they WILL
        # be spent by this code! So only put funds that you want to distribute to pool members here.

        # Using 2164248527
        self.default_target_puzzle_hash: bytes32 = bytes32(decode_puzzle_hash(pool_config["default_target_address"]))

        # The pool fees will be sent to this address. This MUST be on a different key than the target_puzzle_hash,
        # otherwise, the fees will be sent to the users. Using 690783650
        self.pool_fee_puzzle_hash: bytes32 = bytes32(decode_puzzle_hash(pool_config["pool_fee_address"]))

        # This is the wallet fingerprint and ID for the wallet spending the funds from `self.default_target_puzzle_hash`
        self.wallet_fingerprint = pool_config["wallet_fingerprint"]
        self.wallet_id = pool_config["wallet_id"]

        # We need to check for slow farmers. If farmers cannot submit proofs in time, they won't be able to win
        # any rewards either. This number can be tweaked to be more or less strict. More strict ensures everyone
        # gets high rewards, but it might cause some of the slower farmers to not be able to participate in the pool.
        self.partial_time_limit: int = pool_config["partial_time_limit"]

        # There is always a risk of a reorg, in which case we cannot reward farmers that submitted partials in that
        # reorg. That is why we have a time delay before changing any account points.
        self.partial_confirmation_delay: int = pool_config["partial_confirmation_delay"]

        # Only allow PUT /farmer per launcher_id every n seconds to prevent difficulty change attacks.
        self.farmer_update_blocked: set = set()
        self.farmer_update_cooldown_seconds: int = 600

        # These are the phs that we want to look for on chain, that we can claim to our pool
        # 因为pool reward收集不在这里做，所以这个变量不需要了
        # self.scan_p2_singleton_puzzle_hashes: Set[bytes32] = set()

        # Don't scan anything before this height, for efficiency (for example pool start date)
        self.scan_start_height: uint32 = uint32(pool_config["scan_start_height"])

        # Interval for scanning and collecting the pool rewards
        self.collect_pool_rewards_interval = pool_config["collect_pool_rewards_interval"]

        # After this many confirmations, a transaction is considered final and irreversible
        self.confirmation_security_threshold = pool_config["confirmation_security_threshold"]

        # Interval for making payout transactions to farmers
        self.payment_interval = pool_config["payment_interval"]

        # We will not make transactions with more targets than this, to ensure our transaction gets into the blockchain
        # faster.
        self.max_additions_per_transaction = pool_config["max_additions_per_transaction"]

        # This is the list of payments that we have not sent yet, to farmers
        self.pending_payments: Optional[asyncio.Queue] = None

        # Keeps track of the latest state of our node
        self.blockchain_state = {"peak": None}

        # Whether or not the wallet is synced (required to make payments)
        self.wallet_synced = False

        # We target these many partials for this number of seconds. We adjust after receiving this many partials.
        self.number_of_partials_target: int = pool_config["number_of_partials_target"]
        self.time_target: int = pool_config["time_target"]

        # kafka
        self.kafka_server = pool_config["kafka_server"]
        self.farmer_topic = pool_config["farmer_topic"]
        self.share_topic = pool_config["share_topic"]
        self.kafka_server = pool_config["kafka_server"]
        self.kafka_producer = {}

        self.dev_mode = pool_config["dev_mode"]

        #
        self.partial_map = {}

        # redis
        self.redis_host = pool_config["redis_host"]
        self.redis_port = int(pool_config["redis_port"])
        self.passwd = pool_config["redis_passwd"]
        self.redis = {}

        # Tasks (infinite While loops) for different purposes
        self.confirm_partials_loop_task: Optional[asyncio.Task] = None
        self.get_peak_loop_task: Optional[asyncio.Task] = None

        self.node_rpc_client: Optional[FullNodeRpcClient] = None
        self.node_rpc_port = pool_config["node_rpc_port"]
        self.wallet_rpc_client: Optional[WalletRpcClient] = None
        self.wallet_rpc_port = pool_config["wallet_rpc_port"]

        # 模拟测试post_partials
        if self.dev_mode:
            self.simulate_partials_loop_task: Optional[asyncio.Task] = None

    async def start(self):
        await self.store.connect()

        redis_pool = redis.ConnectionPool(host=self.redis_host, port=self.redis_port, password=self.passwd,
                                          decode_responses=True)  # host是redis主机，需要redis服务端和客户端都起着 redis默认端口是6379
        self.redis = redis.Redis(connection_pool=redis_pool)

        self.kafka_producer = KafkaProducer(bootstrap_servers=self.kafka_server)

        self.pending_point_partials = asyncio.Queue()

        self_hostname = self.config["self_hostname"]
        self.node_rpc_client = await FullNodeRpcClient.create(
            self_hostname, uint16(self.node_rpc_port), DEFAULT_ROOT_PATH, self.config
        )
        self.wallet_rpc_client = await WalletRpcClient.create(
            self.config["self_hostname"], uint16(self.wallet_rpc_port), DEFAULT_ROOT_PATH, self.config
        )
        self.blockchain_state = await self.node_rpc_client.get_blockchain_state()
        res = await self.wallet_rpc_client.log_in_and_skip(fingerprint=self.wallet_fingerprint)
        if not res["success"]:
            raise ValueError(f"Error logging in: {res['error']}. Make sure your config fingerprint is correct.")
        self.log.info(f"Logging in: {res}")
        res = await self.wallet_rpc_client.get_wallet_balance(self.wallet_id)
        self.log.info(f"Obtaining balance: {res}")

        self.confirm_partials_loop_task = asyncio.create_task(self.confirm_partials_loop())
        self.get_peak_loop_task = asyncio.create_task(self.get_peak_loop())

        self.pending_payments = asyncio.Queue()
        if self.dev_mode:
            self.simulate_partials_loop_task = asyncio.create_task(self.simulate_partials_loop())

    async def stop(self):
        if self.confirm_partials_loop_task is not None:
            self.confirm_partials_loop_task.cancel()
        if self.get_peak_loop_task is not None:
            self.get_peak_loop_task.cancel()
        if self.dev_mode:
            if self.simulate_partials_loop_task is not None:
                self.simulate_partials_loop_task.cancel()

        self.wallet_rpc_client.close()
        await self.wallet_rpc_client.await_closed()
        self.node_rpc_client.close()
        await self.node_rpc_client.await_closed()
        await self.store.connection.close()

    async def get_peak_loop(self):
        """
        Periodically contacts the full node to get the latest state of the blockchain
        """
        while True:
            try:
                self.blockchain_state = await self.node_rpc_client.get_blockchain_state()
                self.wallet_synced = await self.wallet_rpc_client.get_synced()
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                self.log.info("Cancelled get_peak_loop, closing")
                return
            except Exception as e:
                self.log.error(f"Unexpected error in get_peak_loop: {e}")
                await asyncio.sleep(30)

    async def confirm_partials_loop(self):
        """
        Pulls things from the queue of partials one at a time, and adjusts balances.
        """

        while True:
            try:
                # The points are based on the difficulty at the time of partial submission, not at the time of
                # confirmation
                partial, time_received, points_received, puid = await self.pending_point_partials.get()

                # Wait a few minutes to check if partial is still valid in the blockchain (no reorgs)
                await asyncio.sleep((max(0, time_received + self.partial_confirmation_delay - time.time() - 5)))

                # Starts a task to check the remaining things for this partial and optionally update points
                asyncio.create_task(self.check_and_confirm_partial(partial, points_received, puid))
            except asyncio.CancelledError:
                self.log.info("Cancelled confirm partials loop, closing")
                return
            except Exception as e:
                self.log.error(f"Unexpected error: {e}")

    async def check_and_confirm_partial(self, partial: PostPartialRequest, points_received: uint64, puid : int) -> None:
        try:
            if not self.dev_mode:
                # TODO(pool): these lookups to the full node are not efficient and can be cached, especially for
                #  scaling to many users
                if partial.payload.end_of_sub_slot:
                    response = await self.node_rpc_client.get_recent_signage_point_or_eos(None, partial.payload.sp_hash)
                    if response is None or response["reverted"]:
                        self.log.info(f"Partial EOS reverted: {partial.payload.sp_hash}")
                        return
                else:
                    response = await self.node_rpc_client.get_recent_signage_point_or_eos(partial.payload.sp_hash, None)
                    if response is None or response["reverted"]:
                        self.log.info(f"Partial SP reverted: {partial.payload.sp_hash}")
                        return

                # Now we know that the partial came on time, but also that the signage point / EOS is still in the
                # blockchain. We need to check for double submissions.
                pos_hash = partial.payload.proof_of_space.get_hash()
                if self.recent_points_added.get(pos_hash):
                    self.log.info(f"Double signage point submitted for proof: {partial.payload}")
                    return
                self.recent_points_added.put(pos_hash, uint64(1))

                # Now we need to check to see that the singleton in the blockchain is still assigned to this pool
                singleton_state_tuple: Optional[
                    Tuple[CoinSpend, PoolState, bool]
                ] = await self.get_and_validate_singleton_state(partial.payload.launcher_id)

                if singleton_state_tuple is None:
                    self.log.info(f"Invalid singleton {partial.payload.launcher_id}")
                    return

                _, _, is_member = singleton_state_tuple
                if not is_member:
                    self.log.info(f"Singleton is not assigned to this pool")
                    return

            async with self.store.lock:
                farmer_record: Optional[FarmerRecord] = await self.store.get_farmer_record(partial.payload.launcher_id)

                assert (
                        partial.payload.proof_of_space.pool_contract_puzzle_hash == farmer_record.p2_singleton_puzzle_hash
                )

                if farmer_record.is_pool_member:
                    # 修改读内存
                    # self.add_partial(partial.payload.launcher_id, uint64(int(time.time())), points_received)

                    # 向后台统计模块发送share
                    msg = ShareMsg()
                    msg.launcherid = partial.payload.launcher_id.hex()
                    msg.userid = puid
                    msg.difficulty = points_received
                    msg.timestamp = uint64(int(time.time()))
                    self.produceShareMsg(msg.SerializeToString())

                    # await self.store.add_partial(partial.payload.launcher_id, uint64(int(time.time())), points_received)
                    self.log.info(
                        f"Farmer {farmer_record.launcher_id} updated points to: " f"{farmer_record.points + points_received}")
        except Exception as e:
            error_stack = traceback.format_exc()
            self.log.error(f"Exception in confirming partial: {e} {error_stack}")

    def add_partial(self, launcher_id, timestamp, points):
        val = (timestamp, points)
        if self.partial_map.get(launcher_id) is None:
            self.log.info(f"get_new_difficulty ,add_partial : {launcher_id.hex()} is None")
            partial_list = [val]
            self.partial_map[launcher_id] = partial_list
        else:
            self.log.info(f"get_new_difficulty ,add_partial : {launcher_id.hex()} is Exist")
            partial_list = self.partial_map[launcher_id]
            partial_list.append(val)
            if len(partial_list) > self.number_of_partials_target:
                partial_list.pop(0)

    def get_recent_partials(self, launcher_id: bytes32, count: int) -> List[Tuple[uint64, uint64]]:
        if self.partial_map.get(launcher_id) is None:
            self.log.info(f"get_new_difficulty ,get_recent_partials: {launcher_id.hex()} is None")
            return []
        else:
            ret: List[Tuple[uint64, uint64]] = [(uint64(timestamp), uint64(difficulty)) for timestamp, difficulty in
                                                self.partial_map.get(launcher_id)]

            res = ret[0 - count:]
            self.log.info(f"get_new_difficulty , get_recent_partials: {launcher_id.hex()} is Exist")
            return res[::-1]

    async def add_farmer(self, request: PostFarmerRequest, metadata: RequestMetadata) -> Dict:
        async with self.store.lock:
            farmer_record: Optional[FarmerRecord] = await self.store.get_farmer_record(request.payload.launcher_id)
            if farmer_record is not None:
                return error_dict(
                    PoolErrorCode.FARMER_ALREADY_KNOWN,
                    f"Farmer with launcher_id {request.payload.launcher_id} already known.",
                )

            singleton_state_tuple: Optional[
                Tuple[CoinSpend, PoolState, bool]
            ] = await self.get_and_validate_singleton_state(request.payload.launcher_id)

            if singleton_state_tuple is None:
                return error_dict(PoolErrorCode.INVALID_SINGLETON, f"Invalid singleton {request.payload.launcher_id}")

            last_spend, last_state, is_member = singleton_state_tuple
            if is_member is None:
                return error_dict(PoolErrorCode.INVALID_SINGLETON, f"Singleton is not assigned to this pool")

            if (
                    request.payload.suggested_difficulty is None
                    or request.payload.suggested_difficulty < self.min_difficulty
            ):
                difficulty: uint64 = self.default_difficulty
            else:
                difficulty = request.payload.suggested_difficulty

            if len(hexstr_to_bytes(request.payload.payout_instructions)) != 32:
                return error_dict(
                    PoolErrorCode.INVALID_PAYOUT_INSTRUCTIONS,
                    f"Payout instructions must be an xch address for this pool.",
                )

            if not AugSchemeMPL.verify(last_state.owner_pubkey, request.payload.get_hash(), request.signature):
                return error_dict(PoolErrorCode.INVALID_SIGNATURE, f"Invalid signature")

            launcher_coin: Optional[CoinRecord] = await self.node_rpc_client.get_coin_record_by_name(
                request.payload.launcher_id
            )
            assert launcher_coin is not None and launcher_coin.spent

            launcher_solution: Optional[CoinSpend] = await get_coin_spend(self.node_rpc_client, launcher_coin)
            delay_time, delay_puzzle_hash = get_delayed_puz_info_from_launcher_spend(launcher_solution)

            if delay_time < 3600:
                return error_dict(PoolErrorCode.DELAY_TIME_TOO_SHORT, f"Delay time too short, must be at least 1 hour")

            p2_singleton_puzzle_hash = launcher_id_to_p2_puzzle_hash(
                request.payload.launcher_id, delay_time, delay_puzzle_hash
            )

            farmer_record = FarmerRecord(
                request.payload.launcher_id,
                p2_singleton_puzzle_hash,
                delay_time,
                delay_puzzle_hash,
                request.payload.authentication_public_key,
                last_spend,
                last_state,
                uint64(0),
                difficulty,
                request.payload.payout_instructions,
                True,
            )
            """
            msg = FarmerMsg()
            msg.launcherid = request.payload.launcher_id.hex()
            msg.singletonpuzzlehash = p2_singleton_puzzle_hash.hex()
            msg.delaytime = delay_time
            msg.delaypuzzlehash = delay_puzzle_hash.hex()
            msg.authenticationpublickey = bytes(request.payload.authentication_public_key).hex()
            msg.singletontip = bytes(last_spend).hex()
            msg.singletontipstate = bytes(last_state).hex()
            msg.points = 0
            msg.difficulty = difficulty
            msg.payoutinstructions = request.payload.payout_instructions
            msg.ispoolmember = True
            msg.timestamp = uint64(int(time.time()))  # 是不是需要int64还是直接用int
            msg.flag = 0
            await self.produceFarmerMsg(msg.SerializeToString())
            """
            # 当新农民加入进来的时候，需要增加，并不频繁
            await self.store.add_farmer_record(farmer_record)

            return PostFarmerResponse(self.welcome_message).to_json_dict()

    async def update_farmer(self, request: PutFarmerRequest, metadata: RequestMetadata) -> Dict:
        launcher_id = request.payload.launcher_id
        # First check if this launcher_id is currently blocked for farmer updates, if so there is no reason to validate
        # all the stuff below
        if launcher_id in self.farmer_update_blocked:
            return error_dict(PoolErrorCode.REQUEST_FAILED, f"Cannot update farmer yet.")
        farmer_record: Optional[FarmerRecord] = await self.store.get_farmer_record(launcher_id)
        if farmer_record is None:
            return error_dict(PoolErrorCode.FARMER_NOT_KNOWN, f"Farmer with launcher_id {launcher_id} not known.")

        singleton_state_tuple: Optional[
            Tuple[CoinSpend, PoolState, bool]
        ] = await self.get_and_validate_singleton_state(launcher_id)

        if singleton_state_tuple is None:
            return error_dict(PoolErrorCode.INVALID_SINGLETON, f"Invalid singleton {request.payload.launcher_id}")

        last_spend, last_state, is_member = singleton_state_tuple
        if not is_member:
            return error_dict(PoolErrorCode.INVALID_SINGLETON, f"Singleton is not assigned to this pool")

        if not AugSchemeMPL.verify(last_state.owner_pubkey, request.payload.get_hash(), request.signature):
            return error_dict(PoolErrorCode.INVALID_SIGNATURE, f"Invalid signature")

        farmer_dict = farmer_record.to_json_dict()
        response_dict = {}
        if request.payload.authentication_public_key is not None:
            is_new_value = farmer_record.authentication_public_key != request.payload.authentication_public_key
            response_dict["authentication_public_key"] = is_new_value
            if is_new_value:
                farmer_dict["authentication_public_key"] = request.payload.authentication_public_key

        if request.payload.payout_instructions is not None:
            is_new_value = (
                    farmer_record.payout_instructions != request.payload.payout_instructions
                    and request.payload.payout_instructions is not None
                    and len(hexstr_to_bytes(request.payload.payout_instructions)) == 32
            )
            response_dict["payout_instructions"] = is_new_value
            if is_new_value:
                farmer_dict["payout_instructions"] = request.payload.payout_instructions

        if request.payload.suggested_difficulty is not None:
            is_new_value = (
                    farmer_record.difficulty != request.payload.suggested_difficulty
                    and request.payload.suggested_difficulty is not None
                    and request.payload.suggested_difficulty >= self.min_difficulty
            )
            response_dict["suggested_difficulty"] = is_new_value
            if is_new_value:
                farmer_dict["difficulty"] = request.payload.suggested_difficulty

        async def update_farmer_later():
            await asyncio.sleep(self.farmer_update_cooldown_seconds)

            """
            # 发送给kafka
            record = FarmerRecord.from_json_dict(farmer_dict)
            msg = FarmerMsg()
            msg.launcherid = record.launcher_id.hex()
            #msg.singletonpuzzlehash = record.p2_singleton_puzzle_hash.hex()
            #msg.delaytime = record.delay_time
            #msg.delaypuzzlehash = record.delay_puzzle_hash.hex()
            msg.authenticationpublickey = bytes(record.authentication_public_key).hex()
            #msg.singletontip = bytes(record.singleton_tip).hex()
            #msg.singletontipstate = bytes(record.singleton_tip_state).hex()
            #msg.points = record.points
            msg.difficulty = record.difficulty
            msg.payoutinstructions = record.payout_instructions
            #msg.ispoolmember = record.is_pool_member
            msg.timestamp = uint64(int(time.time()))  # 是不是需要int64还是直接用int
            msg.flag = 1
            await self.produceFarmerMsg(msg.SerializeToString())
            """

            # 没有用户提交partial，只是更改基本信息
            await self.store.add_farmer_record(FarmerRecord.from_json_dict(farmer_dict))
            self.farmer_update_blocked.remove(launcher_id)
            self.log.info(f"Updated farmer: {response_dict}")

        self.farmer_update_blocked.add(launcher_id)
        asyncio.create_task(update_farmer_later())

        # TODO Fix chia-blockchain's Streamable implementation to support Optional in `from_json_dict`, then use
        # PutFarmerResponse here and in the trace up.
        return response_dict

    async def get_and_validate_singleton_state(
            self, launcher_id: bytes32
    ) -> Optional[Tuple[CoinSpend, PoolState, bool]]:
        """
        :return: the state of the singleton, if it currently exists in the blockchain, and if it is assigned to
        our pool, with the correct parameters. Otherwise, None. Note that this state must be buried (recent state
        changes are not returned)
        """
        singleton_task: Optional[Task] = self.follow_singleton_tasks.get(launcher_id, None)
        remove_after = False
        farmer_rec = None
        if singleton_task is None or singleton_task.done():
            farmer_rec: Optional[FarmerRecord] = await self.store.get_farmer_record(launcher_id)
            singleton_task = asyncio.create_task(
                get_singleton_state(
                    self.node_rpc_client,
                    launcher_id,
                    farmer_rec,
                    self.blockchain_state["peak"].height,
                    self.confirmation_security_threshold,
                    self.constants.GENESIS_CHALLENGE,
                )
            )
            self.follow_singleton_tasks[launcher_id] = singleton_task
            remove_after = True

        optional_result: Optional[Tuple[CoinSpend, PoolState, PoolState]] = await singleton_task
        if remove_after and launcher_id in self.follow_singleton_tasks:
            await self.follow_singleton_tasks.pop(launcher_id)

        if optional_result is None:
            return None

        buried_singleton_tip, buried_singleton_tip_state, singleton_tip_state = optional_result

        # Validate state of the singleton
        is_pool_member = True
        if singleton_tip_state.target_puzzle_hash != self.default_target_puzzle_hash:
            self.log.info(
                f"Wrong target puzzle hash: {singleton_tip_state.target_puzzle_hash} for launcher_id {launcher_id}"
            )
            is_pool_member = False
        elif singleton_tip_state.relative_lock_height != self.relative_lock_height:
            self.log.info(
                f"Wrong relative lock height: {singleton_tip_state.relative_lock_height} for launcher_id {launcher_id}"
            )
            is_pool_member = False
        elif singleton_tip_state.version != POOL_PROTOCOL_VERSION:
            self.log.info(f"Wrong version {singleton_tip_state.version} for launcher_id {launcher_id}")
            is_pool_member = False
        elif singleton_tip_state.state == PoolSingletonState.SELF_POOLING.value:
            self.log.info(f"Invalid singleton state {singleton_tip_state.state} for launcher_id {launcher_id}")
            is_pool_member = False
        elif singleton_tip_state.state == PoolSingletonState.LEAVING_POOL.value:
            coin_record: Optional[CoinRecord] = await self.node_rpc_client.get_coin_record_by_name(
                buried_singleton_tip.coin.name()
            )
            assert coin_record is not None
            if self.blockchain_state["peak"].height - coin_record.confirmed_block_index > self.relative_lock_height:
                self.log.info(f"launcher_id {launcher_id} got enough confirmations to leave the pool")
                is_pool_member = False

        self.log.info(f"Is {launcher_id} pool member: {is_pool_member}")

        if farmer_rec is not None and (
                farmer_rec.singleton_tip != buried_singleton_tip
                or farmer_rec.singleton_tip_state != buried_singleton_tip_state
        ):
            # This means the singleton has been changed in the blockchain (either by us or someone else). We
            # still keep track of this singleton if the farmer has changed to a different pool, in case they
            # switch back.
            self.log.info(f"Updating singleton state for {launcher_id}")

            """
            msg = FarmerMsg()
            msg.launcherid = launcher_id.hex()
            msg.singletontip = bytes(buried_singleton_tip).hex()
            msg.singletontipstate = bytes(buried_singleton_tip_state).hex()
            msg.ispoolmember = is_pool_member
            msg.timestamp = uint64(int(time.time()))  # 是不是需要int64还是直接用int
            msg.flag = 2
            await self.produceFarmerMsg(msg.SerializeToString())
            """
            # 只是更新基本信息，改动的频率非常不频繁
            await self.store.update_singleton(
                launcher_id, buried_singleton_tip, buried_singleton_tip_state, is_pool_member
            )

        return buried_singleton_tip, buried_singleton_tip_state, is_pool_member

    async def process_partial(
            self,
            partial: PostPartialRequest,
            farmer_record: FarmerRecord,
            time_received_partial: uint64,
    ) -> Dict:
        # 检查redis中是否有launcherid对应的puid
        """
        redis中value的格式
        {
            "puid":123,
            "timestamp": 123
        }
        """
        redis_value = self.redis.get(partial.payload.launcher_id.hex())
        if redis_value is None:
            return error_dict(
                PoolErrorCode.NOT_FOUND,
                f"The launcher_id should bind okex account",
            )

        redis_res = json.loads(redis_value)
        puid = redis_res["puid"]

        # Validate signatures
        message: bytes32 = partial.payload.get_hash()
        pk1: G1Element = partial.payload.proof_of_space.plot_public_key
        pk2: G1Element = farmer_record.authentication_public_key
        if not self.dev_mode:
            valid_sig = AugSchemeMPL.aggregate_verify([pk1, pk2], [message, message], partial.aggregate_signature)
            if not valid_sig:
                return error_dict(
                    PoolErrorCode.INVALID_SIGNATURE,
                    f"The aggregate signature is invalid {partial.aggregate_signature}",
                )

        if partial.payload.proof_of_space.pool_contract_puzzle_hash != farmer_record.p2_singleton_puzzle_hash:
            return error_dict(
                PoolErrorCode.INVALID_P2_SINGLETON_PUZZLE_HASH,
                f"Invalid pool contract puzzle hash {partial.payload.proof_of_space.pool_contract_puzzle_hash}",
            )

        async def get_signage_point_or_eos():
            if partial.payload.end_of_sub_slot:
                return await self.node_rpc_client.get_recent_signage_point_or_eos(None, partial.payload.sp_hash)
            else:
                return await self.node_rpc_client.get_recent_signage_point_or_eos(partial.payload.sp_hash, None)

        if not self.dev_mode:
            response = await get_signage_point_or_eos()
            if response is None:
                # Try again after 10 seconds in case we just didn't yet receive the signage point
                await asyncio.sleep(10)
                response = await get_signage_point_or_eos()

            if response is None or response["reverted"]:
                return error_dict(
                    PoolErrorCode.NOT_FOUND, f"Did not find signage point or EOS {partial.payload.sp_hash}, {response}"
                )
            node_time_received_sp = response["time_received"]

            signage_point: Optional[SignagePoint] = response.get("signage_point", None)
            end_of_sub_slot: Optional[EndOfSubSlotBundle] = response.get("eos", None)

            if time_received_partial - node_time_received_sp > self.partial_time_limit:
                return error_dict(
                    PoolErrorCode.TOO_LATE,
                    f"Received partial in {time_received_partial - node_time_received_sp}. "
                    f"Make sure your proof of space lookups are fast, and network connectivity is good."
                    f"Response must happen in less than {self.partial_time_limit} seconds. NAS or network"
                    f" farming can be an issue",
                )

            # Validate the proof
            if signage_point is not None:
                challenge_hash: bytes32 = signage_point.cc_vdf.challenge
            else:
                challenge_hash = end_of_sub_slot.challenge_chain.get_hash()

            quality_string: Optional[bytes32] = partial.payload.proof_of_space.verify_and_get_quality_string(
                self.constants, challenge_hash, partial.payload.sp_hash
            )
            if quality_string is None:
                return error_dict(PoolErrorCode.INVALID_PROOF, f"Invalid proof of space {partial.payload.sp_hash}")

        current_difficulty = farmer_record.difficulty
        if not self.dev_mode:
            required_iters: uint64 = calculate_iterations_quality(
                self.constants.DIFFICULTY_CONSTANT_FACTOR,
                quality_string,
                partial.payload.proof_of_space.size,
                current_difficulty,
                partial.payload.sp_hash,
            )

            if required_iters >= self.iters_limit:
                return error_dict(
                    PoolErrorCode.PROOF_NOT_GOOD_ENOUGH,
                    f"Proof of space has required iters {required_iters}, too high for difficulty " f"{current_difficulty}",
                )

        await self.pending_point_partials.put((partial, time_received_partial, current_difficulty, puid))

        async with self.store.lock:
            # Obtains the new record in case we just updated difficulty
            farmer_record: Optional[FarmerRecord] = await self.store.get_farmer_record(partial.payload.launcher_id)
            if farmer_record is not None:
                current_difficulty = farmer_record.difficulty
                # Decide whether to update the difficulty
                # 是否合理，存内存行不行，是否一定要存数据库

                recent_partials = await self.store.get_recent_partials(
                    partial.payload.launcher_id, self.number_of_partials_target
                )
                """
                recent_partials = self.get_recent_partials(
                    partial.payload.launcher_id, self.number_of_partials_target
                )
                """

                # Only update the difficulty if we meet certain conditions
                self.log.info(f"get_new_difficulty number_of_partials_target:{int(self.number_of_partials_target)}"
                              f" num_recent_partials: {len(recent_partials)} time_received_partial:{time_received_partial}")
                new_difficulty: uint64 = self.difficulty_function(
                    partial.payload.launcher_id.hex(),
                    recent_partials,
                    int(self.number_of_partials_target),
                    int(self.time_target),
                    current_difficulty,
                    time_received_partial,
                    self.min_difficulty,
                )

                self.log.info(f"post_partials new_difficulty:{new_difficulty} current_difficulty:{current_difficulty}")
                if current_difficulty != new_difficulty:
                    """
                    msg = FarmerMsg()
                    msg.launcherid = partial.payload.launcher_id.hex()
                    msg.difficulty = new_difficulty
                    msg.timestamp = uint64(int(time.time()))
                    msg.flag = 3
                    await self.produceFarmerMsg(msg.SerializeToString())
                    """
                    # 更新难度，更新的并不频繁
                    await self.store.update_difficulty(partial.payload.launcher_id, new_difficulty)
                    current_difficulty = new_difficulty

        return PostPartialResponse(current_difficulty).to_json_dict()

    def produceFarmerMsg(self, msg):
        self.kafka_producer.send(self.farmer_topic, msg)

    def produceShareMsg(self, msg):
        self.log.info("produceShareMsg msg:%s", msg)
        self.kafka_producer.send(self.share_topic, msg)

    async def simulate_partials_loop(self):
        """
            模拟假的用户提交partials
        """

        while True:
            try:
                # TODO(pool): add rate limiting
                start_time = time.time()
                data = {
                    'payload': {
                        'launcher_id': '0xe090d5fd3ef9067b1002f85ff8922469bc788b8cb09d32eac385d8bc57741888',
                        'authentication_token': 5426297,
                        'proof_of_space': {
                            'challenge': '0x592c9406169f7844260cc722ee3905efda515284c3b03d4927d70f09f4349b29',
                            'pool_public_key': None,
                            'pool_contract_puzzle_hash': '0x486494c9357b384c8aef24e486b2e93113ce7234a8c445ce4e217a68ce049ae6',
                            'plot_public_key': '0x91c9863fde7544d604d37f41f05ad790148f331267a34f5a739e0372855003edf30c8bc70ae0d3a0a1ab3a3d0e6552c7',
                            'size': 32,
                            'proof': '0x4d11ee0d717a0eac443a31e827a6114393c2103cfd2681783b8ae66cd08c2e830137356649c55d0c0f1ff46017e24982de0dc42c115b1b495035a4f93fcd619fb7c609f01269d912c3d1ceeea85966c24842f8835f47dc23f1c54ab55855c33bcbe7d1713a0aa08bf2e80512f8bffceed3caf852303cff00d6e77c2e23b57acf21e2fe627282e532dc000aee4b99e65699b4acfad1bc2c5721d7a3c4573b6a2b3fef20438c5802756f4b5bff9ae554fd2f7eb6c7a2edad4260206c43aedd6124ccf187e371d7c155a3dc507d6dd60c6db99b401dcf908f1f9846c4d3b12d5b28fe950bfe0a61e76fc7692f02d93c879af7ab8772a7957baf024467ef7a539096'
                        },
                        'sp_hash': '0x16ed0a19832f25c494049d34286e574c1f8e4d5c75a57367c3d29adfe92321e5',
                        'end_of_sub_slot': False,
                        'harvester_id': '0x3d295ae210482f107fb50c96b4e1306645fafb4fce115f22fffdf5a03271b3ef'
                    },
                    'aggregate_signature': '0x87caff94d8f2d5bb9fa21d13034cb54285ef57e7901c2c23f702373011c9df10157f6b6febc4566dccfde83b4b10e1800a23e79cb465013a40901f54e94d9b349e0a747d1887d7d98706e8078f46a03426069dd24efbe188b05cf225295f3de9'
                }
                for i in range(100, 699):
                    launcher_id = 'e090d5fd3ef9067b1002f85ff8922469bc788b8cb09d32eac385d8bc57741' + str(i)
                    data['payload']['launcher_id'] = launcher_id
                    str_data = json.dumps(data)
                    request = json.loads(str_data)
                    partial: PostPartialRequest = PostPartialRequest.from_json_dict(request)

                    self.log.info(f"post_partial launcher_id: {partial.payload.launcher_id.hex()}")

                    farmer_record: Optional[FarmerRecord] = await self.store.get_farmer_record(
                        partial.payload.launcher_id)
                    if farmer_record is None:
                        self.log.info(f"Farmer with launcher_id {partial.payload.launcher_id.hex()} not known.")
                        continue

                    post_partial_response = await self.process_partial(partial, farmer_record, uint64(int(start_time)))

                    self.log.info(
                        f"post_partial response {post_partial_response}, time: {time.time() - start_time} "
                        f"launcher_id: {request['payload']['launcher_id']}"
                    )

                # 每间隔5分钟发送一次
                await asyncio.sleep(500)
            except asyncio.CancelledError:
                self.log.info("Cancelled confirm partials loop, closing")
                return
            except Exception as e:
                self.log.error(f"Unexpected error: {e}")
