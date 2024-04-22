import tkinter as tk
from tkinter import simpledialog, scrolledtext


class MyApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.layout = 1  # Изначально устанавливаем макет 1

        self.app_bar = self.create_appbar()
        self.content = tk.Frame(self)
        self.content.pack(fill="both", expand=True)

        self.update_content()

    def create_appbar(self):
        app_bar = tk.Frame(self, height=56, bg="#1976D2")
        app_bar.pack(side="top", fill="x")

        label = tk.Label(app_bar, text="Мои камеры", font=("Arial", 20, "bold"), fg="white", bg="#1976D2")
        label.pack(side="left", padx=10)

        pb = tk.Menubutton(app_bar, text="Расположение камер", relief=tk.RAISED)
        pb.menu = tk.Menu(pb, tearoff=0)

        pb.menu.add_command(label="1x1", command=lambda: self.set_layout(1))
        pb.menu.add_command(label="2x2", command=lambda: self.set_layout(2))
        pb.menu.add_command(label="3x3", command=lambda: self.set_layout(3))
        pb.menu.add_command(label="4x4", command=lambda: self.set_layout(4))

        pb["menu"] = pb.menu
        pb.pack(side="right", padx=10, pady=5)

        return app_bar

    def set_layout(self, layout):
        self.layout = layout
        self.update_content()

    def update_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

        self.create_buttons_layout()

    def create_buttons_layout(self):
        for _ in range(self.layout):
            row = tk.Frame(self.content)
            row.pack(side="top", padx=5, pady=5)
            for _ in range(self.layout):
                box = tk.Frame(row, bg="blue", bd=5, relief="ridge", width=150, height=150)  # Изменим размеры box
                box.pack(side="left", padx=5, pady=5)
                btn = tk.Button(box, text="Выбрать камеру", command=lambda b=box: self.open_video_in_box(b))
                btn.pack(padx=10, pady=10)

    def open_video_in_box(self, box):
        # Пока просто зададим текст box'у, чтобы показать, что функция вызывается
        language = simpledialog.askstring("Выбор языка", "Выберите язык программирования:")
        if language:
            # box.config(text=language)
            self.data_text = scrolledtext.ScrolledText(box, wrap=tk.WORD, width=50, height=20)
            self.data_text.pack(pady=10)


if __name__ == "__main__":
    app = MyApp()
    app.mainloop()
