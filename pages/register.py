import re
import tkinter as tk
from tkinter import messagebox
import psycopg2
import bcrypt
from Helps.translations import translations
from Helps.utils import connect_db

class RegisterPage(tk.Toplevel):
    def __init__(self, parent, language='ru'):
        super().__init__(parent)
        self.title()
        self.geometry("300x550")
        self.resizable(False, False)
        self.configure(bg="#f0f0f0")
        self.parent = parent
        self.current_language = language  # Сохраняем переданный язык
        self.create_widgets()
        self.update_language()

    def update_language(self):
        self.title(translations[self.current_language]['register_window_title'])
        # Обновление текста виджетов на выбранный язык
        self.label_username.config(text=translations[self.current_language]['Username'])
        self.label_email.config(text=translations[self.current_language]['Email'])
        self.label_password.config(text=translations[self.current_language]['Password'])
        self.label_confirm_password.config(text=translations[self.current_language]['Confirm_password'])
        self.label_position.config(text=translations[self.current_language]['Position'])
        self.label_password_requirements.config(text=translations[self.current_language]['Password_requirements'])
        self.button_register.config(text=translations[self.current_language]['Register'])
        self.show_password_button.config(text=translations[self.current_language]['Show_password'])
        self.login_button.config(text=translations[self.current_language]['Already_registered'])

    def create_widgets(self):
        """Создание виджетов для регистрационной формы."""
        label_style = {"font": ("Arial", 12), "bg": "#f0f0f0"}
        entry_style = {"font": ("Arial", 12)}

        self.label_username = tk.Label(self, **label_style)
        self.label_username.pack(pady=(10, 5))
        self.entry_username = tk.Entry(self, **entry_style)
        self.entry_username.pack(pady=5)

        self.label_email = tk.Label(self, **label_style)
        self.label_email.pack(pady=(5, 5))
        self.entry_email = tk.Entry(self, **entry_style)
        self.entry_email.pack(pady=5)

        self.label_password = tk.Label(self, **label_style)
        self.label_password.pack(pady=(5, 5))
        self.entry_password = tk.Entry(self, show="*", **entry_style)
        self.entry_password.pack(pady=5)

        self.label_confirm_password = tk.Label(self, **label_style)
        self.label_confirm_password.pack(pady=(5, 5))
        self.entry_confirm_password = tk.Entry(self, show="*", **entry_style)
        self.entry_confirm_password.pack(pady=5)

        # Добавляем текст для требований к паролю
        self.label_password_requirements = tk.Label(self, **label_style)
        self.label_password_requirements.pack(pady=(5, 5))

        # Загрузка и отображение должностей
        self.label_position = tk.Label(self, **label_style)
        self.label_position.pack(pady=(5, 5))
        self.positions = self.fetch_positions()
        self.selected_position = tk.StringVar(self)
        self.selected_position.set(self.positions[0][1])  # Устанавливаем первую должность как значение по умолчанию
        self.option_menu = tk.OptionMenu(self, self.selected_position, *[pos[1] for pos in self.positions])
        self.option_menu.config(font=("Arial", 12))
        self.option_menu.pack(pady=5)

        button_style = {"font": ("Arial", 12), "bg": "#1976D2", "fg": "white", "relief": "flat"}
        self.button_register = tk.Button(self, command=self.register, **button_style)
        self.button_register.pack(pady=(10, 5))

        # Добавляем кнопку для показа пароля
        self.show_password = tk.BooleanVar(self)
        self.show_password.set(False)
        self.show_password_button = tk.Checkbutton(self, variable=self.show_password,
                                                   command=self.toggle_password, **label_style)
        self.show_password_button.pack(pady=5)

        # Добавляем кнопку для перехода к окну авторизации
        self.login_button = tk.Button(self, command=self.go_to_login_page,
                                      **button_style)
        self.login_button.pack(pady=(10, 5))

    def is_valid_email(self, email):
        # Простая регулярная выражение для проверки формата электронной почты
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        return re.match(pattern, email) is not None

    def is_unique_email(self, email, conn):
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT EXISTS(SELECT 1 FROM users WHERE email = %s)", (email,))
            exists = cursor.fetchone()[0]
            cursor.close()
            return not exists
        except psycopg2.Error as e:
            print(f"Ошибка при проверке уникальности email: {e}")
            return False

    def toggle_password(self):
        """Переключение видимости пароля."""
        if self.show_password.get():
            self.entry_password.config(show="")
            self.entry_confirm_password.config(show="")
        else:
            self.entry_password.config(show="*")
            self.entry_confirm_password.config(show="*")

    def go_to_login_page(self):
        # Закрываем текущее окно и открываем окно авторизации
        # self.withdraw()
        # auth_window = AuthPage(self.parent)
        # auth_window.grab_set()  # Переводим фокус на окно авторизации
        self.destroy()

    def fetch_positions(self):
        """Загрузка и перевод должностей из базы данных."""
        conn = connect_db()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT id, title FROM positions ORDER BY title")
                positions = cursor.fetchall()
                # Переводим названия должностей
                translated_positions = [(pos[0], translations[self.current_language]['positions'].get(pos[1], pos[1]))
                                        for pos in positions]
                cursor.close()
                conn.close()
                return translated_positions
            except psycopg2.Error as e:
                print(f"Ошибка запроса к базе данных: {e}")
                return []
        return []

    def validate_password(self, password):
        """Проверка пароля на соответствие требованиям."""
        if len(password) < 8:
            return False, translations[self.current_language]['Password_too_short']
        if not re.search(r'[A-Z]', password):
            return False, translations[self.current_language]['Password_needs_uppercase']
        if not re.search(r'[a-z]', password):
            return False, translations[self.current_language]['Password_needs_lowercase']
        if not re.search(r'[0-9]', password):
            return False, translations[self.current_language]['Password_needs_digit']
        if not re.search(r'[!@#\$%\^&\*(),.?":{}|<>]', password):
            return False, translations[self.current_language]['Password_needs_special']
        return True, ""

    def register(self):
        """Регистрация нового пользователя."""
        username = self.entry_username.get()
        email = self.entry_email.get()
        password = self.entry_password.get()
        confirm_password = self.entry_confirm_password.get()
        position_title = self.selected_position.get()
        position_id = next(pos[0] for pos in self.positions if pos[1] == position_title)

        if not all([username, email, password, confirm_password]):
            messagebox.showerror(translations[self.current_language]['error'], translations[self.current_language]['Please_fill_in_all_fields'])
            return

        if not self.is_valid_email(email):
            messagebox.showerror(translations[self.current_language]['error'], translations[self.current_language]['Enter_a_valid_email_address'])
            return

        conn = connect_db()
        if not conn:
            messagebox.showerror(translations[self.current_language]['error'], translations[self.current_language]['Failed_to_connect_to_the_database'])
            return

        if not self.is_unique_email(email, conn):
            messagebox.showerror(translations[self.current_language]['error'], translations[self.current_language]['This_email_address_is_already_in_use'])
            return

        if password != confirm_password:
            messagebox.showerror(translations[self.current_language]['error'], translations[self.current_language]['Password_mismatch'])
            return

        is_valid, validation_msg = self.validate_password(password)
        if not is_valid:
            messagebox.showerror(translations[self.current_language]['error'], validation_msg)
            return

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')  # Хеширование пароля

        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, email, password, position_id) VALUES (%s, %s, %s, %s)",
                           (username, email, hashed_password, position_id))
            conn.commit()
            cursor.close()
            messagebox.showinfo(translations[self.current_language]['success'], translations[self.current_language]['Registration_completed'])
            self.go_to_login_page()
        except psycopg2.Error as e:
            print("Ошибка при выполнении SQL-запроса:", e)
            messagebox.showerror(translations[self.current_language]['error'], translations[self.current_language]['An_error_registration_Please_again'])
        finally:
            if conn:
                conn.close()

if __name__ == "__main__":
    app = tk.Tk()
    register_window = RegisterPage(app)
    app.mainloop()
