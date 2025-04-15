import tkinter as tk
from tkinter import scrolledtext

class VideoView:
    WIDTH = 600
    HEIGHT = 400

    def __init__(self, controller):
        self.controller = controller

        self.root = tk.Tk()
        self.root.title("FYP Project")
        
        self.root.geometry(f"{self.WIDTH}x{self.HEIGHT}")

        self.browse_button = tk.Button(self.root, text="Browse", command=self.controller.browse_video)
        self.browse_button.pack(pady=5)

        self.upload_button = tk.Button(self.root, text="Upload", command=self.controller.upload_video)
        self.upload_button.pack(pady=5)
        
        self.log_area = scrolledtext.ScrolledText(self.root, width=60, height=40, state="disabled")
        self.log_area.pack(pady=10)
        
    def log_message(self, title, message):
        self.log_area.config(state="normal")
        self.log_area.insert(tk.END, f"{title + " " +message}\n")
        self.log_area.config(state="disabled")
        self.log_area.yview(tk.END)

    def mainloop(self):
        self.root.mainloop()
