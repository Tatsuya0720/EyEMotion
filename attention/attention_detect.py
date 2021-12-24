import pandas as pd
import numpy as np
from tqdm import tqdm

class Attention_Detect:
    def __init__(self, input_path, output_path):
        self.input_path = input_path
        self.output_path = output_path
        self.lim_x_std = 0.5
        self.lim_y_std = 0.5

    def attention_detect(self, n=20, grid_x=10, grid_y=7):
        gaze = pd.read_csv(self.input_path)

        gaze_std = gaze[['gaze2d_x','gaze2d_y']].rolling(n).std()
        gaze_std.columns = ['gaze2d_x_std', 'gaze2d_y_std']
        # gaze_std = self.__calc_std(gaze, n)
        gaze_std = pd.concat([gaze, gaze_std], axis=1)

        # 1マスの半分の長さ(許容できる標準偏差)
        self.lim_x_std = 1 / (2 * grid_x)
        self.lim_y_std = 1 / (2 * grid_y)

        gaze_judge = gaze_std.apply(self.__detect_attention, axis=1)

        gaze_attention = gaze_judge
        continuous_gaze_attention = gaze_attention.copy()
        continuous_gaze_attention = self.__merge_rec_detecting(continuous_gaze_attention).rename('attention')
        gaze_attention = gaze_attention.rename('continuous_attention')

        gaze = pd.concat([gaze_std, gaze_attention, continuous_gaze_attention], axis=1).drop(columns=['Unnamed: 0'])

        gaze.to_csv(self.output_path, index=False)

        return gaze

    def __calc_std(self, data, n):
        coordinate = data.copy()
        coordinate = coordinate[['gaze2d_x','gaze2d_y']]
        coordinate['gaze2d_x_std'] = 7777
        coordinate['gaze2d_y_std'] = 7777

        for i in tqdm(range(coordinate.shape[0]-n)):
            target_x = coordinate.iloc[i]['gaze2d_x']
            target_y = coordinate.iloc[i]['gaze2d_y']

            """
            total_x = (coordinate['gaze2d_x'].iloc[i:i+n] - target_x)**2
            total_y = (coordinate['gaze2d_y'].iloc[i:i+n] - target_y)**2
            print(total_x)
            print('----------------------------------')

            coordinate['gaze2d_x_std'].iloc[i+n] = np.sqrt(total_x.sum()/n)
            coordinate['gaze2d_y_std'].iloc[i+n] = np.sqrt(total_y.sum()/n)"""

            total_x = abs((coordinate['gaze2d_x'].iloc[i:i + n]) - target_x).max()
            total_y = abs((coordinate['gaze2d_y'].iloc[i:i + n]) - target_y).max()
            print(total_x)
            print('----------------------------------')

            coordinate['gaze2d_x_std'].iloc[i + n] = total_x
            coordinate['gaze2d_y_std'].iloc[i + n] = total_y

        coordinate = coordinate[['gaze2d_x_std', 'gaze2d_y_std']]

        return coordinate


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
