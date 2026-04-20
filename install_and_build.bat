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

if exist "assets\icon.ico" (
    pyinstaller --onefile --windowed --name "GameTranslator" --icon=assets\icon.ico --collect-all winrt --hidden-import anthropic --hidden-import keyboard --hidden-import PIL main.py
) else (
    echo [WARNING] Icon not found, building without icon
    pyinstaller --onefile --windowed --name "GameTranslator" --collect-all winrt --hidden-import anthropic --hidden-import keyboard --hidden-import PIL main.py
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
