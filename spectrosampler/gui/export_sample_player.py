"""Simplified sample player widget for export dialog."""

from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


class ExportSamplePlayerWidget(QWidget):
    """Simplified sample player widget for export dialog preview."""

    play_requested = Signal()  # Emitted when play is requested
    pause_requested = Signal()  # Emitted when pause is requested
    stop_requested = Signal()  # Emitted when stop is requested
    loop_changed = Signal(bool)  # Emitted when loop state changes
    auto_play_changed = Signal(bool)  # Emitted when auto-play state changes
    seek_requested = Signal(int)  # Emitted when seek is requested (position in milliseconds)

    def __init__(self, parent: QWidget | None = None):
        """Initialize export sample player widget.

        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        self.setMinimumHeight(100)

        # Playback state
        self._is_playing = False
        self._is_looping = False
        self._auto_play = False

        # Playback position
        self._current_position = 0  # milliseconds
        self._duration = 0  # milliseconds
        self._is_scrubbing = False

        # Theme colors
        self._theme_colors = {
            "background": QColor(0x25, 0x25, 0x26),
            "text": QColor(0xCC, 0xCC, 0xCC),
            "text_secondary": QColor(0x99, 0x99, 0x99),
        }

        # Load icons
        self._load_icons()

        # Setup UI
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup UI components."""
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(8)

        # Play button
        self._play_button = QPushButton()
        self._play_button.setIcon(self._play_icon)
        self._play_button.setIconSize(QSize(24, 24))
        self._play_button.setToolTip("Play")
        self._play_button.setMaximumWidth(60)
        self._play_button.clicked.connect(self._on_play_clicked)
        controls_layout.addWidget(self._play_button)

        # Pause button
        self._pause_button = QPushButton()
        self._pause_button.setIcon(self._pause_icon)
        self._pause_button.setIconSize(QSize(24, 24))
        self._pause_button.setToolTip("Pause")
        self._pause_button.setMaximumWidth(60)
        self._pause_button.clicked.connect(self._on_pause_clicked)
        self._pause_button.setEnabled(False)  # Initially disabled
        controls_layout.addWidget(self._pause_button)

        # Stop button
        self._stop_button = QPushButton()
        self._stop_button.setIcon(self._stop_icon)
        self._stop_button.setIconSize(QSize(32, 32))  # Larger than other icons
        self._stop_button.setToolTip("Stop")
        self._stop_button.setMaximumWidth(50)
        self._stop_button.clicked.connect(self._on_stop_clicked)
        controls_layout.addWidget(self._stop_button)

        controls_layout.addStretch()

        # Loop checkbox
        self._loop_checkbox = QCheckBox("Loop")
        self._loop_checkbox.setToolTip("Loop playback")
        self._loop_checkbox.toggled.connect(self._on_loop_toggled)
        controls_layout.addWidget(self._loop_checkbox)

        # Auto-play checkbox (different from main player's auto-play-next)
        self._autoplay_checkbox = QCheckBox("Auto-Play")
        self._autoplay_checkbox.setToolTip(
            "Automatically play when navigating samples with Next/Previous buttons"
        )
        self._autoplay_checkbox.toggled.connect(self._on_autoplay_toggled)
        controls_layout.addWidget(self._autoplay_checkbox)

        layout.addLayout(controls_layout)

        # Playback progress bar (scrubbable)
        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(8)

        # Time label (current)
        self._time_current_label = QLabel("0:00")
        self._time_current_label.setMinimumWidth(50)
        self._time_current_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        progress_layout.addWidget(self._time_current_label)

        # Scrubbable slider
        self._progress_slider = QSlider(Qt.Orientation.Horizontal)
        self._progress_slider.setRange(0, 0)
        self._progress_slider.setValue(0)
        self._progress_slider.setToolTip("Drag to seek")
        self._progress_slider.sliderPressed.connect(self._on_slider_pressed)
        self._progress_slider.sliderMoved.connect(self._on_slider_moved)
        self._progress_slider.sliderReleased.connect(self._on_slider_released)
        progress_layout.addWidget(self._progress_slider)

        # Time label (total)
        self._time_total_label = QLabel("0:00")
        self._time_total_label.setMinimumWidth(50)
        self._time_total_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        progress_layout.addWidget(self._time_total_label)

        layout.addLayout(progress_layout)

        self.setLayout(layout)

        # Apply checkbox styling
        from spectrosampler.gui.ui_utils import apply_checkbox_styling_to_all_checkboxes

        apply_checkbox_styling_to_all_checkboxes(self)

    def _load_icons(self) -> None:
        """Load SVG icons from assets folder, preserving colors."""
        assets_dir = Path(__file__).parent.parent.parent / "assets"
        icon_size = 24  # Base size, can be adjusted
        stop_icon_size = 32  # Larger size for stop icon

        def load_svg_icon(path: Path, size: int = icon_size) -> QIcon:
            """Load SVG icon preserving colors by rendering to pixmap."""
            if not path.exists():
                return QIcon()
            renderer = QSvgRenderer(str(path))
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            return QIcon(pixmap)

        self._play_icon = load_svg_icon(assets_dir / "play.svg")
        self._pause_icon = load_svg_icon(assets_dir / "pause.svg")
        self._stop_icon = load_svg_icon(assets_dir / "stop.svg", size=stop_icon_size)

    def set_playing(self, is_playing: bool) -> None:
        """Set playing state.

        Args:
            is_playing: True if playing, False otherwise.
        """
        self._is_playing = is_playing
        # Update button states based on playing state
        if is_playing:
            self._play_button.setEnabled(False)
            self._pause_button.setEnabled(True)
        else:
            self._play_button.setEnabled(True)
            self._pause_button.setEnabled(False)

    def set_position(self, position_ms: int, duration_ms: int) -> None:
        """Set playback position.

        Args:
            position_ms: Current position in milliseconds.
            duration_ms: Total duration in milliseconds.
        """
        if not self._is_scrubbing:
            self._current_position = position_ms
            self._duration = duration_ms
            self._progress_slider.setRange(0, max(1, duration_ms))
            self._progress_slider.setValue(position_ms)
            self._update_time_labels()

    def _update_time_labels(self) -> None:
        """Update time labels."""
        current_sec = self._current_position / 1000.0
        total_sec = self._duration / 1000.0

        # Format current time
        current_mins = int(current_sec // 60)
        current_secs = int(current_sec % 60)
        self._time_current_label.setText(f"{current_mins}:{current_secs:02d}")

        # Format total time
        total_mins = int(total_sec // 60)
        total_secs = int(total_sec % 60)
        self._time_total_label.setText(f"{total_mins}:{total_secs:02d}")

    def _on_slider_pressed(self) -> None:
        """Handle slider pressed."""
        self._is_scrubbing = True

    def _on_slider_moved(self, value: int) -> None:
        """Handle slider moved during scrubbing.

        Args:
            value: Slider value in milliseconds.
        """
        if self._is_scrubbing:
            self._current_position = value
            self._update_time_labels()

    def _on_slider_released(self) -> None:
        """Handle slider released."""
        if self._is_scrubbing:
            self._is_scrubbing = False
            # Emit seek signal
            self.seek_requested.emit(self._progress_slider.value())

    def set_looping(self, is_looping: bool) -> None:
        """Set looping state.

        Args:
            is_looping: True if looping, False otherwise.
        """
        self._is_looping = is_looping
        self._loop_checkbox.setChecked(is_looping)

    def set_auto_play(self, enabled: bool) -> None:
        """Set auto-play state.

        Args:
            enabled: True if auto-play should be enabled.
        """
        self._auto_play = enabled
        self._autoplay_checkbox.setChecked(enabled)

    def is_looping(self) -> bool:
        """Return current looping state."""
        return self._is_looping

    def is_auto_play(self) -> bool:
        """Return current auto-play state."""
        return self._auto_play

    def _on_play_clicked(self) -> None:
        """Handle play button click."""
        self.play_requested.emit()

    def _on_pause_clicked(self) -> None:
        """Handle pause button click."""
        self.pause_requested.emit()

    def _on_stop_clicked(self) -> None:
        """Handle stop button click."""
        self.stop_requested.emit()

    def _on_loop_toggled(self, checked: bool) -> None:
        """Handle loop checkbox toggle.

        Args:
            checked: True if checked, False otherwise.
        """
        self._is_looping = checked
        self.loop_changed.emit(checked)

    def _on_autoplay_toggled(self, checked: bool) -> None:
        """Handle auto-play checkbox toggle.

        Args:
            checked: True if checked, False otherwise.
        """
        self._auto_play = checked
        self.auto_play_changed.emit(checked)

    def set_theme_colors(self, colors: dict[str, QColor]) -> None:
        """Set theme colors.

        Args:
            colors: Dictionary with color definitions.
        """
        self._theme_colors.update(colors)
