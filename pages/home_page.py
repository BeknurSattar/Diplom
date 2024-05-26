import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import psycopg2
import requests
from Helps.utils import connect_db
from Helps.translations import translations

SERVER_URL = "http://127.0.0.1:5000"

class HomePage(tk.Frame):
    # Конструктор класса HomePage
    def __init__(self, parent, app, user_id=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        now = datetime.datetime.now()
        self.app = app  # Ссылка на главное приложение
        self.user_id = user_id
        # Определение приветствия в зависимости от времени суток

        # Установка и отображение заголовка страницы
        self.home_label = tk.Label(self,  font=("Arial", 16),
                              bg="#ffffff")
        self.home_label.pack(pady=20)

        # Инициализация содержимого страницы
        self.display_content()

    translation_key = 'home'
    def set_language(self, language):
        now = datetime.datetime.now()
        # Обновляем приветствие в зависимости от времени суток и выбранного языка
        greeting = translations[language]["good_morning"] if 5 <= now.hour < 12 else \
            translations[language]["good_afternoon"] if 12 <= now.hour < 18 else \
                translations[language]["good_evening"]

        self.home_label.config(text=f"{greeting}, {translations[language]['welcome_home']}")
        # Обновление текста на информационных карточках
        self.people_card.config(text=f"{translations[language]['total_detected_people']}: {self.fetch_total_people()}")

    def display_content(self):
        # Размещение фреймов для информационных карточек, графиков и данных
        info_frame = tk.Frame(self)
        info_frame.pack(pady=10, fill="x")

        graphs_frame = tk.Frame(self)
        graphs_frame.pack(pady=10, fill="x")

        data_frame = tk.Frame(self)
        data_frame.pack(pady=10, fill="x")

        # Отображение содержимого в соответствующих фреймах
        self.display_info_cards(info_frame)
        self.display_latest_graphs(graphs_frame)
        self.display_latest_data(data_frame)

    def display_info_cards(self, frame):
        # Отображение информационной карточки с общим количеством обнаруженных людей
        try:
            self.people_card = tk.Label(frame, font=("Arial", 12),
                                   bg="lightgrey")
            self.people_card.pack(side=tk.LEFT, padx=10, pady=10, fill="both", expand=True)
        except Exception as e:
            error_msg = translations[self.app.current_language]['fetch_data_error'].format(error=e)
            messagebox.showerror(translations[self.app.current_language]['error'], error_msg)

    def fetch_total_people(self):
        # Извлечение общего количества обнаруженных людей из базы данных
        try:
            response = requests.get(f"{SERVER_URL}/total_people", params={"user_id": self.user_id})
            if response.status_code == 200:
                data = response.json()
                return data["total_people"]
            else:
                error_msg = translations[self.app.current_language]['database_error_message'].format(
                    error=response.json().get("error"))
                messagebox.showerror(translations[self.app.current_language]['database_error'], error_msg)
        except Exception as e:
            error_msg = translations[self.app.current_language]['fetch_data_error'].format(error=e)
            messagebox.showerror(translations[self.app.current_language]['error'], error_msg)

    def display_latest_graphs(self, frame):
        # Отображение последних графиков
        try:
            response = requests.get(f"{SERVER_URL}/latest_graphs", params={"user_id": self.user_id})
            if response.status_code == 200:
                paths = response.json().get("graph_paths", [])
                center_frame = tk.Frame(frame)
                center_frame.pack(fill="both", expand=True)

                if paths:
                    for path in paths:
                        self.display_graph(center_frame, path)
                    center_frame.pack(side="top", fill="x", expand=True)
                else:
                    label = tk.Label(center_frame, text=translations[self.app.current_language]['no_graphs_found'],
                                     font=("Arial", 12))
                    label.pack(side="top", pady=20)
            else:
                error_msg = translations[self.app.current_language]['database_query_error'].format(
                    error=response.json().get("error"))
                messagebox.showerror(translations[self.app.current_language]['database_error'], error_msg)
        except Exception as e:
            error_msg = translations[self.app.current_language]['graph_error'].format(error=e)
            messagebox.showerror(translations[self.app.current_language]['error'], error_msg)

    def fetch_latest_graphs(self):
        # Извлечение путей к последним графикам каждого типа графика, добавленных этим пользователем, из базы данных
        conn = connect_db()
        if conn:
            try:
                with conn.cursor() as cur:
                    # Сначала получаем время последней сессии для каждого типа графика
                    cur.execute("""
                        SELECT graph_type_id, MAX(session_start) as last_session_start
                        FROM graphs
                        WHERE user_id = %s
                        GROUP BY graph_type_id
                    """, (self.user_id,))
                    latest_sessions = cur.fetchall()

                    # Затем, для каждого типа графика, получаем путь к последнему графику из последней сессии
                    graph_paths = []
                    for graph_type_id, last_session_start in latest_sessions:
                        cur.execute("""
                            SELECT graph_path FROM graphs
                            WHERE graph_type_id = %s AND session_start = %s AND user_id = %s;
                        """, (graph_type_id, last_session_start, self.user_id))
                        result = cur.fetchone()
                        if result:
                            graph_paths.append(result[0])

                    return graph_paths
            except psycopg2.Error as e:
                error_msg = translations[self.app.current_language]['database_query_error'].format(error=e)
                messagebox.showerror(translations[self.app.current_language]['database_error'], error_msg)
            finally:
                conn.close()
        else:
            messagebox.showerror(translations[self.app.current_language]['error_connecting_to_database'],
                                 translations[self.app.current_language]['connection_error'])

    def display_graph(self, frame, path):
        # Загрузка и отображение графика
        try:
            img = Image.open(path)
            img = img.resize((200, 200), Image.LANCZOS)
            imgtk = ImageTk.PhotoImage(image=img)
            label = tk.Label(frame, image=imgtk)
            label.image = imgtk
            label.pack(side=tk.LEFT, padx=10)
        except Exception as e:
            print(translations[self.app.current_language]['loading_image_error'].format(error=e))

    def display_latest_data(self, frame):
        try:
            response = requests.get(f"{SERVER_URL}/latest_data", params={"user_id": self.user_id})
            if response.status_code == 200:
                data = response.json().get("data", [])
                tree = ttk.Treeview(frame, columns=('class_id', 'people_count'), show='headings')
                tree.heading('class_id', text=translations[self.app.current_language]['class_id'])
                tree.heading('people_count', text=translations[self.app.current_language]['people_count'])

                for row in data:
                    tree.insert('', tk.END, values=row)
                tree.pack()
            else:
                error_msg = translations[self.app.current_language]['database_query_error'].format(
                    error=response.json().get("error"))
                messagebox.showerror(translations[self.app.current_language]['error'], error_msg)
        except Exception as e:
            error_msg = translations[self.app.current_language]['database_query_error'].format(error=e)
            messagebox.showerror(translations[self.app.current_language]['error'], error_msg)