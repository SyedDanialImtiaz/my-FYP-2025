import os
import shutil
import cv2
import subprocess
import json
from models import Face

class Video:
    def __init__(self):
        self.video_path = None
        self.file_name = None
        self.fps = None
        self.frame_count = None
        self.duration = None
        self.width = None
        self.height = None

    def get_frame_count(self):
        return self.frame_count

    def set_video_path(self, path):
        self.video_path = path

    def get_video_path(self):
        return self.video_path

    def get_video_info(self):
        cap = cv2.VideoCapture(self.video_path)

        if not cap.isOpened():
            raise ValueError("Cannot open video.")

        self.file_name = os.path.basename(self.video_path)
        self.fps = cap.get(cv2.CAP_PROP_FPS)
        self.frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.duration = self.frame_count / self.fps if self.fps else 0
        self.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        format_ext = os.path.splitext(self.video_path)[-1].replace('.', '')

        cap.release()

        return {
            "File Name": self.file_name,
            "Format": format_ext,
            "Resolution": f"{self.width}x{self.height}",
            "Duration (s)": round(self.duration, 2),
            "FPS": self.fps,
            "Frame Count": self.frame_count
        }
        
    def video_to_frames(self, output_folder="frames", progress_fn=None):

        if not self.video_path:
            raise ValueError("No video file selected.")

        if os.path.exists(output_folder):
            shutil.rmtree(output_folder)      # delete folder + contents
        os.makedirs(output_folder, exist_ok=True)
         
        cap = cv2.VideoCapture(self.video_path)

        if not cap.isOpened():
            raise ValueError("Cannot open video.")

        # total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_file_name = os.path.join(output_folder, f"frame_{frame_count:04d}.png")
            cv2.imwrite(frame_file_name, frame)
            frame_count += 1
            
            if progress_fn:
                progress_fn(frame_count)

        cap.release()
        
        return frame_count
    
    def frames_to_video(self, frames_folder="frames", output_path="video_output.mp4", codec="mp4v", progress_fn=None):
        """
        Stitch frames from a folder back into a video file.

        :param frames_folder: Directory containing image frames.
        :param output_path: Path for saving the output video.
        :param codec: FourCC codec (e.g., 'XVID' for .avi, 'mp4v' for .mp4).
        :param fps: Frames per second. Defaults to original video's FPS if available.
        :return: The output video path.
        """
        fps = self.fps
        size = (self.width, self.height)
        
        # output_path = self.file_name.replace('.mp4', '_output.mp4')

        # Collect and sort frame files
        frames = sorted([
            f for f in os.listdir(frames_folder)
            if f.lower().endswith(('.png'))
        ])
        if not frames:
            raise ValueError(f"No frames found in folder: {frames_folder}")

        # Initialize VideoWriter
        fourcc = cv2.VideoWriter_fourcc(*codec)
        out = cv2.VideoWriter(output_path, fourcc, fps, size)
        if not out.isOpened():
            raise ValueError("Cannot create video writer. Check codec and output path.")

        # Write frames to video
        for idx, fname in enumerate(frames, start=1):
            frame_path = os.path.join(frames_folder, fname)
            img = cv2.imread(frame_path)
            if img is None:
                raise ValueError(f"Cannot read frame: {frame_path}")
            out.write(img)
            
            if progress_fn:
                progress_fn(idx)

        out.release()
        return output_path
    
    def load_face_map(self) -> dict[str, list[Face]] | None:
        """
        Reads the embedded `face_map` tag from this video's metadata
        and reconstructs Face objects. Returns the face_map or None.
        """
        ffprobe = shutil.which("ffprobe") or shutil.which("ffprobe.exe")
        if not ffprobe:
            raise RuntimeError("ffprobe not found on PATH")
        proc = subprocess.run([
            ffprobe,
            "-v", "error",
            "-print_format", "json",
            "-show_format",
            self.video_path
        ], capture_output=True, text=True, check=True)
        info = json.loads(proc.stdout)
        raw = info.get("format", {}).get("tags", {}).get("face_map")
        if not raw:
            return None
        data = json.loads(raw)
        face_map = {
            frame: [
                Face.from_bbox(idx, None, tuple(box), confidence=1.0)
                for idx, box in enumerate(boxes)
            ]
            for frame, boxes in data.items()
        }
        return face_map

    def embed_face_map(self, face_map: dict[str, list[Face]]) -> None:
        """
        Embeds the given face_map into this video’s metadata in place
        (replacing the file), using ffmpeg -codec copy.
        """
        # Serialize to JSON
        serializable = {
            frame: [[*map(int, f.bbox)] for f in faces]
            for frame, faces in face_map.items()
        }
        fm_json = json.dumps(serializable, separators=(",", ":"))

        ffmpeg = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
        if not ffmpeg:
            raise RuntimeError("ffmpeg not found on PATH")

        tmp = self.video_path.replace(".mp4", "_meta.mp4")
        subprocess.run([
            ffmpeg, "-y",
            "-i", self.video_path,
            "-map_metadata", "0",
            "-metadata", f"face_map={fm_json}",
            "-c", "copy",
            tmp
        ], check=True)
        os.replace(tmp, self.video_path)