import cv2
import math
import numpy as np
import pandas as pd
from moviepy.editor import *
from scipy import interpolate
from scipy.signal import decimate
from datetime import datetime, timedelta


class Convertor:
    def __init__(self, mp4_input_path, csv_input_path, attention_input_path):
        self.mp4_input_path = mp4_input_path
        self.csv_input_path = csv_input_path
        self.attention_input_path = attention_input_path

        self.cap = cv2.VideoCapture(self.mp4_input_path)
        self.eeg = pd.read_csv(self.csv_input_path)
        self.eeg = self.eeg.rename(columns={self.eeg.columns[0]: "title"})
        self.eeg = self.eeg.rename(columns={self.eeg.columns[2]: "sampling"})
        self.columns = self.eeg.columns

        self.attention_csv = pd.read_csv(attention_input_path)

        # 動画データのパラメータ
        self.total_video_frame = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
        self.video_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        self.video_play_time = self.total_video_frame / self.video_fps
        self.video_start_time = datetime(2021, 6, 21, 11, 37, 28)
        self.video_end_time = self.video_start_time + timedelta(seconds=self.video_play_time)

        # EEGデータのパラメータ
        self.total_eeg_frame = self.eeg.shape[0]
        self.eeg_fps = 128
        self.eeg_play_time = self.total_eeg_frame / self.eeg_fps
        self.eeg_start_time = datetime(2021, 6, 21, 11, 37, 30)
        self.eeg_end_time = self.eeg_start_time + timedelta(seconds=self.eeg_play_time)

        # お互いのサンプリングレートの最小公倍数
        self.common_multiple = int(self.video_fps * self.eeg_fps / math.gcd(int(self.video_fps), int(self.eeg_fps)))

    def fit_length(self, mp4_output_path, csv_output_path=None):

        # 動画データとEEGデータのサンプリング開始,終了時間の差
        cap_start_diff = float(
            (max(self.video_start_time, self.eeg_start_time) - min(self.video_start_time,
                                                                   self.eeg_start_time)).total_seconds())
        cap_end_diff = float(
            (max(self.video_end_time, self.eeg_end_time) - min(self.video_end_time, self.eeg_end_time)).total_seconds())

        # サンプリング開始,終了時間を合わせる
        if self.video_start_time <= self.eeg_start_time:
            if self.video_end_time <= self.eeg_end_time:  # case1
                # ビデオのカット
                video = VideoFileClip(self.mp4_input_path).subclip(cap_start_diff)
                video.write_videofile(mp4_output_path, codec='libx264')
                self.attention_csv = self.attention_csv.iloc[int(self.video_fps*cap_start_diff):]
                # EEGデータのカット
                self.eeg = self.eeg.iloc[0:int(self.total_eeg_frame - self.eeg_fps * cap_end_diff), :]
            elif self.video_end_time > self.eeg_end_time:  # case2
                # 動画データのカットのみで良い
                video = VideoFileClip(self.mp4_input_path).subclip(cap_start_diff,
                                                                   self.video_play_time - cap_end_diff)
                video.write_videofile(mp4_output_path, codec='libx264')
                self.attention_csv = self.attention_csv.iloc[int(self.video_fps*cap_start_diff):int(self.video_fps*cap_end_diff)]

        elif self.video_start_time > self.eeg_start_time:
            if self.video_end_time <= self.eeg_end_time:  # case3
                # EEGデータのカットのみで良い
                self.eeg = self.eeg.iloc[int(cap_start_diff):int(self.total_eeg_frame - self.eeg_fps * cap_end_diff), :]
            elif self.video_end_time > self.eeg_end_time:  # case4
                video = VideoFileClip(self.mp4_input_path).subclip(0, self.video_play_time - cap_end_diff)
                video.write_videofile(mp4_output_path, codec='libx264')
                self.attention_csv = self.attention_csv.iloc[:int(self.video_fps*cap_end_diff)]
                self.eeg = self.eeg.iloc[int(cap_start_diff):int(self.total_eeg_frame), :]

        if csv_output_path is not None:
            self.eeg.to_csv(csv_output_path, index=False)
        else:
            self.eeg.to_csv(self.csv_input_path, index=False)

        # 動画データのパラメータの更新
        self.cap = cv2.VideoCapture(mp4_output_path)
        self.total_video_frame = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
        self.video_play_time = self.total_video_frame / self.video_fps

        # EEGデータのパラメータの更新
        self.total_eeg_frame = self.eeg.shape[0]
        self.eeg_play_time = self.total_eeg_frame / self.eeg_fps

    def fit_sampling_rate(self, csv_output_path=None):
        x = np.linspace(0, self.eeg.shape[0], self.eeg.shape[0])
        up_data = pd.DataFrame()
        self.up_sampling_sr = float(self.eeg_fps / self.common_multiple)

        for i in range(self.eeg.shape[1]):
            f = interpolate.interp1d(x, self.eeg.iloc[:, i])
            rx = np.arange(np.min(x), np.max(x) + self.up_sampling_sr / 10, self.up_sampling_sr)
            ry_cubic = f(rx)
            # up_data["m" + str(i)] = ry_cubic
            up_data[self.columns[i]] = ry_cubic

        self.down_sampling_sr = int(self.common_multiple / self.video_fps)

        down_data = pd.DataFrame()
        for i in range(up_data.shape[1]):
            tmp = decimate(up_data.iloc[:, i], self.down_sampling_sr, axis=0)
            # down_data["m" + str(i)] = tmp
            down_data[self.columns[i]] = tmp

        # down_data["m0"] = np.linspace(0, down_data.shape[0], down_data.shape[0]).astype(np.int)
        down_data[self.columns[0]] = np.linspace(0, down_data.shape[0], down_data.shape[0]).astype(np.int)

        if csv_output_path is not None:
            self.attention_csv = self.attention_csv.reset_index(drop=True)
            down_data = down_data.reset_index(drop=True)
            down_data = pd.concat([self.attention_csv, down_data], axis=1)
            down_data.to_csv(csv_output_path, index=False)

        return down_data
