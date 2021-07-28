import unittest
import time
from typing import Dict, Optional, Set, List, Tuple, Callable
from pool.pool import Pool

from chia.util.config import load_config
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.util.ints import uint8, uint16, uint32, uint64, int64

partial_map = {}


def add_partial(launcher_id, timestamp, points):
    val = (timestamp, points)
    if partial_map.get(launcher_id) is None:
        print("partial_map can not find launcher_id:%s", launcher_id)
        partial_list = [val]
        partial_map[launcher_id] = partial_list
    else:
        print("partial_map find launcher_id:%s", launcher_id)
        partial_list = partial_map[launcher_id]
        partial_list.append(val)
        if len(partial_list) > 5:
            partial_list.pop(0)


def get_recent_partials(launcher_id: bytes32) -> List[Tuple[uint64, uint64]]:
    if partial_map.get(launcher_id) is None:
        return []
    else:
        ret: List[Tuple[uint64, uint64]] = [(uint64(timestamp), uint64(difficulty)) for timestamp, difficulty in
                                            partial_map.get(launcher_id)]
        return ret


class TestPartialsMap(unittest.TestCase):
    def test_add_partials(self):
        now = time.time()
        launcher_id = bytes.fromhex("e090d5fd3ef9067b1002f85ff8922469bc788b8cb09d32eac385d8bc57741777")
        for i in range(1, 10):
            add_partial(launcher_id, now, i)

        print(partial_map)

        print("=================================")
        res = get_recent_partials(launcher_id)
        print(res)


if __name__ == "__main__":
    unittest.main()
