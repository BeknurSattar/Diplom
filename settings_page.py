import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from auth_page import AuthPage
from translations import translations

class SettingsPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.parent = parent
        self.app = app  # Ссылка на главное приложение
        self.current_language = 'ru'  # Устанавливаем русский язык по умолчанию
        self.configure(bg="#f0f0f0")
        self.content = tk.Frame(self, bg="#f0f0f0")
        self.content.pack(expand=True, fill="both", padx=20, pady=20)
        self.generate_buttons()

    translation_key = 'settings'
    def update_translations(self, new_language):
        self.translations.set_current_language(new_language)
        for page in self.pages:
            if hasattr(page, 'update_language'):
                page.update_language(new_language)
    def set_language(self, language):
        self.current_language = language
        # Обновляем текст на всех кнопках и метках
        self.theme_button.config(text=translations[language]['change_theme'])
        self.notifications_button.config(text=translations[language]['toggle_notifications'])
        self.language_label.config(text=translations[language]['select_language'])
        self.exit_button.config(text=translations[language]['exit'])
        # Обновляем текст на других страницах (если это необходимо)
    def change_theme(self):
        # Изменение темы для всего приложения
        new_theme = "dark" if self.parent.cget('bg') == "#f0f0f0" else "light"
        new_bg = "#303030" if new_theme == "dark" else "#f0f0f0"
        new_fg = "white" if new_theme == "dark" else "black"
        self.apply_theme_to_all(self.parent, new_bg, new_fg)

    def apply_theme_to_all(self, widget, bg, fg):
        # Устанавливаем цвет фона для всех виджетов, которые его поддерживают
        try:
            widget.configure(bg=bg)
            if hasattr(widget, 'configure') and 'fg' in widget.keys():
                widget.configure(fg=fg)
        except tk.TclError:
            pass  # Пропустить, если виджет не поддерживает настройку цвета фона или переднего плана

        for child in widget.winfo_children():
            self.apply_theme_to_all(child, bg, fg)  # Рекурсивно применить тему ко всем дочерним элементам



    def toggle_notifications(self):
        self.notifications_enabled = not getattr(self, 'notifications_enabled', False)
        msg = translations[self.current_language]['notifications_on'] if self.notifications_enabled else \
        translations[self.current_language]['notifications_off']
        messagebox.showinfo(translations[self.current_language]['notifications'], msg)

    def change_language(self, language):
        self.set_language(language)
        self.app.set_language(language)  # Обновляем язык в главном приложении

    def safe_exit(self):
        if messagebox.askokcancel(translations[self.current_language]['exit_confirmation_title'],
                                  translations[self.current_language]['confirm_exit']):
            self.parent.quit()  # Закрыть текущее окно
            self.open_login_window()  # Открыть окно авторизации

    def open_login_window(self):
        auth_window = AuthPage(self.parent)
        auth_window.grab_set()
        # Функция для открытия окна авторизации
        # Здесь должен быть ваш код для инициализации и отображения окна авторизации

    def generate_buttons(self):
        self.theme_button = tk.Button(self.content, command=self.change_theme, bg="#1976D2", fg="white")
        self.theme_button.pack(fill="x", pady=(0, 10), ipady=5)

        self.notifications_button = tk.Button(self.content, command=self.toggle_notifications, bg="#1976D2", fg="white")
        self.notifications_button.pack(fill="x", pady=(0, 10), ipady=5)

        self.language_label = tk.Label(self.content, text="Select Language:", bg="#f0f0f0")
        self.language_label.pack()

        language_options = ["ru", "en", "kz"]
        self.language_dropdown = ttk.Combobox(self.content, values=language_options, state="readonly")
        self.language_dropdown.pack(fill="x", pady=(0, 10), ipady=5)
        self.language_dropdown.set(self.current_language)  # Устанавливаем текущий язык по умолчанию
        self.language_dropdown.bind("<<ComboboxSelected>>", self.change_language_wrapper)

        self.exit_button = tk.Button(self.content, command=self.safe_exit, bg="#1976D2", fg="white")
        self.exit_button.pack(fill="x", ipady=5)

        # Применение начального языка
        self.set_language(self.current_language)

    def change_language_wrapper(self, event=None):
        selected_language = self.language_dropdown.get()
        if selected_language:
            self.change_language(selected_language.lower())
