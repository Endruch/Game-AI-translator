import io
import difflib
import base64
from threading import Lock
from PIL import ImageGrab
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


def _capture_screenshot(x: int, y: int, width: int, height: int,
                        color_filters: list = None, use_color_filters: bool = False) -> str:
    try:
        screenshot = ImageGrab.grab(bbox=(x, y, x + width, y + height))

        if screenshot is None:
            return ""

        if use_color_filters and color_filters:
            screenshot = filter_text_by_color(screenshot, color_filters, tolerance=60)

        img_bytes = io.BytesIO()
        screenshot.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        return base64.standard_b64encode(img_bytes.read()).decode('utf-8')

    except Exception:
        return ""


def capture_screenshot_base64(x: int, y: int, width: int, height: int,
                              color_filters: list = None, use_color_filters: bool = False) -> str:
    return _capture_screenshot(x, y, width, height, color_filters, use_color_filters)


def check_screenshot_changed(current_screenshot_b64: str, similarity_threshold: float = 0.90) -> bool:
    last = _cache.get_last_text()

    if not last or not current_screenshot_b64:
        return True

    if _cache.is_similar(current_screenshot_b64, threshold=similarity_threshold):
        return False

    return True

def update_cache(screenshot_b64: str):
    _cache.set_last_text(screenshot_b64)


def reset_last_text():
    _cache.reset()
