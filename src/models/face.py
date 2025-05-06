from dataclasses import dataclass
import numpy as np

@dataclass
class Face:
    index: int
    bbox: tuple   # (x, y, w, h)
    image: np.ndarray

    @classmethod
    def from_bbox(cls, index: int, frame: np.ndarray, bbox: tuple):
        x, y, w, h = bbox
        face_img = frame[y:y+h, x:x+w]
        return cls(index=index, bbox=bbox, image=face_img)
