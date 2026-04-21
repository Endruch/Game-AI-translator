import asyncio
import io
import difflib
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

    def get_last_text(self) -> str:
        with self._lock:
            return self._last_text

    def set_last_text(self, text: str):
        with self._lock:
            self._last_text = text

    def reset(self):
        with self._lock:
            self._last_text = ""

    def is_similar(self, new_text: str, threshold: float = 0.90) -> bool:
        with self._lock:
            if not self._last_text or not new_text:
                return False

            ratio = difflib.SequenceMatcher(None, self._last_text, new_text).ratio()

            return ratio >= threshold


_cache = OCRCache()


async def _capture_and_recognize(x: int, y: int, width: int, height: int,
                                  color_filters: list = None, use_color_filters: bool = False) -> str:
    try:
        screenshot = ImageGrab.grab(bbox=(x, y, x + width, y + height))

        if screenshot is None:
            return ""

        if use_color_filters and color_filters:
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

        try:
            available_languages = win_ocr.OcrEngine.get_available_recognizer_languages()
        except Exception:
            return ""

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

        if results:
            best_result = max(results, key=len)
            return best_result
        else:
            return ""

    except Exception:
        return ""


def capture_and_recognize_sync(x: int, y: int, width: int, height: int,
                                color_filters: list = None, use_color_filters: bool = False) -> str:
    try:
        return asyncio.run(_capture_and_recognize(x, y, width, height, color_filters, use_color_filters))
    except Exception:
        return ""


def capture_if_changed(x: int, y: int, width: int, height: int,
                       color_filters: list = None, use_color_filters: bool = False, similarity_threshold: float = 0.90) -> tuple[bool, str]:
    text = capture_and_recognize_sync(x, y, width, height, color_filters, use_color_filters)

    if not text:
        return False, ""

    if _cache.is_similar(text, threshold=similarity_threshold):
        return False, ""

    _cache.set_last_text(text)
    return True, text


def reset_last_text():
    _cache.reset()
