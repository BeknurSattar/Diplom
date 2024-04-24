import tkinter as tk
from tkinter import messagebox
import psycopg2
from utils import *

class AuthPage(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Авторизация")
        self.geometry("300x330")
        self.resizable(False, False)
        self.configure(bg="#f0f0f0")

        self.parent = parent
        self.is_authenticated = False

        self.create_widgets()

    def create_widgets(self):
        label_style = {"font": ("Arial", 12), "bg": "#f0f0f0"}
        entry_style = {"font": ("Arial", 12)}

        self.label_username = tk.Label(self, text="Имя пользователя:", **label_style)
        self.label_username.pack(pady=(10, 5))
        self.entry_username = tk.Entry(self, **entry_style)
        self.entry_username.pack(pady=5)

        self.label_password = tk.Label(self, text="Пароль:", **label_style)
        self.label_password.pack(pady=(5, 5))
        self.entry_password = tk.Entry(self, show="*", **entry_style)
        self.entry_password.pack(pady=5)

        # Кнопка для показа или скрытия пароля
        self.show_password_var = tk.BooleanVar(value=False)
        self.show_password_checkbox = tk.Checkbutton(self, text="Показать пароль", variable=self.show_password_var, bg="#f0f0f0", command=self.toggle_password_visibility)
        self.show_password_checkbox.pack(pady=(5, 10))

        button_style = {"font": ("Arial", 12), "bg": "#1976D2", "fg": "white", "relief": "flat"}
        self.button_login = tk.Button(self, text="Войти", command=self.login, **button_style)
        self.button_login.pack(pady=(5, 5))

        # Кнопка для открытия окна регистрации
        self.button_register = tk.Button(self, text="Зарегистрироваться", command=self.open_register_window, **button_style)
        self.button_register.pack(pady=(0, 5))

        self.button_google = tk.Button(self, text="Войти через Google", command=self.login_with_google, **button_style)
        self.button_google.pack(pady=(0, 10))

    def login(self):
        username = self.entry_username.get()
        password = self.entry_password.get()

        if username and password:
            conn = connect_db()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
                    user = cursor.fetchone()
                    cursor.close()
                    conn.close()

                    if user:
                        self.is_authenticated = True
                        self.destroy()
                    else:
                        messagebox.showerror("Ошибка", "Неверное имя пользователя или пароль")
                except psycopg2.Error as e:
                    print("Ошибка при выполнении SQL-запроса:", e)
                    messagebox.showerror("Ошибка", "Произошла ошибка при попытке входа. Пожалуйста, попробуйте снова.")
        else:
            messagebox.showerror("Ошибка", "Пожалуйста, введите имя пользователя и пароль")

    def open_register_window(self):
        from register import RegisterPage
        register_window = RegisterPage(self)

        return register_window

    def login_with_google(self):
        # Здесь можно добавить логику входа через аккаунт Google
        messagebox.showinfo("Вход через Google", "Функция входа через Google будет добавлена позже")

    def toggle_password_visibility(self):
        # Показываем или скрываем пароль в зависимости от состояния флажка
        if self.show_password_var.get():
            self.entry_password.configure(show="")
        else:
            self.entry_password.configure(show="*")

if __name__ == "__main__":
    app = tk.Tk()
    login_window = AuthPage(app)
    app.mainloop()
