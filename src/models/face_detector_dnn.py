import os
import cv2
import numpy as np
from tqdm import tqdm
from models import Face

class FaceDetectorDNN:
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
        
        self.results: dict[str, list[Face]] = {}

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

            faces.append(Face.from_bbox(i, frame, bbox, confidence))

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
