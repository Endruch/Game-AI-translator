from datetime import datetime
from pathlib import Path
from config import get_history_folder


def log_translation(original_text: str, translated_text: str, target_language: str, settings: dict) -> bool:
    if not settings.get("history", {}).get("enabled", True):
        return True

    try:
        folder = get_history_folder(settings)
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = folder / f"translation_log_{today}.txt"

        now = datetime.now().strftime("%H:%M:%S")
        entry = f"\n[{now}] → {target_language}\n{'─' * 50}\nORIGINAL:\n{original_text.strip()}\n\nTRANSLATION:\n{translated_text.strip()}\n{'─' * 50}\n"

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry)

        return True

    except Exception:
        return False
