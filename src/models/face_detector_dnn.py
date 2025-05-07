import os
import cv2
import numpy as np
from models import Face

class FaceDetector:
    """
    A faster/more accurate face detector using OpenCV's DNN (ResNet SSD) model.
    """
    def __init__(self, proto_path: str = None, model_path: str = None, conf_threshold: float = 0.5):
        # defaults assume you’ve placed both files alongside this script:
        base = os.path.dirname(__file__)
        self.proto_path = proto_path or os.path.join(base, "deploy.prototxt")
        self.model_path = model_path or os.path.join(base, "res10_300x300_ssd_iter_140000.caffemodel")
        self.conf_threshold = conf_threshold

        # load network
        self.net = cv2.dnn.readNetFromCaffe(self.proto_path, self.model_path)

    def detect(self, frame: np.ndarray) -> list[Face]:
        h, w = frame.shape[:2]
        # build a 300x300 blob from the frame
        blob = cv2.dnn.blobFromImage(
            cv2.resize(frame, (300, 300)),
            1.0,
            (300, 300),
            (104.0, 177.0, 123.0),
            swapRB=False,
            crop=False
        )
        self.net.setInput(blob)
        detections = self.net.forward()

        faces: list[Face] = []
        for i in range(detections.shape[2]):
            confidence = float(detections[0, 0, i, 2])
            if confidence < self.conf_threshold:
                continue

            # compute the (x, y)-coordinates of the bounding box
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype(int)

            # clamp to frame size
            startX, startY = max(0, startX), max(0, startY)
            endX, endY     = min(w - 1, endX), min(h - 1, endY)
            bbox = (startX, startY, endX - startX, endY - startY)

            faces.append(Face.from_bbox(i, frame, bbox))

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

        return results
