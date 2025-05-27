from tkinter import filedialog
from models import Video, FaceDetectorCascade, FaceDetectorDNN, FaceDetectorMTCNN
from views import VideoView
import atexit
import threading
import os, shutil

class VideoController:
    FRAMES_DIR = "frames"
    
    def __init__(self):
        self.video = Video()
        self.view = VideoView(self)
        self.Cascade = FaceDetectorCascade()
        self.DNN = FaceDetectorDNN()
        self.MTCNN = FaceDetectorMTCNN()
        self._clear_frames_folder()
        atexit.register(self._clear_frames_folder) 
               
        
    def _clear_frames_folder(self):
        if os.path.isdir(self.FRAMES_DIR):
            shutil.rmtree(self.FRAMES_DIR)
        os.makedirs(self.FRAMES_DIR, exist_ok=True) 
           

    def browse_video(self):
        if self.video.get_video_path() is not None:
            self.video = Video()

        path = filedialog.askopenfilename(
            title="Select a Video File",
            filetypes=[("Video Files", "*.mp4 *.mkv")]
        )
        if path:
            self.view.clear_log()
            self.video.set_video_path(path)
            self.view.log_message("[INFO]", f"Video selected: {path}")
            
            try:
                info = self.video.get_video_info()
                for key, value in info.items():
                    self.view.log_message("[INFO]", f"{key}: {value}")
            except Exception as e:
                self.view.log_message("[ERROR_01]", str(e))
            
            self.video_to_frames()
        else:
            self.view.log_message("[ERROR_02]", "No video file selected.")
            
    
    def video_to_frames(self):
        print("Converting video to frames...")
        threading.Thread(target=self.video_to_frames_worker).start()
    
    
    def video_to_frames_worker(self):
        try:
            frame_count = self.video.video_to_frames()
            self.view.log_message("[INFO]", f"{frame_count} frames succesfully extracted from video!")
        except Exception as e:
            self.view.log_message("[ERROR_03]", str(e))

    
    def frames_to_video(self):
        print("Creating video from frames...")
        threading.Thread(target=self.frames_to_video_worker).start()
            
            
    def frames_to_video_worker(self):
        try:
            video_path = self.video.frames_to_video()
            self.view.log_message("[INFO]", f"Video created from frames: {video_path}")
        except Exception as e:
            self.view.log_message("[ERROR_04]", str(e))
            
                   
    def detect_faces(self, method: str):
        print("-------------------------------------------------------------------------")
        threading.Thread(target=self._detect_faces_worker, args=(method,)).start()
        

    def _detect_faces_worker(self, method: str):
        try:
            print(f"Detecting faces using {method.upper()}...")
            if method == "dnn":
                detector = self.DNN
            elif method == "haarcascade":
                detector = self.Cascade
            elif method == "mtcnn":
                detector = self.MTCNN
            else:
                self.view.log_message("[ERROR]", f"Unknown detection method: {method}")
                return

            image_count = self.video.get_frame_count()
            self.view.init_progress(image_count)
            face_map = detector.detect_in_folder(self.FRAMES_DIR, progress_fn=self.view.update_progress)
            self.view.reset_progress()
            print("Drawing face boundary...")
            detector.draw_boundary(self.FRAMES_DIR)
            print("-------------------------------------------------------------------------")

            summary: dict[int, int] = {}
            for fname, faces in face_map.items():
                for face in faces:
                    idx = face.index
                    summary[idx] = summary.get(idx, 0) + 1
                    x, y, w, h = face.bbox
                    conf = face.confidence
                    print(f"{fname}  • Face {idx}: x={x}, y={y}, w={w}, h={h}, confidence={conf:.2f}")

            self.view.log_message("[INFO]", f"Face detection summary: {method.upper()}")
            for idx in sorted(summary):
                count = summary[idx]
                self.view.log_message("[INFO]", f"Face {idx}: detected {count} time{'s' if count!=1 else ''}")

        except Exception as e:
            self.view.log_message("[ERROR_05]", str(e))  
              
    
    def run(self):
        self.view.mainloop()
