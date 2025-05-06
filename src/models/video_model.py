import os
import shutil
import cv2

class Video:
    def __init__(self):
        self.video_path = None
        self.file_name = None
        self.fps = None
        self.frame_count = None
        self.duration = None
        self.width = None
        self.height = None

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
        
    def video_to_frames(self, output_folder="frames"):

        if not self.video_path:
            raise ValueError("No video file selected.")

        if os.path.exists(output_folder):
            shutil.rmtree(output_folder)      # delete folder + contents
        os.makedirs(output_folder, exist_ok=True)
         
        cap = cv2.VideoCapture(self.video_path)

        if not cap.isOpened():
            raise ValueError("Cannot open video.")

        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_file_name = os.path.join(output_folder, f"frame_{frame_count:04d}.jpg")
            cv2.imwrite(frame_file_name, frame)
            frame_count += 1

        cap.release()
        
        return frame_count
    
    def frames_to_video(self, frames_folder="frames", output_path="video_output.mp4", codec="mp4v"):
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
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))
        ])
        if not frames:
            raise ValueError(f"No frames found in folder: {frames_folder}")

        # Initialize VideoWriter
        fourcc = cv2.VideoWriter_fourcc(*codec)
        out = cv2.VideoWriter(output_path, fourcc, fps, size)
        if not out.isOpened():
            raise ValueError("Cannot create video writer. Check codec and output path.")

        # Write frames to video
        for fname in frames:
            frame_path = os.path.join(frames_folder, fname)
            img = cv2.imread(frame_path)
            if img is None:
                raise ValueError(f"Cannot read frame: {frame_path}")
            out.write(img)

        out.release()
        return output_path
    
