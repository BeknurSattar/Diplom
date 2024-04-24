import tkinter as tk
from tkinter import messagebox
import psycopg2

from auth_page import AuthPage
from utils import *


class RegisterPage(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Регистрация")
        self.geometry("300x400")  # Увеличили высоту окна для удобства
        self.resizable(False, False)
        self.configure(bg="#f0f0f0")

        self.parent = parent

        self.create_widgets()

    def create_widgets(self):
        label_style = {"font": ("Arial", 12), "bg": "#f0f0f0"}
        entry_style = {"font": ("Arial", 12)}

        self.label_username = tk.Label(self, text="Имя пользователя:", **label_style)
        self.label_username.pack(pady=(10, 5))
        self.entry_username = tk.Entry(self, **entry_style)
        self.entry_username.pack(pady=5)

        self.label_email = tk.Label(self, text="Email:", **label_style)
        self.label_email.pack(pady=(5, 5))
        self.entry_email = tk.Entry(self, **entry_style)
        self.entry_email.pack(pady=5)

        self.label_password = tk.Label(self, text="Пароль:", **label_style)
        self.label_password.pack(pady=(5, 5))
        self.entry_password = tk.Entry(self, show="*", **entry_style)
        self.entry_password.pack(pady=5)

        self.label_confirm_password = tk.Label(self, text="Подтвердите пароль:", **label_style)
        self.label_confirm_password.pack(pady=(5, 5))
        self.entry_confirm_password = tk.Entry(self, show="*", **entry_style)
        self.entry_confirm_password.pack(pady=5)

        # Добавление списка должностей
        self.label_position = tk.Label(self, text="Должность:", **label_style)
        self.label_position.pack(pady=(5, 5))
        positions = ["Менеджер", "Администратор", "Разработчик", "Дизайнер"]
        self.selected_position = tk.StringVar(self)
        self.selected_position.set(positions[0])  # Устанавливаем первый элемент списка по умолчанию
        self.option_menu = tk.OptionMenu(self, self.selected_position, *positions)
        self.option_menu.config(font=("Arial", 12))
        self.option_menu.pack(pady=5)

        button_style = {"font": ("Arial", 12), "bg": "#1976D2", "fg": "white", "relief": "flat"}
        self.button_register = tk.Button(self, text="Зарегистрироваться", command=self.register, **button_style)
        self.button_register.pack(pady=(10, 5))



    def register(self):
        username = self.entry_username.get()
        email = self.entry_email.get()
        password = self.entry_password.get()
        confirm_password = self.entry_confirm_password.get()
        position = self.selected_position.get()

        if username and email and password and confirm_password:
            if password == confirm_password:
                conn = connect_db()
                if conn:
                    try:
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO users (username, email, password, position) VALUES (%s, %s, %s, %s)", (username, email, password, position))
                        conn.commit()
                        cursor.close()
                        conn.close()
                        messagebox.showinfo("Успех", "Регистрация прошла успешно!")
                        self.destroy()

                        # Перекидываем пользователя в окно авторизации после успешной регистрации
                        auth_window = AuthPage(self.parent)
                    except psycopg2.Error as e:
                        print("Ошибка при выполнении SQL-запроса:", e)
                        messagebox.showerror("Ошибка", "Произошла ошибка при регистрации. Пожалуйста, попробуйте снова.")
            else:
                messagebox.showerror("Ошибка", "Пароли не совпадают")
        else:
            messagebox.showerror("Ошибка", "Пожалуйста, заполните все поля")

if __name__ == "__main__":
    app = tk.Tk()
    register_window = RegisterPage(app)
    app.mainloop()
