import unittest
import time, json
from typing import Dict, Optional, Set, List, Tuple, Callable
from pool.store.mysql_store import MysqlPoolStore
from pool.record import FarmerRecord
from blspy import AugSchemeMPL, G1Element
from chia.pools.pool_wallet_info import PoolState
from chia.protocols.pool_protocol import (
    PostPartialRequest,
)


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

    def test_add_fake_data(self):
        db = MysqlPoolStore()
        lau_id = "e090d5fd3ef9067b1002f85ff8922469bc788b8cb09d32eac385d8bc57741777"
        farmer_record: Optional[FarmerRecord] = db.get_farmer_record(bytes.fromhex(lau_id))
        if farmer_record is None:
            print(f"Farmer with launcher_id {lau_id} unknown.")
        for i in range(100, 102):
            launcher_id = 'e090d5fd3ef9067b1002f85ff8922469bc788b8cb09d32eac385d8bc57741' + str(i)
            new_record = FarmerRecord(
                bytes.fromhex(launcher_id),
                farmer_record.p2_singleton_puzzle_hash,
                farmer_record.delay_time,
                farmer_record.delay_puzzle_hash,
                farmer_record.authentication_public_key,
                farmer_record.singleton_tip,
                farmer_record.singleton_tip_state,
                farmer_record.uint64(0),
                farmer_record.difficulty,
                farmer_record.payout_instructions,
                True,
            )
            db.add_farmer_record(new_record)
        print(f"create_table_dataes is finished!")

if __name__ == "__main__":
    unittest.main()
