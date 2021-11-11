import gzip
import json
import numpy as np
import pandas as pd

class GazeCsv:
    def __init__(self):
        self.gaze_columns = [
            'type',
            'timestamp',
            'gaze2d_x',
            'gaze2d_y',
            'gaze3d_x',
            'gaze3d_y',
            'gaze3d_z',
            'l_gazeorigin_x',
            'l_gazeorigin_y',
            'l_gazeorigin_z',
            'l_gazediretion_x',
            'l_gazediretion_y',
            'l_gazediretion_z',
            'l_pupildiameter',
            'r_gazeorigin_x',
            'r_gazeorigin_y',
            'r_gazeorigin_z',
            'r_gazediretion_x',
            'r_gazediretion_y',
            'r_gazediretion_z',
            'r_pupildiameter',
        ]

        self.imu_columns = [
            "type",
            "timestamp",
            "accel_x",
            "accel_y",
            "accel_z",
            "gyro_x",
            "gyro_y",
            "gyro_z",
        ]

    def __return_gaze(self, json_frame):
        if len(json_frame['data']) == 0:
            gaze2d_x = np.nan
            gaze2d_y = np.nan
            gaze3d_x = np.nan
            gaze3d_y = np.nan
            gaze3d_z = np.nan
            l_origin_x = np.nan
            l_origin_y = np.nan
            l_origin_z = np.nan
            l_direction_x = np.nan
            l_direction_y = np.nan
            l_direction_z = np.nan
            l_pupildiameter = np.nan
            r_origin_x = np.nan
            r_origin_y = np.nan
            r_origin_z = np.nan
            r_direction_x = np.nan
            r_direction_y = np.nan
            r_direction_z = np.nan
            r_pupildiameter = np.nan

        else:
            if len(json_frame['data']['gaze2d']) == 0:
                gaze2d_x = np.nan
                gaze2d_y = np.nan
            else:
                gaze2d_x = json_frame['data']['gaze2d'][0]
                gaze2d_y = json_frame['data']['gaze2d'][1]

            if len(json_frame['data']['gaze3d']) == 0:
                gaze3d_x = np.nan
                gaze3d_y = np.nan
                gaze3d_z = np.nan
            else:
                gaze3d_x = json_frame['data']['gaze3d'][0]
                gaze3d_y = json_frame['data']['gaze3d'][1]
                gaze3d_z = json_frame['data']['gaze3d'][2]

            if len(json_frame['data']['eyeleft']) == 0:
                l_origin_x = np.nan
                l_origin_y = np.nan
                l_origin_z = np.nan
                l_direction_x = np.nan
                l_direction_y = np.nan
                l_direction_z = np.nan
                l_pupildiameter = np.nan
            else:
                l_origin_x = json_frame['data']['eyeleft']['gazeorigin'][0]
                l_origin_y = json_frame['data']['eyeleft']['gazeorigin'][1]
                l_origin_z = json_frame['data']['eyeleft']['gazeorigin'][2]
                l_direction_x = json_frame['data']['eyeleft']['gazedirection'][0]
                l_direction_y = json_frame['data']['eyeleft']['gazedirection'][1]
                l_direction_z = json_frame['data']['eyeleft']['gazedirection'][2]
                l_pupildiameter = json_frame['data']['eyeleft']['pupildiameter']

            if len(json_frame['data']['eyeright']) == 0:
                r_origin_x = np.nan
                r_origin_y = np.nan
                r_origin_z = np.nan
                r_direction_x = np.nan
                r_direction_y = np.nan
                r_direction_z = np.nan
                r_pupildiameter = np.nan
            else:
                r_origin_x = json_frame['data']['eyeright']['gazeorigin'][0]
                r_origin_y = json_frame['data']['eyeright']['gazeorigin'][1]
                r_origin_z = json_frame['data']['eyeright']['gazeorigin'][2]
                r_direction_x = json_frame['data']['eyeright']['gazedirection'][0]
                r_direction_y = json_frame['data']['eyeright']['gazedirection'][1]
                r_direction_z = json_frame['data']['eyeright']['gazedirection'][2]
                r_pupildiameter = json_frame['data']['eyeright']['pupildiameter']

        _gaze = [
            json_frame['type'],
            json_frame['timestamp'],
            gaze2d_x,
            gaze2d_y,
            gaze3d_x,
            gaze3d_y,
            gaze3d_z,
            l_origin_x,
            l_origin_y,
            l_origin_z,
            l_direction_x,
            l_direction_y,
            l_direction_z,
            l_pupildiameter,
            r_origin_x,
            r_origin_y,
            r_origin_z,
            r_direction_x,
            r_direction_y,
            r_direction_z,
            r_pupildiameter
        ]

        return _gaze

    def gaze_json_to_pd(self, input_path, output_path=None):
        with gzip.open(input_path, mode="rt", encoding='utf-8') as f:
            gaze = f.read()

        gaze_tuple = gaze.split("\n")

        df = pd.DataFrame(columns=self.gaze_columns)

        for i in range(len(gaze_tuple) - 2):  # 最後の2要素は関係ない文字列
            json_frame = json.loads(gaze_tuple[i])
            new_list = self.__return_gaze(json_frame)
            new_pd = pd.DataFrame(data=np.array(new_list).reshape(1, -1), columns=self.gaze_columns)
            df = pd.concat([df, new_pd])

        if output_path is not None:
            df.to_csv(output_path)

        return df

    def __return_imu(self, json_frame):
        if len(json_frame['data']) == 0:
            accel_x = np.nan
            accel_y = np.nan
            accel_z = np.nan
            gyro_x = np.nan
            gyro_y = np.nan
            gyro_z = np.nan
        else:
            if len(json_frame['data']) == 2:
                if len(json_frame['data'][list(json_frame['data'].keys())[0]]) == 0:
                    accel_x = np.nan
                    accel_y = np.nan
                    accel_z = np.nan
                else:
                    accel_x = json_frame['data'][list(json_frame['data'].keys())[0]][0]
                    accel_y = json_frame['data'][list(json_frame['data'].keys())[0]][1]
                    accel_z = json_frame['data'][list(json_frame['data'].keys())[0]][2]

                if len(json_frame['data'][list(json_frame['data'].keys())[1]]) == 0:
                    gyro_x = np.nan
                    gyro_y = np.nan
                    gyro_z = np.nan
                else:
                    gyro_x = json_frame['data'][list(json_frame['data'].keys())[1]][0]
                    gyro_y = json_frame['data'][list(json_frame['data'].keys())[1]][1]
                    gyro_z = json_frame['data'][list(json_frame['data'].keys())[1]][2]
            else:
                accel_x = np.nan
                accel_y = np.nan
                accel_z = np.nan
                gyro_x = np.nan
                gyro_y = np.nan
                gyro_z = np.nan

        _imu = [
            json_frame['type'],
            json_frame['timestamp'],
            accel_x,
            accel_y,
            accel_z,
            gyro_x,
            gyro_y,
            gyro_z,
        ]

        return _imu

    def imu_json_to_pd(self, input_path, output_path=None):
        with gzip.open(input_path, mode="rt", encoding='utf-8') as f:
            imu = f.read()

        imu_tuple = imu.split("\n")

        df = pd.DataFrame(columns=self.imu_columns)

        for i in range(len(imu_tuple) - 2):  # 最後の2要素は関係ない文字列
            json_frame = json.loads(imu_tuple[i])
            new_list = self.__return_imu(json_frame)
            new_pd = pd.DataFrame(data=np.array(new_list).reshape(1, -1), columns=self.imu_columns)
            df = pd.concat([df, new_pd])

        if output_path is not None:
            df.to_csv(output_path)

        return df
