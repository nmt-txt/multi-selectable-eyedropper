from PIL import Image
import numpy as np

class colorCircleSquare:

    def __init__(self, path):
        img = Image.open(path).convert("HSV")
        self.original_np = np.array(img)
        self.width = img.width
        self.height = img.height

    def get_shifted_hue(self, shift):
        copied = self.original_np.copy()
        copied[..., 0] = (copied[..., 0].astype(np.uint16) + shift) % 255

        img_shifted = Image.fromarray(copied, mode="HSV").convert("RGBA")
        return np.array(img_shifted, dtype=np.float32) / 255.0