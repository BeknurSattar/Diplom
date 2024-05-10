import tkinter as tk
from tkinter import messagebox
import psycopg2
import bcrypt

from Helps.translations import translations
from Helps.utils import connect_db  # Подключение функции соединения с базой данных
class AuthPage(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title()
        self.geometry("300x330")  # Установка размера окна
        self.resizable(False, False)  # Окно не может быть изменено в размере
        self.configure(bg="#f0f0f0")  # Фоновый цвет окна
        self.lift()  # Поднять окно на передний план
        self.parent = parent
        self.is_authenticated = False  # Статус аутентификации пользователя
        self.user_id = None  # ID аутентифицированного пользователя
        self.current_language = 'ru'  # Начальный язык
        self.create_widgets()  # Создание виджетов окна
        self.change_language('Русский')  # Установка начального языка интерфейса
        self.selected_language = 'ru'

    # Смена языка
    def change_language(self, language_key):
        language_code = self.language_options[language_key]  # Получаем код языка по его полному названию
        self.current_language = language_code
        self.selected_language = language_code
        # Обновление текста виджетов на выбранный язык
        self.title(translations[self.current_language]['login_window_title'])
        self.label_email.config(text=translations[self.current_language]['Email'])
        self.label_password.config(text=translations[self.current_language]['Password'])
        self.show_password_checkbox.config(text=translations[self.current_language]['Show_password'])
        self.button_login.config(text=translations[self.current_language]['Login'])
        self.button_register.config(text=translations[self.current_language]['Register'])

    # Создание элементов
    def create_widgets(self):
        # Стили для виджетов
        label_style = {"font": ("Arial", 12), "bg": "#f0f0f0"}
        entry_style = {"font": ("Arial", 12)}

        # Создание и размещение виджетов для ввода почты и пароля
        self.label_email = tk.Label(self, **label_style)
        self.label_email.pack(pady=(10, 5))
        self.entry_email = tk.Entry(self, **entry_style)
        self.entry_email.pack(pady=5)

        self.label_password = tk.Label(self, **label_style)
        self.label_password.pack(pady=(5, 5))
        self.entry_password = tk.Entry(self, show="*", **entry_style)
        self.entry_password.pack(pady=5)

        # Чекбокс для показа/скрытия пароля
        self.show_password_var = tk.BooleanVar(value=False)
        self.show_password_checkbox = tk.Checkbutton(self, variable=self.show_password_var, bg="#f0f0f0", command=self.toggle_password_visibility)
        self.show_password_checkbox.pack(pady=(5, 10))

        # Кнопки для входа, регистрации и входа через Google
        button_style = {"font": ("Arial", 12), "bg": "#1976D2", "fg": "white", "relief": "flat"}
        self.button_login = tk.Button(self, command=self.login, **button_style)
        self.button_login.pack(pady=(5, 5))

        self.button_register = tk.Button(self, command=self.open_register_window, **button_style)
        self.button_register.pack(pady=(0, 5))

        # Добавление выпадающего списка для выбора языка
        self.language_var = tk.StringVar(value=self.current_language)
        self.language_options = {'Русский': 'ru', 'English': 'en', 'Қазақша': 'kz'}
        self.language_menu = tk.OptionMenu(self, self.language_var, *self.language_options.keys(),
                                           command=self.change_language)
        self.language_menu.pack(pady=(5, 5))

    # Вход в приложения
    def login(self):
        # Метод для обработки входа пользователя
        email = self.entry_email.get()
        password = self.entry_password.get()

        # Проверка заполненности полей ввода
        if not email or not password:
            messagebox.showerror(translations[self.current_language]['error'], translations[self.current_language]['Please_enter_email_and_password'])
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
                        messagebox.showerror(translations[self.current_language]['error'], translations[self.current_language]['lose_password'],)
                else:
                    messagebox.showerror(translations[self.current_language]['error'], translations[self.current_language]['no_polz'])
            except psycopg2.Error as e:
                messagebox.showerror(translations[self.current_language]['error'], translations[self.current_language]['please_again'])
        else:
            messagebox.showerror(translations[self.current_language]['database_error'], translations[self.current_language]['connection_error'])

    # Открытие окна регистрации
    def open_register_window(self):
        # Метод для открытия окна регистрации
        from .register import RegisterPage
        register_window = RegisterPage(self.parent, self.selected_language)
        register_window.grab_set()

    # Скрыт показать пароль
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
