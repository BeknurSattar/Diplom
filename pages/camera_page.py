import time
import tkinter as tk
from tkinter import messagebox
from Helps.translations import translations
from PIL import Image, ImageTk
import os
from matplotlib import pyplot as plt
import datetime
from Helps.utils import *
import cv2
from detection.persondetection import DetectorAPI

class CameraPage(tk.Frame):
    """Страница управления видеокамерами и обработкой видео потоков."""
    def __init__(self, parent, app, user_id=None):
        super().__init__(parent)
        self.parent = parent
        self.content = tk.Frame(self)
        self.user_id = user_id
        self.app = app
        self.current_language = 'ru'
        self.content.pack(expand=True, fill="both")
        self.layout = 1
        # Загрузка списка доступных видео файлов с учетом должности пользователя
        self.videos = self.get_video_files_for_user()
        self.odapi = DetectorAPI()  # Подключение API для обнаружения объектов в видео
        self.get_video_files()
        self.get_content()

    translation_key = 'camera'

    def set_language(self, language):
        self.current_language = language
        # Обновление текстов виджетов

        if hasattr(self, 'cancel_btn'):
            self.cancel_btn.config(text=translations[language]['cancel'])
        if hasattr(self, 'remove_button'):
            self.remove_button.config(text=translations[language]['remove_video'])
        if hasattr(self, 'save_button'):
            self.save_button.config(text=translations[language]['save_graphs'])
        if hasattr(self, 'select_camera_button'):
            self.select_camera_button.config(text=translations[language]['select_camera'])

        # Обновляем текст в заголовке модального окна
        if hasattr(self, 'dlg_modal'):
            self.dlg_modal.title(translations[language]['available_cameras'])

        # Обновляем текст в приложении (app_bar)
        if hasattr(self, 'my_cameras_label'):
            self.my_cameras_label.config(text=translations[language]['my_cameras'])
        if hasattr(self, 'pb'):
            self.pb.config(text=translations[language]['camera_layout'])

        # Обновляем тексты кнопок в диалоговом окне, если оно открыто
        if hasattr(self, 'camera_buttons'):
            for i, btn in self.camera_buttons.items():
                btn.config(text=translations[language]['camera_btn'].format(number=i))

    def get_video_files(self):
        """Сканирует директорию на наличие видео файлов и добавляет их в базу данных."""
        video_files = {}
        videos_directory = "Videoes"  # Название вашей папки с видеофайлами
        if os.path.exists(videos_directory) and os.path.isdir(videos_directory):
            files = os.listdir(videos_directory)
            conn = connect_db()  # Предполагается, что есть функция для подключения к БД
            cursor = conn.cursor()
            for i, file in enumerate(files, start=1):
                if file.endswith(".mp4") or file.endswith(".avi"):
                    video_path = os.path.join(videos_directory, file)
                    video_files[i] = video_path
                    # Добавление файла в базу данных, если он еще не добавлен
                    try:
                        cursor.execute(
                            "INSERT INTO cameras (name, path) VALUES (%s, %s) ON CONFLICT (path) DO NOTHING;",
                            (file, video_path)
                        )
                        conn.commit()
                    except psycopg2.Error as e:
                        print("Ошибка при добавлении видео файла в базу данных:", e)
            cursor.close()
            conn.close()
        return video_files

    def get_user_position_id(self):
        """Получение ID должности пользователя из базы данных."""
        if self.user_id is None:
            print("user_id не установлен.")
            return None

        position_id = None
        try:
            conn = connect_db()
            if conn is None:
                print("Не удалось подключиться к базе данных.")
                return None

            cursor = conn.cursor()
            cursor.execute("SELECT position_id FROM users WHERE user_id = %s;", (self.user_id,))
            result = cursor.fetchone()
            if result:
                position_id = result[0]
            else:
                print(f"Не найден position_id для user_id {self.user_id}.")
            cursor.close()
        except Exception as e:
            print(f"Ошибка при получении ID должности: {e}")
        finally:
            if conn:
                conn.close()

        return position_id

    # Проверка доступных камер для пользователя
    def get_video_files_for_user(self):
        """Получение списка доступных видео файлов из базы данных в зависимости от должности пользователя."""
        video_files = {}
        position_id = self.get_user_position_id()  # Получаем ID должности пользователя

        if position_id is None:
            print("Не удалось получить ID должности пользователя.")
            return video_files

        try:
            conn = connect_db()
            if conn is None:
                print("Не удалось подключиться к базе данных.")
                return video_files

            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.id, c.path
                FROM cameras c
                JOIN camera_permissions cp ON c.id = cp.camera_id
                WHERE cp.position_id = %s;
                """, (position_id,))
            video_files = {row[0]: row[1] for row in cursor.fetchall()}  # Используем строковый ключ для ID
            cursor.close()
        except Exception as e:
            print(f"Ошибка при получении доступных видео: {e}")
        finally:
            if conn:
                conn.close()

        return video_files

    def show_video_in_box(self, index, box, dlg_modal):
        """Отображение видео в выбранном контейнере."""
        if 0 <= index <= len(self.videos):
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

                self.remove_button = tk.Button(box, text=translations[self.current_language]['remove_video'],
                                          command=lambda: self.remove_video(video_label, cap, box))
                self.remove_button.pack(side="left", padx=5)

                # Добавим кнопку для сохранения графиков, которая будет активирована позже
                self.save_button = tk.Button(box, text=translations[self.current_language]['save_graphs'], command=lambda: self.create_and_save_graphs(
                    self.people_data, self.accuracy_data, self.processing_speed_data, index), state=tk.DISABLED)
                self.save_button.pack(side="left", padx=5)

                # Начать обновление изображения
                self.update_image(cap, video_label, video_width, video_height, index, self.save_button)

    def calculate_video_dimensions(self, aspect_ratio, box_width, box_height):
        """Расчет оптимальных размеров видео для отображения."""
        if aspect_ratio * box_height > box_width:
            video_height = box_height
            video_width = int(video_height * aspect_ratio)
        else:
            video_width = box_width
            video_height = int(video_width / aspect_ratio)
        return video_width, video_height

    def create_video_image(self, frame, video_width, video_height):
        """Создание изображения для отображения в интерфейсе из кадра видео."""
        frame_resized = cv2.resize(frame, (video_width, video_height))
        frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        return ImageTk.PhotoImage(image=img)

    def update_image(self, cap, video_label, video_width, video_height, index, save_button):
        """Обновление изображения в интерфейсе и обработка видео потока."""
        global max_count3, county3,  avg_acc3_list,  max_acc3, max_avg_acc3
        # Сброс переменных состояния
        max_acc3 = 0
        max_avg_acc3 = 0

        max_count3 = 0
        county3 = []
        avg_acc3_list = []
        threshold = 0.7  # Порог обнаружения

        people_data = []  # Список для хранения данных о количестве людей по времени
        accuracy_data = []  # Список для хранения данных о точности определения по времени
        processing_speed_data = []  # Список для хранения данных о скорости обработки кадров

        def analyze_and_update():
            """Функция анализа видео кадра и обновления интерфейса."""
            global max_count3, county3,  avg_acc3_list,  max_acc3, max_avg_acc3
            start_time = time.time()  # Засекаем время начала обработки кадра

            ret, frame = cap.read()
            if ret:
                imgtk = self.create_video_image(frame, video_width, video_height)
                video_label.configure(image=imgtk)
                video_label.imgtk = imgtk

                # Анализируем изображение на наличие людей
                img_resized = cv2.resize(frame, (video_width, video_height))  # Подгоняем размер кадра под детектор
                boxes, scores, classes, num = self.odapi.processFrame(img_resized)
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


                if (person >= 1):
                    avg_acc3_list.append(acc / person)
                    if ((acc / person) > max_avg_acc3):
                        max_avg_acc3 = (acc / person)
                else:
                    avg_acc3_list.append(acc)

                start_periodic_data_insert(person, index)

                # Сохранение данных
                people_data.append(person)
                accuracy_data.append(acc / person if person > 0 else 0)

                # Подсчет скорости обработки
                end_time = time.time()  # Засекаем время окончания обработки кадра
                processing_time = end_time - start_time
                fps = 1 / processing_time if processing_time > 0 else 0
                processing_speed_data.append(fps)

                # Повторение обработки через заданный интервал
                video_label.after(33, analyze_and_update)
            else:
                # Создаем графики и сохраняем их
                # Видео закончилось, активируем кнопку сохранения графиков
                save_button.config(state=tk.NORMAL)
                # Сохраняем данные в атрибуты класса для доступа при сохранении
                self.people_data = people_data
                self.accuracy_data = accuracy_data
                self.processing_speed_data = processing_speed_data
                cap.release()



        # Запускаем анализ и обновление изображения в отдельном потоке
        threading.Thread(target=analyze_and_update).start()

    def create_and_save_graphs(self, people_data, accuracy_data, processing_speed_data, class_id):
        """Создание и сохранение графиков по данным."""
        base_directory = 'saved_graphs'
        if not os.path.exists(base_directory):
            os.makedirs(base_directory)

        # Форматируем текущую дату и время для включения в имя файла
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Соединяемся с базой данных для получения идентификаторов и названий типов графиков
        conn = connect_db()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT id, type_name FROM graph_types;")
                graph_types = cursor.fetchall()

                # Проходим по всем типам графиков и сохраняем соответствующие файлы
                for graph_type_id, graph_type_name in graph_types:
                    # Создание папки для каждого типа графика
                    type_directory = os.path.join(base_directory, graph_type_name)
                    if not os.path.exists(type_directory):
                        os.makedirs(type_directory)

                    graph_filename = os.path.join(type_directory, f'{graph_type_name}_{class_id}_{date_str}.png')
                    plt.figure()
                    # Setup data based on graph type
                    if graph_type_name == 'people_graph':
                        data = people_data
                        title = translations[self.app.current_language]['number_of_people_over_time']
                    elif graph_type_name == 'accuracy_graph':
                        data = accuracy_data
                        title = translations[self.app.current_language]['accuracy_over_time']
                    else:  # processing_speed_graph
                        data = processing_speed_data
                        title = translations[self.app.current_language]['processing_speed_over_time']

                    plt.plot(data)
                    plt.title(title)
                    plt.xlabel(translations[self.app.current_language]['time'])
                    plt.ylabel(translations[self.app.current_language][f'{graph_type_name}_y_label'])
                    plt.savefig(graph_filename)
                    plt.close()

                    # Сохраняем информацию о графике в базу данных
                    cursor.execute(
                        "INSERT INTO graphs (class_id, graph_type_id, graph_path, upload_date) VALUES (%s, %s, %s, %s);",
                        (class_id, graph_type_id, graph_filename, datetime.now()))

                conn.commit()
                print(translations[self.app.current_language]['graphs_created_and_saved'])
            except Exception as e:
                error_msg = translations[self.app.current_language]['error_saving_graphs'].format(error=str(e))
                messagebox.showerror(translations[self.app.current_language]['error'], error_msg)
            finally:
                cursor.close()
                conn.close()
        else:
            messagebox.showerror(translations[self.app.current_language]['database_connection_error'],
                                 translations[self.app.current_language]['database_connection_error'])

    def remove_video(self, video_label, cap, box):
        """Удаление видео из интерфейса и остановка анализа видео."""
        cap.release()
        stop_periodic_data_insert()
        video_label.destroy()
        for widget in box.winfo_children():
            widget.destroy()
        self.create_initial_box_view(box)

    def open_dlg_modal(self, box_index):
        """Открытие модального окна для выбора видео источника."""
        def close_dlg():
            dlg_modal.destroy()

        dlg_modal = tk.Toplevel(self.content)
        dlg_modal.title(translations[self.current_language]['available_cameras'])
        dlg_modal.geometry("400x200")
        dlg_modal.transient(self.content)
        dlg_modal.grab_set()
        print(self.videos)


        actions_frame = tk.Frame(dlg_modal)
        actions_frame.pack(padx=10, pady=10)

        for i, (key, medio) in enumerate(self.videos.items(), start=1):
            btn_text = translations[self.current_language]['camera_btn'].format(number=i)
            btn = tk.Button(actions_frame, text=btn_text,
                            command=lambda index=key: self.show_video_in_box(index, box_index, dlg_modal))
            btn.grid(row=i-1, column=0, padx=5, pady=5)

        self.cancel_btn = tk.Button(actions_frame, text=translations[self.current_language]['cancel'], command=close_dlg)
        self.cancel_btn.grid(row=len(self.videos), column=0, padx=5, pady=5)

        dlg_modal.protocol("WM_DELETE_WINDOW", close_dlg)

    def create_initial_box_view(self, box):
        """Создание начального вида контейнера для видео."""
        btn = tk.Button(box, text=translations[self.current_language]['select_camera'], width=15, height=2, font=("Arial", 12), command=lambda b=box: self.open_dlg_modal(b))
        btn.pack(expand=True, fill='both')

    def set_layout(self, layout):
        """Установка расположения виджетов в интерфейсе."""
        self.layout = layout
        self.update_content()

    def update_content(self):
        """Обновление содержимого интерфейса в зависимости от выбранного расположения."""
        for widget in self.content.winfo_children():
            widget.destroy()

        self.create_buttons_layout()

    def create_buttons_layout(self):
        """Создание расположения кнопок для выбора камер."""
        for _ in range(self.layout):
            row = tk.Frame(self.content)
            row.pack(side="top", padx=5, pady=5)

            for _ in range(self.layout):
                # Создаем рамку для кнопки с фиксированным размером и центрированием
                box = tk.Frame(row, bg="blue", bd=5, relief="ridge", width=200, height=200)
                box.pack(side="left", padx=20, pady=20)  # Увеличиваем расстояние между кнопками
                box.grid_propagate(False)  # Отключаем автоматическое изменение размера рамки

                # Создаем кнопку внутри рамки
                self.select_camera_button = tk.Button(box, text=translations[self.current_language]['select_camera'], width=15, height=2, font=("Arial", 12),
                                command=lambda b=box: self.open_dlg_modal(b))
                self.select_camera_button.pack(expand=True, fill='both')  # Располагаем кнопку в центре рамки

    def back_to_menu(self):
        """Возвращение в меню."""
        self.content.destroy()  # Уничтожаем текущее содержимое
        self.content = tk.Frame(self)
        self.content.pack(expand=True, fill="both")
        self.create_buttons_layout()  # Отображаем кнопки снова

    def appbar(self):
        """Создание панели приложения с навигационными кнопками."""
        app_bar = tk.Frame(self, height=56, bg="#1976D2")
        app_bar.pack(side="top", fill="x")

        self.my_cameras_label = tk.Label(app_bar, text=translations[self.current_language]['my_cameras'], font=("Arial", 20, "bold"), fg="white", bg="#1976D2")
        self.my_cameras_label.pack(side="left", padx=10)

        # Создаем Menubutton в app_bar, а не в self.content
        self.pb = tk.Menubutton(app_bar, text=translations[self.current_language]['camera_layout'], relief=tk.RAISED)
        self.pb.menu = tk.Menu(self.pb, tearoff=0)

        self.pb.menu.add_command(label="1x1", command=lambda: self.set_layout(1))
        self.pb.menu.add_command(label="2x2", command=lambda: self.set_layout(2))
        self.pb.menu.add_command(label="3x3", command=lambda: self.set_layout(3))
        self.pb.menu.add_command(label="4x4", command=lambda: self.set_layout(4))

        self.pb["menu"] = self.pb.menu
        self.pb.pack(side="right", padx=10, pady=5)

        return app_bar

    def get_content(self):
        """Получение и настройка начального содержимого страницы."""
        app_bar = self.appbar()
        self.set_layout(1)

        # Размещаем app_bar сверху, а self.content заполняет оставшееся пространство
        app_bar.pack(side="top", fill="x")
        self.content.pack(side="top", fill="both", expand=True)

        return app_bar, self.content
