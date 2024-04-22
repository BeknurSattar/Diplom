import tkinter as tk

class ProfilePage(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        profile_label = tk.Label(self, text="Профиль", font=("Arial", 16), bg="#ffffff")
        profile_label.pack(pady=50)