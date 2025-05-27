import numpy as np
import cv2

class WatermarkAvgHashQim:
    HEADER = "WMARK"
    STEP = 10.0        # quantization step

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
        # convert ROI to grayscale float32
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY).astype(np.float32)
        bits = self._string_to_bits(self.HEADER)
        h, w = gray.shape
        H, W = h - (h % 8), w - (w % 8)
        idx = 0

        # for each 8×8 block, embed one header bit in coefficient (4,1)
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

        # back to BGR uint8
        watermarked = cv2.cvtColor(
            np.clip(gray, 0, 255).astype(np.uint8),
            cv2.COLOR_GRAY2BGR
        )
        return watermarked

    def extract(self, roi: np.ndarray) -> str:
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
        return self.extract(roi) == self.HEADER
