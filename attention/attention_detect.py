import pandas as pd
import numpy as np

class Attention_Detect:
    def __init__(self, input_path, output_path):
        self.input_path = input_path
        self.output_path = output_path
        self.lim_x_std = 0.5
        self.lim_y_std = 0.5

    def attention_detect(self, n=40, grid_x=10, grid_y=7):
        gaze = pd.read_csv(self.input_path)

        gaze_std = gaze[['gaze2d_x','gaze2d_y']].rolling(n).std()
        gaze_std.columns = ['gaze2d_x_std', 'gaze2d_y_std']
        gaze_std = pd.concat([gaze, gaze_std], axis=1)

        # 1マスの半分の長さ(許容できる標準偏差)
        self.lim_x_std = 1 / (2 * grid_x)
        self.lim_y_std = 1 / (2 * grid_y)

        gaze_judge = gaze_std.apply(self.__detect_attention, axis=1)

        gaze_attention = self.__merge_rec_detecting(gaze_judge)

        gaze = pd.concat([gaze_std, gaze_attention], axis=1)

        gaze.to_csv(self.output_path)

        return gaze

    def __detect_attention(self, x):
        if x['gaze2d_x_std'] <= self.lim_x_std:
            if x['gaze2d_y_std'] <= self.lim_y_std:
                return 1

        return 0

    # 連続で注視が検出されないようにデータを整理
    def __merge_rec_detecting(self, gaze_judge):
        count = 0

        gaze_attention = gaze_judge.copy()

        for i in range(gaze_attention.shape[0]):
            if (gaze_attention[i] == 1) & (count != 0):
                gaze_attention[i] = 0
            else:
                count = 0
            if gaze_attention[i] == 1:
                count += 1

        return gaze_attention
