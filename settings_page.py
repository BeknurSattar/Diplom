import tkinter as tk
from tkinter import ttk

class SettingsPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.configure(bg="#f0f0f0")  # Set background color
        self.content = tk.Frame(self, bg="#f0f0f0")  # Create content frame with background color
        self.content.pack(expand=True, fill="both", padx=20, pady=20)  # Add padding around the content
        self.generate_buttons()

    def change_theme(self):
        # Example: Change theme mode
        self.parent.theme_mode = "dark" if self.parent.theme_mode == "light" else "light"
        self.content.update()

    def configure_notifications(self):
        # Example: Configure notifications
        print("Configuring notifications...")

    def change_language(self, event):
        # Example: Change interface language
        selected_language = self.language_dropdown.get()
        print(f"Selected language: {selected_language}")

    def exit_app(self):
        # Exit the application
        self.parent.destroy()

    def generate_buttons(self):
        # Create buttons for different settings
        theme_button = tk.Button(self.content, text="Change Theme", command=self.change_theme, bg="#1976D2", fg="white")
        theme_button.pack(fill="x", pady=(0, 10), ipady=5)  # Add padding and increase internal padding (ipady) for button

        notifications_button = tk.Button(self.content, text="Configure Notifications", command=self.configure_notifications, bg="#1976D2", fg="white")
        notifications_button.pack(fill="x", pady=(0, 10), ipady=5)

        language_label = tk.Label(self.content, text="Select Language:", bg="#f0f0f0")
        language_label.pack()

        # Language dropdown menu
        language_options = ["Russian", "English"]
        self.language_dropdown = ttk.Combobox(self.content, values=language_options, state="readonly")
        self.language_dropdown.pack(fill="x", pady=(0, 10), ipady=5)
        self.language_dropdown.bind("<<ComboboxSelected>>", self.change_language)

        exit_button = tk.Button(self.content, text="Exit", command=self.exit_app, bg="#1976D2", fg="white")
        exit_button.pack(fill="x", ipady=5)
