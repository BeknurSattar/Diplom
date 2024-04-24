import tkinter as tk
from tkinter import messagebox, simpledialog

import cv2
from PIL import Image, ImageTk
import os
from persondetection import DetectorAPI
import matplotlib.pyplot as plt
from fpdf import FPDF
import psycopg2
from datetime import datetime
from utils import *
import base64

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
            # Add more classes and cameras as needed
        }
        self.get_content()

    def open_cam(self, class_id):
        camera_id = self.camera_ids[class_id]
        self.detectByCamera(camera_id, class_id)

    def first_frame(self, camera_id):
        first_frame = None
        video = cv2.VideoCapture(camera_id)
        while True:
            frame = video.read()
            img = cv2.resize(frame, (800, 600))
            if first_frame is None:
                first_frame = img.copy()
        return first_frame

    def detectByCamera(self, camera_id, class_id):
        global max_count3, framex3, county3, max3, avg_acc3_list, max_avg_acc3_list, max_acc3, max_avg_acc3
        max_count3 = 0
        framex3 = []
        county3 = []
        max3 = []
        avg_acc3_list = []
        max_avg_acc3_list = []
        max_acc3 = 0
        max_avg_acc3 = 0

        # function defined to plot the people count in camera

        video = cv2.VideoCapture(camera_id)
        odapi = DetectorAPI()
        threshold = 0.7

        x3 = 0
        while True:
            check, frame = video.read()
            if not check:
                break
            img = cv2.resize(frame, (800, 600))

            boxes, scores, classes, num = odapi.processFrame(img)
            person = 0
            acc = 0
            for i in range(len(boxes)):
                if classes[i] == 1 and scores[i] > threshold:
                    box = boxes[i]
                    person += 1
                    cv2.rectangle(img, (box[1], box[0]), (box[3], box[2]), (255, 0, 0), 2)  # cv2.FILLED
                    cv2.putText(img, f'P{person, round(scores[i], 2)}', (box[1] - 30, box[0] - 8),
                                cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 0, 255), 1)  # (75,0,130),
                    acc += scores[i]
                    if (scores[i] > max_acc3):
                        max_acc3 = scores[i]

            if (person > max_count3):
                max_count3 = person

            # if writer is not None:
            #     writer.write(img)

            cv2.imshow("Analiz", img)
            key = cv2.waitKey(1)
            if key & 0xFF == ord('q'):
                # Функция остановки таймера
                stop_periodic_data_insert()
                break

            county3.append(person)
            x3 += 1
            framex3.append(x3)
            if (person >= 1):
                avg_acc3_list.append(acc / person)
                if ((acc / person) > max_avg_acc3):
                    max_avg_acc3 = (acc / person)
            else:
                avg_acc3_list.append(acc)

            start_periodic_data_insert(person, class_id)

        video.release()

        def cam_enumeration_plot():
            plt.figure(facecolor='orange', )
            ax = plt.axes()
            ax.set_facecolor("yellow")
            plt.plot(framex3, county3, label="Human Count", color="green", marker='o', markerfacecolor='blue')
            plt.plot(framex3, max3, label="Max. Human Count", linestyle='dashed', color='fuchsia')
            plt.xlabel('Time (sec)')
            plt.ylabel('Human Count')
            plt.legend()
            plt.title("Enumeration Plot")
            plt.show()

        def cam_accuracy_plot():
            plt.figure(facecolor='orange', )
            ax = plt.axes()
            ax.set_facecolor("yellow")
            plt.plot(framex3, avg_acc3_list, label="Avg. Accuracy", color="green", marker='o', markerfacecolor='blue')
            plt.plot(framex3, max_avg_acc3_list, label="Max. Avg. Accuracy", linestyle='dashed', color='fuchsia')
            plt.xlabel('Time (sec)')
            plt.ylabel('Avg. Accuracy')
            plt.title('Avg. Accuracy Plot')
            plt.legend()
            plt.show()

        def cam_gen_report():
            pdf = FPDF(orientation='P', unit='mm', format='A4')
            pdf.add_page()
            pdf.set_font("Arial", "", 20)
            pdf.set_text_color(128, 0, 0)
            pdf.image('Images/eyeee.png', x=0, y=0, w=210, h=297)

            pdf.text(125, 150, str(max_count3))
            pdf.text(105, 163, str(max_acc3))
            pdf.text(125, 175, str(max_avg_acc3))
            if (max_count3 > 25):
                pdf.text(26, 220, "Max. Human Detected is greater than MAX LIMIT.")
                pdf.text(70, 235, "Region is Crowded.")
            else:
                pdf.text(26, 220, "Max. Human Detected is in range of MAX LIMIT.")
                pdf.text(65, 235, "Region is not Crowded.")

            pdf.output('Crowd_Report.pdf')

        for i in range(len(framex3)):
            max3.append(max_count3)
            max_avg_acc3_list.append(max_avg_acc3)

        # enumeration_button = TextButton(text="Enumeration\nPlot", on_click=lambda e: cam_enumeration_plot())
        # self.content.controls.append(enumeration_button)
        #
        # avga_button = TextButton(text="Avg. Accuracy\nPlot", on_click=lambda e: cam_accuracy_plot())
        # self.content.controls.append(avga_button)
        #
        # generate_button = TextButton(text="Generate  Crowd  Report", on_click=lambda e: cam_gen_report())
        # self.content.controls.append(generate_button)
        #
        # back_button = TextButton(text="Back to menu", on_click=lambda e: self.back_to_menu())
        # self.content.controls.append(back_button)

        self.content.update()

    def back_to_menu(self):
        """Возвращение в меню."""
        self.content.destroy()  # Уничтожаем текущее содержимое
        self.content = tk.Frame(self)
        self.content.pack(expand=True, fill="both")
        self.get_content()  # Отображаем кнопки снова


    def open_dlg_modal(self, box):
        def close_dlg():
            dlg_modal.destroy()

        dlg_modal = tk.Toplevel(self.content)
        dlg_modal.title("Список доступных камер")
        dlg_modal.geometry("400x200")
        dlg_modal.transient(self.content)
        dlg_modal.grab_set()

        actions_frame = tk.Frame(dlg_modal)
        actions_frame.pack(padx=10, pady=10)

        for i, media in enumerate(self.camera_ids):
            btn_text = f"Камера {i + 1}"
            btn = tk.Button(actions_frame, text=btn_text,
                            command=lambda index=media: self.show_video_in_box(index, box, dlg_modal))
            btn.grid(row=i, column=0, padx=5, pady=5)

        cancel_btn = tk.Button(actions_frame, text="Отмена", command=close_dlg)
        cancel_btn.grid(row=len(self.camera_ids), column=0, padx=5, pady=5)

        dlg_modal.protocol("WM_DELETE_WINDOW", close_dlg)

    def get_video_files(self):
        video_files = []
        videos_directory = "Videoes"  # Название вашей папки с видеофайлами
        if os.path.exists(videos_directory) and os.path.isdir(videos_directory):
            for file in os.listdir(videos_directory):
                if file.endswith(".mp4") or file.endswith(".avi"):
                    video_files.append(os.path.join(videos_directory, file))
        return video_files

    def show_video_in_box(self, index, box, dlg_modal):
        if 0 <= index < len(self.videos):
            video_source = self.videos[index]
            cap = cv2.VideoCapture(video_source)
            dlg_modal.destroy()

            # Удаляем предыдущую видео метку из бокса
            for widget in box.winfo_children():
                widget.destroy()

            # Рассчитываем размеры видео в зависимости от количества боксов
            num_boxes = self.layout * self.layout
            box_width = box.winfo_width()
            box_height = box.winfo_height()

            # Читаем первый кадр из видеопотока
            ret, frame = cap.read()

            # Проверяем успешность чтения кадра
            if ret:
                # Получаем размеры кадра
                frame_height, frame_width, _ = frame.shape

                # Рассчитываем соотношение сторон кадра
                aspect_ratio = frame_width / frame_height

                # Определяем, какое измерение (ширина или высота) бокса ограничивает размеры видео
                if aspect_ratio * box_height > box_width:
                    # Если ширина видео слишком большая, масштабируем по высоте бокса
                    video_height = box_height
                    video_width = int(video_height * aspect_ratio)
                else:
                    # Иначе масштабируем по ширине бокса
                    video_width = box_width
                    video_height = int(video_width / aspect_ratio)

                # Шкалируем кадр до новых размеров
                frame_resized = cv2.resize(frame, (video_width, video_height))

                # Конвертируем кадр из формата BGR в RGB
                frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)

                # Создаем изображение PIL из кадра
                img = Image.fromarray(frame_rgb)

                # Создаем объект PhotoImage изображения
                imgtk = ImageTk.PhotoImage(image=img)

                # Создаем метку для отображения видео
                video_label = tk.Label(box, width=video_width, height=video_height, image=imgtk)
                video_label.imgtk = imgtk  # Сохраняем ссылку на объект PhotoImage, чтобы избежать удаления из памяти
                video_label.pack(fill="both", expand=True)

                # Функция для обновления изображения на метке
                def update_image():
                    ret, frame = cap.read()
                    if ret:
                        # Масштабируем новый кадр и конвертируем его в RGB
                        frame_resized = cv2.resize(frame, (video_width, video_height))
                        frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
                        img = Image.fromarray(frame_rgb)
                        imgtk = ImageTk.PhotoImage(image=img)
                        video_label.configure(image=imgtk)
                        video_label.imgtk = imgtk
                        video_label.after(10, update_image)  # Обновляем изображение каждые 10 миллисекунд

                # Запускаем обновление изображения
                update_image()

            # Закрываем видеопоток при закрытии окна
            def on_closing():
                cap.release()
                dlg_modal.destroy()

            dlg_modal.protocol("WM_DELETE_WINDOW", on_closing)

        else:
            print("Недопустимый индекс видео")
            print(self.videos)

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