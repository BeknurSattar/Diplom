import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from auth_page import AuthPage


class SettingsPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.configure(bg="#f0f0f0")
        self.content = tk.Frame(self, bg="#f0f0f0")
        self.content.pack(expand=True, fill="both", padx=20, pady=20)
        self.generate_buttons()

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
        msg = "Уведомления включены" if self.notifications_enabled else "Уведомления выключены"
        messagebox.showinfo("Уведомления", msg)

    def change_language(self, event):
        selected_language = self.language_dropdown.get()
        print(f"Выбранный язык: {selected_language}")
        # Здесь должна быть реализация изменения языка интерфейса

    def safe_exit(self):
        if messagebox.askokcancel("Подтверждение", "Вы уверены, что хотите выйти из аккаунта?"):
            self.parent.quit()  # Закрыть текущее окно
            self.open_login_window()  # Открыть окно авторизации

    def open_login_window(self):
        auth_window = AuthPage(self.parent)
        auth_window.grab_set()
        # Функция для открытия окна авторизации
        # Здесь должен быть ваш код для инициализации и отображения окна авторизации

    def generate_buttons(self):
        theme_button = tk.Button(self.content, text="Сменить тему", command=self.change_theme, bg="#1976D2", fg="white")
        theme_button.pack(fill="x", pady=(0, 10), ipady=5)

        notifications_button = tk.Button(self.content, text="Настройки уведомлений", command=self.toggle_notifications, bg="#1976D2", fg="white")
        notifications_button.pack(fill="x", pady=(0, 10), ipady=5)

        language_label = tk.Label(self.content, text="Выберите язык:", bg="#f0f0f0")
        language_label.pack()

        language_options = ["Русский", "Английский"]
        self.language_dropdown = ttk.Combobox(self.content, values=language_options, state="readonly")
        self.language_dropdown.pack(fill="x", pady=(0, 10), ipady=5)
        self.language_dropdown.bind("<<ComboboxSelected>>", self.change_language)

        exit_button = tk.Button(self.content, text="Выйти", command=self.safe_exit, bg="#1976D2", fg="white")
        exit_button.pack(fill="x", ipady=5)
