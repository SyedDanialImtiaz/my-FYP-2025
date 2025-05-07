import cv2
import os
import numpy as np
from models import Face

class FaceDetectorCascade:
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
        
        # Try the 3-way API to get levelWeights (confidences)
        bboxes, _, levelWeights = [], [], []
        if hasattr(self.detector, "detectMultiScale3"):
            # OpenCV ≥4.5.1
            bboxes, _, levelWeights = self.detector.detectMultiScale3(
                gray,
                scaleFactor=scaleFactor,
                minNeighbors=minNeighbors,
                minSize=minSize,
                outputRejectLevels=True
            )
            # levelWeights is an array of raw scores
            weights = np.array(levelWeights).flatten()
        elif hasattr(self.detector, "detectMultiScale2"):
            # Older OpenCV versions
            bboxes, levelWeights = self.detector.detectMultiScale2(
                gray,
                scaleFactor=scaleFactor,
                minNeighbors=minNeighbors,
                minSize=minSize
            )
            weights = np.array(levelWeights).flatten()
        else:
            # fallback: no scores, assign 1.0 to all
            bboxes = self.detector.detectMultiScale(
                gray,
                scaleFactor=scaleFactor,
                minNeighbors=minNeighbors,
                minSize=minSize
            )
            weights = np.ones(len(bboxes), dtype=float)
            
        # Normalize weights to 0–1 range per frame
        if len(weights) > 0:
            w_min, w_max = weights.min(), weights.max()
            if w_max > w_min:
                norm_weights = (weights - w_min) / (w_max - w_min)
            else:
                # all equal → treat as full confidence
                norm_weights = np.ones_like(weights)
        else:
            norm_weights = np.array([])        
            
        faces: list[Face] = []
        for i, bbox in enumerate(bboxes):
            x, y, w, h = tuple(bbox)
            confidence = float(norm_weights[i]) if i < len(norm_weights) else 0.0
            faces.append(Face.from_bbox(i, frame, (x, y, w, h), confidence))

        return faces

    def detect_in_folder(self, folder: str = "frames") -> dict[str, list[Face]]:
        """Walks through all image files in `folder`, runs detect(), and returns a mapping: { filename: [Face, …], … }."""
        if not os.path.isdir(folder):
            raise ValueError(f"{folder} folder not found")

        if not os.listdir(folder):
            raise ValueError(f"{folder} folder is empty")

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