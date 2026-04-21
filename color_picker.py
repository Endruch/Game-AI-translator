from PyQt6.QtWidgets import QWidget, QLabel
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QCursor, QColor
from PIL import ImageGrab


class ColorPickerWidget(QWidget):
    color_picked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(120, 120)

        self._is_picking = False
        self._current_color = "#000000"

        self._setup_ui()

        self._timer = QTimer()
        self._timer.timeout.connect(self._update_color)
        self._timer.setInterval(50)

    def _setup_ui(self):
        self._preview = QLabel(self)
        self._preview.setGeometry(10, 10, 100, 80)
        self._preview.setStyleSheet("""
            QLabel {
                background: #000000;
                border: 3px solid white;
                border-radius: 8px;
            }
        """)

        self._label = QLabel("Click to pick", self)
        self._label.setGeometry(10, 95, 100, 20)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet("""
            QLabel {
                color: white;
                background: rgba(0,0,0,180);
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
            }
        """)

    def start_picking(self):
        self._is_picking = True
        self.setCursor(Qt.CursorShape.CrossCursor)
        self._timer.start()
        self._label.setText("Click color")
        self.show()
        self.raise_()

    def _update_color(self):
        if not self._is_picking:
            return

        pos = QCursor.pos()

        try:
            screenshot = ImageGrab.grab(bbox=(pos.x(), pos.y(), pos.x() + 1, pos.y() + 1))
            pixel = screenshot.getpixel((0, 0))

            if len(pixel) >= 3:
                r, g, b = pixel[0], pixel[1], pixel[2]
                self._current_color = f"#{r:02x}{g:02x}{b:02x}".upper()

                self._preview.setStyleSheet(f"""
                    QLabel {{
                        background: {self._current_color};
                        border: 3px solid white;
                        border-radius: 8px;
                    }}
                """)

                self._label.setText(self._current_color)
        except Exception:
            pass

        self.move(pos.x() + 20, pos.y() + 20)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._is_picking:
            self._is_picking = False
            self._timer.stop()
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.color_picked.emit(self._current_color)
            self.hide()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self._is_picking = False
            self._timer.stop()
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.hide()
        super().keyPressEvent(event)

    def closeEvent(self, event):
        self._is_picking = False
        self._timer.stop()
        super().closeEvent(event)
