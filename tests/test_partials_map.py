import unittest
import time
from typing import Dict, Optional, Set, List, Tuple, Callable

from chia.types.blockchain_format.sized_bytes import bytes32
from chia.util.ints import uint8, uint16, uint32, uint64, int64
from pool.difficulty_adjustment import get_new_difficulty

partial_map = {}


def add_partial(launcher_id, timestamp, points):
    val = (timestamp, points)
    if partial_map.get(launcher_id) is None:
        #print("partial_map can not find launcher_id:%s", launcher_id)
        partial_list = [val]
        partial_map[launcher_id] = partial_list
    else:
        #print("partial_map find launcher_id:%s", launcher_id)
        partial_list = partial_map[launcher_id]
        partial_list.append(val)
        if len(partial_list) > 300:
            partial_list.pop(0)


def get_recent_partials(launcher_id: bytes32, count: int) -> List[Tuple[uint64, uint64]]:
    if partial_map.get(launcher_id) is None:
        return []
    else:
        ret: List[Tuple[uint64, uint64]] = [(uint64(timestamp), uint64(difficulty)) for timestamp, difficulty in
                                            partial_map.get(launcher_id)]
        return ret[:count]


class TestPartialsMap(unittest.TestCase):
    """
    def test_add_partials(self):
        now = time.time()
        launcher_id = bytes.fromhex("e090d5fd3ef9067b1002f85ff8922469bc788b8cb09d32eac385d8bc57741777")
        for i in range(1, 10):
            add_partial(launcher_id, now, i)

        print(partial_map)

        print("=================================")
        res = get_recent_partials(launcher_id)
        print(res)

    def test_partials_low_24h_decreases_diff(self):
        num_partials = 150
        time_target = 24 * 3600
        partials = []
        current_time = uint64(time.time())
        launcher_id = bytes.fromhex("e090d5fd3ef9067b1002f85ff8922469bc788b8cb09d32eac385d8bc57741777")
        for i in range(num_partials):
            add_partial(launcher_id, uint64(current_time - (i) * 600), 20)

        partials = get_recent_partials(launcher_id, num_partials)
        assert get_new_difficulty(partials, num_partials * 2, time_target, 20, current_time, 1) != 9

    """
    def test_decreases_diff(self):
        num_partials = 300
        time_target = 24 * 3600
        current_time = uint64(time.time())
        launcher_id = bytes.fromhex("e090d5fd3ef9067b1002f85ff8922469bc788b8cb09d32eac385d8bc57741777")
        for i in range(num_partials):
            add_partial(launcher_id, uint64(current_time - (i) * 380), 20)

        partials = get_recent_partials(launcher_id, num_partials)
        assert get_new_difficulty(partials, num_partials, time_target, 20, current_time, 1) == 15


if __name__ == "__main__":
    unittest.main()
