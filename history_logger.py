"""
History Logger - Save translation history to daily log files
"""

import logging
from datetime import datetime
from pathlib import Path
from config import get_history_folder

# Configure logging
logger = logging.getLogger(__name__)


def log_translation(original_text: str, translated_text: str,
                    target_language: str, settings: dict) -> bool:
    """
    Log translation to daily file

    Args:
        original_text: Original text before translation
        translated_text: Translated text
        target_language: Target language name
        settings: Application settings dictionary

    Returns:
        True if logged successfully, False otherwise
    """
    # Check if history logging is enabled
    if not settings.get("history", {}).get("enabled", True):
        logger.debug("History logging disabled in settings")
        return True

    try:
        # Get history folder
        folder = get_history_folder(settings)

        # Create daily log filename
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = folder / f"translation_log_{today}.txt"

        # Format log entry
        now = datetime.now().strftime("%H:%M:%S")
        entry = (
            f"\n[{now}] → {target_language}\n"
            f"{'─' * 50}\n"
            f"ORIGINAL:\n{original_text.strip()}\n\n"
            f"TRANSLATION:\n{translated_text.strip()}\n"
            f"{'─' * 50}\n"
        )

        # Write to file
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry)

        logger.info(f"Translation logged to: {log_file.name}")
        return True

    except PermissionError as e:
        logger.error(f"Permission denied writing to log file: {e}")
        return False

    except OSError as e:
        logger.error(f"OS error writing log file: {e}")
        return False

    except Exception as e:
        logger.error(f"Unexpected error logging translation: {e}", exc_info=True)
        return False
