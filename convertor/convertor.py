import cv2
import math
import numpy as np
import pandas as pd
from moviepy.editor import *
from scipy import interpolate
from scipy.signal import decimate
from scipy.signal import resample
from datetime import datetime, timedelta


class Convertor:
    def __init__(self, mp4_input_path, csv_input_path, attention_input_path):
        self.mp4_input_path = mp4_input_path
        self.csv_input_path = csv_input_path
        self.attention_input_path = attention_input_path

        self.cap = cv2.VideoCapture(self.mp4_input_path)
        self.eeg = pd.read_csv(self.csv_input_path)
        # self.eeg = self.eeg.rename(columns={self.eeg.columns[0]: "title"})
        # self.eeg = self.eeg.rename(columns={self.eeg.columns[2]: "sampling"})
        self.columns = self.eeg.columns
        print("1:"+str(self.eeg.shape[0]))

        self.attention_csv = pd.read_csv(attention_input_path)
        print('a' + str(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)))
        print('b' + str(self.attention_csv.shape[0]))

        self.video = VideoFileClip(self.mp4_input_path).set_fps(50)

        # 時刻取得のためのpathの加工
        # mp4
        v_time = self.mp4_input_path.split('/')[-2]
        v_time = [
            int(v_time.split('.')[0]),
            int(v_time.split('.')[1]),
            int(v_time.split('.')[2]),
            int(v_time.split('.')[3]),
            int(v_time.split('.')[4]),
            int(v_time.split('.')[5]),
            int(v_time.split('.')[6]),
        ]
        print(v_time)
        # 脳波のファイル名
        e_file = self.csv_input_path.split('/')[-1]
        #　脳波(配列)
        e_time = [
            int(e_file.split('.')[0].split('_')[-1]),
            int(e_file.split('.')[1]),
            int(e_file.split('.')[2].split('T')[0]),
            int(e_file.split('.')[2].split('T')[1]),
            int(e_file.split('.')[3]),
            int(e_file.split('.')[4]),
            int(e_file.split('.')[5].split('+')[0])
        ]
        print(e_time)

        self.total_video_frame = self.video.reader.nframes
        self.video_play_time = self.video.duration
        self.video_fps = self.attention_csv.shape[0] / (self.video_play_time + 1)
        print('ancfdjaljf')
        print(self.video_fps)
        self.video_start_time = datetime(v_time[0], v_time[1], v_time[2], v_time[3], v_time[4], v_time[5], v_time[6])
        self.video_end_time = self.video_start_time + timedelta(seconds=self.video_play_time)

        # EEGデータのパラメータ
        self.total_eeg_frame = self.eeg.shape[0]
        self.eeg_fps = 128
        self.eeg_play_time = self.total_eeg_frame / self.eeg_fps
        self.eeg_start_time = datetime(e_time[0], e_time[1], e_time[2], e_time[3], e_time[4], e_time[5], e_time[6])
        self.eeg_end_time = self.eeg_start_time + timedelta(seconds=self.eeg_play_time)

        # お互いのサンプリングレートの最小公倍数
        self.common_multiple = np.lcm(int(self.video_fps), int(self.eeg_fps))#int(self.video_fps * self.eeg_fps / math.gcd(int(self.video_fps), int(self.eeg_fps)))

    def fit_length(self, data, mp4_output_path):

        self.eeg = data

        # 動画データとEEGデータのサンプリング開始,終了時間の差
        cap_start_diff = float(
            (max(self.video_start_time, self.eeg_start_time) - min(self.video_start_time,
                                                                   self.eeg_start_time)).total_seconds())
        cap_end_diff = float(
            (abs(min(self.video_end_time, self.eeg_end_time)-max(self.video_end_time, self.eeg_end_time))).total_seconds())

        print('cap_start_diff'+str(cap_start_diff))
        print('cap_end_diff'+str(cap_end_diff))
        print('total_range'+str(abs(self.video_play_time-self.eeg_play_time)))

        # サンプリング開始,終了時間を合わせる
        if self.video_start_time <= self.eeg_start_time:
            if self.video_end_time <= self.eeg_end_time:  # case1
                print('start:eeg long end:eeg long')
                # ビデオのカット
                self.video = self.video.subclip(cap_start_diff)
                self.video.write_videofile(mp4_output_path, codec='libx264')
                self.attention_csv = self.attention_csv.iloc[int(self.video_fps*cap_start_diff):, :]
                # EEGデータのカット
                self.eeg = self.eeg.iloc[0:int(self.total_eeg_frame - self.eeg_fps * cap_end_diff), :]
            elif self.video_end_time > self.eeg_end_time:  # case2
                print('start:eeg long end:video long')
                # 動画データのカットのみで良い
                self.video = self.video.subclip(cap_start_diff, self.video_play_time - cap_end_diff)
                self.video.write_videofile(mp4_output_path, codec='libx264')
                self.attention_csv = self.attention_csv.iloc[int(self.video_fps*cap_start_diff):-int(self.video_fps*cap_end_diff), :]

        elif self.video_start_time > self.eeg_start_time:
            if self.video_end_time <= self.eeg_end_time:  # case3
                # EEGデータのカットのみで良い
                print('start:video long end:eeg long')
                self.eeg = self.eeg.iloc[int(self.eeg_fps*cap_start_diff):int(self.total_eeg_frame - self.eeg_fps * cap_end_diff), :]
            elif self.video_end_time > self.eeg_end_time:  # case4
                print('start:video long end:video long')
                self.video = self.video.subclip(0, self.video_play_time - cap_end_diff)
                self.video.write_videofile(mp4_output_path, codec='libx264')
                self.attention_csv = self.attention_csv.iloc[:-int(self.video_fps*cap_end_diff)]
                self.eeg = self.eeg.iloc[int(self.eeg_fps*cap_start_diff):, :]

        #self.eeg.to_csv(csv_output_path, index=False)

        tv = cv2.VideoCapture(mp4_output_path)
        self.total_video_frame = tv.get(cv2.CAP_PROP_FRAME_COUNT)
        self.video_play_time = self.video.duration

        # EEGデータのパラメータの更新
        self.total_eeg_frame = self.eeg.shape[0]
        self.eeg_play_time = self.total_eeg_frame / self.eeg_fps
        print('2:'+str(self.eeg.shape[0]))

        return self.eeg

    def fit_sampling_rate(self, data, csv_output_path=None):
        self.eeg = data
        up_data = pd.DataFrame()

        for i in range(self.eeg.shape[1]):
            up_data[self.columns[i]] = resample(self.eeg.iloc[:,i], int(25*self.eeg.shape[0]))

        print("up_data.shape"+str(up_data.shape[0]))

        down_data = pd.DataFrame()
        for i in range(up_data.shape[1]):
            down_data[self.columns[i]] = resample(up_data.iloc[:,i], int(up_data.shape[0] * (50/3200)))

        print('down_data.shape'+str(down_data.shape[0]))

        if csv_output_path is not None:
            self.attention_csv = self.attention_csv.reset_index(drop=True)
            down_data = down_data.reset_index(drop=True)
            down_data = pd.concat([self.attention_csv, down_data], axis=1)
            down_data.to_csv(csv_output_path, index=False)

        print("total_video_frame" + str(self.total_video_frame))
        print("total_attention_frame" + str(self.attention_csv.shape[0]))
        print("total_eeg_frame" + str(self.total_eeg_frame))

        return down_data
