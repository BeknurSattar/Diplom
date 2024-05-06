import tkinter as tk
from tkinter import scrolledtext, messagebox
import psycopg2
from utils import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import io
from PIL import Image, ImageTk

class DataPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent  # Ссылка на родительский виджет
        self.content = tk.Frame(self)  # Основная рамка для содержимого
        self.content.pack(expand=True, fill="both")
        self.get_content()  # Инициализация контента страницы

    def fetch_and_display_data(self, class_id):
        """Получение и отображение данных."""
        try:
            self.conn = connect_db()
            cur = self.conn.cursor()
            # Запрос данных о последних 10 детекциях по class_id
            cur.execute(
                "SELECT detection_date, people_count FROM occupancy WHERE class_id = %s ORDER BY detection_date DESC LIMIT 10;",
                (class_id-1,))
            rows = cur.fetchall()

            display_text = f"Last 10 detections for class {class_id}:\n\n"
            for row in rows:
                display_text += f"Date: {row[0]}, Count: {row[1]}\n"
            self.data_text.delete(1.0, tk.END)
            self.data_text.insert(tk.END, display_text)
            cur.close()
            self.conn.close()
        except psycopg2.Error as e:
            messagebox.showerror("Database Error", f"Ошибка выполнения запроса к базе данных: {e}")
        finally:
            if self.conn:
                self.conn.close()


    def show_class_data(self, class_id):
        """Отображение данных класса или графиков."""
        self.content.destroy()
        self.content = tk.Frame(self)
        self.content.pack(expand=True, fill="both")

        """Получение контента страницы."""
        self.data_text = scrolledtext.ScrolledText(self.content, wrap=tk.WORD, width=50, height=10)
        self.data_text.pack(pady=10)

        # Добавление кнопок для загрузки графиков и данных
        button_frame = tk.Frame(self.content)
        button_frame.pack(pady=10)

        data_button = tk.Button(button_frame, text="Показать данные",
                                command=lambda: self.fetch_and_display_data(class_id))  # Пример class_id=1
        data_button.pack(side="left", padx=5)

        # Кнопки для отображения графиков
        graph1_button = tk.Button(button_frame, text="График 1", command=lambda: self.display_graph(class_id, 1))
        graph1_button.pack(side="left", padx=5)

        graph2_button = tk.Button(button_frame, text="График 2", command=lambda: self.display_graph(class_id, 2))
        graph2_button.pack(side="left", padx=5)

        graph3_button = tk.Button(button_frame, text="График 3", command=lambda: self.display_graph(class_id, 3))
        graph3_button.pack(side="left", padx=5)

        back_button = tk.Button(self.content, text="Back to menu", command=self.back_to_menu)
        back_button.pack(pady=10)

    def display_graph(self, class_id, graph_number):
        """Отображение выбранного графика."""
        img = self.load_graph_from_db(class_id, graph_number)
        if img:
            img = img.resize((500, 400), Image.LANCZOS)  # Адаптация размера изображения
            imgtk = ImageTk.PhotoImage(image=img)

            # Удаляем предыдущий виджет графика, если он существует
            if hasattr(self, 'graph_label'):
                self.graph_label.destroy()

            # Создаем новый виджет графика
            self.graph_label = tk.Label(self.content, image=imgtk)
            self.graph_label.image = imgtk
            self.graph_label.pack(pady=10)
        else:
            print("График не найден или ошибка загрузки.")

    def load_graph_from_db(self, class_id, graph_number):
        """Загрузка графика из базы данных."""
        try:
            self.conn = connect_db()
            cur = self.conn.cursor()
            # Обновленный способ получения graph_type_id
            graph_type_id = graph_number  # Теперь graph_number напрямую соответствует graph_type_id
            cur.execute("""
                SELECT graph_path FROM graphs
                WHERE class_id = %s AND graph_type_id = %s
                ORDER BY upload_date DESC LIMIT 1;
            """, (class_id, graph_type_id))
            graph_path = cur.fetchone()
            if graph_path:
                img = Image.open(graph_path[0])
                return img
            else:
                return None
            # cur.close()
        except psycopg2.Error as e:
            messagebox.showerror("Database Error", f"Ошибка выполнения запроса к базе данных: {e}")
        finally:
            if self.conn:
                self.conn.close()

    def back_to_menu(self):
        """Возвращение в меню."""
        self.content.destroy()
        self.content = tk.Frame(self)
        self.content.pack(expand=True, fill="both")
        self.get_content()

    def create_button(self, index):
        """Создание кнопки для аудитории."""
        button = tk.Button(self.content, text=f"Данные аудиторий {index}",
                           command=lambda i=index: self.show_class_data(i))
        return button

    def generate_buttons(self):
        """Генерация кнопок для аудиторий на основе данных из базы."""
        try:
            self.conn = connect_db()
            cur = self.conn.cursor()
            cur.execute("SELECT DISTINCT class_id FROM occupancy ORDER BY class_id;")
            class_ids = cur.fetchall()
            for class_id in class_ids:
                button = self.create_button(class_id[0] + 1)
                button.pack(anchor="w", pady=(5, 0), padx=10, fill="x")
            cur.close()
            self.conn.close()
        except psycopg2.Error as e:
            messagebox.showerror("Database Error", f"Ошибка подключения или выполнения запроса к базе данных: {e}")
        finally:
            if self.conn:
                self.conn.close()

    def get_content(self):
        """Получение контента страницы."""
        self.generate_buttons()
        return self.content
