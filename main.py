import sys
import ctypes
from threading import Lock
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

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass


class TranslationWorker(QObject):
    finished = pyqtSignal(str, str)
    error = pyqtSignal(str)
    no_changes = pyqtSignal()

    def __init__(self, rect: QRect, source_lang: str, target_lang: str,
                 api_key: str, color_filters: list, use_color_filters: bool, check_changes: bool = False):
        super().__init__()
        self.rect = rect
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.api_key = api_key
        self.color_filters = color_filters
        self.use_color_filters = use_color_filters
        self.check_changes = check_changes

    def run(self):
        try:
            if self.check_changes:
                changed, text = capture_if_changed(
                    self.rect.x(), self.rect.y(),
                    self.rect.width(), self.rect.height(),
                    self.color_filters, self.use_color_filters
                )
                if not changed:
                    self.no_changes.emit()
                    return
            else:
                text = capture_and_recognize_sync(
                    self.rect.x(), self.rect.y(),
                    self.rect.width(), self.rect.height(),
                    self.color_filters, self.use_color_filters
                )
                if not text:
                    self.error.emit("No text recognized.\nMake sure the frame covers the chat text.")
                    return

            result = translate_text(text, self.source_lang, self.target_lang, self.api_key)

            if result.startswith("[Error]"):
                self.error.emit(result)
            else:
                self.finished.emit(text, result)

        except Exception as e:
            self.error.emit(f"[Error] Translation failed: {str(e)}")


class App:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        self.settings = load_settings()

        self._busy_lock = Lock()
        self._busy = False
        self._active_threads = []

        self._hotkeys = []

        self._auto_timer = QTimer()
        self._auto_timer.timeout.connect(self._auto_translate_tick)

        self.overlay = OverlayWindow(self.settings)
        self.translator_win = TranslatorWindow(self.settings)

        self._connect_signals()
        self._setup_tray()
        self._register_hotkeys()
        self._apply_auto_translate()

        self.overlay.show()
        self.translator_win.show()

    def _connect_signals(self):
        self.translator_win.translate_requested.connect(self._do_translate)
        self.translator_win.settings_requested.connect(self._open_settings)
        self.translator_win.quit_requested.connect(self._quit)
        self.translator_win.target_language_changed.connect(self._on_target_language_changed)
        self.translator_win.source_language_changed.connect(self._on_source_language_changed)
        self.overlay.geometry_changed.connect(self._on_overlay_moved)

    def _setup_tray(self):
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
        self._clear_hotkeys()

        translate_key = self.settings.get("hotkey", "shift+F9")
        hide_key = self.settings.get("hotkey_hide_overlay", "shift+F8")

        try:
            import keyboard
            self._hotkeys.append(keyboard.add_hotkey(translate_key, self._do_translate))
            self._hotkeys.append(keyboard.add_hotkey(hide_key, self._toggle_overlay))
        except Exception:
            pass

    def _clear_hotkeys(self):
        try:
            import keyboard
            for hk in self._hotkeys:
                try:
                    keyboard.remove_hotkey(hk)
                except Exception:
                    pass
        except Exception:
            pass
        finally:
            self._hotkeys.clear()

    def _toggle_overlay(self):
        if self.overlay.isVisible():
            self.overlay.hide()
        else:
            self.overlay.show()
            self.overlay.raise_()

    def _do_translate(self):
        with self._busy_lock:
            if self._busy:
                return
            self._busy = True

        self.translator_win.show_loading()
        self._start_translation(check_changes=False)

    def _start_translation(self, check_changes: bool):
        api_key = self.settings.get("api_key", "").strip()
        if not api_key:
            self.translator_win.show_error("[Error] API key is missing.\nPlease add it in Settings.")
            self._release_busy_flag()
            return

        rect = self.overlay.get_capture_rect()
        source_lang = self.translator_win.get_selected_source_language()
        target_lang = self.translator_win.get_selected_target_language()
        color_filters = self.translator_win.get_enabled_color_filters()
        use_color_filters = self.settings.get("use_color_filters", False)

        worker = TranslationWorker(rect, source_lang, target_lang, api_key, color_filters, use_color_filters, check_changes)
        thread = QThread()
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.finished.connect(self._on_translation_done)
        worker.finished.connect(thread.quit)
        worker.error.connect(self.translator_win.show_error)
        worker.error.connect(thread.quit)
        worker.no_changes.connect(thread.quit)
        worker.no_changes.connect(self._on_no_changes)

        thread.finished.connect(lambda: self._cleanup_thread(thread, worker))

        self._active_threads.append(thread)

        thread.start()

    def _on_translation_done(self, original: str, translated: str):
        self.translator_win.show_translation(translated)
        target_lang = self.translator_win.get_selected_target_language()
        log_translation(original, translated, target_lang, self.settings)

    def _on_no_changes(self):
        pass

    def _cleanup_thread(self, thread: QThread, worker: QObject):
        try:
            if thread in self._active_threads:
                self._active_threads.remove(thread)

            thread.deleteLater()
            worker.deleteLater()

            self._release_busy_flag()

        except Exception:
            pass

    def _release_busy_flag(self):
        with self._busy_lock:
            if self._busy:
                self._busy = False

    def _apply_auto_translate(self):
        at = self.settings.get("auto_translate", {})
        enabled = at.get("enabled", False)
        interval = at.get("interval_seconds", 5) * 1000

        self._auto_timer.stop()
        if enabled:
            self._auto_timer.start(interval)

        self.translator_win.set_auto_translate_indicator(enabled)

    def _auto_translate_tick(self):
        with self._busy_lock:
            if self._busy:
                return
            self._busy = True

        self._start_translation(check_changes=True)

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

    def _on_overlay_moved(self):
        reset_last_text()
        self.overlay.save_geometry_to_settings()
        save_settings(self.settings)

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

        self._clear_hotkeys()

        for thread in self._active_threads[:]:
            if thread.isRunning():
                thread.quit()
                thread.wait(1000)

        self.tray.hide()

        self.app.quit()

    def run(self):
        sys.exit(self.app.exec())


if __name__ == "__main__":
    try:
        app = App()
        app.run()
    except Exception as e:
        sys.exit(1)
