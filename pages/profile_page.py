import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

import bcrypt
import psycopg2
from PIL import Image, ImageTk, ImageOps, ImageDraw

from Helps.translations import translations
from Helps.utils import connect_db

class ProfilePage(tk.Frame):
    """Страница профиля пользователя, позволяющая просматривать и редактировать информацию пользователя."""
    def __init__(self, parent, user_id=None):
        super().__init__(parent)
        self.user_id = user_id
        self.image_path = None
        self.photo_label = None  # Инициализируем здесь, чтобы всегда существовал
        self.label_username = None  # Предварительная инициализация
        self.label_email = None
        self.label_position = None
        self.create_widgets()

    def set_language(self, language):
        self.current_language = language
        # Обновление текстовых меток согласно выбранному языку
        self.change_password_button.config(text=translations[language]['change_password'])
        self.edit_profile_button.config(text=translations[language]['edit_profile'])
        # Обновление текста ошибок, если они отображаются
        if hasattr(self, 'error_label'):
            self.error_label.config(text=translations[language]['profile_load_error'])
        # Обновление информации о пользователе
        if self.label_username:
            self.label_username.config(text=f"{translations[language]['username']}: {self.username}")
        if self.label_email:
            self.label_email.config(text=f"{translations[language]['email']}: {self.email}")
        if self.label_position:
            self.label_position.config(text=f"{translations[language]['position']}: {self.position}")

    def create_widgets(self):
        """Создает виджеты на странице профиля."""
        if self.user_id:
            self.load_user_profile()
            self.add_change_password_button()  # Добавляем кнопку для изменения пароля
            self.add_edit_profile_button()  # Добавляем кнопку для редактирования профиля
        else:
            tk.Label(self, text=translations[self.current_language]['profile_load_error'], font=("Arial", 16)).pack(pady=20)

    def add_edit_profile_button(self):
        """Добавляет кнопку для редактирования профиля."""
        self.edit_profile_button = tk.Button(self, command=self.edit_profile,
                                             font=("Arial", 12))
        self.edit_profile_button.pack(pady=20)
    def add_change_password_button(self):
        """Добавляет кнопку для смены пароля."""
        self.change_password_button = tk.Button(self, command=self.change_password,
                                           font=("Arial", 12))
        self.change_password_button.pack(pady=10)

    def change_password(self):
        new_password = simpledialog.askstring(title=translations[self.current_language]['new_password'],
                                              prompt=translations[self.current_language]['Enter_a_new_password'],
                                              parent=self,
                                              show='*')
        confirm_password = simpledialog.askstring(title=translations[self.current_language]['confirm_password'],
                                                  prompt=translations[self.current_language]['Confirm_your_new_password'],
                                                  parent=self,
                                                  show='*')

        if new_password and new_password == confirm_password:
            self.update_password_in_db(new_password)
        else:
            messagebox.showerror(translations[self.current_language]['error'], translations[self.current_language]['passwords_do_not_match'])

    def update_password_in_db(self, new_password):
        """Обновляет пароль пользователя в базе данных."""
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')  # Хеширование пароля

        try:
            conn = connect_db()
            if conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET password = %s WHERE user_id = %s", (hashed_password, self.user_id))
                conn.commit()
                cursor.close()
                messagebox.showinfo(translations[self.current_language]['success'], translations[self.current_language]['password_successfully_changed'])
            else:
                messagebox.showerror(translations[self.current_language]['database_error'], translations[self.current_language]['connection_error'])
        except psycopg2.Error as e:
            messagebox.showerror(translations[self.current_language]['database_error'], translations[self.current_language]['database_query_error'].format(error=e))
        finally:
            if conn:
                conn.close()

    def load_user_profile(self):
        """Загружает информацию пользователя из базы данных и отображает ее."""
        try:
            conn = connect_db()
            if conn:
                cursor = conn.cursor()
                cursor.execute("""
                            SELECT u.username, u.email, p.title as position, u.image_path
                            FROM users u
                            JOIN positions p ON u.position_id = p.id
                            WHERE u.user_id = %s
                        """, (self.user_id,))
                user_info = cursor.fetchone()
                cursor.close()
                if user_info:
                    self.display_user_image(user_info[3] or "Images/icon.jpg")
                    self.username, self.email, self.position, self.image_path = user_info
                    self.display_user_info()
                else:
                    tk.Label(self, text=translations[self.current_language]['Profile_not_found'], font=("Arial", 16)).pack(pady=20)
            else:
                messagebox.showerror(translations[self.current_language]['database_error'], translations[self.current_language]['connection_error'])
        except psycopg2.Error as e:
            messagebox.showerror(translations[self.current_language]['database_error'], translations[self.current_language]['database_query_error'].format(error=e))
        finally:
            if conn:
                conn.close()
    def display_user_info(self):
        """Отображает информацию пользователя в виде меток."""
        # Убедитесь, что метки создаются здесь, прежде чем они будут использоваться где-либо еще.
        self.label_username = tk.Label(self, text="", font=("Arial", 14))
        self.label_username.pack(pady=10)

        self.label_email = tk.Label(self, text="", font=("Arial", 14))
        self.label_email.pack(pady=10)

        self.label_position = tk.Label(self, text="", font=("Arial", 14))
        self.label_position.pack(pady=10)



    def display_user_image(self, image_path):
        """Отображает круглое изображение пользователя."""
        try:
            original_photo = Image.open(image_path)
            size = (100, 100)  # Размер круглого изображения
            mask = Image.new('L', size, 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0) + size, fill=255)  # Рисуем белый круг на черном фоне

            original_photo = original_photo.resize(size, Image.Resampling.LANCZOS)
            rounded_photo = ImageOps.fit(original_photo, mask.size, centering=(0.5, 0.5))
            rounded_photo.putalpha(mask)  # Применяем маску для создания прозрачности вне круга

            self.profile_photo = ImageTk.PhotoImage(rounded_photo)
            if not self.photo_label:
                self.photo_label = tk.Label(self, image=self.profile_photo)
                self.photo_label.image = self.profile_photo  # Сохраняем ссылку, чтобы избежать сбора мусора
                self.photo_label.pack(pady=10)
            else:
                self.photo_label.configure(image=self.profile_photo)
                self.photo_label.image = self.profile_photo
        except IOError as e:
            tk.Label(self,text=translations[self.current_language]['Failed_load_picture'], font=("Arial", 16)).pack(pady=10)

    # При редактировании профиля
    def edit_profile(self):
        if messagebox.askokcancel(translations[self.current_language]['edit'], translations[self.current_language]['edit_confirmation']):
            self.open_edit_dialog()

    def open_edit_dialog(self):
        # Создаем диалоговое окно для редактирования профиля
        if self.label_username and self.label_username['text']:
            initial_username = self.label_username['text'].split(": ")[1]
        else:
            initial_username = ''
        self.new_username = simpledialog.askstring(translations[self.current_language]['Change_name'],
                                                   translations[self.current_language]['Enter_your_new_username'],
                                                   initialvalue=initial_username, parent=self)

        if self.label_email and self.label_email['text']:
            initial_email = self.label_email['text'].split(": ")[1]
        else:
            initial_email = ''
        self.new_email = simpledialog.askstring(translations[self.current_language]['Change_email'],
                                                translations[self.current_language]['Enter_new_email'],
                                                initialvalue=initial_email, parent=self)


        self.choose_image()
        if self.new_username and self.new_email:
            self.save_profile_changes()

    def choose_image(self):
        """Позволяет пользователю выбрать новое изображение для профиля."""
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg")])
        if file_path:
            self.update_profile_photo(file_path)
            self.save_image_path_to_db(file_path)

    def update_profile_photo(self, file_path):
        """Обновляет изображение профиля пользователя."""
        self.display_user_image(file_path)  # Сохраняем ссылку на изображение

    def save_profile_changes(self):
        # Сохраняем изменения в базе данных
        try:
            conn = connect_db()
            if conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET username = %s, email = %s WHERE user_id = %s",
                               (self.new_username, self.new_email, self.user_id))
                conn.commit()
                cursor.close()
                messagebox.showinfo(translations[self.current_language]['success'], translations[self.current_language]['Profile_successfully_updated'],)
                # Обновляем информацию на странице
                self.label_username.config(
                    text=translations[self.current_language]['username_label'].format(username=self.new_username))
                self.label_email.config(
                    text=translations[self.current_language]['email_label'].format(email=self.new_email))
            else:
                messagebox.showerror(translations[self.current_language]['database_error'], translations[self.current_language]['connection_error'])
        except psycopg2.Error as e:
            messagebox.showerror(translations[self.current_language]['database_error'], translations[self.current_language]['database_query_error'].format(error=e))
        finally:
            if conn:
                conn.close()


    def save_image_path_to_db(self, file_path):
        """Сохраняет путь к новому изображению профиля в базу данных."""
        try:
            conn = connect_db()
            if conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET image_path = %s WHERE user_id = %s", (file_path, self.user_id))
                conn.commit()
                cursor.close()
                messagebox.showinfo(translations[self.current_language]['success'], translations[self.current_language]['Profile_picture_updated'],)
            else:
                messagebox.showerror(translations[self.current_language]['database_error'], translations[self.current_language]['connection_error'])
        except psycopg2.Error as e:
            messagebox.showerror(translations[self.current_language]['database_error'], translations[self.current_language]['database_query_error'].format(error=e))
        finally:
            if conn:
                conn.close()