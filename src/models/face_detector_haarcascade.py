import cv2
import os
import numpy as np
from tqdm import tqdm
from models import Face

class FaceDetectorCascade:
    def __init__(self, cascade_path: str = None):
        # default to OpenCV’s bundled frontal-face Haar cascade
        cascade_path = cascade_path or (
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.detector = cv2.CascadeClassifier(cascade_path)
        
        self.results: dict[str, list[Face]] = {}

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

    def detect_in_folder(self, folder: str = "frames", progress_fn: callable = None) -> dict[str, list[Face]]:
        """Walks through all .jpg/.png in `folder`, runs detect(), returns: { filename: [Face, …], … }"""
        if not os.path.isdir(folder):
            raise ValueError(f"{folder} folder not found")
        
        if not os.listdir(folder):
            raise ValueError(f"{folder} folder is empty")       

        self.results.clear()
        results: dict[str, list[Face]] = {}
        
        image_files = [f for f in sorted(os.listdir(folder)) if f.lower().endswith((".jpg", ".jpeg", ".png"))]

        for fname in tqdm(image_files, desc="Detecting faces", unit="frame"):
            path = os.path.join(folder, fname)
            frame = cv2.imread(path)
            if frame is None:
                continue

            detected = self.detect(frame)
            results[fname] = detected
            self.results[fname] = detected
            
            # Optional GUI log
            if progress_fn:
                progress_fn()   
        
        return results 

    def draw_boundary(self,
                        folder: str = "frames",
                        box_color: tuple[int,int,int] = (0, 255, 0),
                        text_color: tuple[int,int,int] = (0, 0, 255),
                        box_thickness: int = 2,
                        font_scale: float = 0.5,
                        text_thickness: int = 1,
                        font: int = cv2.FONT_HERSHEY_SIMPLEX):
        """
        For each image in `folder`, detect faces, draw a rectangle around each,
        and put "index:confidence" at the bottom-left of the box.
        Overwrites the originals in-place.
        """
        detections = self.results

        for fname, faces in detections.items():
            path = os.path.join(folder, fname)
            frame = cv2.imread(path)
            if frame is None:
                continue

            h_frame, w_frame = frame.shape[:2]
            for face in faces:
                x, y, w, h = face.bbox

                # 1) draw bounding box
                cv2.rectangle(frame, (x, y), (x + w, y + h), box_color, box_thickness)

                # 2) prepare label text
                label = f"face{face.index}"
                (text_w, text_h), baseline = cv2.getTextSize(label, font, font_scale, text_thickness)

                # 3) compute text origin at bottom-left of box
                text_x = x
                text_y = y + h + text_h + 4

                # if text would go off-image, draw it inside the box instead
                if text_y > h_frame:
                    text_y = y + h - 4

                # 4) put the text
                cv2.putText(
                    frame,
                    label,
                    (text_x, text_y),
                    font,
                    font_scale,
                    text_color,
                    text_thickness,
                    cv2.LINE_AA
                )

            # overwrite the original frame
            cv2.imwrite(path, frame) 