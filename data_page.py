import tkinter as tk
from tkinter import scrolledtext
import psycopg2
from utils import *

class DataPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.content = tk.Frame(self)
        self.content.pack(expand=True, fill="both")
        self.get_content()

    def fetch_and_display_data(self, class_id):
        """Получение и отображение данных."""
        try:
            self.conn = connect_db()
            cur = self.conn.cursor()
            cur.execute("SELECT detection_date, people_count FROM occupancy WHERE class_id = %s ORDER BY detection_date DESC LIMIT 10;", (class_id,))
            rows = cur.fetchall()
            display_text = f"Last 10 detections for class {class_id}:\n\n"
            for row in rows:
                display_text += f"Date: {row[0]}, Count: {row[1]}\n"
            self.data_text.delete(1.0, tk.END)  # Очищаем текстовое поле
            self.data_text.insert(tk.END, display_text)
            cur.close()
            self.conn.close()
            self.content.update()
        except psycopg2.Error as e:
            print("Ошибка выполнения запроса к базе данных: ", e)

    def show_class_data(self, class_id):
        """Отображение данных класса."""
        self.content.destroy()
        self.content = tk.Frame(self)
        self.content.pack(expand=True, fill="both")

        self.data_text = scrolledtext.ScrolledText(self.content, wrap=tk.WORD, width=50, height=20)
        self.data_text.pack(pady=10)

        fetch_data_button = tk.Button(self.content, text="Fetch Data", command=lambda: self.fetch_and_display_data(class_id))
        fetch_data_button.pack(pady=10)

        back_button = tk.Button(self.content, text="Back to menu", command=self.back_to_menu)
        back_button.pack(pady=10)

    def back_to_menu(self):
        """Возвращение в меню."""
        self.content.destroy()  # Уничтожаем текущее содержимое
        self.content = tk.Frame(self)
        self.content.pack(expand=True, fill="both")
        self.get_content()  # Отображаем кнопки снова

    def create_button(self, index):
        """Создание кнопки для аудитории."""
        button = tk.Button(self.content, text=f"Данные аудиторий {index}", command=lambda i=index: self.show_class_data(i))
        return button

    def generate_buttons(self):
        """Генерация кнопок для аудиторий."""
        for i in range(1, 11):
            button = self.create_button(i)
            button.pack(anchor="w", pady=(5, 0), padx=10, fill="x")

    def get_content(self):
        """Получение контента страницы."""
        self.generate_buttons()
        return self.content
