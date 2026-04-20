"""
OCR Engine - Windows OCR wrapper with caching and fuzzy matching
"""

import asyncio
import io
import logging
import difflib
from threading import Lock
from PIL import ImageGrab
import winrt.windows.media.ocr as win_ocr
import winrt.windows.graphics.imaging as win_imaging
import winrt.windows.storage.streams as win_streams
from color_detector import filter_text_by_color

# Configure logging
logger = logging.getLogger(__name__)


class OCRCache:
    """Thread-safe OCR result cache with fuzzy matching"""

    def __init__(self):
        self._last_text = ""
        self._lock = Lock()

    def get_last_text(self) -> str:
        """Get last recognized text"""
        with self._lock:
            return self._last_text

    def set_last_text(self, text: str):
        """Store recognized text"""
        with self._lock:
            self._last_text = text

    def reset(self):
        """Clear cache"""
        with self._lock:
            self._last_text = ""

    def is_similar(self, new_text: str, threshold: float = 0.90) -> bool:
        """
        Check if new text is similar to cached text using fuzzy matching

        Args:
            new_text: New text to compare
            threshold: Similarity ratio (0.0-1.0), default 0.90 = 90% similar

        Returns:
            True if texts are similar enough
        """
        with self._lock:
            if not self._last_text or not new_text:
                return False

            # Use SequenceMatcher for fuzzy comparison
            ratio = difflib.SequenceMatcher(None, self._last_text, new_text).ratio()
            logger.debug(f"Text similarity: {ratio:.2%} (threshold: {threshold:.2%})")

            return ratio >= threshold


_cache = OCRCache()


async def _capture_and_recognize(x: int, y: int, width: int, height: int,
                                  color_filters: list = None) -> str:
    """
    Capture screen region and recognize text using Windows OCR

    Args:
        x, y: Top-left corner coordinates
        width, height: Region dimensions
        color_filters: List of hex color strings to filter (e.g., ["#FFFFFF", "#FFD700"])

    Returns:
        Recognized text string
    """
    try:
        # Capture screenshot
        logger.debug(f"Capturing region: ({x}, {y}, {width}, {height})")
        screenshot = ImageGrab.grab(bbox=(x, y, x + width, y + height))

        if screenshot is None:
            logger.warning("Screenshot capture returned None")
            return ""

        # Apply color filtering if specified
        if color_filters:
            logger.debug(f"Applying color filters: {len(color_filters)} colors")
            screenshot = filter_text_by_color(screenshot, color_filters, tolerance=40)

        # Convert to BMP format for Windows OCR
        img_bytes = io.BytesIO()
        screenshot.save(img_bytes, format="BMP")
        img_bytes.seek(0)
        raw_bytes = img_bytes.read()

        # Create InMemoryRandomAccessStream
        mem_stream = win_streams.InMemoryRandomAccessStream()
        writer = win_streams.DataWriter(mem_stream)
        writer.write_bytes(list(raw_bytes))
        await writer.store_async()
        await writer.flush_async()
        mem_stream.seek(0)

        # Decode bitmap
        decoder = await win_imaging.BitmapDecoder.create_async(mem_stream)
        bitmap = await decoder.get_software_bitmap_async()

        # Try OCR with all available languages
        results = []
        available_languages = win_ocr.OcrEngine.get_available_recognizer_languages()

        if not available_languages:
            logger.error("No OCR languages available on this system")
            return ""

        logger.debug(f"Available OCR languages: {len(available_languages)}")

        for lang in available_languages:
            try:
                engine = win_ocr.OcrEngine.try_create_from_language(lang)
                if engine:
                    result = await engine.recognize_async(bitmap)
                    text = result.text.strip()
                    if text:
                        results.append(text)
                        logger.debug(f"OCR result from {lang.display_name}: {len(text)} chars")
            except Exception as e:
                logger.warning(f"OCR failed for language {lang.display_name}: {e}")
                continue

        # Return longest result (usually most accurate)
        if results:
            best_result = max(results, key=len)
            logger.info(f"OCR success: {len(best_result)} characters recognized")
            return best_result
        else:
            logger.warning("No text recognized by OCR")
            return ""

    except Exception as e:
        logger.error(f"OCR error: {e}", exc_info=True)
        return ""


def capture_and_recognize_sync(x: int, y: int, width: int, height: int,
                                color_filters: list = None) -> str:
    """
    Synchronous wrapper for OCR capture

    Args:
        x, y: Top-left corner coordinates
        width, height: Region dimensions
        color_filters: List of hex color strings to filter

    Returns:
        Recognized text string
    """
    try:
        return asyncio.run(_capture_and_recognize(x, y, width, height, color_filters))
    except Exception as e:
        logger.error(f"Sync OCR wrapper error: {e}", exc_info=True)
        return ""


def capture_if_changed(x: int, y: int, width: int, height: int,
                       color_filters: list = None, similarity_threshold: float = 0.90) -> tuple[bool, str]:
    """
    Capture and check if text has changed since last capture (with fuzzy matching)

    Args:
        x, y: Top-left corner coordinates
        width, height: Region dimensions
        color_filters: List of hex color strings to filter
        similarity_threshold: How similar text must be to be considered "unchanged" (0.0-1.0)

    Returns:
        Tuple of (changed: bool, text: str)
        - changed: True if text is different from cached version
        - text: Recognized text (empty string if no change or no text found)
    """
    text = capture_and_recognize_sync(x, y, width, height, color_filters)

    if not text:
        logger.debug("No text captured, treating as no change")
        return False, ""

    # Check if text is similar to last captured text
    if _cache.is_similar(text, threshold=similarity_threshold):
        logger.debug("Text unchanged (fuzzy match)")
        return False, ""

    # Text has changed significantly
    _cache.set_last_text(text)
    logger.info("Text changed detected")
    return True, text


def reset_last_text():
    """Reset the OCR cache (call when overlay is moved)"""
    _cache.reset()
    logger.debug("OCR cache reset")
