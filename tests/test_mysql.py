import unittest
from pool.store.mysql_store import MysqlPoolStore
from pool.record import FarmerRecord
from blspy import AugSchemeMPL, G1Element
from chia.pools.pool_wallet_info import PoolState
from chia.types.coin_solution import CoinSolution


class TestMysql(unittest.TestCase):

    def test_add_farmer(self):
        db = MysqlPoolStore()
        sql = "INSERT INTO farmer VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY " \
              "UPDATE p2_singleton_puzzle_hash = %s, delay_time = %s, delay_puzzle_hash = %s, " \
              "authentication_public_key = %s, singleton_tip = %s, singleton_tip_state = %s, " \
              "points = %s, difficulty = %s, payout_instructions = %s, is_pool_member = %s"

        param = (
            "1234",
            "5678",
            10002,
            "9876",
            'aaaaaa',
            "bbbbbb",
            "cccccc",
            100,
            2,
            "dddddd",
            True,
            "5678",
            10002,
            "9876",
            'aaaaaa',
            "bbbbbb",
            "cccccc",
            100,
            2,
            "dddddd",
            True,
        )
        count = db.add_farmer_record1(sql, param)
        print(count)

        param2 = (
            "1238",
            "5678",
            100,
            "9876",
            'aaaaaa',
            "bbbbbb",
            "cccccc",
            100,
            2,
            "dddddd",
            True,
            "5678",
            100,
            "9876",
            'aaaaaa',
            "bbbbbb",
            "cccccc",
            100,
            2,
            "dddddd",
            True,
        )

        count = db.add_farmer_record1(sql, param2)
        print(count)


if __name__ == "__main__":
    unittest.main()
