import requests
import json


class Settings:
    def __init__(self, ipv4_address):
        self.ipv4_address = ipv4_address
        self.default = "http://" + ipv4_address + "/rest/"

    def rest_battery(self):
        """
        :return: 残りのバッテリーの残量
        """
        return requests.get(self.default+"system/battery.remaining-time").text
