"""
Color Detector - Filter images by specific text colors for better OCR
"""

import logging
from PIL import Image
import numpy as np

# Configure logging
logger = logging.getLogger(__name__)


def filter_text_by_color(image: Image.Image, allowed_colors: list,
                          tolerance: int = 30) -> Image.Image:
    """
    Filter image to keep only pixels matching specified colors

    This improves OCR accuracy by isolating text of specific colors
    (e.g., white chat text, yellow player names, etc.)

    Args:
        image: PIL Image to filter
        allowed_colors: List of hex color strings (e.g., ["#FFFFFF", "#FFD700"])
        tolerance: Color matching tolerance (0-255), higher = more lenient

    Returns:
        Filtered PIL Image with non-matching pixels turned white
    """
    if not allowed_colors:
        logger.debug("No color filters specified, returning original image")
        return image

    try:
        logger.debug(f"Filtering image with {len(allowed_colors)} colors, tolerance={tolerance}")

        # Convert to RGB array
        img_array = np.array(image.convert('RGB'), dtype=np.float32)
        height, width = img_array.shape[:2]

        # Parse hex colors to RGB
        allowed_rgb = []
        for hex_color in allowed_colors:
            try:
                hex_color = hex_color.lstrip('#')
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                allowed_rgb.append([r, g, b])
                logger.debug(f"Color filter: {hex_color} -> RGB({r}, {g}, {b})")
            except (ValueError, IndexError) as e:
                logger.warning(f"Invalid hex color '{hex_color}': {e}")
                continue

        if not allowed_rgb:
            logger.warning("No valid colors after parsing, returning original image")
            return image

        allowed_rgb = np.array(allowed_rgb, dtype=np.float32)

        # Create mask for pixels matching any allowed color
        mask = np.zeros((height, width), dtype=bool)

        for color in allowed_rgb:
            # Calculate Euclidean distance in RGB space
            distances = np.sqrt(np.sum((img_array - color) ** 2, axis=2))
            mask |= distances < tolerance

        # Turn non-matching pixels white (better for OCR)
        img_array[~mask] = [255, 255, 255]

        matching_pixels = np.sum(mask)
        total_pixels = height * width
        match_percentage = (matching_pixels / total_pixels) * 100

        logger.info(f"Color filter: {matching_pixels}/{total_pixels} pixels matched ({match_percentage:.1f}%)")

        return Image.fromarray(img_array.astype(np.uint8))

    except Exception as e:
        logger.error(f"Color filtering failed: {e}", exc_info=True)
        logger.warning("Returning original image due to filter error")
        return image
