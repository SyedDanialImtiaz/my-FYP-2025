import os
import shutil

class Upload:
    def __init__(self):
        self.video_path = None

    def set_video_path(self, path):
        self.video_path = path

    def get_video_path(self):
        return self.video_path

    def upload_video(self, destination_folder="uploaded_videos"):
        if not self.video_path:
            raise ValueError("No video file selected.")

        os.makedirs(destination_folder, exist_ok=True)
        file_name = os.path.basename(self.video_path)
        destination_path = os.path.join(destination_folder, file_name)

        shutil.copy(self.video_path, destination_path)
        return destination_path
