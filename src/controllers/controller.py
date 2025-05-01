from tkinter import filedialog
from models import Video
from views import VideoView

class VideoController:
    def __init__(self):
        self.model = Video()
        self.view = VideoView(self)

    def browse_video(self):
        if self.model.get_video_path() is not None:
            self.model = Video()

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

    # def upload_video(self):
    #     try:
    #         uploaded_path = self.model.upload_video()
    #         self.view.log_message("[INFO]", f"Video uploaded to: {uploaded_path}")
    #     except Exception as e:
    #         self.view.log_message("[ERROR_03]", str(e))
    
    def video_to_frames(self):
        try:
            frame_count = self.model.video_to_frames()
            self.view.log_message("[INFO]", f"{frame_count} frames succesfully extracted from video!")
        except Exception as e:
            self.view.log_message("[ERROR_04]", str(e))
            
    def frames_to_video(self):
        try:
            video_path = self.model.frames_to_video()
            self.view.log_message("[INFO]", f"Video created from frames: {video_path}")
        except Exception as e:
            self.view.log_message("[ERROR_05]", str(e))

    def run(self):
        self.view.mainloop()
