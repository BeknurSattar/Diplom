import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from translations import translations
from home_page import HomePage
from data_page import DataPage
from camera_page import CameraPage
from settings_page import SettingsPage
from profile_page import ProfilePage
from auth_page import AuthPage

class Page(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AnaLiz")  # Установка названия окна
        self.geometry("800x600")  # Установка размеров окна
        self.full_screen = True  # Установка цвета фона
        self.translations = translations
        self.current_language = 'ru'  # Устанавливаем русский язык по умолчанию
        # Состояние аутентификации пользователя
        self.is_authenticated = False
        self.selected_index = 0  # Индекс выбранной вкладки в навигации

        self.full_screen = False
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", self.end_fullscreen)

        self.configure(bg="#f0f0f0")
        self.check_authentication()  # Проверка статуса аутентификации пользователя

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

    def check_authentication(self):
        # Проверяем, авторизован ли пользователь
        if not self.is_authenticated:
            try:
                # Если не авторизован, открываем окно авторизации
                login_window = AuthPage(self)  # Создание окна аутентификации
                login_window.attributes('-topmost', True)  # Установка окна аутентификации поверх других окон

                self.wait_window(login_window)  # Ожидание закрытия окна аутентификации

                # После закрытия окна авторизации, проверяем результат
                if login_window.is_authenticated:
                    self.user_id = login_window.user_id
                    self.is_authenticated = True
                    self.create_widgets()  # Создание виджетов интерфейса
                    self.current_language = login_window.selected_language  # Установка языка из AuthPage
                    self.set_language(self.current_language)  # Обновляем язык интерфейса
                    self.lift()  # Поднимаем окно приложения на передний план
                    self.attributes('-topmost', False)
                else:
                    self.destroy()  # Закрытие приложения, если аутентификация не пройдена
            except Exception as e:
                messagebox.showerror(translations[self.current_language]['error'], translations[self.current_language]['authentication_error'].format(error=e))
                self.destroy()
        else:
            self.create_widgets()

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
            self.is_authenticated = False
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
            except Exception as e:
                messagebox.showerror(translations[self.current_language]['error'], translations[self.current_language]['profile_creation_error'].format(error=e))
        else:
            try:
                page = self.pages[self.selected_index](self.body_frame, self)
                page.set_language(self.current_language)  # Установка языка для текущей страницы
                page.pack(fill="both", expand=True)
            except Exception as e:
                messagebox.showerror(translations[self.current_language]['error'], translations[self.current_language]['page_creation_error'].format(error=e))

    def on_navigation_selected(self, index):
        # Обработка выбора элемента навигации
        self.selected_index = index
        self.update_body_content()

if __name__ == "__main__":
    app = Page()
    app.mainloop()

