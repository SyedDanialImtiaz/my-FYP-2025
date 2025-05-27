import numpy as np
import pywt
import cv2

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
        # grayscale ROI
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        bits = self._string_to_bits(self.HEADER)

        # single-level Haar DWT
        LL, (LH, HL, HH) = pywt.dwt2(gray, 'haar')
        flat = LH.flatten()
        if len(bits) > flat.size:
            raise ValueError("ROI too small for DWT header")
        # LSB on LH coefficients
        for i, bit in enumerate(bits):
            coeff = flat[i]
            # convert to int for bit ops
            val = int(np.round(coeff))
            val = (val & ~1) | bit
            flat[i] = val
        LH_wm = flat.reshape(LH.shape)

        # inverse DWT
        watermarked = pywt.idwt2((LL, (LH_wm, HL, HH)), 'haar')
        wm_uint8 = np.clip(watermarked, 0, 255).astype(np.uint8)
        return cv2.cvtColor(wm_uint8, cv2.COLOR_GRAY2BGR)

    def extract(self, roi: np.ndarray) -> str:
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        LL, (LH, HL, HH) = pywt.dwt2(gray, 'haar')
        flat = LH.flatten()
        n = len(self._string_to_bits(self.HEADER))
        bits = [int(int(np.round(flat[i])) & 1) for i in range(n)]
        return self._bits_to_string(bits)

    def verify(self, roi: np.ndarray) -> bool:
        return self.extract(roi) == self.HEADER
