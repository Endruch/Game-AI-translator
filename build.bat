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

echo.
echo Checking if icon exists...
if exist "assets\icon.ico" (
    echo [OK] Icon found
    set ICON_PARAM=--icon=assets\icon.ico
) else (
    echo [WARNING] Icon not found - building without icon
    set ICON_PARAM=
)

echo.
echo Building with PyInstaller...
echo.

REM Build with console for debugging (change --onedir to --onefile for single exe)
pyinstaller --onefile --windowed --name "GameTranslator" %ICON_PARAM% --collect-all winrt --hidden-import anthropic --hidden-import keyboard --hidden-import PIL main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed! Check errors above.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Build completed successfully!
echo ============================================
echo.
echo EXE location: dist\GameTranslator.exe
echo.
echo If the app crashes on startup:
echo   1. Check that you're running on Windows 10/11
echo   2. Make sure all dependencies are installed
echo   3. Try running from command line to see errors
echo.
pause
