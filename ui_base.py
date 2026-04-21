from PyQt6.QtWidgets import QWidget, QSizeGrip
from PyQt6.QtCore import Qt, QEvent


class ResizableWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._drag_pos = None
        self._resize_grips = []

    def _create_corner_grips(self):
        grips = []
        for _ in range(4):
            grip = QSizeGrip(self)
            grip.setFixedSize(16, 16)
            grips.append(grip)
        return grips

    def _position_grips(self, grips):
        if len(grips) >= 4:
            grips[0].move(self.width() - 16, self.height() - 16)
            grips[1].move(0, self.height() - 16)
            grips[2].move(self.width() - 16, 0)
            grips[3].move(0, 0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_resize_grips') and self._resize_grips:
            self._position_grips(self._resize_grips)

    def eventFilter(self, obj, event):
        if obj in self._resize_grips and event.type() == QEvent.Type.MouseButtonPress:
            grip_index = self._resize_grips.index(obj)
            self._setup_resize_corner(grip_index)
        return super().eventFilter(obj, event)

    def _setup_resize_corner(self, corner_index):
        corners = [
            Qt.Corner.BottomRightCorner,
            Qt.Corner.BottomLeftCorner,
            Qt.Corner.TopRightCorner,
            Qt.Corner.TopLeftCorner
        ]
        if 0 <= corner_index < len(corners):
            for i, grip in enumerate(self._resize_grips):
                if i == corner_index:
                    grip.setVisible(True)
                else:
                    grip.setVisible(False)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


class DraggableWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._drag_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
