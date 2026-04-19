"""
color_detector.py - Detects dominant text colors in screenshot
Used for filtering chat messages by color
"""

from PIL import Image, ImageGrab
from collections import Counter
import colorsys


def rgb_to_hex(rgb):
    """Convert RGB tuple to hex color string"""
    return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))


def get_dominant_colors(x: int, y: int, width: int, height: int, max_colors: int = 10) -> list:
    """
    Captures screenshot and detects dominant text colors.
    Returns list of hex color strings sorted by frequency.
    """
    try:
        # Capture region
        screenshot = ImageGrab.grab(bbox=(x, y, x + width, y + height))
        if screenshot is None:
            return []

        # Convert to RGB
        img = screenshot.convert('RGB')
        pixels = list(img.getdata())

        # Filter to get only text colors (bright, saturated colors)
        # Text in games is usually bright and colorful
        filtered_pixels = []
        for pixel in pixels:
            r, g, b = pixel
            brightness = (r + g + b) / 3

            # Text colors are usually medium-bright to very bright (80-255)
            # Skip very dark colors (backgrounds, shadows)
            if brightness < 80:
                continue

            # Skip nearly white/gray colors (often background or UI elements)
            if brightness > 240:
                max_val = max(r, g, b)
                min_val = min(r, g, b)
                # If it's too close to white (all values high and similar), skip it
                if max_val - min_val < 30:
                    continue

            # Check color saturation - text usually has strong color
            max_val = max(r, g, b)
            min_val = min(r, g, b)
            saturation = (max_val - min_val) / max_val if max_val > 0 else 0

            # Keep colors with decent saturation (colorful text)
            # Or very bright colors even with lower saturation (white/yellow text)
            if saturation > 0.3 or brightness > 200:
                filtered_pixels.append(pixel)

        if not filtered_pixels:
            return []

        # Count color frequency
        color_counts = Counter(filtered_pixels)

        # Get most common colors
        most_common = color_counts.most_common(max_colors)

        # Group similar colors together
        grouped_colors = []
        for color, count in most_common:
            # Check if this color is similar to any already grouped color
            is_similar = False
            for grouped_color, grouped_count in grouped_colors:
                if _colors_similar(color, grouped_color, threshold=30):
                    # Merge counts
                    idx = grouped_colors.index((grouped_color, grouped_count))
                    grouped_colors[idx] = (grouped_color, grouped_count + count)
                    is_similar = True
                    break

            if not is_similar:
                grouped_colors.append((color, count))

        # Sort by frequency again after grouping
        grouped_colors.sort(key=lambda x: x[1], reverse=True)

        # Convert to hex and return
        result = [rgb_to_hex(color) for color, count in grouped_colors[:max_colors]]

        return result

    except Exception as e:
        print(f"[Color Detection] {e}")
        return []


def _colors_similar(color1, color2, threshold=30):
    """Check if two RGB colors are similar within threshold"""
    r1, g1, b1 = color1
    r2, g2, b2 = color2

    distance = ((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2) ** 0.5
    return distance < threshold


def filter_text_by_color(image, allowed_colors: list, tolerance: int = 30):
    """
    Creates a mask that only keeps pixels matching allowed colors.
    Returns modified PIL Image.
    """
    if not allowed_colors:
        return image

    try:
        img = image.convert('RGB')
        pixels = img.load()
        width, height = img.size

        # Convert hex colors to RGB
        allowed_rgb = []
        for hex_color in allowed_colors:
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            allowed_rgb.append((r, g, b))

        # Create new image
        for y_coord in range(height):
            for x_coord in range(width):
                pixel = pixels[x_coord, y_coord]

                # Check if pixel color matches any allowed color
                matches = False
                for allowed_color in allowed_rgb:
                    if _colors_similar(pixel, allowed_color, tolerance):
                        matches = True
                        break

                # If doesn't match, make it white (background)
                if not matches:
                    pixels[x_coord, y_coord] = (255, 255, 255)

        return img

    except Exception as e:
        print(f"[Color Filter] {e}")
        return image
