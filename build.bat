@echo off
REM Build GameTranslator EXE

echo Building GameTranslator...
echo.

REM Install PyInstaller if needed
pip install pyinstaller

REM Clean old builds
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /q *.spec

REM Build (--noconsole removes console window!)
pyinstaller --onefile --noconsole --name "GameTranslator" --icon=assets\icon.ico --collect-all winrt main.py

echo.
echo Done! EXE location: dist\GameTranslator.exe
pause
