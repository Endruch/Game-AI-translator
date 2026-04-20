from PIL import Image, ImageGrab
import numpy as np


def filter_text_by_color(image, allowed_colors: list, tolerance: int = 30):
    if not allowed_colors:
        return image

    try:
        img_array = np.array(image.convert('RGB'), dtype=np.float32)
        height, width = img_array.shape[:2]

        allowed_rgb = []
        for hex_color in allowed_colors:
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            allowed_rgb.append([r, g, b])

        allowed_rgb = np.array(allowed_rgb, dtype=np.float32)

        mask = np.zeros((height, width), dtype=bool)
        for color in allowed_rgb:
            distances = np.sqrt(np.sum((img_array - color) ** 2, axis=2))
            mask |= distances < tolerance

        img_array[~mask] = [255, 255, 255]

        return Image.fromarray(img_array.astype(np.uint8))

    except Exception:
        return image
