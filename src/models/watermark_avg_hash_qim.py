# src/models/watermark_avg_hash_qim.py

import os
import numpy as np
import cv2
from .face import Face

class WatermarkAvgHashQim:
    HEADER = "WMARK"
    STEP = 10.0   # quantization step for QIM

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
        """
        Embed HEADER bits into the ROI by modifying one DCT coefficient per 8×8 block.
        Only the HEADER string is embedded (no extra payload).
        """
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY).astype(np.float32)
        bits = self._string_to_bits(self.HEADER)
        h, w = gray.shape
        H, W = h - (h % 8), w - (w % 8)
        idx = 0

        for y in range(0, H, 8):
            for x in range(0, W, 8):
                if idx >= len(bits):
                    break
                block = gray[y:y+8, x:x+8]
                dct = cv2.dct(block)
                b = bits[idx]
                coeff = dct[4, 1]
                q = np.round(coeff / self.STEP)
                if (q % 2) != b:
                    q += (b - (q % 2))
                dct[4, 1] = q * self.STEP
                gray[y:y+8, x:x+8] = cv2.idct(dct)
                idx += 1
            if idx >= len(bits):
                break

        watermarked = cv2.cvtColor(
            np.clip(gray, 0, 255).astype(np.uint8),
            cv2.COLOR_GRAY2BGR
        )
        return watermarked

    def extract(self, roi: np.ndarray) -> str:
        """
        Read back the HEADER bits from the ROI by examining the same DCT coefficient.
        Returns the extracted string (ideally 'WMARK').
        """
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY).astype(np.float32)
        bits = []
        h, w = gray.shape
        H, W = h - (h % 8), w - (w % 8)
        needed = len(self._string_to_bits(self.HEADER))
        idx = 0

        for y in range(0, H, 8):
            for x in range(0, W, 8):
                if idx >= needed:
                    break
                dct = cv2.dct(gray[y:y+8, x:x+8])
                q = np.round(dct[4, 1] / self.STEP)
                bits.append(int(q % 2))
                idx += 1
            if idx >= needed:
                break

        return self._bits_to_string(bits)

    def verify(self, roi: np.ndarray) -> bool:
        """True if the extracted HEADER matches exactly."""
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