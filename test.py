import tkinter as tk
from tkinter import messagebox
from home_page import HomePage
from data_page import DataPage
from camera_page import CameraPage
from settings_page import SettingsPage
from profile_page import ProfilePage
from auth_page import AuthPage

class Page(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AnaLiz")
        self.geometry("800x600")
        self.full_screen = True

        self.is_authenticated = False
        self.selected_index = 0

        self.configure(bg="#f0f0f0")
        self.check_authentication()

    def check_authentication(self):
        # Проверяем, авторизован ли пользователь
        if not self.is_authenticated:
            # Если не авторизован, открываем окно авторизации
            login_window = AuthPage(self)
            self.wait_window(login_window)  # Ждем, пока окно авторизации будет закрыто

            # После закрытия окна авторизации, проверяем результат
            if login_window.is_authenticated:
                self.is_authenticated = True
                self.create_widgets()
            else:
                # Если пользователь не авторизован, закрываем приложение
                self.destroy()
        else:
            self.create_widgets()

    def create_widgets(self):
        self.app_bar = tk.Frame(self, height=56, bg="#1976D2")
        self.app_bar.pack(side="top", fill="x")

        self.home_button = tk.Button(self.app_bar, text="AnaLiz", font=("Arial", 20, "bold"), bg="#1976D2", fg="white", relief="flat", command=self.show_home)
        self.home_button.pack(side="left", padx=(10, 0))

        self.profile_button = tk.Button(self.app_bar, text="Профиль", bg="#1976D2", fg="white", relief="flat", command=self.show_profile)
        self.profile_button.pack(side="right", padx=(0, 10))

        self.exit_button = tk.Button(self.app_bar, text="Выход", bg="#1976D2", fg="white", relief="flat", command=self.confirm_exit)
        self.exit_button.pack(side="right")

        self.nav_frame = tk.Frame(self, bg="#ffffff", width=200)
        self.nav_frame.pack(side="left", fill="y")

        self.body_frame = tk.Frame(self, bg="#ffffff", width=600)
        self.body_frame.pack(side="right", fill="both", expand=True)

        self.navigation_buttons = []
        self.pages = [HomePage, DataPage, CameraPage, SettingsPage]
        destinations = ["Главная страница", "Данные", "Камеры", "Настройки"]
        for i, destination in enumerate(destinations):
            button = tk.Button(self.nav_frame, text=destination, bg="#1976D2", fg="white", font=("Arial", 12), relief="flat", command=lambda i=i: self.on_navigation_selected(i))
            button.pack(anchor="w", pady=(5, 0), padx=10, fill="x")
            self.navigation_buttons.append(button)

        self.separator_line = tk.Frame(self, width=2, bg="#1976D2")
        self.separator_line.pack(side="left", fill="y")

        self.update_body_content()

    def show_home(self):
        self.selected_index = 0
        self.update_body_content()

    def show_profile(self):
        self.selected_index = -1  # Специальный индекс для страницы профиля
        self.update_body_content()

    def confirm_exit(self):
        # Запрашиваем подтверждение выхода
        if messagebox.askokcancel("Выход", "Вы уверены, что хотите выйти?"):
            # Если пользователь подтвердил выход, перекидываем на окно авторизации
            self.is_authenticated = False
            self.destroy()

    def update_body_content(self):
        for widget in self.body_frame.winfo_children():
            widget.destroy()

        if self.selected_index == -1:
            ProfilePage(self.body_frame).pack(fill="both", expand=True)
        else:
            self.pages[self.selected_index](self.body_frame).pack(fill="both", expand=True)

    def on_navigation_selected(self, index):
        self.selected_index = index
        self.update_body_content()

if __name__ == "__main__":
    app = Page()
    app.mainloop()
