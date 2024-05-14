import os
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser  # Добавляем импорт модуля webbrowser
from .auth_page import AuthPage
from Helps.translations import translations
class SettingsPage(tk.Frame):
    def __init__(self, parent, app, user_id=None):
        super().__init__(parent)
        self.parent = parent
        self.app = app  # Ссылка на главное приложение
        self.user_id = user_id
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
        self.help_button.config(text=translations[language]['help'])
        self.language_label.config(text=translations[language]['select_language'])
        self.exit_button.config(text=translations[language]['exit'])
        # Обновляем текст на других страницах (если это необходимо)

    def change_theme(self):
        new_theme = "dark" if self.app.cget('bg') == "#f0f0f0" else "light"
        new_bg = "#1976D2" if new_theme == "dark" else "#f0f0f0"
        new_fg = "white" if new_theme == "dark" else "black"

        # Применяем новую тему к основному окну приложения и всем виджетам
        self.app.configure(bg=new_bg)  # Изменяем цвет фона главного окна
        self.apply_theme_to_all(self.app, new_bg, new_fg)

    def apply_theme_to_all(self, widget, bg, fg):
        try:
            widget.configure(bg=bg)
            if hasattr(widget, 'configure') and 'fg' in widget.keys():
                widget.configure(fg=fg)
        except tk.TclError:
            pass  # Пропустить, если виджет не поддерживает настройку цвета фона или переднего плана

        for child in widget.winfo_children():
            self.apply_theme_to_all(child, bg, fg)  # Рекурсивно применить тему ко всем дочерним элементам

    def open_help_document(self):
        # Путь к файлу теперь формируется через os.path.join для корректной работы на разных ОС
        help_path = os.path.join('Helps', 'Diplom.pdf')
        if os.path.exists(help_path):
            webbrowser.open(help_path)
        else:
            messagebox.showerror("Ошибка", "Файл не найден. Проверьте путь: " + help_path)
            print("Файл не найден. Проверьте путь:", help_path)

    def change_language(self, language):
        self.set_language(language)
        self.app.set_language(language)  # Обновляем язык в главном приложении

    def change_language_wrapper(self, event=None):
        selected_language = self.language_dropdown.get()
        if selected_language:
            self.change_language(selected_language.lower())

    def safe_exit(self):
        """Запрашивает подтверждение выхода и выходит из аккаунта, перезапускает окно авторизации."""
        if messagebox.askokcancel(translations[self.current_language]['exit_confirmation_title'],
                                  translations[self.current_language]['confirm_exit']):
            self.app.logout()  # Выход из аккаунта

    def generate_buttons(self):
        self.theme_button = tk.Button(self.content, command=self.change_theme, bg="#1976D2", fg="white")
        self.theme_button.pack(fill="x", pady=(0, 10), ipady=5)

        # Кнопка Help
        self.help_button = tk.Button(self.content, command=self.open_help_document, bg="#1976D2", fg="white")
        self.help_button.pack(fill="x", pady=(0, 10), ipady=5)

        self.language_label = tk.Label(self.content, bg="#f0f0f0")
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