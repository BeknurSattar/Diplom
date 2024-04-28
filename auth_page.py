import tkinter as tk
from tkinter import messagebox
import psycopg2
import bcrypt
from utils import connect_db  # Проверьте, что функция connect_db правильно импортирована и работает

class AuthPage(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Авторизация")
        self.geometry("300x330")
        self.resizable(False, False)
        self.configure(bg="#f0f0f0")
        self.lift()
        self.parent = parent
        self.is_authenticated = False
        self.user_id = None  # Для хранения идентификатора аутентифицированного пользователя
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

        self.show_password_var = tk.BooleanVar(value=False)
        self.show_password_checkbox = tk.Checkbutton(self, text="Показать пароль", variable=self.show_password_var, bg="#f0f0f0", command=self.toggle_password_visibility)
        self.show_password_checkbox.pack(pady=(5, 10))

        button_style = {"font": ("Arial", 12), "bg": "#1976D2", "fg": "white", "relief": "flat"}
        self.button_login = tk.Button(self, text="Войти", command=self.login, **button_style)
        self.button_login.pack(pady=(5, 5))

        self.button_register = tk.Button(self, text="Зарегистрироваться", command=self.open_register_window, **button_style)
        self.button_register.pack(pady=(0, 5))

        self.button_google = tk.Button(self, text="Войти через Google", command=self.login_with_google, **button_style)
        self.button_google.pack(pady=(0, 10))

    def login(self):
        username = self.entry_username.get()
        password = self.entry_password.get()

        if not username or not password:
            messagebox.showerror("Ошибка", "Пожалуйста, введите имя пользователя и пароль")
            return

        conn = connect_db()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT user_id, password FROM users WHERE username = %s", (username,))
                user = cursor.fetchone()
                cursor.close()
                conn.close()

                if user:
                    user_id, hashed_password = user
                    if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
                        self.user_id = user_id
                        self.is_authenticated = True
                        self.destroy()
                    else:
                        messagebox.showerror("Ошибка", "Неверный пароль")
                else:
                    messagebox.showerror("Ошибка", "Пользователь с таким именем не найден")
            except psycopg2.Error as e:
                print("Ошибка при выполнении SQL-запроса:", e)
                messagebox.showerror("Ошибка", "Произошла ошибка при попытке входа. Пожалуйста, попробуйте снова.")

    def open_register_window(self):
        from register import RegisterPage
        register_window = RegisterPage(self.parent)
        register_window.grab_set()

    def login_with_google(self):
        # Дополнительная функциональность в будущем
        messagebox.showinfo("Вход через Google", "Функция входа через Google будет добавлена позже")

    def toggle_password_visibility(self):
        if self.show_password_var.get():
            self.entry_password.configure(show="")
        else:
            self.entry_password.configure(show="*")

if __name__ == "__main__":
    app = tk.Tk()
    login_window = AuthPage(app)
    app.mainloop()
