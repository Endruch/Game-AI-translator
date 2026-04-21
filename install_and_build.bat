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
echo [Step 3/5] Downloading Tesseract OCR...

if not exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
    echo Tesseract not found. Downloading installer...
    curl -L -o tesseract-installer.exe https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.3.20231005.exe

    if errorlevel 1 (
        echo [ERROR] Failed to download Tesseract!
        pause
        exit /b 1
    )

    echo.
    echo Installing Tesseract OCR...
    echo IMPORTANT: Install to default location: C:\Program Files\Tesseract-OCR
    echo Select ALL language packs during installation!
    echo.
    pause

    tesseract-installer.exe
    del tesseract-installer.exe

    echo.
    echo Waiting for Tesseract installation...
    pause
)

echo.
echo [Step 4/5] Copying Tesseract to build...
if not exist "tesseract" mkdir tesseract
xcopy "C:\Program Files\Tesseract-OCR\*" "tesseract\" /E /I /Y >nul

echo.
echo [Step 5/5] Building EXE...
echo.

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /q *.spec
if exist __pycache__ rmdir /s /q __pycache__
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
del /s /q *.pyc 2>nul

echo Clearing application cache and settings...
if exist "%APPDATA%\GameTranslator" rmdir /s /q "%APPDATA%\GameTranslator"
echo Cache cleared.

if exist "assets\icon.ico" (
    pyinstaller --onefile --windowed --name "GameTranslator" --icon=assets\icon.ico --add-data "tesseract;tesseract" --collect-all winrt --collect-all PyQt6 --hidden-import anthropic --hidden-import keyboard --hidden-import PIL --hidden-import pytesseract --hidden-import PyQt6.QtWidgets --hidden-import PyQt6.QtCore --hidden-import PyQt6.QtGui --hidden-import winrt.windows.media.ocr --hidden-import winrt.windows.graphics.imaging --hidden-import winrt.windows.storage.streams main.py
) else (
    echo [WARNING] Icon not found, building without icon
    pyinstaller --onefile --windowed --name "GameTranslator" --add-data "tesseract;tesseract" --collect-all winrt --collect-all PyQt6 --hidden-import anthropic --hidden-import keyboard --hidden-import PIL --hidden-import pytesseract --hidden-import PyQt6.QtWidgets --hidden-import PyQt6.QtCore --hidden-import PyQt6.QtGui --hidden-import winrt.windows.media.ocr --hidden-import winrt.windows.graphics.imaging --hidden-import winrt.windows.storage.streams main.py
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
