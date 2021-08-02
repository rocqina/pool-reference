import unittest
import os, yaml
from typing import Dict, Optional, Set, List, Tuple, Callable



class TestConfig(unittest.TestCase):
    def test_config(self):
        with open(os.getcwd() + "/../config-example.yaml") as f:
            pool_config: Dict = yaml.safe_load(f)

        print(pool_config["server"]["server_host"])
        print(int(pool_config["server"]["server_port"]))
        dev_mode = pool_config["dev_mode"]
        print(dev_mode)
        if dev_mode:
            print("dev mode is true")
        else:
            print("dev mode is false")

    def test_json(self):
        # import requests module
        import requests

        # Making a get request
        response = requests.get('https://api.github.com')

        # print response
        print(response)

        # print json content
        print(response.json())


if __name__ == "__main__":
    unittest.main()
