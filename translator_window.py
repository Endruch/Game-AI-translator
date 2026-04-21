from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QComboBox, QPushButton, QFrame, QSizeGrip, QCheckBox, QScrollArea, QWidget, QDialog
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import sys
from pathlib import Path

from config import SUPPORTED_LANGUAGES, SOURCE_LANGUAGES, save_settings
from ui_base import DraggableWidget
from color_picker import ColorPickerWidget


class HelpWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_pos = None
        self._setup_window()
        self._build_ui()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and event.position().y() < 40:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def _setup_window(self):
        self.setWindowTitle("Help — Game Translator")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(650, 550)
        self.setStyleSheet("""
            QDialog {
                background-color: #12121c;
                color: white;
                border: 2px solid rgba(100,100,180,150);
                border-radius: 8px;
            }
            QLabel {
                color: #ccccee;
                font-size: 12px;
            }
            QTextEdit {
                background: #1e1e30;
                color: #e0e0ff;
                border: 1px solid rgba(100,100,180,100);
                border-radius: 6px;
                padding: 12px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                line-height: 1.5;
            }
            QScrollBar:vertical {
                background: rgba(30,30,50,150);
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: rgba(100,100,180,150);
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(120,120,200,180);
            }
        """)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title_bar = QWidget()
        title_bar.setFixedHeight(40)
        title_bar.setStyleSheet("background: rgba(30,30,50,220); border-bottom: 2px solid rgba(100,100,180,100);")
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(16, 0, 8, 0)

        title = QLabel("❓  Help — Game Translator")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title.setStyleSheet("color: #aaaaff;")
        title_bar_layout.addWidget(title)
        title_bar_layout.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #888;
                border: none;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(200,50,50,180);
                color: white;
                border-radius: 4px;
            }
        """)
        close_btn.clicked.connect(self.accept)
        title_bar_layout.addWidget(close_btn)

        layout.addWidget(title_bar)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(12)

        help_text = self._load_help_text()

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlainText(help_text)
        content_layout.addWidget(text_edit)

        ok_btn = QPushButton("OK")
        ok_btn.setFixedHeight(32)
        ok_btn.setStyleSheet("""
            QPushButton {
                background: rgba(60,100,200,220);
                color: white;
                border: none;
                border-radius: 5px;
                padding: 0 24px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(80,120,220,230);
            }
        """)
        ok_btn.clicked.connect(self.accept)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        content_layout.addLayout(btn_layout)

        layout.addWidget(content)

    def _load_help_text(self):
        try:
            if getattr(sys, 'frozen', False):
                base_path = Path(sys.executable).parent
            else:
                base_path = Path(__file__).parent

            help_file = base_path / "help_text.txt"

            if help_file.exists():
                return help_file.read_text(encoding="utf-8")
            else:
                return "Help file not found.\n\nPlease make sure help_text.txt exists in the application directory."
        except Exception:
            return "Error loading help file."


class TranslatorWindow(DraggableWidget):
    translate_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    quit_requested     = pyqtSignal()
    target_language_changed = pyqtSignal(str)
    source_language_changed = pyqtSignal(str)
    color_filters_changed = pyqtSignal(list)

    def __init__(self, settings: dict):
        super().__init__()
        self.settings = settings
        self._color_checkboxes = {}
        self._color_picker = ColorPickerWidget()
        self._color_picker.color_picked.connect(self._on_color_picked)
        self._setup_window()
        self._build_ui()
        self._apply_settings()
        self._init_color_filters()

    def _setup_window(self):
        self.setWindowTitle("Game Translator")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(300, 200)

    def _build_ui(self):
        self._container = QFrame(self)
        self._container.setObjectName("container")
        self._container.setStyleSheet("""
            #container {
                background-color: rgba(18, 18, 28, 230);
                border: 1px solid rgba(100, 100, 180, 150);
                border-radius: 10px;
            }
        """)

        main_layout = QVBoxLayout(self._container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        title_bar = QFrame()
        title_bar.setFixedHeight(36)
        title_bar.setStyleSheet("background: rgba(40,40,70,200); border-radius: 10px 10px 0 0;")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 8, 0)

        title_label = QLabel("🌐 Game Translator")
        title_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #aaaaff;")

        self._auto_dot = QLabel("●")
        self._auto_dot.setStyleSheet("color: #444466; font-size: 10px;")
        self._auto_dot.setToolTip("Auto-translate: OFF")

        btn_min = QPushButton("─")
        btn_close = QPushButton("✕")
        for btn in [btn_min, btn_close]:
            btn.setFixedSize(24, 24)
            btn.setStyleSheet("""
                QPushButton { background: transparent; color: #888; border: none; font-size: 11px; }
                QPushButton:hover { color: white; background: rgba(255,255,255,30); border-radius: 4px; }
            """)
        btn_min.clicked.connect(self.showMinimized)
        btn_close.clicked.connect(self.quit_requested.emit)

        title_layout.addWidget(title_label)
        title_layout.addWidget(self._auto_dot)
        title_layout.addStretch()
        title_layout.addWidget(btn_min)
        title_layout.addWidget(btn_close)

        controls = QFrame()
        controls.setStyleSheet("background: rgba(25,25,45,180);")
        ctrl_layout = QHBoxLayout(controls)
        ctrl_layout.setContentsMargins(8, 6, 8, 6)
        ctrl_layout.setSpacing(6)

        from_label = QLabel("From:")
        from_label.setStyleSheet("color: #888; font-size: 11px;")

        self.source_lang_combo = QComboBox()
        self.source_lang_combo.addItems(SOURCE_LANGUAGES)
        self.source_lang_combo.setFixedHeight(26)
        self.source_lang_combo.setStyleSheet("""
            QComboBox {
                background: rgba(50,50,80,200); color: white;
                border: 1px solid rgba(100,100,180,150); border-radius: 4px;
                padding: 2px 8px; font-size: 11px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background: #1e1e30; color: white;
                selection-background-color: #3a3a6a;
            }
        """)
        self.source_lang_combo.currentTextChanged.connect(self.source_language_changed.emit)

        arrow_label = QLabel("→")
        arrow_label.setStyleSheet("color: #6688ff; font-size: 16px; font-weight: bold;")

        to_label = QLabel("To:")
        to_label.setStyleSheet("color: #888; font-size: 11px;")

        self.target_lang_combo = QComboBox()
        self.target_lang_combo.addItems(SUPPORTED_LANGUAGES)
        self.target_lang_combo.setFixedHeight(26)
        self.target_lang_combo.setStyleSheet("""
            QComboBox {
                background: rgba(50,50,80,200); color: white;
                border: 1px solid rgba(100,100,180,150); border-radius: 4px;
                padding: 2px 8px; font-size: 11px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background: #1e1e30; color: white;
                selection-background-color: #3a3a6a;
            }
        """)
        self.target_lang_combo.currentTextChanged.connect(self.target_language_changed.emit)

        self.translate_btn = QPushButton("⚡ Translate")
        self.translate_btn.setFixedHeight(26)
        self.translate_btn.setStyleSheet("""
            QPushButton {
                background: rgba(60,100,200,200); color: white; border: none;
                border-radius: 4px; padding: 0 12px; font-size: 11px; font-weight: bold;
            }
            QPushButton:hover { background: rgba(80,120,220,220); }
            QPushButton:pressed { background: rgba(40,80,180,220); }
            QPushButton:disabled { background: rgba(40,40,70,150); color: #666; }
        """)
        self.translate_btn.clicked.connect(self.translate_requested.emit)

        btn_settings = QPushButton("⚙")
        btn_settings.setFixedSize(26, 26)
        btn_settings.setStyleSheet("""
            QPushButton {
                background: rgba(50,50,80,150); color: #aaa;
                border: 1px solid rgba(100,100,180,100); border-radius: 4px; font-size: 13px;
            }
            QPushButton:hover { color: white; background: rgba(70,70,110,200); }
        """)
        btn_settings.clicked.connect(self.settings_requested.emit)

        btn_help = QPushButton("?")
        btn_help.setFixedSize(26, 26)
        btn_help.setStyleSheet("""
            QPushButton {
                background: rgba(50,50,80,150); color: #aaa;
                border: 1px solid rgba(100,100,180,100); border-radius: 4px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { color: white; background: rgba(70,70,110,200); }
        """)
        btn_help.clicked.connect(self._show_help)

        ctrl_layout.addWidget(from_label)
        ctrl_layout.addWidget(self.source_lang_combo)
        ctrl_layout.addWidget(arrow_label)
        ctrl_layout.addWidget(to_label)
        ctrl_layout.addWidget(self.target_lang_combo)
        ctrl_layout.addStretch()
        ctrl_layout.addWidget(self.translate_btn)
        ctrl_layout.addWidget(btn_help)
        ctrl_layout.addWidget(btn_settings)

        content_row = QHBoxLayout()
        content_row.setSpacing(0)
        content_row.setContentsMargins(0, 0, 0, 0)

        self._color_panel = QFrame()
        self._color_panel.setFixedWidth(50)
        self._color_panel.setStyleSheet("background: rgba(15,15,25,200); border-right: 1px solid rgba(100,100,180,80);")
        color_panel_layout = QVBoxLayout(self._color_panel)
        color_panel_layout.setContentsMargins(4, 8, 4, 4)
        color_panel_layout.setSpacing(6)

        filter_label = QLabel("🎨")
        filter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        filter_label.setStyleSheet("color: #888; font-size: 12px;")
        filter_label.setToolTip("Color Filters\nCheck colors to translate")
        color_panel_layout.addWidget(filter_label)

        add_color_btn = QPushButton("+")
        add_color_btn.setFixedSize(40, 24)
        add_color_btn.setStyleSheet("""
            QPushButton {
                background: rgba(50,100,80,180);
                color: white;
                border: 1px solid rgba(100,180,100,150);
                border-radius: 4px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(60,120,90,220);
            }
        """)
        add_color_btn.setToolTip("Add new color (Color Picker)")
        add_color_btn.clicked.connect(self._start_color_picker)
        color_panel_layout.addWidget(add_color_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self._color_scroll = QScrollArea()
        self._color_scroll.setWidgetResizable(True)
        self._color_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._color_scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical { background: rgba(20,20,30,100); width: 4px; }
            QScrollBar::handle:vertical { background: rgba(100,100,180,150); border-radius: 2px; }
        """)

        self._color_container = QWidget()
        self._color_layout = QVBoxLayout(self._color_container)
        self._color_layout.setContentsMargins(0, 0, 0, 0)
        self._color_layout.setSpacing(4)
        self._color_layout.addStretch()

        self._color_scroll.setWidget(self._color_container)
        color_panel_layout.addWidget(self._color_scroll)

        content_row.addWidget(self._color_panel)

        self.text_output = QTextEdit()
        self.text_output.setReadOnly(True)
        self.text_output.setStyleSheet("""
            QTextEdit {
                background: transparent; color: #e0e0ff;
                border: none; padding: 10px;
            }
            QScrollBar:vertical {
                background: rgba(30,30,50,150); width: 6px; border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: rgba(100,100,180,150); border-radius: 3px;
            }
        """)
        self._update_font()
        self._set_placeholder()

        content_row.addWidget(self.text_output)

        self._status_label = QLabel("Ready")
        self._status_label.setFixedHeight(22)
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setStyleSheet(
            "color: rgba(150,150,200,180); font-size: 10px;"
            "background: rgba(20,20,40,150); border-radius: 0 0 10px 10px; padding: 0 8px;"
        )

        main_layout.addWidget(title_bar)
        main_layout.addWidget(controls)
        main_layout.addLayout(content_row)
        main_layout.addWidget(self._status_label)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._container)

        self._grip = QSizeGrip(self)
        self._grip.setFixedSize(16, 16)

    def _apply_settings(self):
        tw = self.settings.get("translator_window", {})
        self.setGeometry(
            tw.get("x", 550), tw.get("y", 100),
            tw.get("width", 400), tw.get("height", 300)
        )
        opacity = tw.get("opacity", 230)
        self._container.setStyleSheet(f"""
            #container {{
                background-color: rgba(18, 18, 28, {opacity});
                border: 1px solid rgba(100, 100, 180, 150);
                border-radius: 10px;
            }}
        """)
        source_lang = self.settings.get("source_language", "Auto-detect")
        index = self.source_lang_combo.findText(source_lang)
        if index >= 0:
            self.source_lang_combo.setCurrentIndex(index)

        target_lang = self.settings.get("target_language", "Russian")
        index = self.target_lang_combo.findText(target_lang)
        if index >= 0:
            self.target_lang_combo.setCurrentIndex(index)

        self._update_font()
        self._update_status_with_hotkey()

    def _update_font(self):
        size = self.settings.get("ui", {}).get("font_size", 11)
        self.text_output.setFont(QFont("Segoe UI", size))

    def _update_status_with_hotkey(self):
        hotkey = self.settings.get("hotkey", "Shift+F9")
        self.set_status(f"Ready  |  Press {hotkey} or click Translate")

    def apply_new_settings(self, settings: dict):
        self.settings = settings
        self._apply_settings()
        self._set_placeholder()
        self._update_status_with_hotkey()

    def set_auto_translate_indicator(self, enabled: bool):
        if enabled:
            self._auto_dot.setStyleSheet("color: #44ff88; font-size: 10px;")
            self._auto_dot.setToolTip("Auto-translate: ON")
        else:
            self._auto_dot.setStyleSheet("color: #444466; font-size: 10px;")
            self._auto_dot.setToolTip("Auto-translate: OFF")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._container.setGeometry(0, 0, self.width(), self.height())
        self._grip.move(self.width() - 16, self.height() - 16)

    def _set_placeholder(self):
        hotkey = self.settings.get("hotkey", "Shift+F9")
        self.text_output.setPlaceholderText(
            "Translation will appear here...\n\n"
            "1. Position the green frame over the game chat\n"
            f"2. Press {hotkey} to translate"
        )

    def set_status(self, text: str, color: str = "rgba(150,150,200,180)"):
        self._status_label.setText(text)
        self._status_label.setStyleSheet(
            f"color: {color}; font-size: 10px;"
            "background: rgba(20,20,40,150); border-radius: 0 0 10px 10px; padding: 0 8px;"
        )

    def show_translation(self, text: str):
        self.text_output.setPlainText(text)
        self.translate_btn.setEnabled(True)
        self.set_status("✓ Translation complete", "#80ff80")

    def show_loading(self):
        self.text_output.setPlainText("Translating...")
        self.translate_btn.setEnabled(False)
        self.set_status("⏳ Working...", "#ffcc44")

    def show_error(self, text: str):
        self.text_output.setPlainText(text)
        self.translate_btn.setEnabled(True)
        self.set_status("✗ Error", "#ff6666")

    def get_selected_source_language(self) -> str:
        return self.source_lang_combo.currentText()

    def get_selected_target_language(self) -> str:
        return self.target_lang_combo.currentText()

    def save_geometry_to_settings(self):
        geo = self.geometry()
        if "translator_window" not in self.settings:
            self.settings["translator_window"] = {}
        self.settings["translator_window"]["x"] = geo.x()
        self.settings["translator_window"]["y"] = geo.y()
        self.settings["translator_window"]["width"] = geo.width()
        self.settings["translator_window"]["height"] = geo.height()

    def _init_color_filters(self):
        color_filters = self.settings.get("color_filters", {})

        if isinstance(color_filters, list):
            color_filters = {}
            self.settings["color_filters"] = color_filters

        for hex_color, enabled in color_filters.items():
            self._add_color_checkbox(hex_color, enabled)

    def _add_color_checkbox(self, hex_color: str, checked: bool = True):
        if hex_color in self._color_checkboxes:
            return

        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(2)

        checkbox = QCheckBox()
        checkbox.setChecked(checked)
        checkbox.setFixedSize(30, 24)
        checkbox.setStyleSheet(f"""
            QCheckBox {{
                spacing: 0px;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border: 2px solid rgba(100,100,180,150);
                border-radius: 4px;
                background: {hex_color};
            }}
            QCheckBox::indicator:checked {{
                border-color: #88ff88;
            }}
            QCheckBox::indicator:unchecked {{
                border-color: #ff8888;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {hex_color}, stop:1 rgba(50,50,50,200));
            }}
        """)
        checkbox.setToolTip(f"Color: {hex_color}\nClick to toggle filter")
        checkbox.stateChanged.connect(self._on_color_filter_changed)

        del_btn = QPushButton("×")
        del_btn.setFixedSize(14, 24)
        del_btn.setStyleSheet("""
            QPushButton {
                background: rgba(100,40,40,150);
                color: #ff6666;
                border: none;
                border-radius: 2px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(150,50,50,220);
                color: white;
            }
        """)
        del_btn.setToolTip("Remove this color")
        del_btn.clicked.connect(lambda: self._remove_color(hex_color, container))

        container_layout.addWidget(checkbox)
        container_layout.addWidget(del_btn)

        self._color_layout.insertWidget(self._color_layout.count() - 1, container)
        self._color_checkboxes[hex_color] = checkbox

    def get_enabled_color_filters(self) -> list:
        enabled = []
        for hex_color, checkbox in self._color_checkboxes.items():
            if checkbox.isChecked():
                enabled.append(hex_color)
        return enabled

    def _on_color_filter_changed(self):
        enabled = self.get_enabled_color_filters()
        self.color_filters_changed.emit(enabled)

        color_filters = {}
        for hex_color, checkbox in self._color_checkboxes.items():
            color_filters[hex_color] = checkbox.isChecked()
        self.settings["color_filters"] = color_filters

    def _show_help(self):
        help_window = HelpWindow(self)
        help_window.exec()

    def _start_color_picker(self):
        self._color_picker.start_picking()

    def _on_color_picked(self, hex_color: str):
        if hex_color not in self._color_checkboxes:
            self._add_color_checkbox(hex_color, True)
            self._on_color_filter_changed()
            save_settings(self.settings)

    def _remove_color(self, hex_color: str, container: QWidget):
        if hex_color in self._color_checkboxes:
            del self._color_checkboxes[hex_color]
            container.deleteLater()
            self._on_color_filter_changed()
            save_settings(self.settings)
