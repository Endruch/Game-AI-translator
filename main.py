"""
main.py - Application entry point
Manages all windows, hotkeys, auto-translate timer, history logging.
"""

import sys
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QWidget
from PyQt6.QtGui import QIcon, QPixmap, QColor
from PyQt6.QtCore import QThread, pyqtSignal, QObject, QTimer, QEvent

import keyboard

from config import load_settings, save_settings
from overlay import OverlayWindow
from translator_window import TranslatorWindow
from settings import SettingsWindow
from help import HelpWindow
from ocr_engine import capture_and_recognize_sync, capture_if_changed, reset_last_text
from claude_api import translate_text
from history_logger import log_translation

# DPI fix — must be before QApplication
import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass


# ─────────────────────────────────────────────────────────
# Background worker: OCR + Claude translation
# ─────────────────────────────────────────────────────────
class TranslationWorker(QObject):
    finished = pyqtSignal(str, str)   # (original_text, translated_text)
    error    = pyqtSignal(str)

    def __init__(self, x, y, width, height, source_language, target_language, api_key, color_filters=None):
        super().__init__()
        self.x               = x
        self.y               = y
        self.width           = width
        self.height          = height
        self.source_language = source_language
        self.target_language = target_language
        self.api_key         = api_key
        self.color_filters   = color_filters

    def run(self):
        # Run OCR with color filters
        text = capture_and_recognize_sync(self.x, self.y, self.width, self.height, self.color_filters)
        if not text:
            self.error.emit("No text recognized in the capture area.\n"
                            "Make sure the frame covers the chat text clearly.")
            return
        result = translate_text(text, self.source_language, self.target_language, self.api_key)
        if result.startswith("[Error]"):
            self.error.emit(result)
        else:
            self.finished.emit(text, result)


# ─────────────────────────────────────────────────────────
# Auto-translate worker: only translates if text changed
# ─────────────────────────────────────────────────────────
class AutoTranslateWorker(QObject):
    finished = pyqtSignal(str, str)
    no_change = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, x, y, width, height, source_language, target_language, api_key, color_filters=None):
        super().__init__()
        self.x = x; self.y = y
        self.width = width; self.height = height
        self.source_language = source_language
        self.target_language = target_language
        self.api_key = api_key
        self.color_filters = color_filters

    def run(self):
        changed, text = capture_if_changed(self.x, self.y, self.width, self.height, self.color_filters)
        if not changed:
            self.no_change.emit()
            return
        result = translate_text(text, self.source_language, self.target_language, self.api_key)
        if result.startswith("[Error]"):
            self.error.emit(result)
        else:
            self.finished.emit(text, result)


# ─────────────────────────────────────────────────────────
# Custom Qt event for hotkey → main thread
# ─────────────────────────────────────────────────────────
class _TranslateEvent(QEvent):
    TYPE = QEvent.Type(QEvent.registerEventType())
    def __init__(self): super().__init__(self.TYPE)

class _ToggleOverlayEvent(QEvent):
    TYPE = QEvent.Type(QEvent.registerEventType())
    def __init__(self): super().__init__(self.TYPE)


# ─────────────────────────────────────────────────────────
# Main application controller
# ─────────────────────────────────────────────────────────
class App:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        self.settings = load_settings()
        self._worker_thread   = None
        self._auto_thread     = None
        self._hotkeys         = []
        self._auto_timer      = QTimer()
        self._auto_timer.timeout.connect(self._auto_translate_tick)
        self._busy            = False   # prevent overlapping translations

        # Create windows
        self.overlay        = OverlayWindow(self.settings)
        self.translator_win = TranslatorWindow(self.settings)
        self.help_win       = None

        # Patch event handler for hotkey→Qt thread bridging
        self._patch_event_handler()

        self._connect_signals()
        self._setup_tray()
        self._register_hotkeys()
        self._apply_auto_translate()

        self.overlay.show()
        self.translator_win.show()

    # ── Signals ──────────────────────────────────────────
    def _connect_signals(self):
        self.translator_win.translate_requested.connect(self._do_translate)
        self.translator_win.settings_requested.connect(self._open_settings)
        self.translator_win.help_requested.connect(self._open_help)
        self.translator_win.quit_requested.connect(self._quit)
        self.translator_win.target_language_changed.connect(self._on_target_language_changed)
        self.translator_win.source_language_changed.connect(self._on_source_language_changed)
        self.translator_win.color_filters_changed.connect(self._on_color_filters_changed)
        self.overlay.geometry_changed.connect(self._on_overlay_moved)

    # ── System tray ──────────────────────────────────────
    def _setup_tray(self):
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor("#6666cc"))
        icon = QIcon(pixmap)

        self.tray = QSystemTrayIcon(icon, self.app)
        self.tray.setToolTip("Game Translator")

        menu = QMenu()
        menu.setStyleSheet("""
            QMenu { background: #1e1e30; color: white; border: 1px solid #3a3a6a; }
            QMenu::item:selected { background: #3a3a6a; }
        """)
        menu.addAction("Show Windows").triggered.connect(self._show_all)
        menu.addAction("Settings").triggered.connect(self._open_settings)
        menu.addSeparator()
        menu.addAction("Quit").triggered.connect(self._quit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(
            lambda r: self._show_all() if r == QSystemTrayIcon.ActivationReason.DoubleClick else None
        )
        self.tray.show()

    # ── Hotkeys ──────────────────────────────────────────
    def _register_hotkeys(self):
        for hk in self._hotkeys:
            try: keyboard.remove_hotkey(hk)
            except Exception: pass
        self._hotkeys.clear()

        translate_key = self.settings.get("hotkey", "ctrl+F9")
        hide_key      = self.settings.get("hotkey_hide_overlay", "ctrl+F8")

        try:
            h1 = keyboard.add_hotkey(translate_key, self._on_translate_hotkey)
            self._hotkeys.append(h1)
        except Exception as e:
            print(f"[Hotkey] translate: {e}")

        try:
            h2 = keyboard.add_hotkey(hide_key, self._on_toggle_overlay_hotkey)
            self._hotkeys.append(h2)
        except Exception as e:
            print(f"[Hotkey] toggle overlay: {e}")

    def _on_translate_hotkey(self):
        self.app.postEvent(self.translator_win, _TranslateEvent())

    def _on_toggle_overlay_hotkey(self):
        self.app.postEvent(self.overlay, _ToggleOverlayEvent())

    # ── Translation (manual) ─────────────────────────────
    def _do_translate(self):
        if self._busy:
            return
        self._busy = True
        self.translator_win.show_loading()

        geo          = self.overlay.get_capture_rect()
        source_lang  = self.translator_win.get_selected_source_language()
        target_lang  = self.translator_win.get_selected_target_language()
        api_key      = self.settings.get("api_key", "")
        color_filters = self.translator_win.get_enabled_color_filters()

        self._worker = TranslationWorker(
            geo.x(), geo.y(), geo.width(), geo.height(), source_lang, target_lang, api_key, color_filters
        )
        self._worker_thread = QThread()
        self._worker.moveToThread(self._worker_thread)
        self._worker_thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_translation_done)
        self._worker.finished.connect(lambda *_: self._worker_thread.quit())
        self._worker.error.connect(self.translator_win.show_error)
        self._worker.error.connect(lambda: self._worker_thread.quit())
        self._worker_thread.finished.connect(lambda: setattr(self, '_busy', False))
        self._worker_thread.start()

    def _on_translation_done(self, original: str, translated: str):
        self.translator_win.show_translation(translated)
        self._save_to_history(original, translated)

    # ── Auto-translate ────────────────────────────────────
    def _apply_auto_translate(self):
        at = self.settings.get("auto_translate", {})
        enabled  = at.get("enabled", False)
        interval = at.get("interval_seconds", 5) * 1000

        self._auto_timer.stop()
        if enabled:
            self._auto_timer.start(interval)

        self.translator_win.set_auto_translate_indicator(enabled)

    def _auto_translate_tick(self):
        if self._busy:
            return
        self._busy = True

        geo          = self.overlay.get_capture_rect()
        source_lang  = self.translator_win.get_selected_source_language()
        target_lang  = self.translator_win.get_selected_target_language()
        api_key      = self.settings.get("api_key", "")
        color_filters = self.translator_win.get_enabled_color_filters()

        self._auto_worker = AutoTranslateWorker(
            geo.x(), geo.y(), geo.width(), geo.height(), source_lang, target_lang, api_key, color_filters
        )
        self._auto_thread = QThread()
        self._auto_worker.moveToThread(self._auto_thread)
        self._auto_thread.started.connect(self._auto_worker.run)
        self._auto_worker.finished.connect(self._on_translation_done)
        self._auto_worker.finished.connect(lambda *_: self._auto_thread.quit())
        self._auto_worker.no_change.connect(lambda: self._auto_thread.quit())
        self._auto_worker.error.connect(self.translator_win.show_error)
        self._auto_worker.error.connect(lambda: self._auto_thread.quit())
        self._auto_thread.finished.connect(lambda: setattr(self, '_busy', False))
        self._auto_thread.start()

    # ── History ───────────────────────────────────────────
    def _save_to_history(self, original: str, translated: str):
        target_lang = self.translator_win.get_selected_target_language()
        log_translation(original, translated, target_lang, self.settings)

    # ── Settings ──────────────────────────────────────────
    def _open_settings(self):
        dlg = SettingsWindow(self.settings, self.translator_win)
        dlg.settings_saved.connect(self._on_settings_saved)
        dlg.exec()

    def _on_settings_saved(self, new_settings: dict):
        self.settings = new_settings
        self._register_hotkeys()
        ov = self.settings.get("overlay", {})
        self.overlay.update_style(ov.get("border_color", "#00FF00"), ov.get("border_width", 3))
        self.translator_win.apply_new_settings(self.settings)
        self._apply_auto_translate()

    def _on_target_language_changed(self, lang: str):
        self.settings["target_language"] = lang
        save_settings(self.settings)

    def _on_source_language_changed(self, lang: str):
        self.settings["source_language"] = lang
        save_settings(self.settings)

    def _on_color_filters_changed(self, enabled_colors: list):
        """Color filters are saved in translator_window, no need to save here"""
        pass

    def _on_overlay_moved(self):
        reset_last_text()   # force re-translate on next auto tick
        self.overlay.save_geometry_to_settings()
        save_settings(self.settings)

    # ── Window management ─────────────────────────────────
    def _open_help(self):
        # Always create a new instance to avoid showing closed/deleted windows
        self.help_win = HelpWindow(self.translator_win)
        self.help_win.show()
        self.help_win.raise_()

    def _show_all(self):
        self.overlay.show()
        self.overlay.raise_()
        self.translator_win.show()
        self.translator_win.raise_()

    def _quit(self):
        self._auto_timer.stop()
        self.overlay.save_geometry_to_settings()
        self.translator_win.save_geometry_to_settings()
        save_settings(self.settings)
        for hk in self._hotkeys:
            try: keyboard.remove_hotkey(hk)
            except Exception: pass
        self.tray.hide()
        self.app.quit()

    # ── Event handler patch ───────────────────────────────
    def _patch_event_handler(self):
        """Patch windows to handle custom events from hotkey threads"""
        app_ref = self

        def translator_event(self_win, event):
            if event.type() == _TranslateEvent.TYPE:
                self_win.translate_requested.emit()
                return True
            return QWidget.event(self_win, event)

        def overlay_event(self_ov, event):
            if event.type() == _ToggleOverlayEvent.TYPE:
                if self_ov.isVisible():
                    self_ov.hide()
                else:
                    self_ov.show()
                    self_ov.raise_()
                return True
            return QWidget.event(self_ov, event)

        TranslatorWindow.event = translator_event
        OverlayWindow.event    = overlay_event

    def run(self):
        sys.exit(self.app.exec())


if __name__ == "__main__":
    try:
        app = App()
        app.run()
    except Exception as e:
        import traceback
        error_msg = f"Fatal error:\n{str(e)}\n\n{traceback.format_exc()}"
        print(error_msg)
        try:
            from PyQt6.QtWidgets import QMessageBox
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("GameTranslator Error")
            msg.setText("Application failed to start")
            msg.setDetailedText(error_msg)
            msg.exec()
        except:
            pass
        sys.exit(1)
