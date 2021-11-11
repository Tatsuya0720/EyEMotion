import requests
import json


class Calibrate:
    def __init__(self, ipv4_address):
        self.ipv4_address = ipv4_address
        self.default = "http://" + ipv4_address + "/rest/"
        self.time = None
        self.x = None
        self.y = None

    def test_calibrate(self):
        """
        n個のcalibrationデータの取得 ※確認 positionデータを返してくれる
        :return [time, x, y]
        """
        requests.post(self.default + "calibrate!emit-markers", data='[]')
        _status = requests.post(self.default + "calibrate:marker", data="").json()
        self.time = _status[0]
        self.x = _status[1]
        self.y = _status[2]

    def calibrate(self):
        """
        calibration
        :return true or false:
        """
        return requests.post(self.default + "calibrate!run", data='[]').text
