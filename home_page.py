import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import psycopg2
from utils import connect_db

class HomePage(tk.Frame):
    # Конструктор класса HomePage
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        now = datetime.datetime.now()
        # Определение приветствия в зависимости от времени суток
        greeting = "Доброе утро" if 5 <= now.hour < 12 else "Добрый день" if 12 <= now.hour < 18 else "Добрый вечер"

        # Установка и отображение заголовка страницы
        home_label = tk.Label(self, text=f"{greeting}, добро пожаловать на главную страницу", font=("Arial", 16),
                              bg="#ffffff")
        home_label.pack(pady=20)

        # Инициализация содержимого страницы
        self.display_content()

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
            total_people = self.fetch_total_people()
            people_card = tk.Label(frame, text=f"Общее количество обнаруженных людей: {total_people}", font=("Arial", 12),
                                   bg="lightgrey")
            people_card.pack(side=tk.LEFT, padx=10, pady=10, fill="both", expand=True)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при получении данных: {e}")

    def fetch_total_people(self):
        # Извлечение общего количества обнаруженных людей из базы данных
        conn = connect_db()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT SUM(people_count) FROM occupancy")
                    total_people = cur.fetchone()[0]
                return total_people if total_people else 0
            except psycopg2.Error as e:
                messagebox.showerror("Ошибка базы данных", f"Ошибка запроса: {e}")
            finally:
                conn.close()
        else:
            messagebox.showerror("Ошибка подключения", "Не удалось подключиться к базе данных.")

    def display_latest_graphs(self, frame):
        # Отображение последних графиков
        try:
            paths = self.fetch_latest_graphs()
            for path in paths:
                self.display_graph(frame, path)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при отображении графиков: {e}")

    def fetch_latest_graphs(self):
        # Извлечение путей к последним графикам из базы данных
        conn = connect_db()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT graph_path FROM graphs
                        ORDER BY upload_date DESC
                        LIMIT 3
                    """)
                    rows = cur.fetchall()
                    return [row[0] for row in rows]
            except psycopg2.Error as e:
                messagebox.showerror("Ошибка базы данных", f"Ошибка запроса: {e}")
            finally:
                conn.close()
        else:
            messagebox.showerror("Ошибка подключения", "Не удалось подключиться к базе данных.")


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
            print("Ошибка при загрузке изображения: ", e)

    def display_latest_data(self, frame):
        # Отображение последних данных о количестве людей по классам
        conn = connect_db()
        if conn:
            try:
                tree = ttk.Treeview(frame, columns=('class_id', 'people_count'), show='headings')
                tree.heading('class_id', text='ID класса')
                tree.heading('people_count', text='Количество людей')
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT class_id, MAX(people_count) FROM occupancy
                        GROUP BY class_id
                        ORDER BY class_id
                    """)
                    for row in cur:
                        tree.insert('', tk.END, values=row)
                tree.pack()
            except psycopg2.Error as e:
                messagebox.showerror("Ошибка базы данных", f"Ошибка запроса: {e}")
            finally:
                conn.close()
        else:
            messagebox.showerror("Ошибка подключения", "Не удалось подключиться к базе данных.")
