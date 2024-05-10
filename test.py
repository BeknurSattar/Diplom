import tkinter as tk
from tkinter import messagebox
import shelve
import os
from datetime import datetime, timedelta
from PIL import Image, ImageTk
from Helps.translations import translations
from pages.home_page import HomePage
from pages.data_page import DataPage
from pages.camera_page import CameraPage
from pages.settings_page import SettingsPage
from pages.profile_page import ProfilePage
from pages.auth_page import AuthPage
from Helps.utils import *

class Page(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AnaLiz")  # Установка названия окна
        self.geometry("800x600")  # Установка размеров окна
        self.full_screen = False
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", self.end_fullscreen)
        self.current_theme_bg = "#f0f0f0"
        self.current_theme_fg = "black"
        self.configure(bg="#f0f0f0")

        # Инициализация пути к директории сессии
        self.session_dir = os.path.join(os.path.expanduser('~'), 'AnaLizSessions')
        if not os.path.exists(self.session_dir):
            os.makedirs(self.session_dir)

        self.translations = translations
        self.current_language = 'ru'  # Устанавливаем русский язык по умолчанию
        self.is_authenticated = False
        self.user_id = None  # Инициализация user_id с None
        # Состояние аутентификации пользователя

        self.selected_index = 0  # Индекс выбранной вкладки в навигации

        # Попытка загрузить активную сессию, и если она есть, то не требовать повторной аутентификации
        if not self.load_session_from_db():
            self.check_authentication()
        else:
            self.create_widgets()

        # Обработка закрытия окна
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        """Обработчик закрытия окна."""
        self.save_session()  # Сохранение сеанса перед закрытием
        self.destroy()  # Закрытие приложения

    def save_session(self):
        """Сохраняет текущее состояние сессии в базу данных PostgreSQL."""
        conn = None
        try:
            conn = connect_db()
            cur = conn.cursor()
            # Подготовка и выполнение запроса на вставку данных сессии
            cur.execute(
                "INSERT INTO sessions (user_id, authenticated, language, last_access) VALUES (%s, %s, %s, %s)",
                (self.user_id, self.is_authenticated, self.current_language, datetime.now())
            )
            conn.commit()  # Подтверждение изменений
            cur.close()
        except psycopg2.DatabaseError as error:
            print("Ошибка базы данных:", error)
        finally:
            if conn is not None:
                conn.close()

    # Дополнительные функции для управления полноэкранным режимом (при желании):
    def toggle_fullscreen(self, event=None):
        self.full_screen = not self.full_screen
        self.attributes('-fullscreen', self.full_screen)
        return "break"

    def end_fullscreen(self, event=None):
        self.full_screen = False
        self.attributes('-fullscreen', False)
        return "break"
    def set_language(self, language):
        self.current_language = language
        # Обновляем тексты на всех кнопках
        self.home_button.config(text=self.translations[language]['home'])
        self.profile_button.config(text=self.translations[language]['profile'])
        self.exit_button.config(text=self.translations[language]['exit'])
        for i, button in enumerate(self.navigation_buttons):
            button.config(text=self.translations[language][self.pages[i].translation_key])

        # Обновляем страницы
        self.update_body_content()

    def apply_theme_to_all(self, bg, fg):
        self.current_theme_bg = bg  # сохраняем текущие цвета темы
        self.current_theme_fg = fg
        self.apply_theme_to_all_for_child(self, bg, fg)  # применяем тему ко всему приложению

    def apply_theme_to_all_for_child(self, widget, bg, fg):
        try:
            widget.configure(bg=bg)
            if hasattr(widget, 'configure') and 'fg' in widget.keys():
                widget.configure(fg=fg)
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self.apply_theme_to_all_for_child(child, bg, fg)

    def load_session_from_db(self):
        """Загружает последнюю активную сессию пользователя из базы данных."""
        conn = None
        try:
            conn = connect_db()
            cur = conn.cursor()
            cur.execute("SELECT user_id, authenticated, language FROM sessions ORDER BY last_access DESC LIMIT 1")
            result = cur.fetchone()

            if result:
                self.user_id, self.is_authenticated, self.current_language = result
                if self.is_authenticated:
                    return True
            return False
        except psycopg2.DatabaseError as error:
            print("Ошибка базы данных:", error)
            return False
        finally:
            if conn:
                conn.close()

    def logout(self):
        """Очищает сессию и перезапускает приложение для новой аутентификации."""
        self.is_authenticated = False
        self.save_session()  # Обновляем сессию в базе данных перед выходом
        self.restart()

    def restart(self):
        """Перезапускает интерфейс пользователя, начиная с окна авторизации."""
        self.destroy()  # Закрываем текущее окно
        self.__init__()  # Пересоздаём окно приложения
    def show_login_window(self):
        login_window = AuthPage(self)
        login_window.attributes('-topmost', True)
        self.wait_window(login_window)
        if login_window.is_authenticated:
            self.user_id = login_window.user_id
            self.is_authenticated = True
            self.current_language = login_window.selected_language
            self.set_language(self.current_language)
            self.create_widgets()
            self.lift()
            self.attributes('-topmost', False)
        else:
            self.destroy()

    def check_authentication(self):

            # Попытка загрузить данные сессии из базы данных
                try:
                    login_window = AuthPage(self)  # Создание окна аутентификации
                    login_window.attributes('-topmost', True)  # Установка окна аутентификации поверх других окон
                    self.wait_window(login_window)  # Ожидание закрытия окна аутентификации
                    if login_window.is_authenticated:
                        self.user_id = login_window.user_id
                        self.is_authenticated = True
                        self.create_widgets()
                        self.set_language(login_window.selected_language)  # Установка языка из AuthPage
                        self.lift()  # Поднимаем окно приложения на передний план
                        self.attributes('-topmost', False)
                    else:
                        self.destroy()  # Закрытие приложения, если аутентификация не пройдена
                except Exception as e:
                    messagebox.showerror(translations[self.current_language]['error'],
                                         translations[self.current_language]['authentication_error'].format(error=e))
                    self.destroy()


    def create_widgets(self):
        # Создание элементов интерфейса
        self.app_bar = tk.Frame(self, height=56, bg="#1976D2")
        self.app_bar.pack(side="top", fill="x")

        # Загрузка и масштабирование иконки
        icon_image = Image.open("Images/eyeee.png")  # Укажите путь к файлу иконки
        # Расчет новой ширины для сохранения пропорций
        base_height = 40  # Высота иконки меньше высоты app_bar для визуальной симметрии
        img_ratio = icon_image.width / icon_image.height
        new_width = int(base_height * img_ratio)
        icon_image = icon_image.resize((new_width, base_height), Image.LANCZOS)
        icon_photo = ImageTk.PhotoImage(icon_image)

        # Кнопки навигации с иконкой
        self.home_button = tk.Button(self.app_bar, image=icon_photo, bg="#1976D2", relief="flat",
                                     command=self.show_home)
        self.home_button.image = icon_photo  # Сохраняем ссылку на изображение
        self.home_button.pack(side="left", padx=(10, 0))

        self.profile_button = tk.Button(self.app_bar, text=self.translations[self.current_language]['profile'],
                                        bg="#1976D2", fg="white", relief="flat", command=self.show_profile)
        self.profile_button.pack(side="right", padx=(0, 10))

        self.exit_button = tk.Button(self.app_bar, text=self.translations[self.current_language]['exit'], bg="#1976D2",
                                     fg="white", relief="flat", command=self.confirm_exit)
        self.exit_button.pack(side="right")

        # Панели для навигации и контента
        self.nav_frame = tk.Frame(self, bg="#ffffff", width=200)
        self.nav_frame.pack(side="left", fill="y")

        self.body_frame = tk.Frame(self, bg="#ffffff", width=600)
        self.body_frame.pack(side="right", fill="both", expand=True)

        # Создание кнопок навигации и ассоциированных страниц
        self.navigation_buttons = []
        self.pages = [HomePage, DataPage, CameraPage, SettingsPage]
        destinations = [self.translations[self.current_language]['home'], self.translations[self.current_language]['data'], self.translations[self.current_language]['camera'], self.translations[self.current_language]['settings']]
        for i, destination in enumerate(destinations):
            button = tk.Button(self.nav_frame, text=destination, bg="#1976D2", fg="white", font=("Arial", 12), relief="flat", command=lambda i=i: self.on_navigation_selected(i))
            button.pack(anchor="w", pady=(5, 0), padx=10, fill="x")
            self.navigation_buttons.append(button)

        self.separator_line = tk.Frame(self, width=2, bg="#1976D2")
        self.separator_line.pack(side="left", fill="y")

        self.update_body_content()

    def show_home(self):
        # Переход на главную страницу
        self.selected_index = 0
        self.update_body_content()

    def show_profile(self):
        # Переход на страницу профиля
        self.selected_index = -1  # Специальный индекс для страницы профиля
        self.update_body_content()

    def confirm_exit(self):
        # Запрашиваем подтверждение выхода
        if messagebox.askokcancel(translations[self.current_language]['exit'], translations[self.current_language]['confirm_exit']):
            # Если пользователь подтвердил выход, перекидываем на окно авторизации
            self.save_session()  # Save session before exiting
            self.destroy()

    def update_body_content(self):
        # Очистка и обновление содержимого главного фрейма
        for widget in self.body_frame.winfo_children():
            widget.destroy()

        if self.selected_index == -1:
            try:
                page = ProfilePage(self.body_frame, self.user_id)  # Передача user_id
                page.set_language(self.current_language)  # Установка языка для текущей страницы
                page.pack(fill="both", expand=True)

                # Применяем текущую тему к новой странице
                self.apply_theme_to_all_for_child(page, self.current_theme_bg, self.current_theme_fg)
            except Exception as e:
                messagebox.showerror(translations[self.current_language]['error'], translations[self.current_language]['profile_creation_error'].format(error=e))
        else:
            try:
                page = self.pages[self.selected_index](self.body_frame, self, self.user_id)
                page.set_language(self.current_language)  # Установка языка для текущей страницы
                page.pack(fill="both", expand=True)

                # Применяем текущую тему к новой странице
                self.apply_theme_to_all_for_child(page, self.current_theme_bg, self.current_theme_fg)
            except Exception as e:
                messagebox.showerror(translations[self.current_language]['error'], translations[self.current_language]['page_creation_error'].format(error=e))

    def on_navigation_selected(self, index):
        # Обработка выбора элемента навигации
        self.selected_index = index
        self.update_body_content()

if __name__ == "__main__":
    app = Page()
    app.mainloop()

