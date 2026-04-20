import json
import os
import copy
from pathlib import Path


DEFAULT_SETTINGS = {
    "api_key": "",
    "source_language": "Auto-detect",
    "target_language": "Russian",
    "color_filters": {
        "#FFFFFF": True,
        "#FFD700": True,
        "#00FF00": True,
        "#FF8C00": True,
        "#A0A0A0": True,
        "#00BFFF": True,
        "#00E5FF": True,
        "#4169FF": True,
    },
    "hotkey": "shift+F9",
    "hotkey_hide_overlay": "shift+F8",
    "overlay": {
        "x": 100,
        "y": 100,
        "width": 400,
        "height": 200,
        "border_color": "#00FF00",
        "border_width": 3
    },
    "translator_window": {
        "x": 550,
        "y": 100,
        "width": 400,
        "height": 300,
        "opacity": 230
    },
    "auto_translate": {
        "enabled": False,
        "interval_seconds": 5
    },
    "history": {
        "enabled": True,
        "folder": ""
    },
    "ui": {
        "font_size": 11,
        "sound_on_translate": False,
        "autostart_with_windows": False
    }
}

SUPPORTED_LANGUAGES = [
    "Russian", "English", "German", "French", "Spanish", "Italian", "Portuguese",
    "Chinese (Simplified)", "Chinese (Traditional)", "Japanese", "Korean", "Arabic", "Turkish", "Polish", "Ukrainian"
]

SOURCE_LANGUAGES = ["Auto-detect"] + SUPPORTED_LANGUAGES


def get_settings_path() -> Path:
    appdata = os.environ.get("APPDATA", str(Path.home()))
    settings_dir = Path(appdata) / "GameTranslator"
    settings_dir.mkdir(parents=True, exist_ok=True)
    return settings_dir / "settings.json"


def get_documents_folder() -> Path:
    docs = Path.home() / "Documents"
    docs.mkdir(parents=True, exist_ok=True)
    return docs


def get_history_folder(settings: dict) -> Path:
    custom = settings.get("history", {}).get("folder", "")
    if custom:
        custom_path = Path(custom)
        if custom_path.exists() and custom_path.is_dir():
            return custom_path
    folder = get_documents_folder() / "GameTranslator"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def load_settings() -> dict:
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
    path = get_settings_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def _deep_merge(base: dict, override: dict):
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
