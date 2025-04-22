import os
import shutil
import cv2

class Video:
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

    def get_video_info(self):
        cap = cv2.VideoCapture(self.video_path)

        if not cap.isOpened():
            raise ValueError("Cannot open video.")

        file_name = os.path.basename(self.video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps else 0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        format_ext = os.path.splitext(self.video_path)[-1].replace('.', '')

        cap.release()

        return {
            "File Name": file_name,
            "Format": format_ext,
            "Resolution": f"{width}x{height}",
            "Duration (s)": round(duration, 2),
            "FPS": fps,
            "Frame Count": frame_count
        }