import unittest
import time
from pool.proto.farmer_pb2 import FarmerMsg



class TestProtobuf(unittest.TestCase):
    def test_sendproto(self):
        msg = FarmerMsg()
        msg.launcherid = "5ec4f8db24bff68a85cfa9bd86ce7bd23bcb33b823b56bd393355053d5bfe5a2"
        msg.singletonpuzzlehash = "9a4d2686cf883b7c43df3fe31c3615bd7c3abcb9d7bb2d97a4f5d6221f6a7964"
        msg.delaytime = 604800
        msg.delaypuzzlehash = "f9a4689bba2b20f2709e969af2049995228ac5ed5db3a2fff530fc6533335c19"
        msg.authenticationpublickey = bytes("1234".encode('utf-8'))
        msg.singletontip = bytes("5678".encode('utf-8'))
        msg.singletontipstate = bytes("9876".encode('utf-8'))
        msg.points = 10000000
        msg.difficulty = 604800
        msg.payoutinstructions = "0e62c7ada08746c2eb5841d6041e79c9cbe8a0c1410e9e2005883567727b63db"
        msg.ispoolmember = True
        msg.timestamp = int(time.time())
        msg.flag = 1

        print(msg.difficulty)

    def test_proto_encode_decode(self):
        msg = FarmerMsg()
        msg.launcherid = "5ec4f8db24bff68a85cfa9bd86ce7bd23bcb33b823b56bd393355053d5bfe5a2"
        msg.difficulty = 10
        str = msg.SerializeToString()
        new_msg = FarmerMsg()
        new_msg.ParseFromString(str)
        print(new_msg.difficulty)


if __name__ == "__main__":
    unittest.main()
