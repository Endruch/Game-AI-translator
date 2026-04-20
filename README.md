# Game Translator
Real-time game chat translator powered by Claude AI + Windows OCR

## 🚀 Quick Start

### Automated Installation (Recommended)
```batch
install_and_build.bat
```
This will install all dependencies and build the EXE automatically.

### Manual Installation
```batch
pip install -r requirements.txt
build.bat
```

### Debug Version (if app crashes)
```batch
build_debug.bat
```
Creates version with console to see error messages.

---

## ⚠️ IMPORTANT - Correct Build Command

If you're building manually with PyInstaller, you **MUST** include all dependencies:

```batch
pyinstaller --onefile --windowed --name "GameTranslator" --icon=assets\icon.ico --collect-all winrt --hidden-import anthropic --hidden-import keyboard --hidden-import PIL main.py
```

### ❌ WRONG (will crash):
```batch
pyinstaller --onefile main.py
```
This doesn't include required modules!

### Required PyInstaller Flags:
- `--collect-all winrt` - Windows OCR support
- `--hidden-import anthropic` - Claude API
- `--hidden-import keyboard` - Hotkeys
- `--hidden-import PIL` - Screenshots
- `--windowed` - No console window

---

## 📋 Requirements

- **Windows 10 or 11** (64-bit)
- **Python 3.11+** (for development)
- **Claude API key** (get at [console.anthropic.com](https://console.anthropic.com))

---

## 🎮 First Launch

1. Run `dist\GameTranslator.exe`
2. Click **⚙ Settings**
3. Enter your Claude API key
4. Configure hotkeys (default: **Shift+F9**)
5. Choose target language

---

## ✨ Features

- **Windows OCR** - No external OCR dependencies
- **Color Filtering** - 7 predefined chat text colors
- **Auto-translate** - Configurable interval
- **Translation History** - Daily log files
- **Hotkeys** - Shift+F9 (translate), Shift+F8 (hide/show)
- **Lock/Unlock** - Lock overlay position with 🔒 button
- **Click-through** - Overlay transparent to mouse (except title bar)
- **Source Language** - Auto-detect or manual selection
- **Target Language** - Choose from 15+ languages

---

## 📖 Usage

1. **Position Overlay**: Drag the green frame over game chat
2. **Lock Position**: Click 🔒 in overlay title bar (optional)
3. **Select Colors**: Check/uncheck colors in left panel of translator window
4. **Translate**: Press **Shift+F9** or click Translate button
5. **Auto-translate**: Enable in Settings → Auto-Translate tab

---

## 🐛 Troubleshooting

### App doesn't start
1. Use `build_debug.bat` to see error messages
2. Or run directly: `python main.py`
3. Check you're on Windows 10/11 (won't work on older versions)
4. Make sure all dependencies installed: `pip install -r requirements.txt`

### Hotkeys don't work
1. Default is **Shift+F9** (not just F9!)
2. Check Settings → General → Hotkeys
3. Try running as Administrator
4. Some games may block global hotkeys

### OCR doesn't recognize text
1. Install Windows language pack for your game's language:
   - Settings → Time & Language → Language
   - Add a language → Download language pack
2. Make sure overlay frame covers text clearly
3. Adjust color filters - uncheck colors you don't need

### Translation errors
1. Check API key is valid in Settings
2. Check internet connection
3. Look at error message in translator window

---

## 🎨 Color Filters

7 predefined chat text colors:
- `#FFFFFF` - White
- `#FFD700` - Gold
- `#C8C8C8` - Gray
- `#00BFFF` - Deep Sky Blue
- `#00FF7F` - Spring Green
- `#87CEEB` - Sky Blue
- `#4169FF` - Royal Blue

Uncheck colors you don't need (e.g., system messages, timestamps).

---

## 📁 Project Structure
```
GameTranslator/
├── main.py              # Entry point
├── overlay.py           # Capture frame overlay
├── translator_window.py # Translation output window
├── settings.py          # Settings dialog
├── help.py              # Help window
├── ocr_engine.py        # Windows OCR integration
├── claude_api.py        # Claude API translation
├── color_detector.py    # Color filtering
├── config.py            # Settings management
├── history_logger.py    # Translation history
├── requirements.txt     # Python dependencies
├── build.bat            # Build script
├── build_debug.bat      # Debug build script
└── assets/
    └── icon.ico         # Application icon
```

---

## 💾 Settings Location

Settings saved to: `%APPDATA%\GameTranslator\settings.json`

Translation history: `%USERPROFILE%\Documents\GameTranslator\translation_log_YYYY-MM-DD.txt`

---

## 🔧 Development

### Run from source:
```batch
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Test changes:
```batch
python main.py
```

### Build EXE:
```batch
build.bat
```

---

## 📝 Notes

- No screenshots saved to disk — all processing in memory
- Supports automatic language detection
- Can translate from any language to any language
- Works with any game that displays text on screen

---

## 🆘 Support

If you encounter issues:
1. Check [QUICK_START.txt](QUICK_START.txt) for detailed instructions
2. Use `build_debug.bat` to see error messages
3. Make sure you're using correct PyInstaller command
4. Verify all dependencies are installed

---

## 📜 License

MIT License - Feel free to use and modify
