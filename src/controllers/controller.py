from tkinter import filedialog
from models.video_model import Upload
from views.view import VideoView

class VideoController:
    def __init__(self):
        self.model = Upload()
        self.view = VideoView(self)

    def browse_video(self):
        path = filedialog.askopenfilename(
            title="Select a Video File",
            filetypes=[("Video Files", "*.mp4 *.mkv")]
        )
        if path:
            self.model.set_video_path(path)
            # self.view.update_label(f"Selected: {path}")
            self.view.log_message("[INFO]", f"Video selected: {path}")
        else:
            # self.view.update_label("No video selected")
            self.view.log_message("[ERROR]", "No video selected")

    def upload_video(self):
        try:
            uploaded_path = self.model.upload_video()
            # self.view.log_message(f"Video uploaded to: {uploaded_path}")
            self.view.log_message("[INFO]", f"Video uploaded to: {uploaded_path}")
        except Exception as e:
            # self.view.log_message(f"Upload failed: {str(e)}")
            self.view.log_message("[ERROR]", str(e))

    def run(self):
        self.view.mainloop()
