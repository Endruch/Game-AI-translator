"""
config.py - Load and save application settings
Settings are stored in %APPDATA%/GameTranslator/settings.json
"""

import json
import os
import copy
from pathlib import Path


DEFAULT_SETTINGS = {
    "api_key": "",
    "source_language": "Auto-detect",
    "target_language": "Russian",

    # Color filters - predefined chat text colors
    "color_filters": {
        "#FFFFFF": True,  # White
        "#FFD700": True,  # Gold
        "#C8C8C8": True,  # Gray
        "#00BFFF": True,  # Deep Sky Blue
        "#00FF7F": True,  # Spring Green
        "#87CEEB": True,  # Sky Blue
        "#4169FF": True,  # Royal Blue
    },

    # Hotkeys (use + for combinations, e.g. "shift+F9")
    "hotkey": "shift+F9",
    "hotkey_hide_overlay": "shift+F8",

    # Overlay (Window 1) appearance and position
    "overlay": {
        "x": 100,
        "y": 100,
        "width": 400,
        "height": 200,
        "border_color": "#00FF00",
        "border_width": 3
    },

    # Translator output window position
    "translator_window": {
        "x": 550,
        "y": 100,
        "width": 400,
        "height": 300,
        "opacity": 230       # 0-255, window background opacity
    },

    # Auto-translate settings
    "auto_translate": {
        "enabled": False,
        "interval_seconds": 5    # check every N seconds
    },

    # Translation history log
    "history": {
        "enabled": True,
        "folder": ""             # empty = Documents\GameTranslator\
    },

    # UI preferences
    "ui": {
        "font_size": 11,
        "sound_on_translate": False,
        "autostart_with_windows": False
    }
}

SUPPORTED_LANGUAGES = [
    "Russian",
    "English",
    "German",
    "French",
    "Spanish",
    "Italian",
    "Portuguese",
    "Chinese (Simplified)",
    "Chinese (Traditional)",
    "Japanese",
    "Korean",
    "Arabic",
    "Turkish",
    "Polish",
    "Ukrainian",
]

SOURCE_LANGUAGES = [
    "Auto-detect",
    "English",
    "Russian",
    "German",
    "French",
    "Spanish",
    "Italian",
    "Portuguese",
    "Chinese (Simplified)",
    "Chinese (Traditional)",
    "Japanese",
    "Korean",
    "Arabic",
    "Turkish",
    "Polish",
    "Ukrainian",
]


def get_settings_path() -> Path:
    """Returns path to settings file in %APPDATA%"""
    appdata = os.environ.get("APPDATA", str(Path.home()))
    settings_dir = Path(appdata) / "GameTranslator"
    settings_dir.mkdir(parents=True, exist_ok=True)
    return settings_dir / "settings.json"


def get_documents_folder() -> Path:
    """Returns the user's Documents folder"""
    docs = Path.home() / "Documents"
    docs.mkdir(parents=True, exist_ok=True)
    return docs


def get_history_folder(settings: dict) -> Path:
    """Returns the folder where daily translation logs are saved"""
    custom = settings.get("history", {}).get("folder", "")
    if custom and Path(custom).exists():
        return Path(custom)
    folder = get_documents_folder() / "GameTranslator"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def load_settings() -> dict:
    """Load settings from file, return defaults if not found"""
    path = get_settings_path()
    if not path.exists():
        return copy.deepcopy(DEFAULT_SETTINGS)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        merged = copy.deepcopy(DEFAULT_SETTINGS)
        _deep_merge(merged, data)
        return merged
    except Exception:
        return copy.deepcopy(DEFAULT_SETTINGS)


def save_settings(settings: dict) -> bool:
    """Save settings to file. Returns True on success."""
    path = get_settings_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def _deep_merge(base: dict, override: dict):
    """Recursively merge override into base dict"""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
