from tkinter import filedialog
from models import Video, FaceDetectorCascade, FaceDetectorDNN, FaceDetectorMTCNN
from models import WatermarkLsbFragile, WatermarkAvgHashQim, WatermarkBlockChecksumDwt
from views import VideoView
import atexit
import threading
import json
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
       

    def browse_video(self):
        if self.video.get_video_path() is not None:
            self._clear_frames_folder()
            self.video = Video()

        path = filedialog.askopenfilename(
            title="Select a Video File",
            filetypes=[("Video Files", "*.mp4 *.mkv")]
        )
        if path:
            self.view.clear_log()
            self.video.set_video_path(path)
            self.view.log_message("[INFO]", f"Video selected: {path}")
            
            # loaded = self._load_face_map_from_video(path)
            # if loaded:
            #     self.detect_face_map = loaded.copy()
            #     self.view.log_message("[INFO]", "Face map loaded from video metadata.")
            # else:
            #     self.detect_face_map = {}
            #     self.view.log_message("[INFO]", "No face map found in video metadata.")
            
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
            # 1) Use existing code to stitch PNG frames into an MP4 or MKV (via your Video.frames_to_video)
            total = self.video.get_frame_count()
            self.view.init_progress(total)
            temp_path = self.video.frames_to_video(progress_fn=self.view.update_progress)
            self.view.reset_progress()
            self.view.log_message("[INFO]", f"Temporary video created: {temp_path}")

            # 2) Remux with PyAV to inject metadata (face_map) into a *new* file of the same format
            try:
                ext = os.path.splitext(temp_path)[1].lower()  # e.g. ".mp4" or ".mkv"
                # a) Build a Python dict of your bounding-box lists
                serializable = {
                    fname: [
                        [int(f.bbox[0]), int(f.bbox[1]), int(f.bbox[2]), int(f.bbox[3])]
                        for f in faces
                    ]
                    for fname, faces in self.detect_face_map.items()
                }
                face_map_json = json.dumps(serializable)

                # b) Open the just‐created temp video for reading
                inp = av.open(temp_path)

                # c) Choose a new filename for the remuxed output (same extension)
                base, _ = os.path.splitext(temp_path)
                tmp_path = f"{base}_meta{ext}"

                # d) Open an output container with the same format
                if ext == ".mp4":
                    out = av.open(tmp_path, mode="w", format="mp4")
                    # MP4 only supports standard tags: we’ll store JSON in “comment”
                    metadata_key = "comment"
                    metadata_value = face_map_json
                else:
                    # For MKV (or other Matroska‐compatible), use a custom “face_map” tag
                    out = av.open(tmp_path, mode="w", format="matroska")
                    metadata_key = "face_map"
                    metadata_value = face_map_json

                # e) Assign metadata (keys must be str, values must be str for these containers)
                if metadata_value:
                    out.metadata[metadata_key] = metadata_value

                # f) Copy each input stream into the output (copy‐scheme)
                for inp_stream in inp.streams:
                    print("111")
                    out.add_stream(None, template=inp_stream)
                    print("222")

                # g) Demux packets from inp and mux them into out
                for packet in inp.demux():
                    # Skip empty/dummy packets
                    if packet.dts is None:
                        continue
                    in_index = packet.stream.index
                    packet.stream = out.streams[in_index]
                    out.mux(packet)

                # h) Close both containers to write headers/trailers
                out.close()
                inp.close()

                # i) Remove the original temp video and rename the “_meta” one to the original name
                os.remove(temp_path)
                os.replace(tmp_path, temp_path)

                self.view.log_message("[INFO]", f"Embedded face_map metadata into: {temp_path}")
            except Exception as e:
                self.view.log_message("[ERROR_041]", f"Failed to embed face_map metadata: {e}")

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
                try:
                    container = av.open(self.video.get_video_path())
                    raw_json = container.metadata.get("face_map") \
                               or container.metadata.get("comment", "")
                    container.close()
                    if raw_json:
                        data = json.loads(raw_json)
                        from models.face import Face
                        loaded_map: dict[str, list[Face]] = {}
                        for fname, boxes in data.items():
                            faces_list: list[Face] = []
                            for i, bbox_list in enumerate(boxes):
                                x, y, w, h = bbox_list
                                faces_list.append(
                                    Face.from_bbox(i, None, (x, y, w, h), confidence=1.0)
                                )
                            loaded_map[fname] = faces_list
                        self.detect_face_map = loaded_map.copy()
                        self.view.log_message("[INFO]", "Face map loaded from video metadata.")
                    else:
                        self.view.log_message("[ERROR_13]", "No face map found in metadata; cannot verify.")
                        return
                except Exception:
                    self.view.log_message("[ERROR_13]", "Failed to read metadata; cannot verify.")
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
