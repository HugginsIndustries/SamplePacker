"""Loading screen widget shown during project/audio file loading."""

import logging
from typing import Any

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPaintEvent, QPen
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QLabel, QVBoxLayout, QWidget

from spectrosampler.gui.theme import ThemeManager

logger = logging.getLogger(__name__)


class LoadingSpinner(QWidget):
    """Animated loading spinner widget."""

    def __init__(
        self,
        parent: QWidget | None = None,
        theme_manager: ThemeManager | None = None,
    ):
        """Initialize loading spinner.

        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_timer)
        self._timer.start(16)  # ~60 FPS
        self.setFixedSize(48, 48)
        # Cache theme manager
        self._theme_manager = theme_manager or ThemeManager(self)
        # Ensure widget is visible and can receive paint events
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, False)

    def _on_timer(self) -> None:
        """Handle timer tick."""
        self._angle = (self._angle + 8) % 360
        self.update()

    def paintEvent(self, event: QPaintEvent | Any) -> None:
        """Paint spinner.

        Args:
            event: Paint event.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Get theme colors
        palette = self._theme_manager.palette
        accent_color = palette["accent"]

        # Draw spinner
        center = self.rect().center()
        radius = min(self.width(), self.height()) // 2 - 4

        # Draw spinner arc (no background circle)
        pen = QPen(accent_color)
        pen.setWidth(3)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        path = QPainterPath()
        path.arcMoveTo(
            center.x() - radius, center.y() - radius, radius * 2, radius * 2, self._angle
        )
        path.arcTo(
            center.x() - radius, center.y() - radius, radius * 2, radius * 2, self._angle, 270
        )

        painter.drawPath(path)


class LoadingContainer(QWidget):
    """Container widget with rounded rectangle background."""

    def __init__(self, parent: QWidget | None = None):
        """Initialize loading container.

        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        self._theme_manager = ThemeManager(self)
        # Make widget transparent so we can draw custom background
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        # Hide by default - only show when explicitly requested
        self.hide()
        # Set initial geometry to 0 to prevent showing in wrong place
        self.setGeometry(0, 0, 0, 0)

    def paintEvent(self, event: QPaintEvent | Any) -> None:
        """Paint rounded rectangle background.

        Args:
            event: Paint event.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Dark grey background with 80% opacity
        bg_color = QColor(40, 40, 40, 204)  # Darker grey, 80% opacity (204/255)

        # Light grey outline
        outline_color = QColor(200, 200, 200, 255)  # Light grey

        # Draw rounded rectangle background
        rect = self.rect().adjusted(0, 0, -1, -1)  # Adjust for border
        corner_radius = 15

        # Background
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(rect, corner_radius, corner_radius)

        # Outline
        pen = QPen(outline_color)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, corner_radius, corner_radius)


class LoadingScreen(QWidget):
    """Loading screen overlay widget."""

    def __init__(
        self,
        parent: QWidget | None = None,
        message: str = "Loading...",
        theme_manager: ThemeManager | None = None,
    ):
        """Initialize loading screen.

        Args:
            parent: Parent widget.
            message: Loading message to display.
        """
        super().__init__(parent)
        self._message = message

        # Theme manager
        self._theme_manager = theme_manager or ThemeManager(self)
        self._theme_manager.apply_theme()

        # Setup UI
        self._setup_ui()

        # Apply theme
        self._apply_theme()

        # Make background transparent so we can see through to the application
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # Hide by default - only show when explicitly requested
        self.hide()

    def _setup_ui(self) -> None:
        """Setup UI components."""
        # No layout on main widget - we'll position container absolutely
        self.setLayout(None)

        # Container widget with rounded rectangle background
        self._container = LoadingContainer(self)
        # Hide container by default - it will be shown when overlay is shown
        self._container.hide()
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(40, 40, 40, 40)  # Padding inside container
        container_layout.setSpacing(20)

        # Spinner
        self._spinner = LoadingSpinner(self._container, theme_manager=self._theme_manager)
        container_layout.addWidget(self._spinner, alignment=Qt.AlignmentFlag.AlignCenter)

        # Message
        self._message_label = QLabel(self._message, self._container)
        message_font = QFont()
        message_font.setPointSize(14)
        self._message_label.setFont(message_font)
        self._message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Add drop shadow effect for better legibility
        shadow = QGraphicsDropShadowEffect(self._message_label)
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 200))  # Black shadow with good opacity
        shadow.setOffset(2, 2)  # Offset shadow slightly
        self._message_label.setGraphicsEffect(shadow)

        container_layout.addWidget(self._message_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self._container.setLayout(container_layout)

    def _apply_theme(self) -> None:
        """Apply theme to loading screen."""
        palette = self._theme_manager.palette
        # Main widget is transparent, container draws its own background
        self.setStyleSheet(
            f"""
            QWidget {{
                background-color: transparent;
            }}
            QLabel {{
                color: {palette['text'].name()};
                background-color: transparent;
            }}
        """
        )
        self._message_label.setStyleSheet(f"color: {palette['text'].name()};")
        self._container.update()
        self._spinner.update()

    def refresh_theme(self, preference: str | None = None) -> None:
        """Refresh theme colors from a shared preference."""
        self._theme_manager.apply_theme(preference)
        self._apply_theme()

    def set_message(self, message: str) -> None:
        """Set loading message.

        Args:
            message: Loading message to display.
        """
        self._message = message
        self._message_label.setText(message)

    def show_overlay(self, parent: QWidget) -> None:
        """Show loading screen as overlay on parent widget.

        Args:
            parent: Parent widget to overlay.
        """
        # Update parent if changed
        if self.parent() != parent:
            self.setParent(parent)

        # Update geometry to fill parent (always update in case parent size changed)
        self.setGeometry(0, 0, parent.width(), parent.height())

        # Calculate container size (1/3 of window size)
        container_width = parent.width() // 3
        container_height = parent.height() // 3

        # Ensure minimum size for readability
        container_width = max(container_width, 300)
        container_height = max(container_height, 150)

        # Calculate centered position
        container_x = (parent.width() - container_width) // 2
        container_y = (parent.height() - container_height) // 2

        # Ensure container exists and is properly parented and positioned
        if hasattr(self, "_container"):
            self._container.setParent(self)
            # Position container first, then show
            self._container.setGeometry(container_x, container_y, container_width, container_height)
            self._container.show()
            self._container.raise_()

        # Make sure main widget is on top and visible
        self.raise_()
        self.show()
        self.update()  # Force update to ensure proper rendering

        # Start the spinner animation if not already running
        if hasattr(self, "_spinner") and hasattr(self._spinner, "_timer"):
            if not self._spinner._timer.isActive():
                self._spinner._timer.start(16)  # ~60 FPS

    def hide_overlay(self) -> None:
        """Hide loading screen overlay."""
        # Hide container first and reset its position
        if hasattr(self, "_container"):
            self._container.hide()
            # Reset container position to prevent it from appearing in wrong place
            self._container.setGeometry(0, 0, 0, 0)
        # Hide main widget
        self.hide()
        # Reset main widget geometry
        self.setGeometry(0, 0, 0, 0)
        self.setParent(None)
