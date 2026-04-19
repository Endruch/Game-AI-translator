"""
help.py - Help / About window (Window 4)
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QFrame
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QFont, QDesktopServices


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
        self._setup_window()
        self._build_ui()

    def _setup_window(self):
        self.setWindowTitle("Help — Game Translator")
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.resize(500, 550)
        self.setStyleSheet("""
            QDialog { background: #12121c; color: white; }
            QScrollArea { background: transparent; border: none; }
            QWidget#scroll_content { background: transparent; }
        """)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setFixedHeight(50)
        header.setStyleSheet("background: rgba(40,40,70,220); border-bottom: 1px solid rgba(100,100,180,100);")
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(20, 0, 20, 0)
        title = QLabel("❓ Help & Guide")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet("color: #aaaaff;")
        h_layout.addWidget(title)
        layout.addWidget(header)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content = QWidget()
        content.setObjectName("scroll_content")
        c_layout = QVBoxLayout(content)
        c_layout.setContentsMargins(20, 16, 20, 16)

        text = QLabel(HELP_TEXT)
        text.setWordWrap(True)
        text.setOpenExternalLinks(True)
        text.setTextFormat(Qt.TextFormat.RichText)
        text.setFont(QFont("Segoe UI", 10))
        c_layout.addWidget(text)
        c_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

        # Footer
        footer = QFrame()
        footer.setFixedHeight(50)
        footer.setStyleSheet("background: rgba(20,20,40,200); border-top: 1px solid rgba(100,100,180,60);")
        f_layout = QVBoxLayout(footer)
        f_layout.setContentsMargins(20, 0, 20, 0)

        footer_text = QLabel("Game Translator v1.0  •  Powered by Claude AI")
        footer_text.setStyleSheet("color: #555577; font-size: 10px;")
        footer_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        f_layout.addWidget(footer_text)

        close_btn = QPushButton("Close")
        close_btn.setFixedSize(80, 28)
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(60,60,100,200);
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover { background: rgba(80,80,130,220); }
        """)
        close_btn.clicked.connect(self.accept)

        f_layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)
