from tkinter import filedialog
from models import Video, FaceDetector
from views import VideoView
import atexit

class VideoController:
    FRAMES_DIR = "frames"
    
    def __init__(self):
        self.model = Video()
        self.view = VideoView(self)
        self.detector = FaceDetector()
        self._clear_frames_folder()
        atexit.register(self._clear_frames_folder)        
        
    def _clear_frames_folder(self):
        """Delete + recreate the frames folder so it's empty."""
        import os, shutil
        if os.path.isdir(self.FRAMES_DIR):
            shutil.rmtree(self.FRAMES_DIR)
        os.makedirs(self.FRAMES_DIR, exist_ok=True)    

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
            
    def detect_faces(self):
        try:
            face_map = self.detector.detect_in_folder(self.FRAMES_DIR)  
            for fname, faces in face_map.items():
                self.view.log_message("[INFO]", f"{fname}: {len(faces)} face(s) detected")
                for face in faces:
                    x, y, w, h = face.bbox
                    # self.view.log_message("[INFO]", f"  • Face {face.index}: x={x}, y={y}, w={w}, h={h}")
        except Exception as e:
            self.view.log_message("[ERROR_06]", str(e))

    def run(self):
        self.view.mainloop()
