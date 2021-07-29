import unittest
import time
from chia.util.ints import uint8, uint16, uint32, uint64, int64
from kafka import KafkaProducer
from pool.proto.chia_pb2 import ShareMsg


class TestSendShare(unittest.TestCase):
    def test_sendshare(self):
        kafka_producer = KafkaProducer(bootstrap_servers="127.0.0.1:9092")
        msg = ShareMsg()
        msg.launcherid = "e090d5fd3ef9067b1002f85ff8922469bc788b8cb09d32eac385d8bc57741888"
        for i in range(10, 100):
            msg.points = i
            msg.timestamp = uint64(int(time.time()))
            str = msg.SerializeToString()
            print(str)
            kafka_producer.send("share_chia", str)

if __name__ == "__main__":
    unittest.main()