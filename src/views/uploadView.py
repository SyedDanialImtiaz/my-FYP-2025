import tkinter as tk
from tkinter import filedialog, messagebox

class UploadView:
    def __init__(self, controller):
        self.controller = controller

        self.root = tk.Tk()
        self.root.title("Video Uploader")
        
        self.root.geometry("400x200")

        self.label = tk.Label(self.root, text="No video selected")
        self.label.pack(pady=10)

        self.browse_button = tk.Button(self.root, text="Browse", command=self.controller.browse_video)
        self.browse_button.pack(pady=5)

        self.upload_button = tk.Button(self.root, text="Upload", command=self.controller.upload_video)
        self.upload_button.pack(pady=5)

    def update_label(self, text):
        self.label.config(text=text)

    def show_message(self, title, message):
        messagebox.showinfo(title, message)

    def show_error(self, title, message):
        messagebox.showerror(title, message)

    def mainloop(self):
        self.root.mainloop()
