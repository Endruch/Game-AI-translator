@echo off
echo ================================================
echo   Game Translator - Install and Build
echo ================================================
echo.

echo [Step 1/3] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies!
    pause
    exit /b 1
)

echo.
echo [Step 2/3] Installing PyInstaller...
pip install pyinstaller
if errorlevel 1 (
    echo [ERROR] Failed to install PyInstaller!
    pause
    exit /b 1
)

echo.
echo [Step 3/3] Building EXE...
echo.

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /q *.spec
if exist __pycache__ rmdir /s /q __pycache__
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
del /s /q *.pyc 2>nul

if exist "assets\icon.ico" (
    pyinstaller --onefile --windowed --name "GameTranslator" --icon=assets\icon.ico --add-data "help_text.txt;." --collect-all winrt --collect-all PyQt6 --hidden-import anthropic --hidden-import keyboard --hidden-import PIL --hidden-import PyQt6.QtWidgets --hidden-import PyQt6.QtCore --hidden-import PyQt6.QtGui main.py
) else (
    echo [WARNING] Icon not found, building without icon
    pyinstaller --onefile --windowed --name "GameTranslator" --add-data "help_text.txt;." --collect-all winrt --collect-all PyQt6 --hidden-import anthropic --hidden-import keyboard --hidden-import PIL --hidden-import PyQt6.QtWidgets --hidden-import PyQt6.QtCore --hidden-import PyQt6.QtGui main.py
)

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo ================================================
echo   SUCCESS! EXE created
echo ================================================
echo.
echo Location: dist\GameTranslator.exe
echo.
pause
