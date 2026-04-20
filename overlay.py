from PyQt6.QtWidgets import QSizeGrip, QLabel, QPushButton, QHBoxLayout, QWidget
from PyQt6.QtCore import Qt, QRect, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from ui_base import DraggableWidget


class OverlayWindow(DraggableWidget):
    geometry_changed = pyqtSignal()

    def __init__(self, settings: dict):
        super().__init__()
        self.settings = settings
        self._locked = False

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setMinimumSize(150, 80)

        self._title_bar = QWidget(self)
        self._title_bar.setStyleSheet("background: rgba(30,30,50,180); border-top-left-radius: 4px; border-top-right-radius: 4px;")

        title_layout = QHBoxLayout(self._title_bar)
        title_layout.setContentsMargins(6, 2, 6, 2)
        title_layout.setSpacing(4)

        self._label = QLabel("📷 Capture Area")
        self._label.setFont(QFont("Segoe UI", 8))
        self._label.setStyleSheet("color: rgba(200,255,200,200); background: transparent;")
        title_layout.addWidget(self._label)
        title_layout.addStretch()

        self._lock_btn = QPushButton("🔓")
        self._lock_btn.setFixedSize(20, 20)
        self._lock_btn.setStyleSheet("QPushButton { background: rgba(60,60,100,150); border: 1px solid rgba(100,100,180,100); border-radius: 3px; color: #ffcc66; font-size: 11px; padding: 0px; } QPushButton:hover { background: rgba(80,80,120,200); }")
        self._lock_btn.setToolTip("Lock/Unlock position")
        self._lock_btn.clicked.connect(self._toggle_lock)
        title_layout.addWidget(self._lock_btn)

        self._size_grip = QSizeGrip(self)
        self._size_grip.setFixedSize(16, 16)
        self._size_grip.setStyleSheet("background: rgba(0,255,0,80);")

        ov = self.settings.get("overlay", {})
        self.setGeometry(ov.get("x", 100), ov.get("y", 100), ov.get("width", 400), ov.get("height", 200))

    def _toggle_lock(self):
        self._locked = not self._locked
        if self._locked:
            self._lock_btn.setText("🔒")
            self._size_grip.setVisible(False)
        else:
            self._lock_btn.setText("🔓")
            self._size_grip.setVisible(True)

    def update_style(self, color: str, border_width: int):
        self.settings["overlay"]["border_color"] = color
        self.settings["overlay"]["border_width"] = border_width
        self.update()

    def get_capture_rect(self) -> QRect:
        return self.geometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._title_bar.setGeometry(0, 0, self.width(), 24)
        self._size_grip.move(self.width() - 16, self.height() - 16)
        self.geometry_changed.emit()

    def moveEvent(self, event):
        super().moveEvent(event)
        self.geometry_changed.emit()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        ov = self.settings.get("overlay", {})
        border_color = QColor(ov.get("border_color", "#00FF00"))
        border_width = ov.get("border_width", 3)

        pen = QPen(border_color, border_width)
        painter.setPen(pen)
        painter.drawRect(border_width // 2, border_width // 2, self.width() - border_width, self.height() - border_width)

    def mousePressEvent(self, event):
        if not self._locked and event.position().y() <= 24:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self._locked:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)

    def save_geometry_to_settings(self):
        geo = self.geometry()
        if "overlay" not in self.settings:
            self.settings["overlay"] = {}
        self.settings["overlay"]["x"] = geo.x()
        self.settings["overlay"]["y"] = geo.y()
        self.settings["overlay"]["width"] = geo.width()
        self.settings["overlay"]["height"] = geo.height()
