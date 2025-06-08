# src/models/watermark_block_checksum_dwt.py

import os
import numpy as np
import pywt
import cv2
from .face import Face

class WatermarkBlockChecksumDwt:
    HEADER = "WMARK"

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
        Embed HEADER bits into the LH subband of a 1-level Haar DWT of the grayscale ROI,
        using LSB on each coefficient to encode one bit.
        """
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        bits = self._string_to_bits(self.HEADER)

        LL, (LH, HL, HH) = pywt.dwt2(gray, 'haar')
        flat = LH.flatten()
        if len(bits) > flat.size:
            raise ValueError("ROI too small for DWT header")

        for i, bit in enumerate(bits):
            coeff = flat[i]
            val = int(np.round(coeff))
            val = (val & ~1) | bit       # clear LSB, set to bit
            flat[i] = val
        LH_wm = flat.reshape(LH.shape)

        watermarked = pywt.idwt2((LL, (LH_wm, HL, HH)), 'haar')
        wm_uint8 = np.clip(watermarked, 0, 255).astype(np.uint8)
        return cv2.cvtColor(wm_uint8, cv2.COLOR_GRAY2BGR)

    def extract(self, roi: np.ndarray) -> str:
        """
        Extract HEADER bits from the LH subband LSBs, reconstruct the string.
        """
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        LL, (LH, HL, HH) = pywt.dwt2(gray, 'haar')
        flat = LH.flatten()
        n = len(self._string_to_bits(self.HEADER))
        bits = [int(int(np.round(flat[i])) & 1) for i in range(n)]
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