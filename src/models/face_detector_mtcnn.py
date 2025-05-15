# src/models/face_detector_mtcnn.py

import os
import torch
import cv2
from PIL import Image
from facenet_pytorch import MTCNN
from .face import Face
import numpy as np

class FaceDetectorMTCNN:
    """
    Uses facenet-pytorch's MTCNN for face detection.
    API matches your other detectors:
      - detect(frame: np.ndarray) -> list[Face]
      - detect_in_folder(folder: str) -> dict[str, list[Face]]
    """

    def __init__(self,
                 device: str | torch.device = None,
                 thresholds: tuple[float, float, float] = (0.7, 0.8, 0.8)):
        # choose GPU if available
        self.device = device or (torch.device('cuda:0') if torch.cuda.is_available() else torch.device('cpu'))
        # keep_all=True so we get all faces per frame
        self.mtcnn = MTCNN(
            keep_all=True,
            min_face_size= 20,
            device=self.device,
            thresholds=thresholds,
        )

    def detect(self, frame: np.ndarray) -> list[Face]:
        """
        Run MTCNN on a single BGR frame (H×W×3 numpy array).
        Returns a list of Face(index, bbox, image, confidence).
        """
        # convert BGR->RGB, to PIL
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)

        # boxes: Nx4 array of [x1, y1, x2, y2], probs: N-array of confidences
        boxes, probs = self.mtcnn.detect(img)

        faces: list[Face] = []
        if boxes is None or probs is None:
            return faces

        h, w = frame.shape[:2]
        for i, (box, prob) in enumerate(zip(boxes, probs)):
            # clamp & build integer bbox (x, y, width, height)
            x1, y1, x2, y2 = box
            x1, y1 = max(0, int(x1)), max(0, int(y1))
            x2, y2 = min(w-1, int(x2)), min(h-1, int(y2))
            bbox = (x1, y1, x2 - x1, y2 - y1)

            # confidence is already in [0,1]
            confidence = float(prob)
            faces.append(Face.from_bbox(i, frame, bbox, confidence))

        return faces

    def detect_in_folder(self, folder: str = "frames") -> dict[str, list[Face]]:
        """Walks through all .jpg/.png in `folder`, runs detect(), returns: { filename: [Face, …], … }"""
        if not os.path.isdir(folder):
            raise ValueError(f"{folder} folder not found")
        
        if not os.listdir(folder):
            raise ValueError(f"{folder} folder is empty")       

        results: dict[str, list[Face]] = {}
        for fname in sorted(os.listdir(folder)):
            if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
                continue

            path = os.path.join(folder, fname)
            frame = cv2.imread(path)
            if frame is None:
                continue

            results[fname] = self.detect(frame)
            print(f"Detected {len(results[fname])} face(s) in {fname}")     # this line is for debugging
        
        return results

    def draw_boundary(self,
                        folder: str = "frames",
                        box_color: tuple[int,int,int] = (0, 255, 0),
                        text_color: tuple[int,int,int] = (255, 0, 0),
                        box_thickness: int = 2,
                        font_scale: float = 0.5,
                        text_thickness: int = 1,
                        font: int = cv2.FONT_HERSHEY_SIMPLEX):
        """
        For each image in `folder`, detect faces, draw a rectangle around each,
        and put "index:confidence" at the bottom-left of the box.
        Overwrites the originals in-place.
        """
        detections = self.detect_in_folder(folder)

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