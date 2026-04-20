"""
Game AI Translator - Main Application
A real-time OCR and translation tool for games
"""

import sys
import ctypes
import logging
from threading import Lock
from typing import Optional
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QColor
from PyQt6.QtCore import QThread, pyqtSignal, QObject, QTimer, QRect

from config import load_settings, save_settings
from overlay import OverlayWindow
from translator_window import TranslatorWindow
from settings import SettingsWindow
from ocr_engine import capture_and_recognize_sync, capture_if_changed, reset_last_text
from claude_api import translate_text
from history_logger import log_translation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('game_translator.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Enable high DPI awareness on Windows
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
    logger.info("DPI awareness enabled")
except Exception as e:
    logger.warning(f"Could not set DPI awareness: {e}")


class TranslationWorker(QObject):
    """Worker for OCR and translation in background thread"""

    finished = pyqtSignal(str, str)  # original_text, translated_text
    error = pyqtSignal(str)  # error_message
    no_changes = pyqtSignal()  # text hasn't changed (for auto-translate)

    def __init__(self, rect: QRect, source_lang: str, target_lang: str,
                 api_key: str, color_filters: list, check_changes: bool = False):
        super().__init__()
        self.rect = rect
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.api_key = api_key
        self.color_filters = color_filters
        self.check_changes = check_changes

    def run(self):
        """Execute OCR and translation"""
        try:
            # OCR: Capture and recognize text
            if self.check_changes:
                changed, text = capture_if_changed(
                    self.rect.x(), self.rect.y(),
                    self.rect.width(), self.rect.height(),
                    self.color_filters
                )
                if not changed:
                    logger.debug("No text changes detected")
                    self.no_changes.emit()  # Signal instead of return!
                    return
            else:
                text = capture_and_recognize_sync(
                    self.rect.x(), self.rect.y(),
                    self.rect.width(), self.rect.height(),
                    self.color_filters
                )
                if not text:
                    self.error.emit("No text recognized.\nMake sure the frame covers the chat text.")
                    return

            # Translation: Call Claude API
            result = translate_text(text, self.source_lang, self.target_lang, self.api_key)

            if result.startswith("[Error]"):
                self.error.emit(result)
            else:
                self.finished.emit(text, result)

        except Exception as e:
            logger.error(f"Worker error: {e}", exc_info=True)
            self.error.emit(f"[Error] Translation failed: {str(e)}")


class App:
    """Main application class"""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        # Settings
        self.settings = load_settings()

        # Thread management
        self._busy_lock = Lock()
        self._busy = False
        self._active_threads = []  # Store thread references to prevent GC

        # Hotkeys
        self._hotkeys = []

        # Auto-translate timer
        self._auto_timer = QTimer()
        self._auto_timer.timeout.connect(self._auto_translate_tick)

        # Windows
        self.overlay = OverlayWindow(self.settings)
        self.translator_win = TranslatorWindow(self.settings)

        # Setup
        self._connect_signals()
        self._setup_tray()
        self._register_hotkeys()
        self._apply_auto_translate()

        # Show windows
        self.overlay.show()
        self.translator_win.show()

        logger.info("Application started successfully")

    def _connect_signals(self):
        """Connect all Qt signals and slots"""
        self.translator_win.translate_requested.connect(self._do_translate)
        self.translator_win.settings_requested.connect(self._open_settings)
        self.translator_win.quit_requested.connect(self._quit)
        self.translator_win.target_language_changed.connect(self._on_target_language_changed)
        self.translator_win.source_language_changed.connect(self._on_source_language_changed)
        self.overlay.geometry_changed.connect(self._on_overlay_moved)

    def _setup_tray(self):
        """Setup system tray icon"""
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor("#6666cc"))
        self.tray = QSystemTrayIcon(QIcon(pixmap), self.app)
        self.tray.setToolTip("Game Translator")

        menu = QMenu()
        menu.setStyleSheet(
            "QMenu { background: #1e1e30; color: white; border: 1px solid #3a3a6a; } "
            "QMenu::item:selected { background: #3a3a6a; }"
        )
        menu.addAction("Show Windows").triggered.connect(self._show_all)
        menu.addAction("Settings").triggered.connect(self._open_settings)
        menu.addSeparator()
        menu.addAction("Quit").triggered.connect(self._quit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(
            lambda r: self._show_all() if r == QSystemTrayIcon.ActivationReason.DoubleClick else None
        )
        self.tray.show()

    def _register_hotkeys(self):
        """Register keyboard hotkeys"""
        self._clear_hotkeys()

        translate_key = self.settings.get("hotkey", "shift+F9")
        hide_key = self.settings.get("hotkey_hide_overlay", "shift+F8")

        try:
            import keyboard
            self._hotkeys.append(keyboard.add_hotkey(translate_key, self._do_translate))
            self._hotkeys.append(keyboard.add_hotkey(hide_key, self._toggle_overlay))
            logger.info(f"Hotkeys registered: {translate_key}, {hide_key}")
        except Exception as e:
            logger.error(f"Failed to register hotkeys: {e}")

    def _clear_hotkeys(self):
        """Clear all registered hotkeys"""
        try:
            import keyboard
            for hk in self._hotkeys:
                try:
                    keyboard.remove_hotkey(hk)
                except Exception as e:
                    logger.warning(f"Failed to remove hotkey: {e}")
        except Exception as e:
            logger.error(f"Error clearing hotkeys: {e}")
        finally:
            self._hotkeys.clear()

    def _toggle_overlay(self):
        """Toggle overlay visibility"""
        if self.overlay.isVisible():
            self.overlay.hide()
            logger.debug("Overlay hidden")
        else:
            self.overlay.show()
            self.overlay.raise_()
            logger.debug("Overlay shown")

    def _do_translate(self):
        """Start manual translation (triggered by hotkey or button)"""
        with self._busy_lock:
            if self._busy:
                logger.debug("Translation already in progress, skipping")
                return
            self._busy = True

        logger.info("Starting manual translation")
        self.translator_win.show_loading()
        self._start_translation(check_changes=False)

    def _start_translation(self, check_changes: bool):
        """Start translation worker thread"""
        # Validate API key before starting
        api_key = self.settings.get("api_key", "").strip()
        if not api_key:
            self.translator_win.show_error("[Error] API key is missing.\nPlease add it in Settings.")
            self._release_busy_flag()
            logger.warning("Translation aborted: API key missing")
            return

        # Get parameters
        rect = self.overlay.get_capture_rect()
        source_lang = self.translator_win.get_selected_source_language()
        target_lang = self.translator_win.get_selected_target_language()
        color_filters = self.translator_win.get_enabled_color_filters()

        # Create worker and thread
        worker = TranslationWorker(rect, source_lang, target_lang, api_key, color_filters, check_changes)
        thread = QThread()
        worker.moveToThread(thread)

        # Connect signals
        thread.started.connect(worker.run)
        worker.finished.connect(self._on_translation_done)
        worker.finished.connect(thread.quit)
        worker.error.connect(self.translator_win.show_error)
        worker.error.connect(thread.quit)
        worker.no_changes.connect(thread.quit)  # Handle no changes
        worker.no_changes.connect(self._on_no_changes)  # Release busy flag

        # Cleanup after thread finishes
        thread.finished.connect(lambda: self._cleanup_thread(thread, worker))

        # Store thread reference to prevent garbage collection
        self._active_threads.append(thread)

        # Start thread
        thread.start()
        logger.debug(f"Translation thread started (check_changes={check_changes})")

    def _on_translation_done(self, original: str, translated: str):
        """Handle successful translation"""
        self.translator_win.show_translation(translated)
        target_lang = self.translator_win.get_selected_target_language()
        log_translation(original, translated, target_lang, self.settings)
        logger.info(f"Translation completed: {len(original)} -> {len(translated)} chars")

    def _on_no_changes(self):
        """Handle case when text hasn't changed (auto-translate)"""
        logger.debug("No text changes detected")

    def _cleanup_thread(self, thread: QThread, worker: QObject):
        """Cleanup thread and worker after completion"""
        try:
            # Remove from active threads
            if thread in self._active_threads:
                self._active_threads.remove(thread)

            # Schedule deletion
            thread.deleteLater()
            worker.deleteLater()

            # Release busy flag if still set
            self._release_busy_flag()

            logger.debug(f"Thread cleaned up. Active threads: {len(self._active_threads)}")
        except Exception as e:
            logger.error(f"Error cleaning up thread: {e}")

    def _release_busy_flag(self):
        """Safely release the busy flag"""
        with self._busy_lock:
            if self._busy:
                self._busy = False
                logger.debug("Busy flag released")

    def _apply_auto_translate(self):
        """Apply auto-translate settings"""
        at = self.settings.get("auto_translate", {})
        enabled = at.get("enabled", False)
        interval = at.get("interval_seconds", 5) * 1000

        self._auto_timer.stop()
        if enabled:
            self._auto_timer.start(interval)
            logger.info(f"Auto-translate enabled: {interval}ms interval")
        else:
            logger.info("Auto-translate disabled")

        self.translator_win.set_auto_translate_indicator(enabled)

    def _auto_translate_tick(self):
        """Auto-translate timer tick"""
        with self._busy_lock:
            if self._busy:
                logger.debug("Auto-translate tick skipped: busy")
                return
            self._busy = True

        logger.debug("Auto-translate tick: starting translation")
        self._start_translation(check_changes=True)

    def _open_settings(self):
        """Open settings dialog"""
        dlg = SettingsWindow(self.settings, self.translator_win)
        dlg.settings_saved.connect(self._on_settings_saved)
        dlg.exec()

    def _on_settings_saved(self, new_settings: dict):
        """Handle settings update"""
        self.settings = new_settings
        self._register_hotkeys()

        ov = self.settings.get("overlay", {})
        self.overlay.update_style(ov.get("border_color", "#00FF00"), ov.get("border_width", 3))

        self.translator_win.apply_new_settings(self.settings)
        self._apply_auto_translate()

        logger.info("Settings updated")

    def _on_target_language_changed(self, lang: str):
        """Save target language change"""
        self.settings["target_language"] = lang
        save_settings(self.settings)
        logger.info(f"Target language changed to: {lang}")

    def _on_source_language_changed(self, lang: str):
        """Save source language change"""
        self.settings["source_language"] = lang
        save_settings(self.settings)
        logger.info(f"Source language changed to: {lang}")

    def _on_overlay_moved(self):
        """Handle overlay position/size change"""
        reset_last_text()
        self.overlay.save_geometry_to_settings()
        save_settings(self.settings)
        logger.debug("Overlay geometry saved")

    def _show_all(self):
        """Show all windows"""
        self.overlay.show()
        self.overlay.raise_()
        self.translator_win.show()
        self.translator_win.raise_()
        logger.debug("All windows shown")

    def _quit(self):
        """Graceful application shutdown"""
        logger.info("Application shutting down...")

        # Stop auto-translate
        self._auto_timer.stop()

        # Save geometry
        self.overlay.save_geometry_to_settings()
        self.translator_win.save_geometry_to_settings()
        save_settings(self.settings)

        # Clear hotkeys
        self._clear_hotkeys()

        # Wait for active threads to finish (with timeout)
        for thread in self._active_threads[:]:  # Copy list
            if thread.isRunning():
                logger.debug(f"Waiting for thread to finish...")
                thread.quit()
                thread.wait(1000)  # Wait max 1 second

        # Hide tray
        self.tray.hide()

        # Quit application
        self.app.quit()
        logger.info("Application quit")

    def run(self):
        """Run the application"""
        sys.exit(self.app.exec())


if __name__ == "__main__":
    try:
        app = App()
        app.run()
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
