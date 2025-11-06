"""
Subtitle Overlay Module

Displays transparent, always-on-top subtitles over any window.
Perfect for YouTube, Teams, Zoom, Netflix, etc.
"""
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QPalette, QPainter, QFontMetrics
from typing import Optional
from dataclasses import dataclass
from enum import Enum


class SubtitlePosition(Enum):
    """Subtitle position on screen"""
    TOP = "top"
    BOTTOM = "bottom"
    CENTER = "center"


@dataclass
class SubtitleConfig:
    """Configuration for subtitle overlay"""
    position: SubtitlePosition = SubtitlePosition.BOTTOM
    font_size: int = 28
    font_family: str = "Arial"
    show_original: bool = True
    show_translation: bool = True
    background_opacity: float = 0.8  # 0.0 to 1.0
    text_color_original: str = "#FFFFFF"  # White
    text_color_translation: str = "#FFD700"  # Gold
    auto_hide_seconds: int = 5
    max_width_percent: float = 0.9  # 90% of screen width
    padding: int = 20
    line_spacing: int = 5


class SubtitleOverlay(QWidget):
    """
    Transparent overlay window for displaying subtitles

    Features:
    - Always on top of all windows
    - Transparent background
    - Auto-fade after N seconds
    - Dual language display (original + translation)
    - Click-through (doesn't block mouse events)
    - Customizable position and styling
    """

    # Signals
    subtitle_clicked = pyqtSignal()

    def __init__(self, config: Optional[SubtitleConfig] = None):
        super().__init__()

        self.config = config or SubtitleConfig()

        # Current subtitle texts
        self.original_text = ""
        self.translated_text = ""

        # Auto-hide timer
        self.hide_timer = QTimer()
        self.hide_timer.timeout.connect(self._auto_hide)
        self.hide_timer.setSingleShot(True)

        # Fade animation
        self.fade_animation = None

        # Setup window
        self._setup_window()
        self._create_labels()

    def _setup_window(self):
        """Configure window properties"""
        # Window flags for transparent, always-on-top, frameless window
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput  # Click-through
        )

        # Transparent background
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        # Position and size
        self._update_geometry()

    def _update_geometry(self):
        """Update window position and size based on config"""
        screen = QApplication.primaryScreen().geometry()
        screen_width = screen.width()
        screen_height = screen.height()

        # Calculate width
        width = int(screen_width * self.config.max_width_percent)
        height = 200  # Will adjust based on content

        # Calculate position
        x = (screen_width - width) // 2  # Center horizontally

        if self.config.position == SubtitlePosition.BOTTOM:
            y = screen_height - height - 50  # 50px from bottom
        elif self.config.position == SubtitlePosition.TOP:
            y = 50  # 50px from top
        else:  # CENTER
            y = (screen_height - height) // 2

        self.setGeometry(x, y, width, height)

    def _create_labels(self):
        """Create subtitle labels"""
        layout = QVBoxLayout()
        layout.setContentsMargins(
            self.config.padding,
            self.config.padding,
            self.config.padding,
            self.config.padding
        )
        layout.setSpacing(self.config.line_spacing)

        # Original text label
        self.original_label = QLabel()
        self.original_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.original_label.setWordWrap(True)
        self._setup_label_style(
            self.original_label,
            self.config.text_color_original,
            italic=True
        )

        # Translation label
        self.translation_label = QLabel()
        self.translation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.translation_label.setWordWrap(True)
        self._setup_label_style(
            self.translation_label,
            self.config.text_color_translation,
            bold=True
        )

        # Add to layout
        if self.config.show_original:
            layout.addWidget(self.original_label)

        if self.config.show_translation:
            layout.addWidget(self.translation_label)

        layout.addStretch()
        self.setLayout(layout)

    def _setup_label_style(self, label: QLabel, color: str,
                          bold: bool = False, italic: bool = False):
        """Setup label styling"""
        font = QFont(self.config.font_family, self.config.font_size)
        font.setBold(bold)
        font.setItalic(italic)
        label.setFont(font)

        # Text color with shadow effect
        label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                background-color: transparent;
                text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.9);
            }}
        """)

    def paintEvent(self, event):
        """Custom paint event for semi-transparent background"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw semi-transparent background
        background_color = QColor(0, 0, 0, int(255 * self.config.background_opacity))
        painter.fillRect(self.rect(), background_color)

    @pyqtSlot(str, str)
    def update_subtitles(self, original: str, translation: str):
        """
        Update subtitle text

        Args:
            original: Original language text
            translation: Translated text
        """
        self.original_text = original
        self.translated_text = translation

        # Update labels
        if self.config.show_original:
            self.original_label.setText(original)

        if self.config.show_translation:
            self.translation_label.setText(translation)

        # Show window if hidden
        if not self.isVisible():
            self.show()

        # Reset auto-hide timer
        if self.config.auto_hide_seconds > 0:
            self.hide_timer.start(self.config.auto_hide_seconds * 1000)

        # Adjust height based on content
        self._adjust_height()

    def _adjust_height(self):
        """Adjust window height based on text content"""
        total_height = self.config.padding * 2

        if self.config.show_original and self.original_text:
            font_metrics = QFontMetrics(self.original_label.font())
            text_height = font_metrics.boundingRect(
                0, 0,
                self.width() - self.config.padding * 2,
                1000,
                Qt.TextFlag.TextWordWrap,
                self.original_text
            ).height()
            total_height += text_height + self.config.line_spacing

        if self.config.show_translation and self.translated_text:
            font_metrics = QFontMetrics(self.translation_label.font())
            text_height = font_metrics.boundingRect(
                0, 0,
                self.width() - self.config.padding * 2,
                1000,
                Qt.TextFlag.TextWordWrap,
                self.translated_text
            ).height()
            total_height += text_height

        # Update geometry with new height
        current_geo = self.geometry()
        screen = QApplication.primaryScreen().geometry()

        if self.config.position == SubtitlePosition.BOTTOM:
            # Keep bottom position, adjust from bottom
            new_y = screen.height() - total_height - 50
            self.setGeometry(
                current_geo.x(),
                new_y,
                current_geo.width(),
                total_height
            )
        else:
            self.setGeometry(
                current_geo.x(),
                current_geo.y(),
                current_geo.width(),
                total_height
            )

    def _auto_hide(self):
        """Auto-hide after timeout"""
        self.fade_out()

    def fade_out(self):
        """Fade out and hide"""
        # Simple hide for now (can add QPropertyAnimation later)
        self.hide()

    def fade_in(self):
        """Fade in and show"""
        self.show()

    def clear_subtitles(self):
        """Clear all subtitle text"""
        self.original_text = ""
        self.translated_text = ""
        self.original_label.clear()
        self.translation_label.clear()

    def set_position(self, position: SubtitlePosition):
        """Change subtitle position"""
        self.config.position = position
        self._update_geometry()

    def set_font_size(self, size: int):
        """Change font size"""
        self.config.font_size = size
        self._setup_label_style(
            self.original_label,
            self.config.text_color_original,
            italic=True
        )
        self._setup_label_style(
            self.translation_label,
            self.config.text_color_translation,
            bold=True
        )

    def toggle_original(self, show: bool):
        """Toggle original text visibility"""
        self.config.show_original = show
        self.original_label.setVisible(show)

    def toggle_translation(self, show: bool):
        """Toggle translation text visibility"""
        self.config.show_translation = show
        self.translation_label.setVisible(show)


# Example usage
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Create config
    config = SubtitleConfig(
        position=SubtitlePosition.BOTTOM,
        font_size=32,
        show_original=True,
        show_translation=True,
        auto_hide_seconds=5
    )

    # Create overlay
    overlay = SubtitleOverlay(config)
    overlay.show()

    # Test with sample text
    def test_subtitles():
        overlay.update_subtitles(
            "Hello, how are you today?",
            "Hola, ¿cómo estás hoy?"
        )

    # Show test subtitle after 1 second
    QTimer.singleShot(1000, test_subtitles)

    # Update subtitle every 5 seconds
    timer = QTimer()
    counter = [0]

    def update_test():
        counter[0] += 1
        overlay.update_subtitles(
            f"This is test subtitle number {counter[0]}",
            f"Este es el subtítulo de prueba número {counter[0]}"
        )

    timer.timeout.connect(update_test)
    timer.start(5000)

    print("Subtitle overlay demo running...")
    print("Subtitles will appear at the bottom of your screen")
    print("Press Ctrl+C to exit")

    sys.exit(app.exec())
