from typing import Optional, Set, List, Tuple, Dict
import logging, datetime

from blspy import G1Element
from chia.pools.pool_wallet_info import PoolState
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.types.coin_spend import CoinSpend
from chia.util.ints import uint64

from .mysql_poolwrap import MysqlPoolWrap
from ..record import FarmerRecord

log = logging
log.basicConfig(level=logging.INFO)


class MysqlPoolStore():
    """pool store for mysql"""

    def __init__(self, host, port, user, passwd, name):
        self.wrap = MysqlPoolWrap(host, port, user, passwd, name)

    @staticmethod
    def _row_to_farmer_record(res) -> FarmerRecord:
        return FarmerRecord(
            bytes.fromhex(res["launcher_id"].decode()),
            bytes.fromhex(res["p2_singleton_puzzle_hash"].decode()),
            res["delay_time"],
            bytes.fromhex(res["delay_puzzle_hash"].decode()),
            G1Element.from_bytes(bytes.fromhex(res["authentication_public_key"].decode())),
            CoinSpend.from_bytes(res["singleton_tip"]),
            PoolState.from_bytes(res["singleton_tip_state"]),
            res["accept_account"],
            res["difficulty"],
            res["payout_instructions"].decode(),
            True if res["is_pool_member"] == 1 else False, )

    # 不需要
    async def add_farmer_record(self, farmer_record: FarmerRecord) -> int:
        now = datetime.datetime.now()
        now = now.strftime("%Y-%m-%d %H:%M:%S")
        sql = "INSERT INTO MINING_WORKERS_CHIA VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
              "%s) ON DUPLICATE KEY " \
              "UPDATE p2_singleton_puzzle_hash = %s, delay_time = %s, delay_puzzle_hash = %s, " \
              "authentication_public_key = %s, singleton_tip = %s, singleton_tip_state = %s, " \
              "accept_account = %s, difficulty = %s, payout_instructions = %s, is_pool_member = %s, updated_at = %s"

        param = (
            farmer_record.launcher_id.hex(),
            farmer_record.p2_singleton_puzzle_hash.hex(),
            farmer_record.delay_time,
            farmer_record.delay_puzzle_hash.hex(),
            bytes(farmer_record.authentication_public_key).hex(),
            bytes(farmer_record.singleton_tip),
            bytes(farmer_record.singleton_tip_state),
            farmer_record.points,
            farmer_record.difficulty,
            farmer_record.payout_instructions,
            int(farmer_record.is_pool_member),
            now,
            now,
            farmer_record.p2_singleton_puzzle_hash.hex(),
            farmer_record.delay_time,
            farmer_record.delay_puzzle_hash.hex(),
            bytes(farmer_record.authentication_public_key).hex(),
            bytes(farmer_record.singleton_tip),
            bytes(farmer_record.singleton_tip_state),
            farmer_record.points,
            farmer_record.difficulty,
            farmer_record.payout_instructions,
            int(farmer_record.is_pool_member),
            now
        )
        count = self.wrap.insertOne(sql, param)
        return count

    # for test
    def add_farmer_record1(self, sql, param) -> int:
        count = self.wrap.insertOne(sql, param)
        return count

    # 只读，会用到
    async def get_farmer_record(self, launcher_id: bytes32) -> Optional[FarmerRecord]:
        sql = "SELECT * from MINING_WORKERS_CHIA where launcher_id=%s"
        param = (launcher_id.hex(),)
        res = self.wrap.select(sql, param, False)
        if not res:
            log.debug("can not find any record for launcher_id:%s", launcher_id.hex())
            return None
        return self._row_to_farmer_record(res)

    # 更新难度，暂时放到这，更新的不会太频繁
    async def update_difficulty(self, launcher_id: bytes32, difficulty: uint64) -> int:
        sql = "UPDATE MINING_WORKERS_CHIA SET difficulty=%s WHERE launcher_id=%s"
        param = (difficulty, launcher_id.hex())
        count = self.wrap.update(sql, param)
        return count

    async def update_singleton(
            self,
            launcher_id: bytes32,
            singleton_tip: CoinSpend,
            singleton_tip_state: PoolState,
            is_pool_member: bool,
    ) -> int:
        if is_pool_member:
            entry = (bytes(singleton_tip), bytes(singleton_tip_state), 1, launcher_id.hex())
        else:
            entry = (bytes(singleton_tip), bytes(singleton_tip_state), 0, launcher_id.hex())
        sql = "UPDATE MINING_WORKERS_CHIA SET singleton_tip=%s, singleton_tip_state=%s, is_pool_member=%s WHERE " \
              "launcher_id=%s "
        count = self.wrap.update(sql, entry)
        return count

    # 如果放到内存里则不需要
    async def get_recent_partials(self, launcher_id: bytes32, count: int) -> List[Tuple[uint64, uint64]]:
        sql = "SELECT timestamp, difficulty from share_workers_chia WHERE launcher_id=%s ORDER BY timestamp DESC " \
              "LIMIT %s "
        param = (launcher_id.hex(), count)
        rows = self.wrap.select(sql, param, True)
        ret: List[Tuple[uint64, uint64]] = [(uint64(row['timestamp']), uint64(row['difficulty'])) for row in rows]
        return ret
