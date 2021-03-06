import cv2
import os
import tkinter as tk
import matplotlib.pyplot as plt
import datetime
import pandas as pd
import numpy as np
from PIL import Image, ImageTk, ImageOps
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from convertor import convertor
from generater.gen_csv import GazeCsv
from tobii.calibrate import Calibrate
from tobii.recorder import Recorder
from tobii.utils import Settings
from attention import attention_detect
from capture.capture import Capture
from tkinter import ttk
import threading


class Application(tk.Frame):
    def __init__(self, master=None):
        self.master = master
        super().__init__(master)

        # 初期のソフトウェアの大きさ
        master.geometry("1200x900")

        # UIの配色
        self.load_bt_color = "#fb2418"
        self.slider_bar_color = "#ffa500"
        self.graph_back_color = '#d9d9d9'
        self.success_color = "#00e233"

        # マルチスレッド
        self.thread1 = None
        self.thread2 = None
        self.thread3 = None
        self.thread4 = None
        self.thread5 = None
        self.thread6 = None # ↓tobii用のthread
        self.thread7 = None
        self.thread8 = None
        self.thread9 = None

        # canvas
        self.photo_image = None

        # ipv4_address
        self.ipv4_address = "192.168.75.51"
        self.t_capture = None

        # path
        self.dir_input_path = None
        self.eeg_input_path = None
        self.eeg_output_path = None
        self.video_input_path = None
        self.video_output_path = None
        self.gaze_input = None
        self.gaze_output = None
        self.imu_input = None
        self.imu_output = None
        self.attention_input = None
        self.attention_output = None

        # video関係
        self.imageArray = []
        self.image = None
        self.video_playing = False
        self.video_width = 790
        self.video_height = 450

        # tobii関係
        self.uuid = None
        self.current_folder = None
        self.starting_time = None
        self.total_time = None
        self.gaze_frequency = None
        self.gaze_sample_number = None
        self.valid_gaze_samples = None
        self.rest_time = None
        self.rest_battery = None

        self.is_calib = False
        self.recording = False
        self.tobii_playing = False

        self.gaze_csv = None
        self.imu_csv = None
        self.attention_csv = None

        self.column_list = ["None"]

        # graph関係
        self.x_range = int(128 / 2)
        self.eeg_min = 4000
        self.eeg_max = 5000
        self.data = pd.DataFrame(index=range(self.x_range), columns=['val1', 'val2', 'val3', 'val4', 'val5']).fillna(1)

        notebook = ttk.Notebook(width=1200, height=900)
        notebook.pack(fill=tk.BOTH)

        # データ読み込み用のタブ
        convert_tab = tk.Frame(notebook)
        # video,graph描画用のタブ
        plot_tab = tk.Frame(notebook)
        # tobiiのタブ
        tobii_tab = tk.Frame(notebook)

        notebook.add(tobii_tab, text="tobii", padding=10)
        notebook.add(convert_tab, text="csv", padding=10)
        notebook.add(plot_tab, text="plot", padding=10)
        notebook.pack(fill=tk.BOTH)

        # -----------------------------------------------tobii_tab--------------------------------------------
        t_main = tk.Frame(tobii_tab)
        t_main.pack(fill=tk.BOTH, expand=True)
        t_l_sub = tk.Frame(t_main)
        t_l_sub.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        t_r_sub = tk.Frame(t_main)
        t_r_sub.pack(side=tk.LEFT, fill=tk.BOTH, pady=(335, 0)) #275

        #t_movie = tk.Frame(t_l_sub, bg='black')
        #t_movie.pack(side=tk.TOP, fill=tk.BOTH, expand=True) #白い境界線ができてる...
        self.t_canvas = tk.Canvas(t_l_sub, background="#000")
        self.t_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.uuid_box = tk.Label(t_l_sub, text="                           uuid:")
        self.uuid_box.pack(side=tk.TOP, anchor=tk.W)
        self.current_folder_box = tk.Label(t_l_sub, text="            current folder:")
        self.current_folder_box.pack(side=tk.TOP, anchor=tk.W)
        self.starting_time_box = tk.Label(t_l_sub, text="              started time:")
        self.starting_time_box.pack(side=tk.TOP, anchor=tk.W)
        self.gaze_frequency_box = tk.Label(t_l_sub, text="         gaze frequency:")
        self.gaze_frequency_box.pack(side=tk.TOP, anchor=tk.W)
        self.gaze_sample_number_box = tk.Label(t_l_sub, text="gaze sample number:")
        self.gaze_sample_number_box.pack(side=tk.TOP, anchor=tk.W)
        self.valid_gaze_samples_box = tk.Label(t_l_sub, text="   valid gaze samples:")
        self.valid_gaze_samples_box.pack(side=tk.TOP, anchor=tk.W)
        self.recording_time = tk.Label(t_l_sub, text="           recording time:")
        self.recording_time.pack(side=tk.TOP, anchor=tk.W)
        self.rest_time_box = tk.Label(t_l_sub, text="                    rest time:")
        self.rest_time_box.pack(side=tk.TOP, anchor=tk.W)
        self.rest_battery_box = tk.Label(t_l_sub, text="                rest battery:")
        self.rest_battery_box.pack(side=tk.TOP, anchor=tk.W)

        video_start = tk.Button(t_r_sub, text="camera on/off", command=self.real_time_rtsp, relief=tk.RAISED, bd=2, width=20, pady=10)
        video_start.pack(side=tk.TOP, fill=tk.BOTH)
        calibration = tk.Button(t_r_sub, text="calibration", relief=tk.RAISED, bd=2, command=self.calibrate_f, pady=10)
        calibration.pack(side=tk.TOP, fill=tk.BOTH)
        self.calib_status = tk.Label(t_r_sub, text="x:None,    y:None")
        self.calib_status.pack(side=tk.TOP, anchor=tk.W)
        self.calib_judge = tk.Label(t_r_sub, text="please calibration", bg=self.load_bt_color, pady=10)
        self.calib_judge.pack(side=tk.TOP, fill=tk.BOTH)
        recording_start = tk.Button(t_r_sub, text="start recording", command=self.start_record, relief=tk.RAISED, bd=2, pady=10)
        recording_start.pack(side=tk.TOP, fill=tk.BOTH)
        recording_stop = tk.Button(t_r_sub, text="stop recording", command=self.stop_record, relief=tk.RAISED, bd=2, pady=10)
        recording_stop.pack(side=tk.TOP, fill=tk.BOTH)
        snapshot = tk.Button(t_r_sub, text="snapshot", relief=tk.RAISED, bd=2, command=self.snapshot_record, pady=10)
        snapshot.pack(side=tk.TOP, fill=tk.BOTH)
        update = tk.Button(t_r_sub, text="update", relief=tk.RAISED, bd=2, command=self.fetch_tobii_info, pady=10)
        update.pack(side=tk.TOP, fill=tk.BOTH)

        # -----------------------------------------------convert_tab--------------------------------------------
        convert_main = tk.Frame(convert_tab, relief=tk.RAISED, bd=10)
        convert_main.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        convert_discription = tk.Label(convert_main, text="generate csv from sd card", pady=10)
        convert_discription.pack(side=tk.TOP, anchor=tk.W)

        self.imu = tk.Frame(convert_main, relief=tk.RIDGE, bd=5, pady=10)
        self.imu.pack(side=tk.TOP, fill=tk.BOTH)
        self.imu_text = tk.Label(self.imu, text="SDカード内のフォルダを選択してください　例)2021.11.30.13.21.1")
        self.imu_text.pack(side=tk.TOP, anchor=tk.W)
        self.i_imu = tk.Frame(self.imu)
        self.i_imu.pack(side=tk.TOP, fill=tk.BOTH)
        self.i_imu_box = tk.Entry(self.i_imu, width=80)
        self.i_imu_box.pack(side=tk.LEFT, fill=tk.BOTH)
        self.i_imu_load = tk.Button(self.i_imu, bg=self.load_bt_color, command=self.i_folder_dialog, text="input",
                                    width=10)
        self.i_imu_load.pack(side=tk.LEFT, fill=tk.BOTH)
        self.o_imu = tk.Frame(self.imu)
        self.o_imu.pack(side=tk.TOP, fill=tk.BOTH)
        self.o_imu_box = tk.Entry(self.o_imu, width=80)
        self.o_imu_box.pack(side=tk.LEFT, fill=tk.BOTH)
        self.o_imu_load = tk.Button(self.o_imu, bg=self.load_bt_color, command=self.o_folder_dialog, text="output",
                                    width=10)
        self.o_imu_load.pack(side=tk.LEFT, fill=tk.BOTH)
        self.imu_make = tk.Button(self.o_imu, bg=self.load_bt_color, text="読み込み", width=10, command=self.make_file_util)
        self.imu_make.pack(side=tk.RIGHT, anchor=tk.W, fill=tk.BOTH)
        self.imu_status = tk.Label(self.o_imu, text="incomplete", width=10)
        self.imu_status.pack(side=tk.RIGHT, anchor=tk.W, fill=tk.BOTH)

        self.gaze = tk.Frame(convert_main, relief=tk.RIDGE, bd=5, pady=10)
        self.gaze.pack(side=tk.TOP, fill=tk.BOTH)
        self.gaze_text = tk.Label(self.gaze, text="視線データ")
        self.gaze_text.pack(side=tk.TOP, anchor=tk.W)
        self.i_gaze = tk.Frame(self.gaze)
        self.i_gaze.pack(side=tk.TOP, fill=tk.BOTH)
        self.i_gaze_box = tk.Entry(self.i_gaze, width=80)
        self.i_gaze_box.pack(side=tk.LEFT, fill=tk.BOTH)
        self.i_gaze_load = tk.Button(self.i_gaze, bg=self.load_bt_color, command=self.i_gaze_dialog, text="input", width=10)
        self.i_gaze_load.pack(side=tk.LEFT, fill=tk.BOTH)
        self.o_gaze = tk.Frame(self.gaze)
        self.o_gaze.pack(side=tk.TOP, fill=tk.BOTH)
        self.o_gaze_box = tk.Entry(self.o_gaze, width=80)
        self.o_gaze_box.pack(side=tk.LEFT, fill=tk.BOTH)
        self.o_gaze_load = tk.Button(self.o_gaze, bg=self.load_bt_color, command=self.o_gaze_dialog, text="output", width=10)
        self.o_gaze_load.pack(side=tk.LEFT, fill=tk.BOTH)
        self.gaze_make = tk.Button(self.o_gaze, bg=self.load_bt_color, text="読み込み", width=10, command=self.fetch_gaze)
        self.gaze_make.pack(side=tk.RIGHT, anchor=tk.W, fill=tk.BOTH)
        self.gaze_status = tk.Label(self.o_gaze, text="incomplete", width=10)
        self.gaze_status.pack(side=tk.RIGHT, anchor=tk.W, fill=tk.BOTH)

        self.attention = tk.Frame(convert_main, relief=tk.RIDGE, bd=5, pady=10)
        self.attention.pack(side=tk.TOP, fill=tk.BOTH)
        self.attention_text = tk.Label(self.attention, text="視線抽出")
        self.attention_text.pack(side=tk.TOP, anchor=tk.W)
        self.o_attention = tk.Frame(self.attention)
        self.o_attention.pack(side=tk.TOP, fill=tk.BOTH)
        self.o_attention_box = tk.Entry(self.o_attention, width=80)
        self.o_attention_box.pack(side=tk.LEFT, fill=tk.BOTH)
        self.o_attention_load = tk.Button(self.o_attention, bg=self.load_bt_color, command=self.o_attention_dialog, text="output",
                                    width=10)
        self.o_attention_load.pack(side=tk.LEFT, fill=tk.BOTH)
        self.attention_make = tk.Button(self.o_attention, bg=self.load_bt_color, text="実行", width=10, command=self.fetch_attention)
        self.attention_make.pack(side=tk.RIGHT, anchor=tk.W, fill=tk.BOTH)
        self.attention_status = tk.Label(self.o_attention, text="incomplete", width=10)
        self.attention_status.pack(side=tk.RIGHT, anchor=tk.W, fill=tk.BOTH)

        self.eeg = tk.Frame(convert_main, relief=tk.RIDGE, bd=5, pady=10)
        self.eeg.pack(side=tk.TOP, fill=tk.BOTH)
        self.eeg_text = tk.Label(self.eeg, text="脳波データ")
        self.eeg_text.pack(side=tk.TOP, anchor=tk.W)
        self.i_eeg = tk.Frame(self.eeg)
        self.i_eeg.pack(side=tk.TOP, fill=tk.BOTH)
        self.i_eeg_box = tk.Entry(self.i_eeg, width=80)
        self.i_eeg_box.pack(side=tk.LEFT, fill=tk.BOTH)
        self.i_eeg_load = tk.Button(self.i_eeg, bg=self.load_bt_color, command=self.i_csv_file_dialog, text="input",width=10)
        self.i_eeg_load.pack(side=tk.LEFT, fill=tk.BOTH)
        self.o_eeg = tk.Frame(self.eeg)
        self.o_eeg.pack(side=tk.TOP, fill=tk.BOTH)
        self.o_eeg_box = tk.Entry(self.o_eeg, width=80)
        self.o_eeg_box.pack(side=tk.LEFT, fill=tk.BOTH)
        self.o_eeg_load = tk.Button(self.o_eeg, bg=self.load_bt_color, command=self.o_csv_file_dialog, text="output",width=10)
        self.o_eeg_load.pack(side=tk.LEFT, fill=tk.BOTH)
        # self.eeg_make = tk.Button(self.o_eeg, bg=self.load_bt_color, text="make", width=10, command=self.fetch_imu)
        # self.eeg_make.pack(side=tk.RIGHT, anchor=tk.W, fill=tk.BOTH)
        # self.eeg_status = tk.Label(self.o_eeg, text="incomplete", width=10)
        # self.eeg_status.pack(side=tk.RIGHT, anchor=tk.W, fill=tk.BOTH)

        self.mp4 = tk.Frame(convert_main, relief=tk.RIDGE, bd=5, pady=10)
        self.mp4.pack(side=tk.TOP, fill=tk.BOTH)
        self.mp4_text = tk.Label(self.mp4, text="動画")
        self.mp4_text.pack(side=tk.TOP, anchor=tk.W)
        self.i_mp4 = tk.Frame(self.mp4)
        self.i_mp4.pack(side=tk.TOP, fill=tk.BOTH)
        self.i_mp4_box = tk.Entry(self.i_mp4, width=80)
        self.i_mp4_box.pack(side=tk.LEFT, fill=tk.BOTH)
        self.i_mp4_load = tk.Button(self.i_mp4, bg=self.load_bt_color, command=self.i_video_file_dialog, text="input",
                                    width=10)
        self.i_mp4_load.pack(side=tk.LEFT, fill=tk.BOTH)
        self.o_mp4 = tk.Frame(self.mp4)
        self.o_mp4.pack(side=tk.TOP, fill=tk.BOTH)
        self.o_mp4_box = tk.Entry(self.o_mp4, width=80)
        self.o_mp4_box.pack(side=tk.LEFT, fill=tk.BOTH)
        self.o_mp4_load = tk.Button(self.o_mp4, bg=self.load_bt_color, command=self.o_video_file_dialog, text="output",
                                    width=10)
        self.o_mp4_load.pack(side=tk.LEFT, fill=tk.BOTH)
        self.mp4_make = tk.Button(self.o_mp4, bg=self.load_bt_color, text="同期", width=10, command=self.csv_conversion)
        self.mp4_make.pack(side=tk.RIGHT, anchor=tk.W, fill=tk.BOTH)
        self.mp4_status = tk.Label(self.o_mp4, text="incomplete", width=10)
        self.mp4_status.pack(side=tk.RIGHT, anchor=tk.W, fill=tk.BOTH)

        self.extract_button = tk.Button(convert_main, bg=self.load_bt_color, text='注視の切り取り', command=self.extract_picture)
        self.extract_button.pack(side=tk.LEFT, fill=tk.BOTH)

        # ------------------------------------------------plot_tab------------------------------------------

        # 左側のブロック
        canvas_frame = tk.Frame(plot_tab)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # video描画用のブロック
        self.canvas_video = tk.Canvas(canvas_frame, background="black", height=self.video_height)
        self.canvas_video.pack(anchor=tk.E, padx=(70, 0), pady=30, fill=tk.BOTH)
        self.update()

        # graph描画用のブロック
        self.graph = FigureCanvasTkAgg(fig, canvas_frame)
        canvas_graph = self.graph.get_tk_widget()  # matplotlib型をwidget型に変換
        canvas_graph.pack(fill=tk.BOTH)  # , expand=True)

        # graphとvideoのスライダー
        self.x_scale = tk.Scale(
            canvas_frame,
            from_=0,  # to=self.data.shape[0],
            resolution=1,
            bg=self.slider_bar_color,
            orient=tk.HORIZONTAL,
            command=self.plot_f
        )
        self.x_scale.pack(anchor=tk.E, fill="x", padx=(70, 0))

        # 右側のブロック
        self.control_frame = tk.Frame(plot_tab)
        self.control_frame.pack(side=tk.LEFT, fill=tk.BOTH)
        
        # self.tobii_combobox = ttk.Combobox(master=self.control_frame, values=self.column_list)
        # self.tobii_combobox.pack(side=tk.TOP, fill=tk.BOTH)

        # input_csvブロック
        i_csv_frame = tk.Frame(self.control_frame)
        i_csv_frame.pack(side=tk.TOP, fill=tk.BOTH, pady=(200, 0))
        # up
        i_csv_above_frame = tk.Frame(i_csv_frame)
        i_csv_above_frame.pack(side=tk.TOP, fill=tk.BOTH)
        # text
        i_csv_disc_text = tk.Label(i_csv_above_frame, text="INPUT_CSV")
        i_csv_disc_text.pack(side=tk.LEFT, anchor=tk.W)
        # down
        i_csv_below_frame = tk.Frame(i_csv_frame)
        i_csv_below_frame.pack(side=tk.TOP, fill=tk.BOTH)
        # pathのテキストボックス
        self.i_csv_text_box = tk.Entry(i_csv_below_frame)
        self.i_csv_text_box.pack(side=tk.LEFT, fill=tk.BOTH)
        # input_csv_open用のボタン
        i_csv_load_button = tk.Button(
            i_csv_below_frame,
            text='input',
            bg=self.load_bt_color,
            command=self.i_csv_file_dialog,
            width=10,
        )
        i_csv_load_button.pack(side=tk.LEFT, anchor=tk.W)

        # input_videoブロック
        i_video_frame = tk.Frame(self.control_frame)
        i_video_frame.pack(side=tk.TOP, fill=tk.BOTH)
        # up
        i_video_above_frame = tk.Frame(i_video_frame)
        i_video_above_frame.pack(side=tk.TOP, fill=tk.BOTH)
        # text
        i_vide_disc_text = tk.Label(i_video_above_frame, text="INPUT_MP4")
        i_vide_disc_text.pack(side=tk.LEFT, anchor=tk.W)
        # down
        i_video_below_frame = tk.Frame(i_video_frame)
        i_video_below_frame.pack(side=tk.TOP, fill=tk.BOTH)
        # pathのテキストボックス
        self.i_video_text_box = tk.Entry(i_video_below_frame)
        self.i_video_text_box.pack(side=tk.LEFT, fill=tk.BOTH)
        # input_video_open用のボタン
        i_video_load_button = tk.Button(
            i_video_below_frame,
            text='input',
            bg=self.load_bt_color,
            command=self.i_video_file_dialog,
            width=10,
        )
        i_video_load_button.pack(side=tk.LEFT, anchor=tk.W)

        # 読み込みブロック
        read_button = tk.Button(self.control_frame, text="読み込み", command=self.data_read)
        read_button.pack(side=tk.TOP, fill=tk.BOTH, pady=(10, 5))

        self.read_pb = ttk.Progressbar(self.control_frame, mode="indeterminate")
        self.read_pb.pack(fill=tk.BOTH, pady=(0, 30))

        """
        # output_csvブロック
        o_csv_frame = tk.Frame(self.control_frame)
        o_csv_frame.pack(side=tk.TOP, fill=tk.BOTH)
        # up
        o_csv_above_frame = tk.Frame(o_csv_frame)
        o_csv_above_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        # text
        o_csv_disc_text = tk.Label(o_csv_above_frame, text="OUTPUT_CSV")
        o_csv_disc_text.pack(side=tk.LEFT, anchor=tk.W, expand=True)
        # down
        o_csv_below_frame = tk.Frame(o_csv_frame)
        o_csv_below_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        # pathのテキストボックス
        self.o_csv_text_box = tk.Entry(o_csv_below_frame)
        self.o_csv_text_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # output_csv_open用のボタン
        o_csv_load_button = tk.Button(
            o_csv_below_frame,
            text='output',
            bg=self.load_bt_color,
            command=self.o_csv_file_dialog,
            width=10,
        )
        o_csv_load_button.pack(side=tk.LEFT, anchor=tk.W, expand=True)

        # output_videoブロック
        o_video_frame = tk.Frame(self.control_frame)
        o_video_frame.pack(side=tk.TOP, fill=tk.BOTH)
        # up
        o_video_above_frame = tk.Frame(o_video_frame)
        o_video_above_frame.pack(side=tk.TOP, fill=tk.BOTH)
        # text
        o_vide_disc_text = tk.Label(o_video_above_frame, text="OUTPUT_MP4")
        o_vide_disc_text.pack(side=tk.LEFT)
        # down
        o_video_below_frame = tk.Frame(o_video_frame)
        o_video_below_frame.pack(side=tk.TOP, fill=tk.BOTH)
        # pathのテキストボックス
        self.o_video_text_box = tk.Entry(o_video_below_frame)
        self.o_video_text_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # output_video_open用のボタン
        o_video_load_button = tk.Button(
            o_video_below_frame,
            text='output',
            bg=self.load_bt_color,
            command=self.o_video_file_dialog,
            width=10,
        )
        o_video_load_button.pack(side=tk.LEFT, anchor=tk.W, expand=True)

        # 同期ブロック
        fit_button = tk.Button(self.control_frame, text="動画時間,サンプリングレートの同期", command=self.conversion)
        fit_button.pack(side=tk.TOP, fill=tk.BOTH, pady=(10, 5))

        self.fit_pb = ttk.Progressbar(self.control_frame, mode="indeterminate")
        self.fit_pb.pack(fill=tk.BOTH, pady=(0, 30))
        """

        # video再生ブロック
        play_button = tk.Button(self.control_frame, text="再生", command=self.play_video_f)
        play_button.pack(fill=tk.BOTH)

        # video停止用ブロック
        stop_button = tk.Button(self.control_frame, text="停止", command=self.stop_video)
        stop_button.pack(fill=tk.BOTH)

    def i_folder_dialog(self):
        self.dir_input_path = tk.filedialog.askdirectory()
        self.i_imu_box.delete(0, tk.END)
        self.i_imu_box.insert(tk.END, self.dir_input_path)
        self.o_folder_dialog()

    def o_folder_dialog(self):
        self.dir_output_path = self.dir_input_path + "/" + str(self.dir_input_path.split('/')[-1]) + "_OUTPUT"
        try:
            os.mkdir(self.dir_output_path)
        except:
            print("already exist")
        self.o_imu_box.delete(0, tk.END)
        self.o_imu_box.insert(tk.END, self.dir_output_path)

    def make_file_util(self):
        self.gaze_input = self.dir_input_path + '/gazedata.gz'
        self.gaze_output = self.dir_output_path + '/gazedata_OUTPUT.csv'
        self.video_input_path = self.dir_input_path + '/scenevideo.mp4'
        self.video_output_path = self.dir_output_path + '/scenevideo_OUTPUT.mp4'

        self.i_video_text_box.delete(0, tk.END)
        self.i_video_text_box.insert(tk.END, self.video_input_path)
        self.i_mp4_box.delete(0, tk.END)
        self.i_mp4_box.insert(tk.END, self.video_input_path)

        self.o_mp4_box.delete(0, tk.END)
        self.o_mp4_box.insert(tk.END, self.video_output_path)

        self.i_gaze_box.delete(0, tk.END)
        self.i_gaze_box.insert(tk.END, self.gaze_input)

        self.o_gaze_box.delete(0, tk.END)
        self.o_gaze_box.insert(tk.END, self.gaze_output)

        self.attention_output = self.gaze_output
        self.o_attention_box.delete(0, tk.END)
        self.o_attention_box.insert(tk.END, self.attention_output)

        self.imu_status['text'] = "complete!"
        self.imu_status['bg'] = self.success_color

    def i_csv_file_dialog(self):
        file_type = [("csv", "*.csv")]
        initial_dir = os.path.dirname(os.path.abspath(__file__)).rsplit("/", 1)[0]
        self.eeg_input_path = tk.filedialog.askopenfilename(filetypes=file_type, initialdir=initial_dir)
        self.i_csv_text_box.delete(0, tk.END)
        self.i_csv_text_box.insert(tk.END, self.eeg_input_path)
        self.i_eeg_box.delete(0, tk.END)
        self.i_eeg_box.insert(tk.END, self.eeg_input_path)

    def o_csv_file_dialog(self):
        file_type = [("csv_file", "*.csv")]
        if self.eeg_input_path != None:
            #initial_dir = os.path.dirname(os.path.abspath(__file__)).rsplit("/", 1)[0]
            #initialfile = self.eeg_input_path.rsplit(".", 1)[0].split("/")[-1] + "_OUTPUT.csv"
            initial_dir = self.dir_output_path
            initialfile = self.dir_input_path.split('/')[-1] + "_OUTPUT.csv"
            self.eeg_output_path = tk.filedialog.asksaveasfilename(filetypes=file_type, initialdir=initial_dir, initialfile=initialfile)
            self.i_csv_text_box.delete(0, tk.END)
            self.i_csv_text_box.insert(tk.END, self.eeg_output_path)
            self.o_eeg_box.delete(0, tk.END)
            self.o_eeg_box.insert(tk.END, self.eeg_output_path)

    def i_video_file_dialog(self):
        file_type = [("mp4", "*.mp4")]
        initial_dir = os.path.dirname(os.path.abspath(__file__)).rsplit("/", 1)[0]
        self.video_input_path = tk.filedialog.askopenfilename(filetypes=file_type, initialdir=initial_dir)
        self.i_video_text_box.delete(0, tk.END)
        self.i_video_text_box.insert(tk.END, self.video_input_path)
        self.i_mp4_box.delete(0, tk.END)
        self.i_mp4_box.insert(tk.END, self.video_input_path)

    def o_video_file_dialog(self):
        file_type = [("mp4", "*.mp4")]
        if self.video_input_path != None:
            initial_dir = os.path.dirname(os.path.abspath(__file__)).rsplit("/", 1)[0]
            initialfile = self.video_input_path.split("/")[-1].split(".")[0] + "_OUTPUT.MOV"
            self.video_output_path = tk.filedialog.asksaveasfilename(filetypes=file_type, initialdir=initial_dir, initialfile=initialfile)
            self.o_video_text_box.delete(0, tk.END)
            self.o_video_text_box.insert(tk.END, self.video_output_path)
            self.o_mp4_box.delete(0, tk.END)
            self.o_mp4_box.insert(tk.END, self.video_output_path)

    def i_gaze_dialog(self):
        file_type = [("compress_file", "*.gz")]
        initial_dir = os.path.dirname(os.path.abspath(__file__)).rsplit("/", 1)[0]
        self.gaze_input = tk.filedialog.askopenfilename(filetypes=file_type, initialdir=initial_dir)
        self.i_gaze_box.delete(0, tk.END)
        self.i_gaze_box.insert(tk.END, self.gaze_input)

    def o_gaze_dialog(self):
        file_type = [("output_file", "*.csv")]
        if self.gaze_input != None:
            initial_dir = os.path.dirname(os.path.abspath(__file__)).rsplit("/", 1)[0]
            initialfile = self.gaze_input.split("/")[-1].split(".")[0] + ".csv"
            self.gaze_output = tk.filedialog.asksaveasfilename(filetypes=file_type, initialdir=initial_dir, initialfile=initialfile)
            self.o_gaze_box.delete(0, tk.END)
            self.o_gaze_box.insert(tk.END, self.gaze_output)

            self.attention_output = self.gaze_output
            self.o_attention_box.delete(0, tk.END)
            self.o_attention_box.insert(tk.END, self.attention_output)

    def i_imu_dialog(self):
        file_type = [("compress_file", "*.gz")]
        initial_dir = os.path.dirname(os.path.abspath(__file__)).rsplit("/", 1)[0]
        self.imu_input = tk.filedialog.askopenfilename(filetypes=file_type, initialfile=initial_dir)
        self.i_imu_box.delete(0, tk.END)
        self.i_imu_box.insert(tk.END, self.imu_input)

    def o_imu_dialog(self):
        file_type = [("output_file", "*.csv")]
        if self.imu_input != None:
            initial_dir = os.path.dirname(os.path.abspath(__file__)).rsplit("/", 1)[0]
            initialfile = self.imu_input.split("/")[-1].split(".")[0] + ".csv"
            self.imu_output = tk.filedialog.asksaveasfilename(initialdir=initial_dir, initialfile=initialfile, filetypes=file_type)
            self.o_imu_box.delete(0, tk.END)
            self.o_imu_box.insert(tk.END, self.imu_output)

    def o_attention_dialog(self):
        file_type = [("output_file", "*.csv")]
        self.attention_input = self.gaze_output
        if self.attention_input != None:
            initial_dir = os.path.dirname(os.path.abspath(__file__)).rsplit("/", 1)[0]
            initialfile = self.attention_input.split("/")[-1].split(".")[0] + ".csv"
            self.attention_output = tk.filedialog.asksaveasfilename(initialdir=initial_dir, initialfile=initialfile, filetypes=file_type)
            self.o_attention_box.delete(0, tk.END)
            self.o_attention_box.insert(tk.END, self.attention_output)

    def data_read(self):
        # self.data_read_r()
        self.thread1 = threading.Thread(target=self.p_r)
        self.thread2 = threading.Thread(target=self.data_read_r)
        self.thread1.start()
        self.thread2.start()

    def p_r(self):
        self.read_pb.start(10)

    def data_read_r(self):
        # csvデータの読み込み
        self.data = pd.read_csv(self.eeg_input_path)
        # videoデータの読み込み
        self.video = cv2.VideoCapture(self.video_input_path)
        frames = int(self.video.get(cv2.CAP_PROP_FRAME_COUNT))
        for i in range(frames):
            ret, frame = self.video.read()
            if ret:
                img_resize = cv2.resize(frame, (self.video_width, self.video_height))
                self.imageArray.append(img_resize)
        # self.init_graph_utils()
        self.read_pb.stop()
        self.add_combo_columns()

    def add_combo_columns(self):
        self.tobii_combobox = ttk.Combobox(master=self.control_frame, values=list(self.data.columns))
        self.tobii_combobox.pack(side=tk.TOP, fill=tk.BOTH)

    def csv_conversion(self):
        self.data_read_r()
        # thread3 = threading.Thread(target=self.p_f)
        thread4 = threading.Thread(target=self.conversion_r)
        # thread3.start()
        thread4.start()

    def conversion(self):
        # thread3 = threading.Thread(target=self.p_f)
        #thread4 = threading.Thread(target=self.conversion_r)
        # thread3.start()
        #thread4.start()

        self.conversion_r()

        self.video_input_path = self.video_output_path
        self.i_mp4_box.delete(0, tk.END)
        self.i_mp4_box.insert(tk.END, self.video_input_path)

    def p_f(self):
        self.fit_pb.start(10)

    def conversion_r(self):
        data = pd.read_csv(self.eeg_input_path)
        data = self.__fill_emotion_column('Engagement', data, 'bfill')
        data = self.__fill_emotion_column('Excitement', data, 'bfill')
        data = self.__fill_emotion_column('Stress', data, 'bfill')
        data = self.__fill_emotion_column('Relaxation', data, 'bfill')
        data = self.__fill_emotion_column('Interest', data, 'bfill')
        data = self.__fill_emotion_column('Focus', data, 'bfill')

        data = self.__fill_emotion_column('Engagement', data, 'ffill')
        data = self.__fill_emotion_column('Excitement', data, 'ffill')
        data = self.__fill_emotion_column('Stress', data, 'ffill')
        data = self.__fill_emotion_column('Relaxation', data, 'ffill')
        data = self.__fill_emotion_column('Interest', data, 'ffill')
        data = self.__fill_emotion_column('Focus', data, 'ffill')

        self.data = data.drop(columns=['type'], errors='ignore')
        self.data.to_csv(self.eeg_input_path, index=False)
        cv = convertor.Convertor(self.video_input_path, self.eeg_input_path, self.attention_output)
        self.data = cv.fit_length(self.data, self.video_output_path)
        print(self.data['PM.Interest.Scaled'])
        self.data = cv.fit_sampling_rate(self.data, self.eeg_output_path)
        # self.init_graph_utils()
        print(self.data['PM.Interest.Scaled'])

        self.draw_plot()
        self.video_plot()
        self.mp4_status['text'] = "complete!"
        self.mp4_status['bg'] = self.success_color

        self.eeg_input_path = self.eeg_output_path
        self.i_eeg_box.delete(0, tk.END)
        self.i_eeg_box.insert(tk.END, self.eeg_output_path)

        self.video_input_path = self.video_output_path
        self.i_mp4_box.delete(0, tk.END)
        self.i_mp4_box.insert(tk.END, self.video_output_path)


    def init_graph_utils(self):
        # self.eeg_min = self.data.iloc[:, 2].min()
        # self.eeg_max = self.data.iloc[:, 2].max()
        self.eeg_min = self.data.iloc[5*128:][self.tobii_combobox.get()].min() - 0.5
        self.eeg_max = self.data.iloc[5*128:][self.tobii_combobox.get()].max() + 0.5
        # tmp = pd.DataFrame(index=range(self.x_range), columns=self.data.columns).fillna(0)
        # self.data = pd.concat([tmp, self.data], axis=0)
        self.data[self.data.columns[0]] = np.linspace(0, self.data.shape[0], self.data.shape[0]).astype(np.int)
        self.x_scale["to"] = self.data.shape[0]

    def draw_plot(self, event=None):
        x = self.x_scale.get()
        ax.set_xlim(x, x + self.x_range)
        ax.set_ylim(self.eeg_min, self.eeg_max)
        # ax.vlines((x + 128) / 2, self.eeg_min, self.eeg_max)
        # plt.axvline((x + self.x_range * 2) / 2, self.eeg_min, self.eeg_max)
        h.set_xdata(self.data.iloc[int(x):int(x + self.x_range), 0])
        h.set_ydata(self.data.iloc[int(x):int(x + self.x_range)][self.tobii_combobox.get()])
        self.graph.draw()

    def video_plot(self):
        image = self.imageArray[self.x_scale.get()]
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(image)
        self.image = ImageTk.PhotoImage(image=image)

        canvas_width = self.canvas_video.winfo_width()
        canvas_height = self.canvas_video.winfo_height()
        self.canvas_video.create_image(
            canvas_width / 2,  # 画像表示位置(Canvasの中心)
            canvas_height / 2,
            image=self.image  # 表示画像データ
        )

    def plot_f(self, event=None):
        if self.video_input_path != None:
            self.video_plot()
        if self.eeg_input_path != None:
            self.draw_plot()

    def stop_video(self):
        if self.video_playing == True:
            self.video_playing = False
        else:
            return

    def play_video(self):
        if (self.x_scale.get() <= self.data.shape[0]) & (self.video_playing==True):
            self.x_scale.set(self.x_scale.get() + 1)
            self.plot_f()
            root.after(1, self.play_video)
        else:
            if self.x_scale.get() >= self.data.shape[0]:
                self.x_scale.set(0)
            else:
                return

    def play_video_f(self, event=None):
        self.video_playing = True
        self.init_graph_utils()
        self.thread5 = threading.Thread(target=self.play_video)
        self.thread5.start()

    def real_time_rtsp(self):
        if self.tobii_playing==False:
            self.tobii_playing = True
            self.t_capture = cv2.VideoCapture("rtsp://" + self.ipv4_address + ":8554/live/all?gaze-overlay=true")
            self.thread8 = threading.Thread(target=self.fetch_tobii_info())
            self.thread9 = threading.Thread(target=self.disp_t_movie())
            self.thread8.start()
            self.thread9.start()
        else:
            self.tobii_playing = False

    def fetch_info(self):
        if self.tobii_playing == True:
            self.fetch_tobii_info()
        else:
            return

    """def play_tobii(self):
        if self.tobii_playing == False:
            self.tobii_playing = True
            self.t_capture = cv2.VideoCapture("rtsp://" + self.ipv4_address + ":8554/live/all")
            self.disp_t_movie()
        else:
            self.tobii_playing = False"""

    def disp_t_movie(self):
        if self.tobii_playing == True:
            ret, frame = self.t_capture.read()
            # cv_image = frame
            cv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(cv_image)

            t_canvas_width = self.t_canvas.winfo_width()
            t_canvas_height = self.t_canvas.winfo_height()

            pil_image = ImageOps.pad(pil_image, (t_canvas_width, t_canvas_height))
            self.photo_image = ImageTk.PhotoImage(image=pil_image)

            self.t_canvas.create_image(
                t_canvas_width / 2,  # 画像表示位置(Canvasの中心)
                t_canvas_height / 2,
                image=self.photo_image,  # 表示画像データ
                tag="oval",
            )

            #thread = threading.Thread(target=self.disp_t_movie)
            self.master.after(1, self.disp_t_movie)
        else:
            self.t_canvas.delete('oval')
            return

    def fetch_attention(self):
        at = attention_detect.Attention_Detect(self.gaze_output, self.attention_output)
        self.attention_csv = at.attention_detect(n=20, grid_x=20, grid_y=10)
        self.attention_status['text'] = "complete!"
        self.attention_status['bg'] = self.success_color

    def fetch_gaze(self):
        generator = GazeCsv()
        self.gaze_status['text'] = "complete!"
        self.gaze_status['bg'] = self.success_color
        self.gaze_csv = generator.gaze_json_to_pd(self.gaze_input, self.gaze_output)
        return self.gaze_csv

    def fetch_imu(self):
        generator = GazeCsv()
        self.imu_status['text'] = "complete!"
        self.imu_status['bg'] = self.success_color
        self.imu_csv = generator.imu_json_to_pd(self.imu_input, self.imu_output)
        return self.imu_csv

    def merge_csv_data(self):
        _data = pd.concat([self.gaze_csv, self.imu_csv, self.data])
        return _data

    def fetch_tobii_info(self):
        if self.tobii_playing == True:
            rec = Recorder(self.ipv4_address)
            setting = Settings(self.ipv4_address)

            gaze_frequency = rec.gaze_frequency()
            current_folder = rec.current_folder_name()
            gaze_sample_number = rec.gaze_sampling_number()
            rest_time = rec.rest_time()
            valid_gaze_samples = rec.valid_gaze_sample()
            uuid = rec.uuid()
            recording_time = rec.total_time()
            starting_time = rec.stating_time()
            rest_battery = setting.rest_battery()

            info_dic = {
                "uuid": uuid,
                "current_folder": current_folder,
                "starting_time": starting_time,
                "gaze_frequency": gaze_frequency,
                "gaze_sample_number": gaze_sample_number,
                "valid_gaze_samples": valid_gaze_samples,
                "rest_time": rest_time,
                "rest_battery": rest_battery,
            }

            self.uuid_box['text'] = "                           uuid:" + str(uuid)
            self.current_folder_box['text'] = '            current folder:' + str(current_folder)
            self.starting_time_box['text'] = '              started time:' + str(starting_time)
            self.gaze_frequency_box['text'] = '         gaze frequency:' + str(gaze_frequency)
            self.gaze_sample_number_box['text'] = 'gaze sample number:' + str(gaze_sample_number)
            self.valid_gaze_samples_box['text'] = '   valid gaze samples:' + str(valid_gaze_samples)
            self.recording_time['text'] = "           recording time:" + str(datetime.timedelta(seconds=int(recording_time)))
            self.rest_time_box['text'] = '                    rest time:' + str(rest_time)
            self.rest_battery_box['text'] = '                rest battery:' + str(rest_battery)

            thread = threading.Thread(target=self.fetch_tobii_info)
            root.after(1000, thread.start)
        else:
            return

    def calibrate_f(self):
        self.thread6 = threading.Thread(target=self.calib_record)
        self.thread7 = threading.Thread(target=self.check_calib)
        self.thread6.start()
        self.thread7.start()

    def calib_record(self):
        calib = Calibrate(self.ipv4_address)
        self.is_calib = calib.calibrate()
        self.calib_judge['text'] = "calibration_status:" + str(self.is_calib)
        if self.is_calib == 'true':
            self.calib_judge['text'] = "SUCCESS!!"
            self.calib_judge['bg'] = self.success_color
        else:
            self.calib_judge['text'] = "calibration_status:false"
            self.calib_judge['bg'] = self.load_bt_color

    def check_calib(self):
        calib = Calibrate(self.ipv4_address)
        for i in range(10):
            calib.test_calibrate()
            self.calib_status['text'] = "x:" + str(int(calib.x[0])) + ",    " + "y:" + str(int(calib.y[0]))


    def start_record(self):
        if self.is_calib == 'true':
            if self.recording==False:
                self.recording = True
                rec = Recorder(self.ipv4_address)
                rec.set_folder_name()
                rec.set_gaze_frequency()
                rec.start()

    def stop_record(self):
        self.recording = False
        rec = Recorder(self.ipv4_address)
        rec.stop()

    def snapshot_record(self):
        if self.is_calib == 'true':
            rec = Recorder(self.ipv4_address)
            rec.snapshot()

    def __fill_emotion_column(self, emotion, eeg_attention_list, command):
        if str('PM.' + emotion + '.IsActive') in eeg_attention_list.columns:
            eeg_attention_list['PM.' + emotion + '.IsActive'] = eeg_attention_list['PM.' + emotion + '.IsActive'].fillna(method=command)
            eeg_attention_list['PM.' + emotion + '.Scaled'] = eeg_attention_list['PM.' + emotion + '.Scaled'].fillna(method=command)
            eeg_attention_list['PM.' + emotion + '.Raw'] = eeg_attention_list['PM.' + emotion + '.Raw'].fillna(method=command)
            eeg_attention_list['PM.' + emotion + '.Min'] = eeg_attention_list['PM.' + emotion + '.Min'].fillna(method=command)
            eeg_attention_list['PM.' + emotion + '.Max'] = eeg_attention_list['PM.' + emotion + '.Max'].fillna(method=command)

            return eeg_attention_list

    def extract_picture(self):
        cap = Capture(attention_column='attention')
        if self.eeg_input_path is not None:
            cap.capture_attention_scene(self.video_output_path, self.eeg_output_path, self.dir_output_path, command='all')
        else:
            cap.capture_attention_scene(self.video_input_path, self.attention_output, self.dir_output_path, command='gaze_only')


if __name__ == "__main__":
    fig = Figure(figsize=(8, 3), dpi=100)
    ax = fig.add_subplot(111)
    fig.subplots_adjust(left=0.08, right=0.999, bottom=0.1, top=0.95)
    root = tk.Tk()
    app = Application(master=root)
    fig.patch.set_facecolor(app.graph_back_color)
    h, = ax.plot([], [], 'purple')
    app.mainloop()
