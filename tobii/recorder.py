import requests
import json
import datetime


class Recorder:
    """
    録画中(前後)の動作を制御するクラス
    """
    def __init__(self, ipv4_address):
        self.ipv4_address = ipv4_address
        self.default = "http://" + ipv4_address + "/rest/"

    def start(self):
        """
        :return: if failed recording return statoment of error
        """
        return requests.post(self.default+"recorder!start", data='[]')

    def stop(self):
        """
        レコーディングの停止
        """
        requests.post(self.default + "recorder!stop", data='[]')

    def snapshot(self):
        """
        スクショ
        """
        requests.post(self.default + "recorder!snapshot", data='[]')

    def gaze_frequency(self):
        """
        :return: 現在のサンプリングレート
        """
        return requests.get(self.default+"recorder.current-gaze-frequency").json()

    def current_folder_name(self):
        """
        :return: 録画中のデータのフォルダ名
        """
        return requests.get(self.default+"recorder.folder").json()

    def gaze_sampling_number(self):
        """
        :return: 視線データのサンプル数
        """
        return requests.get(self.default + "recorder.gaze-samples").json()

    def rest_time(self):
        """
        :return: 録画残り時間
        """
        return requests.get(self.default + "recorder.remaining-time").json()

    def total_time(self):
        """
        :return: 現在の録画時間
        """
        return requests.get(self.default + "recorder.duration").json()

    def uuid(self):
        """
        :return: 録画中の動画のuuid
        """
        return requests.get(self.default+"recorder.uuid").json()

    def valid_gaze_sample(self):
        """
        :return: 有効な視線データの数
        """
        return requests.get(self.default+"recorder.valid-gaze-samples").json()

    def stating_time(self):
        """
        tobiiのシステム時間ベースなのでズレがひどい
        :return: 録画開始時間を返す
        """
        return requests.get(self.default+"recorder.created").json()

    def set_folder_name(self):
        time = datetime.datetime.now()

        folder_name = str(
            str(time.year) + "." +
            str(time.month) + "." +
            str(time.day) + "." +
            str(time.hour) + "." +
            str(time.minute) + "." +
            str(time.second)
        )

        requests.post(url=self.default+"recorder.folder", data="'" + str(folder_name) + "'")

    def set_gaze_frequency(self, frequency=50):
        requests.post(self.default + "settings.gaze-frequency", data=str(frequency))
        requests.post(self.default + "settings.gaze-overlay", data="true")
