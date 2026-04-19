"""
overlay.py - Transparent overlay window (Window 1)
A resizable, draggable frame that sits on top of the game.
The area inside the frame is what gets captured for OCR.
"""

from PyQt6.QtWidgets import QWidget, QSizeGrip, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt, QPoint, QRect, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QFont


class OverlayWindow(QWidget):
    """
    Semi-transparent overlay window that stays on top of all windows.
    Shows a colored border frame with title bar for dragging.
    The inside is transparent (click-through) except title bar.
    User can lock/unlock position and resize from bottom-right corner only.
    """

    geometry_changed = pyqtSignal()

    def __init__(self, settings: dict):
        super().__init__()
        self.settings = settings
        self._drag_pos = None
        self._locked = False  # Lock state for position
        self._setup_window()
        self._create_ui()
        self._apply_settings()

    def _setup_window(self):
        """Configure window flags for overlay behavior"""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # Make window transparent to mouse events except where we have widgets
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setMinimumSize(150, 80)

    def _create_ui(self):
        """Create title bar with label and lock button"""
        # Title bar frame (only this part is draggable)
        self._title_bar = QWidget(self)
        self._title_bar.setGeometry(0, 0, self.width(), 24)
        self._title_bar.setStyleSheet("""
            QWidget {
                background: rgba(30, 30, 50, 180);
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
        """)

        # Title bar layout
        title_layout = QHBoxLayout(self._title_bar)
        title_layout.setContentsMargins(6, 2, 6, 2)
        title_layout.setSpacing(4)

        # Label
        self._label = QLabel("📷 Capture Area")
        self._label.setFont(QFont("Segoe UI", 8))
        self._label.setStyleSheet("color: rgba(200,255,200,200); background: transparent;")
        title_layout.addWidget(self._label)

        title_layout.addStretch()

        # Lock button
        self._lock_btn = QPushButton("🔓")
        self._lock_btn.setFixedSize(20, 20)
        self._lock_btn.setStyleSheet("""
            QPushButton {
                background: rgba(60, 60, 100, 150);
                border: 1px solid rgba(100,100,180,100);
                border-radius: 3px;
                color: #ffcc66;
                font-size: 11px;
                padding: 0px;
            }
            QPushButton:hover {
                background: rgba(80, 80, 120, 200);
            }
        """)
        self._lock_btn.setToolTip("Lock/Unlock position")
        self._lock_btn.clicked.connect(self._toggle_lock)
        title_layout.addWidget(self._lock_btn)

        # Resize grip (bottom-right only)
        self._size_grip = QSizeGrip(self)
        self._size_grip.setFixedSize(16, 16)
        self._size_grip.setStyleSheet("background: rgba(0,255,0,80);")

    def _toggle_lock(self):
        """Toggle lock state"""
        self._locked = not self._locked
        if self._locked:
            self._lock_btn.setText("🔒")
            self._lock_btn.setToolTip("Locked - Click to unlock")
        else:
            self._lock_btn.setText("🔓")
            self._lock_btn.setToolTip("Unlocked - Click to lock")

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
        # Keep title bar at top, full width
        self._title_bar.setGeometry(0, 0, self.width(), 24)
        # Keep size grip at bottom-right
        self._size_grip.move(self.width() - 16, self.height() - 16)
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

        # Draw border
        pen = QPen(border_color, border_width)
        painter.setPen(pen)
        painter.drawRect(
            border_width // 2,
            border_width // 2,
            self.width() - border_width,
            self.height() - border_width
        )

    def mousePressEvent(self, event):
        """Handle drag only on title bar and only when unlocked"""
        if event.button() == Qt.MouseButton.LeftButton and not self._locked:
            # Check if click is in title bar area
            if event.position().y() <= 24:
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        """Move window if dragging from title bar"""
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos and not self._locked:
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
