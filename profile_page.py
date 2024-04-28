import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import psycopg2
from PIL import Image, ImageTk, ImageOps, ImageDraw
from utils import connect_db

class ProfilePage(tk.Frame):
    def __init__(self, parent, user_id=None):
        super().__init__(parent)
        self.user_id = user_id
        self.image_path = None
        self.photo_label = None  # Инициализируем здесь, чтобы всегда существовал
        self.create_widgets()

    def create_widgets(self):
        if self.user_id:
            self.load_user_profile()
        else:
            tk.Label(self, text="Ошибка: Не удалось загрузить профиль пользователя.", font=("Arial", 16)).pack(pady=20)

    def load_user_profile(self):
        conn = connect_db()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT username, email, position, image_path FROM users WHERE user_id = %s", (self.user_id,))
                user_info = cursor.fetchone()
                cursor.close()
                conn.close()

                if user_info:
                    username, email, position, self.image_path = user_info
                    try:
                        self.display_user_image(self.image_path or "Images/icon.jpg")
                        self.display_user_info(username, email, position)

                    except IOError as e:
                        print(f"Ошибка загрузки изображения профиля: {e}")
                        tk.Label(self, text="Не удалось загрузить изображение профиля.", font=("Arial", 16)).pack(pady=10)
                else:
                    tk.Label(self, text="Профиль не найден.", font=("Arial", 16)).pack(pady=20)
            except psycopg2.Error as e:
                print(f"Ошибка запроса к базе данных: {e}")
                tk.Label(self, text="Произошла ошибка при загрузке данных профиля.", font=("Arial", 16)).pack(pady=20)
        else:
            tk.Label(self, text="Не удалось подключиться к базе данных.", font=("Arial", 16)).pack(pady=20)

    def display_user_info(self, username, email, position):
        self.label_username = tk.Label(self, text=f"Имя пользователя: {username}", font=("Arial", 14))
        self.label_username.pack(pady=10)
        self.label_email = tk.Label(self, text=f"Email: {email}", font=("Arial", 14))
        self.label_email.pack(pady=10)
        self.label_position = tk.Label(self, text=f"Должность: {position}", font=("Arial", 14))
        self.label_position.pack(pady=10)
        edit_button = tk.Button(self, text="Редактировать профиль", command=self.edit_profile, font=("Arial", 12))
        edit_button.pack(pady=20)

    def display_user_image(self, image_path):
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
            print(f"Ошибка загрузки изображения профиля: {e}")
            tk.Label(self, text="Не удалось загрузить изображение профиля.", font=("Arial", 16)).pack(pady=10)
    def edit_profile(self):
        if messagebox.askokcancel("Подтверждение", "Вы действительно хотите редактировать профиль?"):
            self.open_edit_dialog()

    def open_edit_dialog(self):
        # Создаем диалоговое окно для редактирования профиля
        self.new_username = simpledialog.askstring("Изменить имя", "Введите новое имя пользователя:", initialvalue=self.label_username['text'].split(": ")[1], parent=self)
        self.new_email = simpledialog.askstring("Изменить email", "Введите новый email:", initialvalue=self.label_email['text'].split(": ")[1], parent=self)
        self.new_position = simpledialog.askstring("Изменить должность", "Введите новую должность:", initialvalue=self.label_position['text'].split(": ")[1], parent=self)
        self.choose_image()
        if self.new_username and self.new_email and self.new_position:
            self.save_profile_changes()

    def choose_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg")])
        if file_path:
            self.update_profile_photo(file_path)
            self.save_image_path_to_db(file_path)

    def update_profile_photo(self, file_path):
        self.display_user_image(file_path)  # Сохраняем ссылку на изображение

    def save_profile_changes(self):
        # Сохраняем изменения в базе данных
        conn = connect_db()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET username = %s, email = %s, position = %s WHERE user_id = %s", (self.new_username, self.new_email, self.new_position, self.user_id))
                conn.commit()
                cursor.close()
                conn.close()
                messagebox.showinfo("Успех", "Профиль успешно обновлен.")
                self.label_username.config(text=f"Имя пользователя: {self.new_username}")
                self.label_email.config(text=f"Email: {self.new_email}")
                self.label_position.config(text=f"Должность: {self.new_position}")
            except psycopg2.Error as e:
                print(f"Ошибка при обновлении данных в базе: {e}")
                messagebox.showerror("Ошибка", "Не удалось обновить данные профиля.")
        else:
            messagebox.showerror("Ошибка", "Не удалось подключиться к базе данных.")

    def save_image_path_to_db(self, file_path):
        conn = connect_db()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET image_path = %s WHERE user_id = %s", (file_path, self.user_id))
                conn.commit()
                cursor.close()
                conn.close()
                messagebox.showinfo("Успех", "Изображение профиля обновлено.")
            except psycopg2.Error as e:
                print(f"Ошибка при обновлении изображения в базе: {e}")
                messagebox.showerror("Ошибка", "Не удалось обновить изображение профиля.")
        else:
            messagebox.showerror("Ошибка", "Не удалось подключиться к базе данных.")