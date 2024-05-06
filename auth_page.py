import tkinter as tk
from tkinter import messagebox
import psycopg2
import bcrypt
from utils import connect_db  # Подключение функции соединения с базой данных

class AuthPage(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Авторизация")
        self.geometry("300x330")   # Установка размера окна
        self.resizable(False, False)  # Окно не может быть изменено в размере
        self.configure(bg="#f0f0f0")  # Фоновый цвет окна
        self.lift()  # Поднять окно на передний план
        self.parent = parent
        self.is_authenticated = False  # Статус аутентификации пользователя
        self.user_id = None  # ID аутентифицированного пользователя
        self.create_widgets()  # Создание виджетов окна

    def create_widgets(self):
        # Стили для виджетов
        label_style = {"font": ("Arial", 12), "bg": "#f0f0f0"}
        entry_style = {"font": ("Arial", 12)}

        # Создание и размещение виджетов для ввода почты и пароля
        self.label_email = tk.Label(self, text="Электронная почта:", **label_style)
        self.label_email.pack(pady=(10, 5))
        self.entry_email = tk.Entry(self, **entry_style)
        self.entry_email.pack(pady=5)

        self.label_password = tk.Label(self, text="Пароль:", **label_style)
        self.label_password.pack(pady=(5, 5))
        self.entry_password = tk.Entry(self, show="*", **entry_style)
        self.entry_password.pack(pady=5)

        # Чекбокс для показа/скрытия пароля
        self.show_password_var = tk.BooleanVar(value=False)
        self.show_password_checkbox = tk.Checkbutton(self, text="Показать пароль", variable=self.show_password_var, bg="#f0f0f0", command=self.toggle_password_visibility)
        self.show_password_checkbox.pack(pady=(5, 10))

        # Кнопки для входа, регистрации и входа через Google
        button_style = {"font": ("Arial", 12), "bg": "#1976D2", "fg": "white", "relief": "flat"}
        self.button_login = tk.Button(self, text="Войти", command=self.login, **button_style)
        self.button_login.pack(pady=(5, 5))

        self.button_register = tk.Button(self, text="Зарегистрироваться", command=self.open_register_window, **button_style)
        self.button_register.pack(pady=(0, 5))

        self.button_google = tk.Button(self, text="Войти через Google", command=self.login_with_google, **button_style)
        self.button_google.pack(pady=(0, 10))

    def login(self):
        # Метод для обработки входа пользователя
        email = self.entry_email.get()
        password = self.entry_password.get()

        # Проверка заполненности полей ввода
        if not email or not password:
            messagebox.showerror("Ошибка", "Пожалуйста, введите электронную почту и пароль")
            return

        conn = connect_db()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT user_id, password FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()
                cursor.close()
                conn.close()

                # Проверка наличия пользователя и корректности пароля
                if user:
                    user_id, hashed_password = user
                    if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
                        self.user_id = user_id
                        self.is_authenticated = True
                        self.destroy()
                    else:
                        messagebox.showerror("Ошибка", "Неверный пароль")
                else:
                    messagebox.showerror("Ошибка", "Пользователь с таким адресом электронной почты не найден")
            except psycopg2.Error as e:
                print("Ошибка при выполнении SQL-запроса:", e)
                messagebox.showerror("Ошибка", "Произошла ошибка при попытке входа. Пожалуйста, попробуйте снова.")
        else:
            messagebox.showerror("Ошибка подключения", "Не удалось подключиться к базе данных.")
    def open_register_window(self):
        # Метод для открытия окна регистрации
        from register import RegisterPage
        register_window = RegisterPage(self.parent)
        register_window.grab_set()

    def login_with_google(self):
        # Запланированная функциональность для входа через Google
        messagebox.showinfo("Вход через Google", "Функция входа через Google будет добавлена позже")

    def toggle_password_visibility(self):
        # Переключение видимости пароля
        if self.show_password_var.get():
            self.entry_password.configure(show="")
        else:
            self.entry_password.configure(show="*")

if __name__ == "__main__":
    app = tk.Tk()
    login_window = AuthPage(app)
    app.mainloop()
