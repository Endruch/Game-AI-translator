"""
help.py - Help / About window (Window 4)
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QFrame, QHBoxLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


HELP_TEXT = """
<h3 style="color:#aaaaff;">🚀 Quick Start</h3>
<ol style="color:#ccccee; line-height:1.8;">
  <li>Open <b>Settings (⚙)</b> and enter your Claude API key</li>
  <li>Choose the language you want to translate <b>to</b></li>
  <li>Drag the <b>green frame (Window 1)</b> over the game chat area</li>
  <li>Resize the frame to cover exactly the chat text</li>
  <li>Press <b>F9</b> (or your hotkey) to translate!</li>
</ol>

<h3 style="color:#aaaaff;">🖼 Window 1 — Capture Frame</h3>
<p style="color:#ccccee; line-height:1.6;">
  This is the transparent frame you place over the game chat.<br>
  • <b>Drag</b> to move it anywhere on screen<br>
  • <b>Resize</b> from the corners to adjust the capture area<br>
  • The frame color and border width can be changed in Settings
</p>

<h3 style="color:#aaaaff;">🌐 Window 2 — Translation</h3>
<p style="color:#ccccee; line-height:1.6;">
  Shows the translated text from the capture area.<br>
  • Select <b>target language</b> from the dropdown<br>
  • Press <b>⚡ Translate</b> or use the hotkey<br>
  • Supports any mix of languages in the chat automatically
</p>

<h3 style="color:#aaaaff;">⚙ Settings</h3>
<p style="color:#ccccee; line-height:1.6;">
  • <b>API Key</b> — your Claude API key from console.anthropic.com<br>
  • <b>Hotkey</b> — key to trigger translation (default: F9)<br>
  • <b>Border Color</b> — color of the capture frame<br>
  • <b>Border Width</b> — thickness of the capture frame border
</p>

<h3 style="color:#aaaaff;">💡 Tips</h3>
<p style="color:#ccccee; line-height:1.6;">
  • Make the frame <b>slightly larger</b> than the chat box for best results<br>
  • Claude auto-detects language — Spanish, Korean, English, etc. all work<br>
  • No screenshots are saved to disk — everything is in memory only<br>
  • Settings are saved in <code style="color:#88ff88;">%APPDATA%\\GameTranslator\\settings.json</code>
</p>

<h3 style="color:#aaaaff;">❓ Troubleshooting</h3>
<p style="color:#ccccee; line-height:1.6;">
  <b>"Invalid API key"</b> — Check your key in Settings<br>
  <b>"No text recognized"</b> — Make sure the frame covers text clearly<br>
  <b>"Rate limit"</b> — Wait a few seconds and try again<br>
  <b>Poor OCR</b> — Try resizing the frame; Windows OCR works best at 100% display scaling
</p>
"""


class HelpWindow(QDialog):
    """Help and About dialog"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_pos = None
        self._setup_window()
        self._build_ui()

    def _setup_window(self):
        self.setWindowTitle("Help — Game Translator")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(520, 580)
        self.setStyleSheet("""
            QDialog {
                background: #12121c;
                color: white;
                border: 2px solid rgba(100,100,180,180);
                border-radius: 10px;
            }
            QScrollArea { background: transparent; border: none; }
            QWidget#scroll_content { background: transparent; }
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if event.position().y() < 50:
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setFixedHeight(50)
        header.setStyleSheet("background: rgba(30,30,50,230); border-bottom: 2px solid rgba(100,100,180,120); border-top-left-radius: 10px; border-top-right-radius: 10px;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(20, 0, 12, 0)

        title = QLabel("❓ Help & Guide")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet("color: #aaaaff;")
        h_layout.addWidget(title)
        h_layout.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(36, 36)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #888;
                border: none;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(220,60,60,200);
                color: white;
                border-radius: 6px;
            }
        """)
        close_btn.clicked.connect(self.close)
        h_layout.addWidget(close_btn)

        layout.addWidget(header)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        content = QWidget()
        content.setObjectName("scroll_content")
        c_layout = QVBoxLayout(content)
        c_layout.setContentsMargins(20, 20, 20, 20)

        text = QLabel(HELP_TEXT)
        text.setWordWrap(True)
        text.setOpenExternalLinks(False)
        text.setTextFormat(Qt.TextFormat.RichText)
        text.setFont(QFont("Segoe UI", 10))
        text.setStyleSheet("line-height: 1.5;")
        c_layout.addWidget(text)
        c_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

        # Footer
        footer = QFrame()
        footer.setFixedHeight(48)
        footer.setStyleSheet("background: rgba(20,20,40,230); border-bottom-left-radius: 10px; border-bottom-right-radius: 10px;")
        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(20, 0, 20, 0)

        footer_text = QLabel("Game Translator v1.0  •  Powered by Claude AI + Windows OCR")
        footer_text.setStyleSheet("color: #555577; font-size: 10px;")
        f_layout.addWidget(footer_text, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(footer)
