import cv2
import pandas as pd
import os
from tqdm import tqdm
import numpy as np


class Capture:
    def __init__(self, attention_column='attention'):
        self.mp4 = None
        self.mp4_cv = []
        self.mp4_frames = None
        self.eeg_attention_list = []
        self.mp4_input_path = None
        self.eeg_attention_path = None
        self.picture_output_path = None
        self.attention_column = attention_column

        self.engagement = 0
        self.excitement = 0
        self.stress = 0
        self.relaxation = 0
        self.interest = 0
        self.focus = 0
        self.gazeonly = 0

        # keyはエクセルの表記に変更しておくべし
        self.emotion_count = {
            'Engagement': self.engagement,
            'Excitement': self.excitement,
            'Stress': self.stress,
            'Relaxation': self.relaxation,
            'Interest': self.interest,
            'Focus': self.focus,
            'gazeonly': self.gazeonly,
        }

    def capture_attention_scene(self, mp4_input, eeg_attention_input, picture_output, command='all'):
        self.mp4_input_path = mp4_input
        self.eeg_attention_path = eeg_attention_input
        self.picture_output_path = picture_output

        self.eeg_attention_list = pd.read_csv(self.eeg_attention_path)

        self.__fill_emotion_column(emotion='Engagement')
        self.__fill_emotion_column(emotion='Excitement')
        self.__fill_emotion_column(emotion='Stress')
        self.__fill_emotion_column(emotion='Relaxation')
        self.__fill_emotion_column(emotion='Interest')
        self.__fill_emotion_column(emotion='Focus')

        self.__mp4_to_list()  # self.mp4_listにframeが格納される

        self.__extract_attention_scene(command)

        # picture_outputに写真を保存完了

    def get_emotion(self, eeg_list, target_index, eeg_input_path=None):
        emotion = 'None'

        if self.eeg_attention_list is not None:
            eeg_list = self.eeg_attention_list
        else:
            eeg_list = pd.read_csv(eeg_input_path)

        # ここにmax_emotionを取得するアルゴリズムを書く
        column = [
            'PM.Engagement.Scaled',
            'PM.Excitement.Scaled',
            'PM.Stress.Scaled',
            'PM.Relaxation.Scaled',
            'PM.Interest.Scaled',
            'PM.Focus.Scaled'
        ]
        # eeg_list.iloc[target_index][column].max(axis=1) しきい値を設定するなら必要
        emotion = eeg_list.iloc[target_index][column].astype(np.float).idxmax().split('.')[1]

        return emotion

    def __extract_attention_scene(self, command):
        for frame in tqdm(range(self.mp4_frames)):
            if self.eeg_attention_list.iloc[frame][self.attention_column] == 1:
                if command == 'all':
                    emotion = self.get_emotion(self.eeg_attention_list, frame)
                else:
                    emotion = 'gazeonly'

                emotion_picture = self.__draw_emotion(mp4_attention_index=frame, emotion=emotion)
                emotion_picture_resize = cv2.resize(emotion_picture, (1920, 1080))
                # ここまでで画像内に情報を書き込むのは終わった
                self.__save_picture_emotion(emotion_picture_resize, emotion)

    def __mp4_to_list(self):
        self.mp4 = cv2.VideoCapture(self.mp4_input_path)
        self.mp4_frames = int(self.mp4.get(cv2.CAP_PROP_FRAME_COUNT))

        """for i in range(self.mp4_frames):
            status, frame = self.mp4.read()
            if status:
                frame_resize = cv2.resize(frame, (1920, 1080))
                self.mp4_list.append(frame_resize)
        """

    def __draw_emotion(self, mp4_attention_index=0, emotion="None"):
        '''
        :param mp4_attention_index: cv2で作成したframe配列の注目しているindex番号
        :param emotion: 感情カラムの列名
        :return: 感情データを書き込んだ画像
        '''
        # 画像内に文字を書き込んでください

        self.mp4.set(cv2.CAP_PROP_POS_FRAMES, mp4_attention_index)
        ret, picture = self.mp4.read()

        return picture

    def __save_picture_emotion(self, image, emotion):
        try:
            os.mkdir(self.picture_output_path + '/emotion_picture')
        except:
            pass
        filename = emotion + '_' + str(self.emotion_count[emotion]) + '.png'
        cv2.imwrite(self.picture_output_path + '/emotion_picture/' + str(filename), image)
        self.emotion_count[emotion] += 1

    def __fill_emotion_column(self, emotion):
        if str('PM.' + emotion + '.IsActive') in self.eeg_attention_list.columns:
            self.eeg_attention_list['PM.' + emotion + '.IsActive'] = self.eeg_attention_list[
                'PM.' + emotion + '.IsActive'].fillna(method='bfill')
            self.eeg_attention_list['PM.' + emotion + '.Scaled'] = self.eeg_attention_list[
                'PM.' + emotion + '.Scaled'].fillna(method='bfill')
            self.eeg_attention_list['PM.' + emotion + '.Raw'] = self.eeg_attention_list[
                'PM.' + emotion + '.Raw'].fillna(method='bfill')
            self.eeg_attention_list['PM.' + emotion + '.Min'] = self.eeg_attention_list[
                'PM.' + emotion + '.Min'].fillna(method='bfill')
            self.eeg_attention_list['PM.' + emotion + '.Max'] = self.eeg_attention_list[
                'PM.' + emotion + '.Max'].fillna(method='bfill')
