"""
overlay.py - Transparent overlay window (Window 1)
A resizable, draggable frame that sits on top of the game.
The area inside the frame is what gets captured for OCR.
"""

from PyQt6.QtWidgets import QWidget, QSizeGrip, QLabel
from PyQt6.QtCore import Qt, QPoint, QRect, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QFont


class OverlayWindow(QWidget):
    """
    Semi-transparent overlay window that stays on top of all windows.
    Shows a colored border frame. The inside is transparent (click-through).
    User can drag to move and resize from corners.
    """

    # Signal emitted when overlay position/size changes
    geometry_changed = pyqtSignal()

    def __init__(self, settings: dict):
        super().__init__()
        self.settings = settings
        self._drag_pos = None
        self._setup_window()
        self._apply_settings()

    def _setup_window(self):
        """Configure window flags for overlay behavior"""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |       # No title bar
            Qt.WindowType.WindowStaysOnTopHint |      # Always on top
            Qt.WindowType.Tool                        # No taskbar entry
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(100, 60)

        # Add resize grip at bottom-right corner
        self._size_grip = QSizeGrip(self)
        self._size_grip.setFixedSize(20, 20)

        # Label shown at top of overlay
        self._label = QLabel("📷 Capture Area", self)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setFont(QFont("Segoe UI", 8))
        self._label.setStyleSheet("color: rgba(255,255,255,180); background: transparent;")
        self._label.setGeometry(0, 0, self.width(), 20)

    def _apply_settings(self):
        """Apply position, size from settings"""
        ov = self.settings.get("overlay", {})
        self.setGeometry(
            ov.get("x", 100),
            ov.get("y", 100),
            ov.get("width", 400),
            ov.get("height", 200)
        )

    def update_style(self, color: str, border_width: int):
        """Update border color and width"""
        self.settings["overlay"]["border_color"] = color
        self.settings["overlay"]["border_width"] = border_width
        self.update()

    def get_capture_rect(self) -> QRect:
        """Returns the screen geometry of this overlay (for OCR capture)"""
        return self.geometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Keep size grip at bottom-right
        self._size_grip.move(self.width() - 20, self.height() - 20)
        # Keep label at top
        self._label.setGeometry(0, 0, self.width(), 20)
        self.geometry_changed.emit()

    def moveEvent(self, event):
        super().moveEvent(event)
        self.geometry_changed.emit()

    def paintEvent(self, event):
        """Draw the transparent overlay with colored border"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        ov = self.settings.get("overlay", {})
        border_color = QColor(ov.get("border_color", "#00FF00"))
        border_width = ov.get("border_width", 3)

        # Fill inside with very slight tint (semi-transparent)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 30))

        # Draw border
        pen = QPen(border_color, border_width)
        painter.setPen(pen)
        painter.drawRect(
            border_width // 2,
            border_width // 2,
            self.width() - border_width,
            self.height() - border_width
        )

        # Draw corner handles for visual resize hint
        handle_size = 8
        painter.fillRect(0, 0, handle_size, handle_size, border_color)
        painter.fillRect(self.width() - handle_size, 0, handle_size, handle_size, border_color)
        painter.fillRect(0, self.height() - handle_size, handle_size, handle_size, border_color)
        painter.fillRect(self.width() - handle_size, self.height() - handle_size, handle_size, handle_size, border_color)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def save_geometry_to_settings(self):
        """Save current position and size to settings dict"""
        geo = self.geometry()
        self.settings["overlay"]["x"] = geo.x()
        self.settings["overlay"]["y"] = geo.y()
        self.settings["overlay"]["width"] = geo.width()
        self.settings["overlay"]["height"] = geo.height()
