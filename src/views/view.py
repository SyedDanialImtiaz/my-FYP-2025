import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext

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
        
        # ─── temporary “Run All” button ─────────────────────────────
        self.run_all_button = tk.Button(left_frame, text="Run All Pipeline", width=20, command=self._on_run_all)
        self.run_all_button.pack(pady=5)
        
        self.video_button = tk.Button(left_frame, text="Create Video", width=20, command=self.controller.frames_to_video)
        self.video_button.pack(pady=5)
        
        self.clear_button = tk.Button(left_frame, text="Clear Log", width=20, command=lambda: self.clear_log())
        self.clear_button.pack(pady=5)
        
        # Detector selection dropdown
        self.detector_var = tk.StringVar(value="dnn")
        self.detector_dropdown = ttk.Combobox(
            left_frame,
            textvariable=self.detector_var,
            values=["dnn", "haarcascade", "mtcnn"],
            state="readonly",
            width=18
        )
        self.detector_dropdown.pack(pady=5)

        self.detect_button = tk.Button(left_frame, text="Detect Faces", width=20, command=lambda: self.controller.detect_faces(self.detector_var.get()))
        self.detect_button.pack(pady=5)
        
        # Watermark selection dropdown
        self.watermark_var = tk.StringVar(value="lsb")
        self.watermark_dropdown = ttk.Combobox(
            left_frame,
            textvariable=self.watermark_var,
            values=["lsb", "avgqim", "dwt"],
            state="readonly",
            width=18
        )
        self.watermark_dropdown.pack(pady=5)
        
        self.embed_button = tk.Button(left_frame, text="Embed watermark", width=20, command=lambda: self.controller.embed_watermark(self.watermark_var.get()))
        self.embed_button.pack(pady=5)
        
        self.verify_button = tk.Button(left_frame, text="Verify watermark", width=20, command=lambda: self.controller.verify_watermark(self.watermark_var.get()))
        self.verify_button.pack(pady=5)
        
        self.progress_bar = ttk.Progressbar(right_frame, mode='determinate')
        self.progress_bar.pack(fill="x", pady=(5, 15))
        self.progress_bar["value"] = 0
        
        self.log_area = scrolledtext.ScrolledText(right_frame, wrap="word", state="disabled")
        self.log_area.pack(fill="both", expand=True)
        
        # disable all the other controls for now // temporary
        for btn in (
            self.video_button,
            self.detect_button,
            self.embed_button,
            self.verify_button,
        ):
            btn.config(state="normal")
    
    def _on_run_all(self):
        detector =  self.detector_var.get()
        watermark = self.watermark_var.get()
        self.run_all_button.config(state="disabled")
        self.controller.full_run(detector, watermark)
    
    def init_progress(self, total):
        self.progress_bar["maximum"] = total
        self.progress_bar["value"] = 0
        self.root.update_idletasks()

    def update_progress(self, step=1):
        self.progress_bar["value"] += step
        self.root.update_idletasks()

    def reset_progress(self):
        self.progress_bar["value"] = 0
        self.root.update_idletasks()
    
    def log_message(self, title, message):
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
