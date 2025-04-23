import tkinter as tk
from tkinter import scrolledtext
import datetime

class VideoView:
    WIDTH = 800
    HEIGHT = 400

    def __init__(self, controller):
        self.controller = controller

        self.root = tk.Tk()
        self.root.title("FYP Project")
        self.root.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        
        # Main horizontal layout
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill="both", expand=True)
        
        # Left frame for buttons
        left_frame = tk.Frame(main_frame, width=200)
        left_frame.pack(side="left", fill="y", padx=10, pady=10)
        
        # Right frame for logs
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self.browse_button = tk.Button(left_frame, text="Browse", width=20, command=self.controller.browse_video)
        self.browse_button.pack(pady=5)

        # self.upload_button = tk.Button(left_frame, text="Upload", width=20, command=self.controller.upload_video)
        # self.upload_button.pack(pady=5)
        
        # add some buttons to use for later
        self.button1 = tk.Button(left_frame, text="Get Frames", width=20, command=self.controller.video_to_frames)
        self.button1.pack(pady=5)
        
        self.button2 = tk.Button(left_frame, text="Clear Log", width=20, command=lambda: self.clear_log())
        self.button2.pack(pady=5)
        
        self.log_area = scrolledtext.ScrolledText(right_frame, wrap="word", state="disabled")
        self.log_area.pack(fill="both", expand=True)
        
    def log_message(self, title, message):
        # timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        full_message = f"{title}: {message}\n"
        
        self.log_area.config(state="normal")
        self.log_area.insert(tk.END, full_message)
        self.log_area.config(state="disabled")
        self.log_area.yview(tk.END)

    def clear_log(self):
        self.log_area.config(state="normal")
        self.log_area.delete("1.0", tk.END)
        self.log_area.config(state="disabled")

    def mainloop(self):
        self.root.mainloop()
