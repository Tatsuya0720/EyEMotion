import cv2
import os
import tkinter as tk
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from PIL import Image, ImageTk, ImageOps
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from convertor import convertor
from generater.gen_csv import GazeCsv
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

        # マルチスレッド
        self.thread1 = None
        self.thread2 = None
        self.thread3 = None
        self.thread4 = None
        self.thread5 = None

        # canvas
        self.photo_image = None

        # ipv4_address
        self.ipv4_address = "192.168.75.51"
        self.t_capture = None

        # path
        self.csv_input_path = None
        self.csv_output_path = None
        self.video_input_path = None
        self.video_output_path = None
        self.gaze_input = None
        self.gaze_output = None
        self.imu_input = None
        self.imu_output = None

        # video関係
        self.imageArray = []
        self.image = None
        self.video_playing = False
        self.video_width = 790
        self.video_height = 450

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

        notebook.add(tobii_tab, text="tobii", padding=3)
        notebook.add(convert_tab, text="convert", padding=3)
        notebook.add(plot_tab, text="plot", padding=3)
        notebook.pack(fill=tk.BOTH)

        # -----------------------------------------------tobii_tab--------------------------------------------
        t_main = tk.Frame(tobii_tab, bg="red")
        t_main.pack(fill=tk.BOTH, expand=True)
        t_l_sub = tk.Frame(t_main, bg="#f9931e")
        t_l_sub.pack(side=tk.LEFT, fill=tk.BOTH, anchor=tk.W, expand=True)
        t_r_sub = tk.Frame(t_main, bg="#f9931e")
        t_r_sub.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        t_movie = tk.Frame(t_l_sub, bg='black')
        t_movie.pack(side=tk.TOP, fill=tk.BOTH)
        self.t_canvas = tk.Canvas(t_movie, background="#000")
        self.t_canvas.pack(side=tk.TOP, fill=tk.BOTH)
        t_status = tk.Button(t_l_sub, text="t_status", bg="blue")
        t_status.pack(side=tk.TOP, fill=tk.BOTH)
        recording_id = tk.Button(t_l_sub, text="recording_id")
        recording_id.pack(side=tk.TOP, fill=tk.BOTH)
        battery = tk.Button(t_l_sub, text="battery")
        battery.pack(side=tk.TOP, fill=tk.BOTH)
        sampling_rate = tk.Button(t_l_sub, text="sampling_rate")
        sampling_rate.pack(side=tk.TOP, fill=tk.BOTH)

        calibration = tk.Button(t_r_sub, text="calibration")
        calibration.pack(side=tk.TOP, fill=tk.BOTH)
        calib_judge = tk.Button(t_r_sub, text="error", bg="red")
        calib_judge.pack(side=tk.TOP, fill=tk.BOTH)
        recording_start = tk.Button(t_r_sub, text="start", command=self.play_tobii)
        recording_start.pack(side=tk.TOP, fill=tk.BOTH)
        recording_time = tk.Label(t_r_sub, text="time : ")
        recording_time.pack(side=tk.TOP, fill=tk.BOTH)
        snapshot = tk.Button(t_r_sub, text="スクショ")
        snapshot.pack(side=tk.TOP, fill=tk.BOTH)
        recording_stop = tk.Button(t_r_sub, text="stop")
        recording_stop.pack(side=tk.TOP, fill=tk.BOTH)

        # -----------------------------------------------convert_tab--------------------------------------------
        convert_main = tk.Frame(convert_tab, relief=tk.RAISED, bd=10)
        convert_main.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.gaze = tk.Frame(convert_main, relief=tk.RIDGE, bd=5)
        self.gaze.pack(side=tk.TOP, fill=tk.BOTH)
        self.gaze_text = tk.Label(self.gaze, text="gaze")
        self.gaze_text.pack(side=tk.TOP, anchor=tk.W)
        self.i_gaze = tk.Frame(self.gaze)
        self.i_gaze.pack(side=tk.TOP, fill=tk.BOTH)
        self.i_gaze_box = tk.Entry(self.i_gaze)
        self.i_gaze_box.pack(side=tk.LEFT, fill=tk.BOTH)
        self.i_gaze_load = tk.Button(self.i_gaze, bg=self.load_bt_color, command=self.i_gaze_dialog)
        self.i_gaze_load.pack(side=tk.LEFT, fill=tk.BOTH)
        self.o_gaze = tk.Frame(self.gaze)
        self.o_gaze.pack(side=tk.TOP, fill=tk.BOTH)
        self.o_gaze_box = tk.Entry(self.o_gaze)
        self.o_gaze_box.pack(side=tk.LEFT, fill=tk.BOTH)
        self.o_gaze_load = tk.Button(self.o_gaze, bg=self.load_bt_color, command=self.o_gaze_dialog)
        self.o_gaze_load.pack(side=tk.LEFT, fill=tk.BOTH)

        self.imu = tk.Frame(convert_main, relief=tk.RIDGE, bd=5)
        self.imu.pack(side=tk.TOP, fill=tk.BOTH)
        self.imu_text = tk.Label(self.imu, text="imu")
        self.imu_text.pack(side=tk.TOP, anchor=tk.W)
        self.i_imu = tk.Frame(self.imu)
        self.i_imu.pack(side=tk.TOP, fill=tk.BOTH)
        self.i_imu_box = tk.Entry(self.i_imu)
        self.i_imu_box.pack(side=tk.LEFT, fill=tk.BOTH)
        self.i_imu_load = tk.Button(self.i_imu, bg=self.load_bt_color, command=self.i_imu_dialog)
        self.i_imu_load.pack(side=tk.LEFT, fill=tk.BOTH)
        self.o_imu = tk.Frame(self.imu)
        self.o_imu.pack(side=tk.TOP, fill=tk.BOTH)
        self.o_imu_box = tk.Entry(self.o_imu)
        self.o_imu_box.pack(side=tk.LEFT, fill=tk.BOTH)
        self.o_imu_load = tk.Button(self.o_imu, bg=self.load_bt_color, command=self.o_imu_dialog)
        self.o_imu_load.pack(side=tk.LEFT, fill=tk.BOTH)



        # ------------------------------------------------plot_tab------------------------------------------

        # 左側のブロック
        canvas_frame = tk.Frame(plot_tab)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # video描画用のブロック
        self.canvas_video = tk.Canvas(canvas_frame, background="#000", height=self.video_height)
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
        control_frame = tk.Frame(plot_tab)
        control_frame.pack(side=tk.LEFT, fill=tk.BOTH)

        # input_csvブロック
        i_csv_frame = tk.Frame(control_frame)
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
            text='csv_path',
            bg=self.load_bt_color,
            command=self.i_csv_file_dialog
        )
        i_csv_load_button.pack(side=tk.LEFT, anchor=tk.W)

        # input_videoブロック
        i_video_frame = tk.Frame(control_frame)
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
            text='video_path',
            bg=self.load_bt_color,
            command=self.i_video_file_dialog
        )
        i_video_load_button.pack(side=tk.LEFT, anchor=tk.W)

        # 読み込みブロック
        read_button = tk.Button(control_frame, text="読み込み", command=self.data_read)
        read_button.pack(side=tk.TOP, fill=tk.BOTH, pady=(10, 5))

        self.read_pb = ttk.Progressbar(control_frame, mode="indeterminate")
        self.read_pb.pack(fill=tk.BOTH, pady=(0, 30))

        # output_csvブロック
        o_csv_frame = tk.Frame(control_frame)
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
            text='csv_path',
            bg=self.load_bt_color,
            command=self.o_csv_file_dialog
        )
        o_csv_load_button.pack(side=tk.LEFT, anchor=tk.W, expand=True)

        # output_videoブロック
        o_video_frame = tk.Frame(control_frame)
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
            text='video_path',
            bg=self.load_bt_color,
            command=self.o_video_file_dialog
        )
        o_video_load_button.pack(side=tk.LEFT, anchor=tk.W, expand=True)

        # 同期ブロック
        fit_button = tk.Button(control_frame, text="動画時間,サンプリングレートの同期", command=self.conversion)
        fit_button.pack(side=tk.TOP, fill=tk.BOTH, pady=(10, 5))

        self.fit_pb = ttk.Progressbar(control_frame, mode="indeterminate")
        self.fit_pb.pack(fill=tk.BOTH, pady=(0, 30))

        # video再生ブロック
        play_button = tk.Button(control_frame, text="再生", command=self.play_video_f)
        play_button.pack(fill=tk.BOTH)

        # video停止用ブロック
        stop_button = tk.Button(control_frame, text="停止", command=self.stop_video)
        stop_button.pack(fill=tk.BOTH)

    def i_csv_file_dialog(self):
        file_type = [("csv", "*.csv")]
        initial_dir = os.path.dirname(__file__).rsplit("/", 1)[0]
        self.csv_input_path = tk.filedialog.askopenfilename(initialdir=initial_dir)
        self.i_csv_text_box.delete(0, tk.END)
        self.i_csv_text_box.insert(tk.END, self.csv_input_path)

    def o_csv_file_dialog(self):
        if self.csv_input_path != None:
            initialfile = self.csv_input_path.rsplit(".", 1)[0].split("/")[-1] + "_OUTPUT.csv"
            self.csv_output_path = tk.filedialog.asksaveasfilename(initialfile=initialfile)
            self.o_csv_text_box.delete(0, tk.END)
            self.o_csv_text_box.insert(tk.END, self.csv_output_path)

    def i_video_file_dialog(self):
        file_type = [("MOV", "*.MOV"), ("mov", "*.mov"), ("mp4", "*.mp4")]
        initial_dir = os.path.dirname(__file__).rsplit("/", 1)[0]
        self.video_input_path = tk.filedialog.askopenfilename(initialdir=initial_dir)
        self.i_video_text_box.delete(0, tk.END)
        self.i_video_text_box.insert(tk.END, self.video_input_path)

    def o_video_file_dialog(self):
        file_type = [("mp4", ".mp4")]
        if self.video_input_path != None:
            initialfile = self.video_input_path.split("/")[-1].split(".")[0] + "_OUTPUT.MOV"
            self.video_output_path = tk.filedialog.asksaveasfilename(initialfile=initialfile)
            self.o_video_text_box.delete(0, tk.END)
            self.o_video_text_box.insert(tk.END, self.video_output_path)

    def i_gaze_dialog(self):
        file_type = [(".gz", "gz")]
        initial_dir = os.path.dirname(__file__).rsplit("/", 1)[0]
        self.gaze_input = tk.filedialog.askopenfilename(initialfile=initial_dir)
        self.i_gaze_box.delete(0, tk.END)
        self.i_gaze_box.insert(tk.END, self.gaze_input)

    def o_gaze_dialog(self):
        file_type = [("csv", ".csv")]
        if self.gaze_input != None:
            initialfile = self.gaze_input.split("/")[-1].split(".")[0] + ".csv"
            self.gaze_output = tk.filedialog.asksaveasfilename(initialfile=initialfile)
            self.o_gaze_box.delete(0, tk.END)
            self.o_gaze_box.insert(tk.END, self.gaze_output)

    def i_imu_dialog(self):
        file_type = [(".gz", "gz")]
        initial_dir = os.path.dirname(__file__).rsplit("/", 1)[0]
        self.imu_input = tk.filedialog.askopenfilename(initialfile=initial_dir)
        self.i_imu_box.delete(0, tk.END)
        self.i_imu_box.insert(tk.END, self.imu_input)

    def o_imu_dialog(self):
        file_type = [("csv", ".csv")]
        if self.imu_input != None:
            initialfile = self.imu_input.split("/")[-1].split(".")[0] + ".csv"
            self.imu_output = tk.filedialog.asksaveasfilename(initialfile=initialfile)
            self.o_imu_box.delete(0, tk.END)
            self.o_imu_box.insert(tk.END, self.imu_output)


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
        self.data = pd.read_csv(self.csv_input_path)
        # videoデータの読み込み
        self.video = cv2.VideoCapture(self.video_input_path)
        frames = int(self.video.get(cv2.CAP_PROP_FRAME_COUNT))
        for i in range(frames):
            ret, frame = self.video.read()
            if ret:
                img_resize = cv2.resize(frame, (self.video_width, self.video_height))
                self.imageArray.append(img_resize)
        self.init_graph_utils()
        self.read_pb.stop()

    def conversion(self):
        thread3 = threading.Thread(target=self.p_f)
        thread4 = threading.Thread(target=self.conversion_r)
        thread3.start()
        thread4.start()

    def p_f(self):
        self.fit_pb.start(10)

    def conversion_r(self):
        cv = convertor.Convertor(self.video_input_path, self.csv_input_path)
        cv.fit_length(self.video_output_path, self.csv_output_path)
        self.data = cv.fit_sampling_rate(self.csv_output_path)
        self.init_graph_utils()
        self.fit_pb.stop()

        self.draw_plot()
        self.video_plot()

    def init_graph_utils(self):
        self.eeg_min = self.data.iloc[:, 2].min()
        self.eeg_max = self.data.iloc[:, 2].max()
        tmp = pd.DataFrame(index=range(self.x_range), columns=self.data.columns).fillna(0)
        self.data = pd.concat([tmp, self.data], axis=0)
        self.data["m0"] = np.linspace(0, self.data.shape[0], self.data.shape[0]).astype(np.int)
        self.x_scale["to"] = self.data.shape[0]

    def draw_plot(self, event=None):
        x = self.x_scale.get()
        ax.set_xlim(x, x + self.x_range)
        ax.set_ylim(self.eeg_min, self.eeg_max)
        plt.axvline((x + self.x_range * 2) / 2, self.eeg_min, self.eeg_max)
        h.set_xdata(self.data.iloc[int(x):int(x + self.x_range), 0])
        h.set_ydata(self.data.iloc[int(x):int(x + self.x_range), 2])
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

    def play_tobii(self):
        self.t_capture = cv2.VideoCapture("rtsp://" + self.ipv4_address + ":8554/live/all")
        self.disp_t_movie()

    def disp_t_movie(self):
        ret, frame = self.t_capture.read()
        cv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(cv_image)

        t_canvas_width = self.t_canvas.winfo_width()
        t_canvas_height = self.t_canvas.winfo_height()

        pil_image = ImageOps.pad(pil_image, (t_canvas_width, t_canvas_height))
        self.photo_image = ImageTk.PhotoImage(image=pil_image)

        self.t_canvas.create_image(
            t_canvas_width / 2,  # 画像表示位置(Canvasの中心)
            t_canvas_height / 2,
            image=self.photo_image  # 表示画像データ
        )

        self.master.after(2, self.disp_t_movie)

    def plot_f(self, event=None):
        if self.video_input_path != None:
            self.video_plot()
        if self.csv_input_path != None:
            self.draw_plot()

    def stop_video(self):
        if self.video_playing == True:
            self.video_playing = False
        else:
            return

    def play_video(self):
        if self.video_playing == False:
            self.video_playing = True
            for i in range(self.data.shape[0]):
                if self.x_scale.get() >= self.data.shape[0]:
                    break
                if self.video_playing == False:
                    break
                self.x_scale.set(self.x_scale.get() + 1)
                self.plot_f()

            if self.x_scale.get() >= self.data.shape[0]:
                self.stop_video()
                self.x_scale.set(0)
        else:
            return

    def play_video_f(self, event=None):
        self.thread5 = threading.Thread(target=self.play_video)
        self.thread5.start()

    def fetch_gaze(self):
        generator = GazeCsv()
        return generator.gaze_json_to_pd(self.gaze_input, self.gaze_output)

    def fetch_imu(self):
        generator = GazeCsv()
        return generator.imu_json_to_pd(self.imu_input, self.imu_output)

if __name__ == "__main__":
    fig = Figure(figsize=(8, 3), dpi=100)
    ax = fig.add_subplot(111)
    fig.subplots_adjust(left=0.08, right=0.999, bottom=0.1, top=0.95)
    root = tk.Tk()
    app = Application(master=root)
    fig.patch.set_facecolor(app.graph_back_color)
    h, = ax.plot([], [], 'purple')
    app.mainloop()
