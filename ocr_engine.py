"""
ocr_engine.py - Screenshot capture and Windows OCR text recognition
Uses built-in Windows OCR (no external dependencies needed)
All processing is done in memory — no files saved to disk.
"""

import asyncio
import io
from PIL import ImageGrab
import winrt.windows.media.ocr as win_ocr
import winrt.windows.graphics.imaging as win_imaging
import winrt.windows.storage.streams as win_streams
from color_detector import filter_text_by_color


# Stores the last recognized text — used by auto-translate to detect changes
_last_ocr_text: str = ""


async def capture_and_recognize(x: int, y: int, width: int, height: int, color_filters: list = None) -> str:
    """
    Captures a screenshot of the specified area and runs Windows OCR on it.
    Returns recognized text or empty string on failure.
    All processing is done in RAM — nothing written to disk.

    Args:
        color_filters: List of hex color strings to filter by (e.g. ["#FF0000", "#0000FF"])
                      Only text in these colors will be recognized.
    """
    try:
        # Capture region into memory only
        screenshot = ImageGrab.grab(bbox=(x, y, x + width, y + height))
        if screenshot is None:
            return ""

        # Apply color filter if specified
        if color_filters:
            screenshot = filter_text_by_color(screenshot, color_filters, tolerance=40)

        # Convert to BMP bytes in memory
        img_bytes = io.BytesIO()
        screenshot.save(img_bytes, format="BMP")
        img_bytes.seek(0)
        raw_bytes = img_bytes.read()
        del screenshot  # free memory immediately

        # Load into Windows Runtime stream
        mem_stream = win_streams.InMemoryRandomAccessStream()
        writer = win_streams.DataWriter(mem_stream)
        writer.write_bytes(list(raw_bytes))
        await writer.store_async()
        await writer.flush_async()
        mem_stream.seek(0)

        decoder = await win_imaging.BitmapDecoder.create_async(mem_stream)
        bitmap = await decoder.get_software_bitmap_async()

        result = await _try_ocr_auto(bitmap)
        return result

    except Exception as e:
        print(f"[OCR Error] {e}")
        return ""


async def _try_ocr_auto(bitmap) -> str:
    """
    Try OCR with all available Windows language packs.
    Returns the longest (most complete) recognized text.
    """
    results = []
    available_languages = win_ocr.OcrEngine.get_available_recognizer_languages()

    if not available_languages:
        return ""

    for lang in available_languages:
        try:
            engine = win_ocr.OcrEngine.try_create_from_language(lang)
            if engine:
                result = await engine.recognize_async(bitmap)
                text = result.text.strip()
                if text:
                    results.append(text)
        except Exception:
            continue

    if not results:
        return ""

    return max(results, key=len)


def capture_and_recognize_sync(x: int, y: int, width: int, height: int, color_filters: list = None) -> str:
    """
    Synchronous wrapper — runs async OCR in a new event loop.
    Safe to call from QThread.
    """
    try:
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(capture_and_recognize(x, y, width, height, color_filters))
        loop.close()
        return result
    except Exception as e:
        print(f"[OCR Sync Error] {e}")
        return ""


def capture_if_changed(x: int, y: int, width: int, height: int, color_filters: list = None) -> tuple[bool, str]:
    """
    For auto-translate: runs OCR and returns (changed, text).
    Returns (True, text) if text differs from last capture.
    Returns (False, "") if text is the same (no need to translate again).
    """
    global _last_ocr_text
    text = capture_and_recognize_sync(x, y, width, height, color_filters)
    if not text:
        return False, ""
    if text == _last_ocr_text:
        return False, ""
    _last_ocr_text = text
    return True, text


def reset_last_text():
    """Reset stored OCR text — call when overlay is moved/resized"""
    global _last_ocr_text
    _last_ocr_text = ""
