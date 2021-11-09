import requests
import json


class Calibrate:
    def __init__(self, ipv4_address):
        self.ipv4_address = ipv4_address
        self.default = "http://" + ipv4_address + "/rest/"

    def test_calibrate(self, n):
        """
        n個のcalibrationデータの取得 ※確認 positionデータを返してくれる
        :return [time, x, y]
        """
        requests.post(self.default + "calibrate!emit-markers", data='[]')
        for i in range(n):
            return requests.post(self.default + "calibrate:marker", data="").json()

    def calibrate(self):
        """
        calibration
        :return true or false:
        """
        return requests.post(self.default + "calibrate!run", data='[]').text
