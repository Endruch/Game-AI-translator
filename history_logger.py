"""
history_logger.py - Save translation history to daily log files
Files are created in Documents\\GameTranslator\\translation_log_YYYY-MM-DD.txt
Nothing is stored in RAM between sessions — each entry is written immediately.
"""

from datetime import datetime
from pathlib import Path
from config import get_history_folder


def log_translation(original_text: str, translated_text: str,
                    target_language: str, settings: dict) -> bool:
    """
    Appends one translation entry to today's log file.
    Returns True on success, False on failure.
    """
    if not settings.get("history", {}).get("enabled", True):
        return True  # logging disabled, not an error

    try:
        folder = get_history_folder(settings)
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = folder / f"translation_log_{today}.txt"

        now = datetime.now().strftime("%H:%M:%S")
        separator = "─" * 50

        entry = (
            f"\n[{now}]  →  {target_language}\n"
            f"{separator}\n"
            f"ORIGINAL:\n{original_text.strip()}\n\n"
            f"TRANSLATION:\n{translated_text.strip()}\n"
            f"{separator}\n"
        )

        with open(log_file, "a", encoding="utf-8") as f:
            # No special header needed — each entry has timestamp
            f.write(entry)

        return True

    except Exception as e:
        print(f"[History] Could not write log: {e}")
        return False


def get_log_file_path(settings: dict) -> Path:
    """Returns path to today's log file (may not exist yet)"""
    folder = get_history_folder(settings)
    today = datetime.now().strftime("%Y-%m-%d")
    return folder / f"translation_log_{today}.txt"


def get_all_log_files(settings: dict) -> list[Path]:
    """Returns list of all existing log files, newest first"""
    try:
        folder = get_history_folder(settings)
        files = sorted(folder.glob("translation_log_*.txt"), reverse=True)
        return files
    except Exception:
        return []
