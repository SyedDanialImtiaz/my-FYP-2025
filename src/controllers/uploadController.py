from tkinter import filedialog
from models.upload import Upload
from views.uploadView import UploadView

class UploadController:
    def __init__(self):
        self.model = Upload()
        self.view = UploadView(self)

    def browse_video(self):
        path = filedialog.askopenfilename(
            title="Select a Video File",
            filetypes=[("Video Files", "*.mp4 *.avi *.mov *.mkv")]
        )
        if path:
            self.model.set_video_path(path)
            self.view.update_label(f"Selected: {path}")
        else:
            self.view.update_label("No video selected")

    def upload_video(self):
        try:
            uploaded_path = self.model.upload_video()
            self.view.show_message("Upload Success", f"Video uploaded to: {uploaded_path}")
        except Exception as e:
            self.view.show_error("Upload Failed", str(e))

    def run(self):
        self.view.mainloop()
