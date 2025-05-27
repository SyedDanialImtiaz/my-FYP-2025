import numpy as np

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
        bits = self._string_to_bits(self.HEADER)
        flat = roi.flatten()
        if len(bits) > flat.size:
            raise ValueError("ROI too small for LSB header")
        # flip LSB of each pixel to match header bit
        for idx, bit in enumerate(bits):
            flat[idx] = (flat[idx] & ~1) | bit
        return flat.reshape(roi.shape)

    def extract(self, roi: np.ndarray) -> str:
        flat = roi.flatten()
        n = len(self._string_to_bits(self.HEADER))
        bits = [int(flat[i] & 1) for i in range(n)]
        return self._bits_to_string(bits)

    def verify(self, roi: np.ndarray) -> bool:
        return self.extract(roi) == self.HEADER
