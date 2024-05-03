import tkinter as tk
from PIL import Image, ImageTk
import os
from utils import *


# Глобальная переменная для таймера
max_count3 = 0
framex3 = []
county3 = []
max3 = []
avg_acc3_list = []
max_avg_acc3_list = []
max_acc3 = 0
max_avg_acc3 = 0
class CameraPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.content = tk.Frame(self)
        self.content.pack(expand=True, fill="both")
        self.layout = 1
        self.videos = self.get_video_files()
        self.camera_ids = {
            1: 0,  # Camera for class 1
            2: 'Videoes/unihub.mp4',
            3: '',
            4: ''  # Camera for class 2
        }
        self.current_videos = {}  # Словарь для управления видеопотоками по их индексам
        self.paused = {}  # Словарь для контроля состояния паузы видеопотоков
        self.get_content()



    def back_to_menu(self):
        """Возвращение в меню."""
        self.content.destroy()  # Уничтожаем текущее содержимое
        self.content = tk.Frame(self)
        self.content.pack(expand=True, fill="both")
        self.create_buttons_layout()  # Отображаем кнопки снова

    def open_dlg_modal(self, box_index):
        def close_dlg():
            dlg_modal.destroy()

        dlg_modal = tk.Toplevel(self.content)
        dlg_modal.title("Список доступных камер")
        dlg_modal.geometry("400x200")
        dlg_modal.transient(self.content)
        dlg_modal.grab_set()
        print(self.videos)
        print(self.current_videos)

        actions_frame = tk.Frame(dlg_modal)
        actions_frame.pack(padx=10, pady=10)

        for i, (key, media) in enumerate(self.videos.items(), start=1):
            btn_text = f"Камера {i}"
            btn = tk.Button(actions_frame, text=btn_text,
                            command=lambda index=key: self.show_video_in_box(index, box_index, dlg_modal))
            btn.grid(row=i - 1, column=0, padx=5, pady=5)

        cancel_btn = tk.Button(actions_frame, text="Отмена", command=close_dlg)
        cancel_btn.grid(row=len(self.videos), column=0, padx=5, pady=5)

        dlg_modal.protocol("WM_DELETE_WINDOW", close_dlg)

    def get_video_files(self):
        video_files = {}
        videos_directory = "Videoes"  # Название вашей папки с видеофайлами
        if os.path.exists(videos_directory) and os.path.isdir(videos_directory):
            files = os.listdir(videos_directory)
            for i, file in enumerate(files):
                if file.endswith(".mp4") or file.endswith(".avi"):
                    video_files[i] = os.path.join(videos_directory, file)
        return video_files

    def show_video_in_box(self, index, box, dlg_modal):
        if 0 <= index < len(self.videos):
            video_source = self.videos[index]
            cap = cv2.VideoCapture(video_source)
            dlg_modal.destroy()

            # Удаляем предыдущую видео метку из бокса
            for widget in box.winfo_children():
                widget.destroy()

            box_width = box.winfo_width()
            box_height = box.winfo_height()

            ret, frame = cap.read()
            if ret:
                frame_height, frame_width, _ = frame.shape
                aspect_ratio = frame_width / frame_height
                video_width, video_height = self.calculate_video_dimensions(aspect_ratio, box_width, box_height)

                imgtk = self.create_video_image(frame, video_width, video_height)
                video_label = tk.Label(box, width=video_width, height=video_height, image=imgtk)
                video_label.imgtk = imgtk
                video_label.pack(fill="both", expand=True)

                remove_button = tk.Button(box, text="Удалить видео", command=lambda: self.remove_video(video_label, cap, box))
                remove_button.pack(side="bottom")

                self.update_image(cap, video_label, video_width, video_height, index)


    def calculate_video_dimensions(self, aspect_ratio, box_width, box_height):
        if aspect_ratio * box_height > box_width:
            video_height = box_height
            video_width = int(video_height * aspect_ratio)
        else:
            video_width = box_width
            video_height = int(video_width / aspect_ratio)
        return video_width, video_height

    def create_video_image(self, frame, video_width, video_height):
        frame_resized = cv2.resize(frame, (video_width, video_height))
        frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        return ImageTk.PhotoImage(image=img)

    def update_image(self, cap, video_label, video_width, video_height, index):
        global max_count3, framex3, county3, max3, avg_acc3_list, max_avg_acc3_list, max_acc3, max_avg_acc3
        max_count3 = 0
        framex3 = []
        county3 = []
        max3 = []
        avg_acc3_list = []
        max_avg_acc3_list = []
        max_acc3 = 0
        max_avg_acc3 = 0

        odapi = DetectorAPI()
        threshold = 0.7

        x3 = 0

        def analyze_and_update():
            global max_count3, framex3, county3, max3, avg_acc3_list, max_avg_acc3_list, max_acc3, max_avg_acc3, x3
            x3 = 0
            ret, frame = cap.read()
            if ret:
                imgtk = self.create_video_image(frame, video_width, video_height)
                video_label.configure(image=imgtk)
                video_label.imgtk = imgtk

                # Анализируем изображение на наличие людей
                img_resized = cv2.resize(frame, (video_width, video_height))  # Подгоняем размер кадра под детектор
                boxes, scores, classes, num = odapi.processFrame(img_resized)
                person = 0
                acc = 0
                for i in range(len(boxes)):
                    if classes[i] == 1 and scores[i] > threshold:
                        box = boxes[i]
                        person += 1
                        cv2.rectangle(img_resized, (box[1], box[0]), (box[3], box[2]), (255, 0, 0), 2)  # cv2.FILLED
                        cv2.putText(img_resized, f'P{person, round(scores[i], 2)}', (box[1] - 30, box[0] - 8),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 0, 255), 1)  # (75,0,130),
                        acc += scores[i]
                        if (scores[i] > max_acc3):
                            max_acc3 = scores[i]
                if (person > max_count3):
                    max_count3 = person

                county3.append(person)
                x3 += 1
                framex3.append(x3)
                if (person >= 1):
                    avg_acc3_list.append(acc / person)
                    if ((acc / person) > max_avg_acc3):
                        max_avg_acc3 = (acc / person)
                else:
                    avg_acc3_list.append(acc)

                start_periodic_data_insert(person, index)

                for i in range(len(framex3)):
                    max3.append(max_count3)
                    max_avg_acc3_list.append(max_avg_acc3)

                # Повторяем анализ и обновление изображения через 10 миллисекунд
                video_label.after(10, analyze_and_update)

        # Запускаем анализ и обновление изображения в отдельном потоке
        threading.Thread(target=analyze_and_update).start()


    def remove_video(self, video_label, cap, box):
        cap.release()
        stop_periodic_data_insert()
        video_label.destroy()
        for widget in box.winfo_children():
            widget.destroy()
        self.create_initial_box_view(box)

    def create_initial_box_view(self, box):
        btn = tk.Button(box, text="Выбрать камеру", width=15, height=2, font=("Arial", 12), command=lambda b=box: self.open_dlg_modal(b))
        btn.pack(expand=True, fill='both')

    def set_layout(self, layout):
        self.layout = layout
        self.update_content()

    def update_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

        self.create_buttons_layout()

    def create_buttons_layout(self):
        for _ in range(self.layout):
            row = tk.Frame(self.content)
            row.pack(side="top", padx=5, pady=5)

            for _ in range(self.layout):
                # Создаем рамку для кнопки с фиксированным размером и центрированием
                box = tk.Frame(row, bg="blue", bd=5, relief="ridge", width=200, height=200)
                box.pack(side="left", padx=20, pady=20)  # Увеличиваем расстояние между кнопками
                box.grid_propagate(False)  # Отключаем автоматическое изменение размера рамки

                # Создаем кнопку внутри рамки
                btn = tk.Button(box, text="Выбрать камеру", width=15, height=2, font=("Arial", 12),
                                command=lambda b=box: self.open_dlg_modal(b))
                btn.pack(expand=True, fill='both')  # Располагаем кнопку в центре рамки

    def appbar(self):
        app_bar = tk.Frame(self, height=56, bg="#1976D2")
        app_bar.pack(side="top", fill="x")

        label = tk.Label(app_bar, text="Мои камеры", font=("Arial", 20, "bold"), fg="white", bg="#1976D2")
        label.pack(side="left", padx=10)

        # Создаем Menubutton в app_bar, а не в self.content
        pb = tk.Menubutton(app_bar, text="Расположение камер", relief=tk.RAISED)
        pb.menu = tk.Menu(pb, tearoff=0)

        pb.menu.add_command(label="1x1", command=lambda: self.set_layout(1))
        pb.menu.add_command(label="2x2", command=lambda: self.set_layout(2))
        pb.menu.add_command(label="3x3", command=lambda: self.set_layout(3))
        pb.menu.add_command(label="4x4", command=lambda: self.set_layout(4))

        pb["menu"] = pb.menu
        pb.pack(side="right", padx=10, pady=5)

        return app_bar

    def get_content(self):
        app_bar = self.appbar()
        self.set_layout(1)

        # Размещаем app_bar сверху, а self.content заполняет оставшееся пространство
        app_bar.pack(side="top", fill="x")
        self.content.pack(side="top", fill="both", expand=True)

        return app_bar, self.content


