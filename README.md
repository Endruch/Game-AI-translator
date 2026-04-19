# Game Translator
Real-time game chat translator powered by Claude AI + Windows OCR

## Project Structure
```
translator/
├── main.py              # Entry point
├── overlay.py           # Window 1 — capture frame overlay
├── translator_window.py # Window 2 — translation output
├── settings.py          # Window 3 — settings dialog
├── help.py              # Window 4 — help/guide
├── ocr_engine.py        # Screenshot + Windows OCR logic
├── claude_api.py        # Claude API translation
├── config.py            # Settings load/save (%APPDATA%)
└── requirements.txt     # Python dependencies
```

## Setup (Development)

1. Install Python 3.11+ (64-bit)
2. Create virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run:
   ```
   python main.py
   ```

## Build to EXE (PyInstaller)

```
pip install pyinstaller
pyinstaller --onefile --windowed --name "GameTranslator" --icon assets/icon.ico main.py
```

The final exe will be in the `dist/` folder.

## Usage

1. Enter your Claude API key in Settings (⚙)
2. Drag the **green frame** (Window 1) over the game chat
3. Choose target language in Window 2
4. Press **F9** (or your custom hotkey) to translate

## Requirements

- Windows 10 or 11 (Windows OCR is built-in, no extra install needed)
- Claude API key from https://console.anthropic.com
- Internet connection

## Notes

- No screenshots are saved to disk — all processing is in memory
- Settings saved to: `%APPDATA%\GameTranslator\settings.json`
- Supports any language mix automatically (Spanish, Korean, English, etc.)
