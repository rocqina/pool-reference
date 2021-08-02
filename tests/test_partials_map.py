import unittest
import time, json
from typing import Dict, Optional, Set, List, Tuple, Callable

from chia.types.blockchain_format.sized_bytes import bytes32
from chia.util.ints import uint8, uint16, uint32, uint64, int64
from pool.difficulty_adjustment import get_new_difficulty

from chia.protocols.pool_protocol import (
    PostPartialRequest,
)

partial_map = {}


def add_partial(launcher_id, timestamp, points):
    val = (timestamp, points)
    if partial_map.get(launcher_id) is None:
        # print("partial_map can not find launcher_id:%s", launcher_id)
        partial_list = [val]
        partial_map[launcher_id] = partial_list
    else:
        # print("partial_map find launcher_id:%s", launcher_id)
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
        reverse_res = ret[0 - count:]
        return reverse_res[::-1]


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
            add_partial(launcher_id, uint64(current_time + (i) * 380), 20)

        partials = get_recent_partials(launcher_id, num_partials)
        assert get_new_difficulty(partials, num_partials, time_target, 20, current_time, 1) == 15

    def test_simulate_partial(self):
        d = {
            'payload': {
                'launcher_id': '0xe090d5fd3ef9067b1002f85ff8922469bc788b8cb09d32eac385d8bc57741777',
                'authentication_token': 5426297,
                'proof_of_space': {
                    'challenge':'0x592c9406169f7844260cc722ee3905efda515284c3b03d4927d70f09f4349b29',
                    'pool_public_key': None,
                    'pool_contract_puzzle_hash': '0x486494c9357b384c8aef24e486b2e93113ce7234a8c445ce4e217a68ce049ae6',
                    'plot_public_key': '0x91c9863fde7544d604d37f41f05ad790148f331267a34f5a739e0372855003edf30c8bc70ae0d3a0a1ab3a3d0e6552c7',
                    'size': 32,
                    'proof': '0x4d11ee0d717a0eac443a31e827a6114393c2103cfd2681783b8ae66cd08c2e830137356649c55d0c0f1ff46017e24982de0dc42c115b1b495035a4f93fcd619fb7c609f01269d912c3d1ceeea85966c24842f8835f47dc23f1c54ab55855c33bcbe7d1713a0aa08bf2e80512f8bffceed3caf852303cff00d6e77c2e23b57acf21e2fe627282e532dc000aee4b99e65699b4acfad1bc2c5721d7a3c4573b6a2b3fef20438c5802756f4b5bff9ae554fd2f7eb6c7a2edad4260206c43aedd6124ccf187e371d7c155a3dc507d6dd60c6db99b401dcf908f1f9846c4d3b12d5b28fe950bfe0a61e76fc7692f02d93c879af7ab8772a7957baf024467ef7a539096'
                },
                'sp_hash':'0x16ed0a19832f25c494049d34286e574c1f8e4d5c75a57367c3d29adfe92321e5',
                'end_of_sub_slot': False,
                'harvester_id': '0x3d295ae210482f107fb50c96b4e1306645fafb4fce115f22fffdf5a03271b3ef'
            },
            'aggregate_signature': '0x87caff94d8f2d5bb9fa21d13034cb54285ef57e7901c2c23f702373011c9df10157f6b6febc4566dccfde83b4b10e1800a23e79cb465013a40901f54e94d9b349e0a747d1887d7d98706e8078f46a03426069dd24efbe188b05cf225295f3de9'
        }
        str = json.dumps(d)
        print(str)

        """
        request = "{'payload': {'launcher_id': '0xe090d5fd3ef9067b1002f85ff8922469bc788b8cb09d32eac385d8bc57741777', " \
                  "'authentication_token': 5426297, 'proof_of_space': {'challenge': " \
                  "'0x592c9406169f7844260cc722ee3905efda515284c3b03d4927d70f09f4349b29','pool_public_key': None," \
                  "'pool_contract_puzzle_hash': '0x486494c9357b384c8aef24e486b2e93113ce7234a8c445ce4e217a68ce049ae6'," \
                  "'plot_public_key': " \
                  "'0x91c9863fde7544d604d37f41f05ad790148f331267a34f5a739e0372855003edf30c8bc70ae0d3a0a1ab3a3d0e6552" \
                  "c7','size': 32,'proof': " \
                  "'0x4d11ee0d717a0eac443a31e827a6114393c2103cfd2681783b8ae66cd08c2e830137356649c55d0c0f1ff46017e2498" \
                  "2de0dc42c115b1b495035a4f93fcd619fb7c609f01269d912c3d1ceeea85966c24842f8835f47dc23f1c54ab55855c33bc" \
                  "be7d1713a0aa08bf2e80512f8bffceed3caf852303cff00d6e77c2e23b57acf21e2fe627282e532dc000aee4b99e65699b" \
                  "4acfad1bc2c5721d7a3c4573b6a2b3fef20438c5802756f4b5bff9ae554fd2f7eb6c7a2edad4260206c43aedd6124ccf18" \
                  "7e371d7c155a3dc507d6dd60c6db99b401dcf908f1f9846c4d3b12d5b28fe950bfe0a61e76fc7692f02d93c879af7ab877" \
                  "2a7957baf024467ef7a539096'},'sp_hash': " \
                  "'0x16ed0a19832f25c494049d34286e574c1f8e4d5c75a57367c3d29adfe92321e5','end_of_sub_slot': False," \
                  "'harvester_id': '0x3d295ae210482f107fb50c96b4e1306645fafb4fce115f22fffdf5a03271b3ef'}," \
                  "'aggregate_signature': " \
                  "'0x87caff94d8f2d5bb9fa21d13034cb54285ef57e7901c2c23f702373011c9df10157f6b6febc4566dccfde83b4b10e18" \
                  "00a23e79cb465013a40901f54e94d9b349e0a747d1887d7d98706e8078f46a03426069dd24efbe188b05cf225295f3de9'} "

        """
        request = "{\"payload\": {\"launcher_id\": \"0xe090d5fd3ef9067b1002f85ff8922469bc788b8cb09d32eac385d8bc57741777\", \"authentication_token\": 5426297, \"proof_of_space\": {\"challenge\": \"0x592c9406169f7844260cc722ee3905efda515284c3b03d4927d70f09f4349b29\", \"pool_public_key\": null, \"pool_contract_puzzle_hash\": \"0x486494c9357b384c8aef24e486b2e93113ce7234a8c445ce4e217a68ce049ae6\", \"plot_public_key\": \"0x91c9863fde7544d604d37f41f05ad790148f331267a34f5a739e0372855003edf30c8bc70ae0d3a0a1ab3a3d0e6552c7\", \"size\": 32, \"proof\": \"0x4d11ee0d717a0eac443a31e827a6114393c2103cfd2681783b8ae66cd08c2e830137356649c55d0c0f1ff46017e24982de0dc42c115b1b495035a4f93fcd619fb7c609f01269d912c3d1ceeea85966c24842f8835f47dc23f1c54ab55855c33bcbe7d1713a0aa08bf2e80512f8bffceed3caf852303cff00d6e77c2e23b57acf21e2fe627282e532dc000aee4b99e65699b4acfad1bc2c5721d7a3c4573b6a2b3fef20438c5802756f4b5bff9ae554fd2f7eb6c7a2edad4260206c43aedd6124ccf187e371d7c155a3dc507d6dd60c6db99b401dcf908f1f9846c4d3b12d5b28fe950bfe0a61e76fc7692f02d93c879af7ab8772a7957baf024467ef7a539096\"}, \"sp_hash\": \"0x16ed0a19832f25c494049d34286e574c1f8e4d5c75a57367c3d29adfe92321e5\", \"end_of_sub_slot\": false, \"harvester_id\": \"0x3d295ae210482f107fb50c96b4e1306645fafb4fce115f22fffdf5a03271b3ef\"}, \"aggregate_signature\": \"0x87caff94d8f2d5bb9fa21d13034cb54285ef57e7901c2c23f702373011c9df10157f6b6febc4566dccfde83b4b10e1800a23e79cb465013a40901f54e94d9b349e0a747d1887d7d98706e8078f46a03426069dd24efbe188b05cf225295f3de9\"}"
        data = json.loads(request)
        partial: PostPartialRequest = PostPartialRequest.from_json_dict(data)
        print(f"post_partial launcher_id: {partial.payload.launcher_id.hex()}")


if __name__ == "__main__":
    unittest.main()
