import os
import cv2
import numpy as np
from models import Face

class WatermarkLsbFragile:
    HEADER = "WMARK"   # 5-byte magic header

    @staticmethod
    def _string_to_bits(s: str) -> list[int]:
        bits = []
        for byte in s.encode('utf-8'):
            for i in range(8):
                bits.append((byte >> (7 - i)) & 1)
        return bits

    @staticmethod
    def _bits_to_string(bits: list[int]) -> str:
        chars = []
        for i in range(0, len(bits), 8):
            byte = 0
            for j in range(8):
                byte = (byte << 1) | bits[i + j]
            chars.append(byte)
        return bytes(chars).decode('utf-8', errors='ignore')

    def embed(self, roi: np.ndarray) -> np.ndarray:
        """Embed HEADER bits into the LSB of each byte in this ROI."""
        bits = self._string_to_bits(self.HEADER)
        # print(f"Embedding {len(bits)} bits into ROI of shape {roi.shape}") # debug
        flat = roi.flatten()
        if len(bits) > flat.size:
            raise ValueError("ROI too small for LSB header")
        for idx, bit in enumerate(bits):
            flat[idx] = (flat[idx] & 0xFE) | bit
        return flat.reshape(roi.shape)

    def extract(self, roi: np.ndarray) -> str:
        """Extract the exact number of HEADER bits from the LSBs and decode."""
        flat = roi.flatten()
        n = len(self._string_to_bits(self.HEADER))
        bits = [int(flat[i] & 1) for i in range(n)]
        return self._bits_to_string(bits)

    def verify(self, roi: np.ndarray) -> bool:
        """True if the extracted header matches exactly."""
        # print(f"Verifying ROI of shape {roi.shape}")  # debug
        return self.extract(roi) == self.HEADER

    def embed_in_folder(self,
                        folder: str,
                        face_map: dict[str, list[Face]],
                        progress_fn=None
                       ) -> dict[str, list[Face]]:
        """
        Uses the provided face_map (cached from controller) to embed HEADER into each face ROI.
        Overwrites frames in-place.
        """
        files = list(face_map.keys())
        for idx, fname in enumerate(files, start=1):
            path = os.path.join(folder, fname)
            frame = cv2.imread(path)
            if frame is None:
                if progress_fn:
                    progress_fn(idx)
                continue

            for face in face_map[fname]:
                x, y, w, h = face.bbox
                roi = frame[y:y+h, x:x+w]
                if roi is None or roi.size == 0:
                    continue
                try:
                    wm_frame = self.embed(roi)
                    frame[y:y+h, x:x+w] = wm_frame
                except Exception:
                    pass
            cv2.imwrite(path, frame)
            
            if progress_fn:
                progress_fn(idx)

    def verify_in_folder(self,
                         folder: str,
                         face_map: dict[str, list[Face]],
                         progress_fn=None
                        ) -> bool:
        """
        Uses the provided face_map to check for any valid HEADER in each face ROI.
        Returns True as soon as one ROI verifies; else False.
        """
        files = list(face_map.keys())
        for idx, fname in enumerate(files, start=1):
            path = os.path.join(folder, fname)
            frame = cv2.imread(path)
            if frame is None:
                if progress_fn:
                    progress_fn(idx)
                continue
            
            for face in face_map[fname]:
                x, y, w, h = face.bbox
                roi = frame[y:y+h, x:x+w]
                if roi is None or roi.size == 0:
                    continue
                try:
                    if self.verify(roi):
                        print(f"Valid header found in {fname} at face index {face.index}.")
                        return True
                except Exception:
                    continue

            if progress_fn:
                progress_fn(idx)
        print("No valid header found in any face.")
        return False
