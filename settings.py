from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSpinBox, QFrame,
    QColorDialog, QMessageBox, QCheckBox, QTabWidget,
    QWidget, QFileDialog, QDoubleSpinBox, QRadioButton, QButtonGroup,
    QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QKeyEvent, QDesktopServices
from PyQt6.QtCore import QUrl

from config import save_settings, get_history_folder
from ai_providers import AI_PROVIDERS


class HotkeyLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Click and press key combination...")
        self.setReadOnly(True)
        self.setStyleSheet("""
            QLineEdit {
                background: rgba(40,40,70,200);
                color: white;
                border: 1px solid rgba(100,100,180,150);
                border-radius: 4px;
                padding: 4px 8px;
            }
            QLineEdit:focus {
                border: 2px solid #6688ff;
                background: rgba(50,50,90,220);
            }
        """)

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()

        if key in (Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta):
            return

        parts = []
        modifiers = event.modifiers()

        if modifiers & Qt.KeyboardModifier.ControlModifier:
            parts.append("ctrl")
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            parts.append("shift")
        if modifiers & Qt.KeyboardModifier.AltModifier:
            parts.append("alt")

        key_name = event.text()
        if not key_name:
            key_name = event.key()
            key_map = {
                Qt.Key.Key_F1: "F1", Qt.Key.Key_F2: "F2", Qt.Key.Key_F3: "F3",
                Qt.Key.Key_F4: "F4", Qt.Key.Key_F5: "F5", Qt.Key.Key_F6: "F6",
                Qt.Key.Key_F7: "F7", Qt.Key.Key_F8: "F8", Qt.Key.Key_F9: "F9",
                Qt.Key.Key_F10: "F10", Qt.Key.Key_F11: "F11", Qt.Key.Key_F12: "F12",
                Qt.Key.Key_Space: "space", Qt.Key.Key_Return: "enter",
                Qt.Key.Key_Escape: "esc", Qt.Key.Key_Tab: "tab",
            }
            key_name = key_map.get(key_name, "")

        if key_name:
            parts.append(key_name)
            self.setText("+".join(parts))

    def focusInEvent(self, event):
        self.setPlaceholderText("Press key combination...")
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        if not self.text():
            self.setPlaceholderText("Click and press key combination...")
        super().focusOutEvent(event)


class SettingsWindow(QDialog):
    settings_saved = pyqtSignal(dict)

    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._border_color = settings.get("overlay", {}).get("border_color", "#00FF00")
        self._drag_pos = None
        self._setup_window()
        self._build_ui()
        self._load_values()

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
        self.setWindowTitle("Settings — Game Translator")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(460, 600)
        self.setStyleSheet("""
            QDialog { background-color: #12121c; color: white; border: 2px solid rgba(100,100,180,150); border-radius: 8px; }
            QTabWidget::pane {
                border: 1px solid rgba(100,100,180,80);
                border-radius: 6px;
                background: #12121c;
            }
            QTabBar::tab {
                background: rgba(30,30,50,200);
                color: #888;
                padding: 7px 18px;
                border: 1px solid rgba(100,100,180,60);
                border-bottom: none;
                border-radius: 5px 5px 0 0;
                font-size: 11px;
            }
            QTabBar::tab:selected { background: #12121c; color: #aaaaff; }
            QTabBar::tab:hover { color: white; }
            QLabel { color: #ccccee; font-size: 12px; }
            QLineEdit, QSpinBox, QDoubleSpinBox {
                background: #1e1e30;
                color: white;
                border: 1px solid rgba(100,100,180,150);
                border-radius: 4px;
                padding: 5px 8px;
                font-size: 12px;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border-color: #6666cc;
            }
            QCheckBox { color: #ccccee; font-size: 12px; spacing: 8px; }
            QCheckBox::indicator {
                width: 16px; height: 16px;
                border: 1px solid rgba(100,100,180,150);
                border-radius: 3px;
                background: #1e1e30;
            }
            QCheckBox::indicator:checked {
                background: #5555cc;
                border-color: #8888ff;
            }
            QScrollArea {
                border: none;
                background: #12121c;
            }
            QScrollArea > QWidget > QWidget {
                background: #12121c;
            }
            QScrollBar:vertical {
                background: rgba(30,30,50,100);
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
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Custom title bar
        title_bar = QWidget()
        title_bar.setFixedHeight(40)
        title_bar.setStyleSheet("background: rgba(30,30,50,220); border-bottom: 2px solid rgba(100,100,180,100);")
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(16, 0, 8, 0)

        title = QLabel("⚙  Settings — Game Translator")
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
        close_btn.clicked.connect(self.reject)
        title_bar_layout.addWidget(close_btn)

        layout.addWidget(title_bar)

        # Content area
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(12)

        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self._tab_ai(), "AI Settings")
        tabs.addTab(self._tab_general(), "General")
        content_layout.addWidget(tabs)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(32)
        cancel_btn.setStyleSheet(self._cancel_style())
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("  Save  ")
        save_btn.setFixedHeight(32)
        save_btn.setStyleSheet(self._save_style())
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        content_layout.addLayout(btn_row)

        layout.addWidget(content)

    def _tab_ai(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 16, 12, 12)

        layout.addWidget(self._section("Select AI Provider"))

        self.ai_radio_buttons = {}
        self.ai_button_group = QButtonGroup()

        for provider_id, provider_info in AI_PROVIDERS.items():
            radio = QRadioButton(provider_info["name"])
            radio.setStyleSheet("color: #ccccee; font-size: 12px;")
            self.ai_radio_buttons[provider_id] = radio
            self.ai_button_group.addButton(radio)
            radio.toggled.connect(self._update_api_visibility)
            layout.addWidget(radio)

        layout.addWidget(self._sep())

        self.api_key_containers = {}
        self.api_key_inputs = {}

        for provider_id, provider_info in AI_PROVIDERS.items():
            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(8)

            label = QLabel(f"{provider_info['name']} API Key:")
            label.setStyleSheet("color: #ccccee; font-size: 12px;")

            self.api_key_inputs[provider_id] = QLineEdit()
            self.api_key_inputs[provider_id].setPlaceholderText("Enter API key...")
            self.api_key_inputs[provider_id].setEchoMode(QLineEdit.EchoMode.Password)

            show_btn = QPushButton("Show")
            show_btn.setFixedWidth(55)
            show_btn.setCheckable(True)
            show_btn.setStyleSheet(self._small_btn_style())
            key_input = self.api_key_inputs[provider_id]
            show_btn.toggled.connect(lambda c, inp=key_input: inp.setEchoMode(
                QLineEdit.EchoMode.Normal if c else QLineEdit.EchoMode.Password))
            show_btn.toggled.connect(lambda c, btn=show_btn: btn.setText("Hide" if c else "Show"))

            link_label = QLabel(f'<a href="{provider_info["url"]}" style="color: #6688ff;">Get API Key</a>')
            link_label.setOpenExternalLinks(False)
            link_label.linkActivated.connect(lambda url: QDesktopServices.openUrl(QUrl(url)))
            link_label.setStyleSheet("font-size: 10px; color: #6688ff;")

            container_layout.addWidget(label)
            row = QHBoxLayout()
            row.addWidget(self.api_key_inputs[provider_id])
            row.addWidget(show_btn)
            container_layout.addLayout(row)
            container_layout.addWidget(link_label)

            self.api_key_containers[provider_id] = container
            layout.addWidget(container)
            container.hide()

        layout.addStretch()
        scroll.setWidget(w)
        return scroll

    def _update_api_visibility(self):
        for provider_id, radio in self.ai_radio_buttons.items():
            if radio.isChecked():
                self.api_key_containers[provider_id].show()
            else:
                self.api_key_containers[provider_id].hide()

    def _tab_general(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 16, 12, 12)

        layout.addWidget(self._section("Hotkeys"))

        hint = QLabel("Click on field and press key combination")
        hint.setStyleSheet("color: #667799; font-size: 10px;")
        layout.addWidget(hint)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Translate:"))
        self.hotkey_input = HotkeyLineEdit()
        self.hotkey_input.setFixedWidth(200)
        row1.addWidget(self.hotkey_input)
        row1.addStretch()
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Show/Hide overlay:"))
        self.hotkey_hide_input = HotkeyLineEdit()
        self.hotkey_hide_input.setFixedWidth(200)
        row2.addWidget(self.hotkey_hide_input)
        row2.addStretch()
        layout.addLayout(row2)

        layout.addWidget(self._sep())

        self.autostart_check = QCheckBox("Launch with Windows")
        layout.addWidget(self.autostart_check)

        layout.addWidget(self._sep())

        layout.addWidget(self._section("Color Filters"))

        self.use_color_filters_check = QCheckBox("Enable color filtering")
        layout.addWidget(self.use_color_filters_check)

        info = QLabel(
            "When enabled, only text of selected colors will be detected.\n"
            "When disabled, text of any color will be detected."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #667799; font-size: 10px;")
        layout.addWidget(info)

        layout.addWidget(self._sep())

        layout.addWidget(self._section("Capture Frame Color"))

        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Border color:"))
        self.color_preview = QPushButton()
        self.color_preview.setFixedSize(40, 26)
        self.color_preview.setCursor(Qt.CursorShape.PointingHandCursor)
        self.color_preview.clicked.connect(self._pick_color)
        self._update_color_preview()
        color_row.addWidget(self.color_preview)
        color_row.addStretch()
        layout.addLayout(color_row)

        width_row = QHBoxLayout()
        width_row.addWidget(QLabel("Border width (px):"))
        self.border_width_spin = QSpinBox()
        self.border_width_spin.setRange(1, 10)
        self.border_width_spin.setFixedWidth(70)
        width_row.addWidget(self.border_width_spin)
        width_row.addStretch()
        layout.addLayout(width_row)

        layout.addWidget(self._sep())

        layout.addWidget(self._section("Automatic Translation"))

        self.auto_enabled_check = QCheckBox("Enable auto-translate")
        layout.addWidget(self.auto_enabled_check)

        info2 = QLabel(
            "When enabled, the app checks the capture area every N seconds.\n"
            "Translation only runs if the text has changed since last check."
        )
        info2.setWordWrap(True)
        info2.setStyleSheet("color: #667799; font-size: 10px;")
        layout.addWidget(info2)

        interval_row = QHBoxLayout()
        interval_row.addWidget(QLabel("Check interval (seconds):"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(2, 60)
        self.interval_spin.setSuffix(" s")
        self.interval_spin.setFixedWidth(80)
        interval_row.addWidget(self.interval_spin)
        interval_row.addStretch()
        layout.addLayout(interval_row)

        layout.addWidget(self._sep())

        layout.addWidget(self._section("Translator Window"))

        opacity_row = QHBoxLayout()
        opacity_row.addWidget(QLabel("Window opacity (%):"))
        self.opacity_spin = QSpinBox()
        self.opacity_spin.setRange(20, 100)
        self.opacity_spin.setSuffix(" %")
        self.opacity_spin.setFixedWidth(80)
        opacity_row.addWidget(self.opacity_spin)
        opacity_row.addStretch()
        layout.addLayout(opacity_row)

        layout.addWidget(self._sep())

        layout.addWidget(self._section("Translation Text"))

        font_row = QHBoxLayout()
        font_row.addWidget(QLabel("Font size (pt):"))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setFixedWidth(70)
        font_row.addWidget(self.font_size_spin)
        font_row.addStretch()
        layout.addLayout(font_row)

        layout.addWidget(self._sep())

        layout.addWidget(self._section("Translation History"))

        self.history_enabled_check = QCheckBox("Save translation history to file")
        layout.addWidget(self.history_enabled_check)

        info3 = QLabel(
            "Each translation is appended to a daily log file:\n"
            "translation_log_YYYY-MM-DD.txt"
        )
        info3.setWordWrap(True)
        info3.setStyleSheet("color: #667799; font-size: 10px;")
        layout.addWidget(info3)

        self.history_folder_input = QLineEdit()
        self.history_folder_input.setPlaceholderText("Default: Documents\\GameTranslator\\")
        self.history_folder_input.setReadOnly(True)
        browse_btn = QPushButton("Browse...")
        browse_btn.setFixedWidth(80)
        browse_btn.setStyleSheet(self._small_btn_style())
        browse_btn.clicked.connect(self._browse_history_folder)

        folder_row = QHBoxLayout()
        folder_row.addWidget(self.history_folder_input)
        folder_row.addWidget(browse_btn)
        layout.addLayout(folder_row)

        self._folder_hint = QLabel("")
        self._folder_hint.setStyleSheet("color: #556688; font-size: 10px;")
        self._folder_hint.setWordWrap(True)
        layout.addWidget(self._folder_hint)

        open_btn = QPushButton("Open log folder")
        open_btn.setFixedWidth(140)
        open_btn.setStyleSheet(self._small_btn_style())
        open_btn.clicked.connect(self._open_history_folder)
        layout.addWidget(open_btn)

        layout.addStretch()
        scroll.setWidget(w)
        return scroll


    def _load_values(self):
        s = self.settings

        selected_provider = s.get("ai_provider", "Claude")
        if selected_provider in self.ai_radio_buttons:
            self.ai_radio_buttons[selected_provider].setChecked(True)

        api_keys = s.get("api_keys", {})
        for provider_id, key_input in self.api_key_inputs.items():
            key_input.setText(api_keys.get(provider_id, ""))

        self._update_api_visibility()

        self.hotkey_input.setText(s.get("hotkey", "shift+F9"))
        self.hotkey_hide_input.setText(s.get("hotkey_hide_overlay", "shift+F8"))

        self.use_color_filters_check.setChecked(s.get("use_color_filters", False))

        ov = s.get("overlay", {})
        self.border_width_spin.setValue(ov.get("border_width", 3))

        tw = s.get("translator_window", {})
        opacity_val = tw.get("opacity", 230)
        opacity_pct = round((opacity_val / 255.0) * 100)
        self.opacity_spin.setValue(opacity_pct)

        at = s.get("auto_translate", {})
        self.auto_enabled_check.setChecked(at.get("enabled", False))
        self.interval_spin.setValue(at.get("interval_seconds", 5))

        h = s.get("history", {})
        self.history_enabled_check.setChecked(h.get("enabled", True))
        custom_folder = h.get("folder", "")
        self.history_folder_input.setText(custom_folder)
        self._update_folder_hint()

        ui = s.get("ui", {})
        self.font_size_spin.setValue(ui.get("font_size", 11))
        self.autostart_check.setChecked(ui.get("autostart_with_windows", False))

    def _save(self):
        s = self.settings

        for provider_id, radio in self.ai_radio_buttons.items():
            if radio.isChecked():
                s["ai_provider"] = provider_id
                s["ai_model"] = AI_PROVIDERS[provider_id]["models"][0]
                break

        if "api_keys" not in s:
            s["api_keys"] = {}
        for provider_id, key_input in self.api_key_inputs.items():
            s["api_keys"][provider_id] = key_input.text().strip()

        s["hotkey"] = self.hotkey_input.text().strip() or "shift+F9"
        s["hotkey_hide_overlay"] = self.hotkey_hide_input.text().strip() or "shift+F8"

        s["use_color_filters"] = self.use_color_filters_check.isChecked()

        s["overlay"]["border_color"] = self._border_color
        s["overlay"]["border_width"] = self.border_width_spin.value()

        opacity_pct = self.opacity_spin.value()
        opacity_val = round((opacity_pct / 100.0) * 255)
        s["translator_window"]["opacity"] = opacity_val

        s["auto_translate"]["enabled"] = self.auto_enabled_check.isChecked()
        s["auto_translate"]["interval_seconds"] = self.interval_spin.value()

        s["history"]["enabled"] = self.history_enabled_check.isChecked()
        s["history"]["folder"] = self.history_folder_input.text().strip()

        s["ui"]["font_size"] = self.font_size_spin.value()
        s["ui"]["autostart_with_windows"] = self.autostart_check.isChecked()

        # Handle autostart registry
        self._apply_autostart(s["ui"]["autostart_with_windows"])

        if save_settings(s):
            self.settings_saved.emit(s)
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Could not save settings file.")

    def _apply_autostart(self, enabled: bool):
        try:
            import winreg
            import sys
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path,
                                 0, winreg.KEY_SET_VALUE)
            if enabled:
                if getattr(sys, 'frozen', False):
                    exe_path = sys.executable
                else:
                    exe_path = f'"{sys.executable}" "{sys.argv[0]}"'
                winreg.SetValueEx(key, "GameTranslator", 0, winreg.REG_SZ, exe_path)
            else:
                try:
                    winreg.DeleteValue(key, "GameTranslator")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except (PermissionError, Exception):
            pass

    def _pick_color(self):
        color = QColorDialog.getColor(QColor(self._border_color), self, "Choose Border Color")
        if color.isValid():
            self._border_color = color.name()
            self._update_color_preview()

    def _update_color_preview(self):
        self.color_preview.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._border_color};
                border: 1px solid rgba(255,255,255,100);
                border-radius: 3px;
            }}
        """)

    def _browse_history_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose Log Folder")
        if folder:
            self.history_folder_input.setText(folder)
            temp_settings = self.settings.copy()
            temp_settings["history"]["folder"] = folder
            folder_to_show = get_history_folder(temp_settings)
            self._folder_hint.setText(f"Current: {folder_to_show}")

    def _update_folder_hint(self):
        folder = get_history_folder(self.settings)
        self._folder_hint.setText(f"Current: {folder}")

    def _open_history_folder(self):
        import subprocess
        folder = get_history_folder(self.settings)
        try:
            subprocess.Popen(['explorer', str(folder)])
        except (FileNotFoundError, Exception):
            pass

    def _section(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        label.setStyleSheet("color: #8888cc;")
        return label

    def _sep(self) -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background: rgba(100,100,180,60);")
        sep.setFixedHeight(1)
        return sep

    def _small_btn_style(self):
        return """
            QPushButton {
                background: rgba(50,50,80,200); color: #aaa;
                border: 1px solid rgba(100,100,180,100);
                border-radius: 4px; padding: 4px; font-size: 11px;
            }
            QPushButton:hover { color: white; }
        """

    def _save_style(self):
        return """
            QPushButton {
                background: rgba(60,100,200,220); color: white;
                border: none; border-radius: 5px;
                padding: 0 16px; font-size: 12px; font-weight: bold;
            }
            QPushButton:hover { background: rgba(80,120,220,230); }
        """

    def _cancel_style(self):
        return """
            QPushButton {
                background: rgba(50,50,70,180); color: #aaa;
                border: 1px solid rgba(100,100,150,100);
                border-radius: 5px; padding: 0 12px; font-size: 12px;
            }
            QPushButton:hover { color: white; }
        """
