import asyncio
import io
from threading import Lock
from PIL import ImageGrab
import winrt.windows.media.ocr as win_ocr
import winrt.windows.graphics.imaging as win_imaging
import winrt.windows.storage.streams as win_streams
from color_detector import filter_text_by_color


class OCRCache:
    def __init__(self):
        self._last_text = ""
        self._lock = Lock()

    def get_last_text(self):
        with self._lock:
            return self._last_text

    def set_last_text(self, text):
        with self._lock:
            self._last_text = text

    def reset(self):
        with self._lock:
            self._last_text = ""


_cache = OCRCache()


async def _capture_and_recognize(x: int, y: int, width: int, height: int, color_filters: list = None) -> str:
    try:
        screenshot = ImageGrab.grab(bbox=(x, y, x + width, y + height))
        if screenshot is None:
            return ""

        if color_filters:
            screenshot = filter_text_by_color(screenshot, color_filters, tolerance=40)

        img_bytes = io.BytesIO()
        screenshot.save(img_bytes, format="BMP")
        img_bytes.seek(0)
        raw_bytes = img_bytes.read()

        mem_stream = win_streams.InMemoryRandomAccessStream()
        writer = win_streams.DataWriter(mem_stream)
        writer.write_bytes(list(raw_bytes))
        await writer.store_async()
        await writer.flush_async()
        mem_stream.seek(0)

        decoder = await win_imaging.BitmapDecoder.create_async(mem_stream)
        bitmap = await decoder.get_software_bitmap_async()

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

        return max(results, key=len) if results else ""

    except Exception:
        return ""


def capture_and_recognize_sync(x: int, y: int, width: int, height: int, color_filters: list = None) -> str:
    try:
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(_capture_and_recognize(x, y, width, height, color_filters))
        loop.close()
        return result
    except Exception:
        return ""


def capture_if_changed(x: int, y: int, width: int, height: int, color_filters: list = None) -> tuple[bool, str]:
    text = capture_and_recognize_sync(x, y, width, height, color_filters)
    if not text:
        return False, ""

    last_text = _cache.get_last_text()
    if text == last_text:
        return False, ""

    _cache.set_last_text(text)
    return True, text


def reset_last_text():
    _cache.reset()
