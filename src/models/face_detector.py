import cv2
import os
import numpy as np
from models import Face

class FaceDetector:
    def __init__(self, cascade_path: str = None):
        # default to OpenCV’s bundled frontal-face Haar cascade
        cascade_path = cascade_path or (
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.detector = cv2.CascadeClassifier(cascade_path)

    def detect(self,
               frame: np.ndarray,
               scaleFactor: float = 1.1,
               minNeighbors: int = 5,
               minSize: tuple = (30, 30)
               ) -> list[Face]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        bboxes = self.detector.detectMultiScale(
            gray,
            scaleFactor=scaleFactor,
            minNeighbors=minNeighbors,
            minSize=minSize
        )
        return [
            Face.from_bbox(i, frame, tuple(bbox))
            for i, bbox in enumerate(bboxes)
        ]

    def detect_in_folder(self, folder: str = "frames") -> dict[str, list[Face]]:
        """Walks through all image files in `folder`, runs detect(), and returns a mapping: { filename: [Face, …], … }."""
        if not os.path.isdir(folder):
            raise ValueError(f"Frames folder not found: {folder}")

        results = {}
        for fname in sorted(os.listdir(folder)):
            if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
                continue

            path = os.path.join(folder, fname)
            frame = cv2.imread(path)
            if frame is None:
                # skip unreadable files
                continue

            faces = self.detect(frame)
            results[fname] = faces

        return results   