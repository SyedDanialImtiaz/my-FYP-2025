from tkinter import filedialog
from models.video_model import Video
from views.view import VideoView

class VideoController:
    def __init__(self):
        self.model = Video()
        self.view = VideoView(self)

    def browse_video(self):
        path = filedialog.askopenfilename(
            title="Select a Video File",
            filetypes=[("Video Files", "*.mp4 *.mkv")]
        )
        if path:
            self.view.clear_log()  # ← clears log before writing new info
            self.model.set_video_path(path)
            self.view.log_message("[INFO]", f"Video selected: {path}")
            
            try:
                info = self.model.get_video_info()
                for key, value in info.items():
                    self.view.log_message("[INFO]", f"{key}: {value}")
            except Exception as e:
                self.view.log_message("[ERROR_01]", str(e))
        else:
            self.view.log_message("[ERROR_02]", "No video file selected.")

    def upload_video(self):
        try:
            uploaded_path = self.model.upload_video()
            self.view.log_message("[INFO]", f"Video uploaded to: {uploaded_path}")
        except Exception as e:
            self.view.log_message("[ERROR_03]", str(e))

    def run(self):
        self.view.mainloop()
