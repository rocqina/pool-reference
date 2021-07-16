from typing import Optional, Set, List, Tuple, Dict

from blspy import G1Element
from chia.pools.pool_wallet_info import PoolState
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.types.coin_solution import CoinSolution
from chia.util.ints import uint64

from .abstract import AbstractPoolStore
from .mysql_poolwrap import MysqlPoolWrap
from ..record import FarmerRecord


class MysqlPoolStore(AbstractPoolStore):
    """pool store for mysql"""

    def __init__(self):
        super().__init__()
        self.wrap = MysqlPoolWrap()

    # 连接数据库，直接在数据库中建表，不需要在建
    async def connect(self):
        pass

    @staticmethod
    def _row_to_farmer_record(row) -> FarmerRecord:
        return FarmerRecord(
            bytes.fromhex(row[0]),
            bytes.fromhex(row[1]),
            row[2],
            bytes.fromhex(row[3]),
            G1Element.from_bytes(bytes.fromhex(row[4])),
            CoinSolution.from_bytes(row[5]),
            PoolState.from_bytes(row[6]),
            row[7],
            row[8],
            row[9],
            True if row[10] == 1 else False, )

    # 不需要
    async def add_farmer_record(self, farmer_record: FarmerRecord) -> int:
        sql = "INSERT INTO farmer VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY " \
              "UPDATE p2_singleton_puzzle_hash = %s, delay_time = %s, delay_puzzle_hash = %s, " \
              "authentication_public_key = %s, singleton_tip = %s, singleton_tip_state = %s, " \
              "points = %s, difficulty = %s, payout_instructions = %s, is_pool_member = %s"
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
            int(farmer_record.is_pool_member,),

            farmer_record.p2_singleton_puzzle_hash.hex(),
            farmer_record.delay_time,
            farmer_record.delay_puzzle_hash.hex(),
            bytes(farmer_record.authentication_public_key).hex(),
            bytes(farmer_record.singleton_tip),
            bytes(farmer_record.singleton_tip_state),
            farmer_record.points,
            farmer_record.difficulty,
            farmer_record.payout_instructions,
            int(farmer_record.is_pool_member, ),
        )
        count = self.wrap.insertOne(sql, param)
        return count

    # for test
    def add_farmer_record1(self, sql ,param) -> int:
        count = self.wrap.insertOne(sql, param)
        return count

    # 只读，会用到
    async def get_farmer_record(self, launcher_id: bytes32) -> Optional[FarmerRecord]:
        sql = "SELECT * from farmer where launcher_id=%s"
        param = (launcher_id.hex(),)
        res = self.wrap.select(sql, param, True)
        if res is None:
            return None
        return self._row_to_farmer_record(res)

    # 更新难度，暂时放到这，更新的不会太频繁
    async def update_difficulty(self, launcher_id: bytes32, difficulty: uint64) -> int:
        sql = "UPDATE farmer SET difficulty=%s WHERE launcher_id=%s"
        param = (difficulty, launcher_id.hex())
        count = self.wrap.update(sql, param)
        return count

    # 扔给kafka
    async def update_singleton(
            self,
            launcher_id: bytes32,
            singleton_tip: CoinSolution,
            singleton_tip_state: PoolState,
            is_pool_member: bool,
    ) -> int:
        if is_pool_member:
            entry = (bytes(singleton_tip), bytes(singleton_tip_state), 1, launcher_id.hex())
        else:
            entry = (bytes(singleton_tip), bytes(singleton_tip_state), 0, launcher_id.hex())
        sql = "UPDATE farmer SET singleton_tip=%s, singleton_tip_state=%s, is_pool_member=%s WHERE launcher_id=%s"
        count = self.wrap.update(sql, entry)
        return count

    # 用不到了
    async def get_pay_to_singleton_phs(self) -> Set[bytes32]:
        sql = "SELECT p2_singleton_puzzle_hash from farmer"
        rows = self.wrap.select(sql, None, True)

        all_phs: Set[bytes32] = set()
        for row in rows:
            all_phs.add(bytes32(bytes.fromhex(row[0])))
        return all_phs

    # 用不到了
    async def get_farmer_records_for_p2_singleton_phs(self, puzzle_hashes: Set[bytes32]) -> List[FarmerRecord]:
        if len(puzzle_hashes) == 0:
            return []
        puzzle_hashes_db = tuple([ph.hex() for ph in list(puzzle_hashes)])
        sql = "SELECT * from farmer WHERE p2_singleton_puzzle_hash in ({})".format(
            ','.join(["'%s'" % item for item in puzzle_hashes_db]))
        rows = self.wrap.select(sql, None, True)
        return [self._row_to_farmer_record(row) for row in rows]

    # 用不到
    async def get_farmer_points_and_payout_instructions(self) -> List[Tuple[uint64, bytes]]:
        sql = "SELECT points, payout_instructions from farmer"
        rows = self.wrap.select(sql, None, True)
        accumulated: Dict[bytes32, uint64] = {}
        for row in rows:
            points: uint64 = uint64(row[0])
            ph: bytes32 = bytes32(bytes.fromhex(row[1]))
            if ph in accumulated:
                accumulated[ph] += points
            else:
                accumulated[ph] = points

        ret: List[Tuple[uint64, bytes32]] = []
        for ph, total_points in accumulated.items():
            ret.append((total_points, ph))
        return ret

    # 用不到
    async def clear_farmer_points(self) -> int:
        sql = "UPDATE farmer set points=0"
        return self.wrap.update(sql)

    # 如果放到内存里，则不需要
    async def add_partial(self, launcher_id: bytes32, timestamp: uint64, difficulty: uint64):
        cursor, conn = self.wrap.getConn()
        try:
            conn.autocommit(0)
            sql = "INSERT into partial VALUES(%s, %s, %s)"
            param = (launcher_id.hex(), timestamp, difficulty)
            cursor.execute(sql, param)

            sql1 = "SELECT points from farmer where launcher_id=%s"
            param1 = (launcher_id.hex(),)
            cursor.execute(sql1, param1)
            row = cursor.fetchone()
            points = row[0]

            sql2 = "UPDATE farmer set points=%s where launcher_id=%s"
            param2 = (points + difficulty, launcher_id.hex())
            cursor.execute(sql2, param2)
            conn.commit()
            self.wrap.close(cursor, conn)
        except Exception as e:
            print(e)
            conn.rollback()
            self.wrap.close(cursor, conn)

    # 如果放到内存里则不需要
    async def get_recent_partials(self, launcher_id: bytes32, count: int) -> List[Tuple[uint64, uint64]]:
        sql = "SELECT timestamp, difficulty from partial WHERE launcher_id=%s ORDER BY timestamp DESC LIMIT %s"
        param = (launcher_id.hex(), count)
        rows = self.wrap.select(sql, param, True)
        ret: List[Tuple[uint64, uint64]] = [(uint64(timestamp), uint64(difficulty)) for timestamp, difficulty in rows]
        return ret

