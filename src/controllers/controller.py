from tkinter import filedialog
from models import Video, FaceDetectorCascade, FaceDetectorDNN, FaceDetectorMTCNN
from models import WatermarkLsbFragile, WatermarkAvgHashQim, WatermarkBlockChecksumDwt
from views import VideoView
import atexit
import threading
import json
import subprocess
import av
import os, shutil

class VideoController:
    FRAMES_DIR = "frames"
    
    def __init__(self):
        self.video = Video()
        self.view = VideoView(self)
        self.Cascade = FaceDetectorCascade()
        self.DNN = FaceDetectorDNN()
        self.MTCNN = FaceDetectorMTCNN()
        self.detect_face_map = {}
        self.wm_lsb = WatermarkLsbFragile()
        self.wm_avgqim = WatermarkAvgHashQim()
        self.wm_dwt = WatermarkBlockChecksumDwt()
        self._clear_frames_folder()
        atexit.register(self._clear_frames_folder) 
               
        
    def _clear_frames_folder(self):
        if os.path.isdir(self.FRAMES_DIR):
            shutil.rmtree(self.FRAMES_DIR)
        os.makedirs(self.FRAMES_DIR, exist_ok=True) 
       

    # def _load_face_map_from_video(self, video_path: str):
    #     """
    #     Load the embedded face_map JSON from the video’s metadata.
    #     Returns:
    #         dict[str, List[Face]] or None if no face_map tag is present.
    #     """
    #     from models.face import Face

    #     # 1️⃣ Find ffprobe on PATH
    #     ffprobe = shutil.which("ffprobe") or shutil.which("ffprobe.exe")
    #     if not ffprobe:
    #         self.view.log_message("[ERROR_03]", "ffprobe not found on PATH.")
    #         return None

    #     try:
    #         # 2️⃣ Grab the full format block as JSON
    #         proc = subprocess.run(
    #             [
    #                 ffprobe,
    #                 "-v", "error",
    #                 "-print_format", "json",
    #                 "-show_format",
    #                 video_path
    #             ],
    #             capture_output=True,
    #             text=True,
    #             check=True
    #         )
    #         info = json.loads(proc.stdout)
    #         print(proc.stdout)  # Debugging line to see the output
    #         tags = info.get("format", {}).get("tags", {})

    #         # 3️⃣ Pull out the face_map field
    #         face_map_raw = tags.get("face_map")
    #         if not face_map_raw:
    #             return None

    #         # 4️⃣ Parse the JSON string stored in that tag
    #         data = json.loads(face_map_raw)

    #         # 5️⃣ Reconstruct your Face objects
    #         face_map = {}
    #         for frame_name, boxes in data.items():
    #             face_map[frame_name] = [
    #                 Face.from_bbox(idx, None, tuple(box), confidence=1.0)
    #                 for idx, box in enumerate(boxes)
    #             ]
    #         return face_map

    #     except subprocess.CalledProcessError as e:
    #         self.view.log_message(
    #             "[ERROR_03]", f"ffprobe execution failed: {e}"
    #         )
    #     except json.JSONDecodeError as e:
    #         self.view.log_message(
    #             "[ERROR_03]", f"face_map JSON malformed or not valid JSON: {e}"
    #         )
    #     except Exception as e:
    #         self.view.log_message(
    #             "[ERROR_03]", f"Unexpected error loading face_map: {e}"
    #         )
    #     return None
   
    
    def browse_video(self):
        if self.video.get_video_path() is not None:
            self._clear_frames_folder()
            self.detect_face_map.clear()
            self.video = Video()

        path = filedialog.askopenfilename(
            title="Select a Video File",
            filetypes=[("Video Files", "*.mp4 *.mkv")]
        )
        if path:
            self.view.clear_log()
            self.video.set_video_path(path)
            self.view.log_message("[INFO]", f"Video selected: {path}")
            
            loaded = self.video.load_face_map(path)
            if loaded:
                self.detect_face_map = loaded
                self.view.log_message("[INFO]", "Face map loaded from video metadata.")
            else:
                self.view.log_message("[INFO]", "No face map found in video metadata.")
            
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
        threading.Thread(target=self._video_to_frames_worker).start()
    
    
    def _video_to_frames_worker(self):
        try:
            total = int(self.video.get_video_info()["Frame Count"])
            self.view.init_progress(total)
            frame_count = self.video.video_to_frames(progress_fn=self.view.update_progress)
            self.view.reset_progress()
            self.view.log_message("[INFO]", f"{frame_count} frames succesfully extracted from video!")
        except Exception as e:
            self.view.log_message("[ERROR_03]", str(e))

    
    def frames_to_video(self):
        print("Creating video from frames...")
        threading.Thread(target=self._frames_to_video_worker).start()
            
            
    def _frames_to_video_worker(self):
        try:
            total = self.video.get_frame_count()
            self.view.init_progress(total)
            video_path = self.video.frames_to_video(progress_fn=self.view.update_progress)
            self.view.reset_progress()
            self.view.log_message("[INFO]", f"Video created: {video_path}")
            
            try:
                self.video.embed_face_map(video_path, self.detect_face_map)
            except Exception as e:
                self.view.log_message("[ERROR_041]", f"FFmpeg embed failed: {e}")

        except Exception as e:
            self.view.log_message("[ERROR_04]", str(e))
            

    # def _embed_face_map(self, video_path: str, face_map: dict) -> None:
    #     """
    #     Embed the given face_map dict into the MP4 at `video_path` as
    #     a format-level metadata tag, using ffmpeg –codec copy.
    #     """
    #     # 1️⃣ Build a pure-Python serializable dict
    #     serializable = {
    #         fname: [
    #             [int(f.bbox[0]), int(f.bbox[1]), int(f.bbox[2]), int(f.bbox[3])]
    #             for f in faces
    #         ]
    #         for fname, faces in face_map.items()
    #     }
    #     face_map_json = json.dumps(serializable, separators=(",", ":"))

    #     # 2️⃣ Locate ffmpeg
    #     ffmpeg_cmd = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
    #     if not ffmpeg_cmd:
    #         raise RuntimeError("ffmpeg not found on PATH – please install or adjust PATH")

    #     # 3️⃣ Run ffmpeg to copy streams and write metadata
    #     tmp_path = video_path.replace(".mp4", "_meta.mp4")
    #     subprocess.run([
    #         ffmpeg_cmd, "-y",
    #         "-i", video_path,
    #         "-metadata", f"face_map={face_map_json}",
    #         "-codec", "copy",
    #         tmp_path
    #     ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    #     # 4️⃣ Replace original with the metadata-stamped file
    #     os.replace(tmp_path, video_path)
    #     self.view.log_message("[INFO]", "face_map embedded via FFmpeg.")

     
    def full_run(self, detector_method: str, watermark_method: str):
        #store the user's choice
        self._full_detector = detector_method
        self._full_watermark = watermark_method
        threading.Thread(target=self._full_run_worker).start()

    def _full_run_worker(self):
        self._detect_faces_worker(self._full_detector)
        self._embed_watermark_worker(self._full_watermark)
        self._verify_watermark_worker(self._full_watermark)
        self._frames_to_video_worker()   
     
                   
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
                self.view.log_message("[ERROR_05]", f"Unknown detection method: {method}")
                return
            
            total = self.video.get_frame_count()
            self.view.init_progress(total)
            face_map = detector.detect_in_folder(self.FRAMES_DIR, progress_fn=self.view.update_progress)
            self.view.reset_progress()
            self.detect_face_map = face_map.copy()
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
            self.view.log_message("[ERROR_06]", str(e))  
              
        
    def embed_watermark(self, method: str):
        threading.Thread(target=self._embed_watermark_worker, args=(method,)).start()

    
    def _embed_watermark_worker(self, method: str):
        try:
            if method == "lsb":
                wm = self.wm_lsb
            elif method == "avgqim":
                wm = self.wm_avgqim 
            elif method == "dwt":
                wm = self.wm_dwt
            else:
                self.view.log_message("[ERROR_08]", f"Unknown watermark method: {method}")
                return
            
            # print(f"Verifying if watermark is already embedded...")
            # total = self.video.get_frame_count()
            # self.view.init_progress(total)
            # watermarked = wm.verify_in_folder(self.FRAMES_DIR, detector, progress_fn=self.view.update_progress)
            # self.view.reset_progress()
            # if watermarked:
            #     self.view.log_message("[ERROR_09]", f"Video is already watermarked with {method.upper()}; skipping re-embed.")
            #     return

            print(f"Embedding {method.upper()} watermark...")
            if not self.detect_face_map:
                self.view.log_message("[ERROR_09]", "No faces detected; cannot embed watermark.")
                return
            total = self.video.get_frame_count()
            self.view.init_progress(total)
            wm.embed_in_folder(self.FRAMES_DIR, self.detect_face_map, progress_fn=self.view.update_progress)
            self.view.reset_progress()
            self.view.log_message("[INFO]", f"{method.upper()} watermark embedded."
            )
        except Exception as e:
            self.view.log_message("[ERROR_10]", str(e))    
    
    
    def verify_watermark(self, method: str):
        threading.Thread(target=self._verify_watermark_worker, args=(method,)).start()
        
    
    def _verify_watermark_worker(self, method: str):
        try:
            if method == "lsb":
                wm = self.wm_lsb
            elif method == "avgqim":
                wm = self.wm_avgqim 
            elif method == "dwt":
                wm = self.wm_dwt
            else:
                self.view.log_message("[ERROR_12]", f"Unknown watermark method: {method}")
                return

            if not self.detect_face_map:
                print("No face map found; attempting to load from video metadata...")
                try:
                    res = subprocess.run([
                        "ffprobe", "-v", "error",
                        "-show_entries", "format_tags=face_map",
                        "-of", "default=noprint_wrappers=1:nokey=1",
                        self.video.get_video_path()
                    ], capture_output=True, text=True, check=True)
                    raw = res.stdout.strip()
                    if not raw:
                        self.view.log_message("[ERROR_13]", "No face_map metadata found; cannot verify.")
                        return
                    data = json.loads(raw)
                    from models.face import Face
                    lm = {}
                    for fname, boxes in data.items():
                        lm[fname] = [
                            Face.from_bbox(i, None, tuple(box), confidence=1.0)
                            for i, box in enumerate(boxes)
                        ]
                    self.detect_face_map = lm
                    self.view.log_message("[INFO]", "face_map loaded via ffprobe.")
                except Exception as ex:
                    self.view.log_message("[ERROR_13]", f"FFprobe load failed: {ex}")
                    return
                
            print(f"Verifying {method.upper()} watermark...")
            total = self.video.get_frame_count()
            self.view.init_progress(total)
            verified = wm.verify_in_folder(self.FRAMES_DIR, self.detect_face_map, progress_fn=self.view.update_progress)
            self.view.reset_progress()
            if verified:
                self.view.log_message("[INFO]", f"{method.upper()} watermark verified successfully!")
            else:
                self.view.log_message("[ERROR_14]", f"{method.upper()} watermark verification failed.")
        except Exception as e:
            self.view.log_message("[ERROR_15]", str(e))     
    
    def run(self):
        self.view.mainloop()
