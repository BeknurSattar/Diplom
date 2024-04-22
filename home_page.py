import tkinter as tk

class HomePage(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        home_label = tk.Label(self, text="Главная страница", font=("Arial", 16), bg="#ffffff")
        home_label.pack(pady=50)