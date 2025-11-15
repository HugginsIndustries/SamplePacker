"""Sample scrubber widget for quick navigation between samples."""

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QCursor, QKeyEvent, QMouseEvent
from PySide6.QtWidgets import QSlider, QToolTip

from spectrosampler.detectors.base import Segment


class SampleScrubber(QSlider):
    """Slider widget for scrubbing through samples with tooltip preview."""

    value_committed = Signal(int)  # Emitted when user releases mouse (final value)
    scrubbing_cancelled = Signal()  # Emitted when ESC is pressed to cancel

    def __init__(self, parent=None):
        """Initialize sample scrubber.

        Args:
            parent: Parent widget.
        """
        super().__init__(Qt.Orientation.Horizontal, parent)
        self.setRange(0, 0)
        self.setValue(0)
        self.setToolTip("Drag to navigate samples")
        # Enable keyboard focus for ESC key handling
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Scrubbing state
        self._is_scrubbing: bool = False
        self._scrub_start_value = 0
        self._pending_value = 0
        self._segments: list[Segment] = []
        self._current_index = 0
        self._last_mouse_pos: QPoint | None = None

    def set_segments(self, segments: list[Segment]) -> None:
        """Set the list of segments for tooltip display.

        Args:
            segments: List of segment objects.
        """
        self._segments = segments
        self.setRange(0, max(0, len(segments) - 1))

    def set_current_index(self, index: int) -> None:
        """Set the current sample index.

        Args:
            index: Current sample index (0-based).
        """
        self._current_index = index
        if not self._is_scrubbing:
            self.setValue(index)

    def is_scrubbing(self) -> bool:
        """Check if scrubber is currently being scrubbed.

        Returns:
            True if scrubbing, False otherwise.
        """
        return self._is_scrubbing

    def _get_sample_tooltip(self, index: int) -> str:
        """Get tooltip text for a sample index.

        Args:
            index: Sample index (0-based).

        Returns:
            Tooltip text string.
        """
        total = len(self._segments) if self._segments else 0
        if not self._segments or index < 0 or index >= len(self._segments):
            return f"Sample {index + 1} of {total}" if total > 0 else "No samples"

        segment = self._segments[index]
        start = segment.start
        end = segment.end
        duration = segment.duration()
        detector = segment.detector or "unknown"

        return f"Sample {index + 1} of {len(self._segments)}\n{detector}\n{start:.3f}s → {end:.3f}s ({duration:.3f}s)"

    def sliderChange(self, change) -> None:
        """Override sliderChange to prevent value changes from being committed during scrubbing.

        Args:
            change: Slider change type.
        """
        # During scrubbing, we only want visual updates, not actual value changes
        # So we allow the visual update but track the pending value separately
        super().sliderChange(change)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press to start scrubbing.

        Args:
            event: Mouse event.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_scrubbing = True
            self._scrub_start_value = self.value()
            self._pending_value = self.value()
            self._last_mouse_pos = event.position().toPoint()
            # Set focus to receive keyboard events (ESC key)
            self.setFocus()
            # Let QSlider handle the press to update visual position
            super().mousePressEvent(event)
            # Calculate and show tooltip for current position
            self._update_tooltip_from_slider_value()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move during scrubbing.

        Args:
            event: Mouse event.
        """
        if self._is_scrubbing:
            self._last_mouse_pos = event.position().toPoint()
            # Let QSlider handle the move to update visual position
            super().mouseMoveEvent(event)
            self._pending_value = self.value()
            # Update tooltip with current slider value
            self._update_tooltip_from_slider_value()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release to commit scrub.

        Args:
            event: Mouse event.
        """
        if event.button() == Qt.MouseButton.LeftButton and self._is_scrubbing:
            self._is_scrubbing = False
            # Commit the final value (even if released outside widget)
            final_value = self.value()
            # Hide tooltip
            QToolTip.hideText()
            # Clear stored mouse position
            self._last_mouse_pos = None
            # Only emit if value actually changed
            if final_value != self._scrub_start_value:
                self.value_committed.emit(final_value)
            else:
                # If no change, ensure we're still in sync
                self.setValue(self._current_index)
            # Call parent to handle any slider cleanup
            super().mouseReleaseEvent(event)

    def cancel_scrubbing(self) -> None:
        """Cancel scrubbing and restore original value."""
        if not self._is_scrubbing:
            return
        self._is_scrubbing = False
        self.setValue(self._scrub_start_value)
        self._pending_value = self._scrub_start_value
        self._last_mouse_pos = None
        QToolTip.hideText()
        self.scrubbing_cancelled.emit()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events.

        Args:
            event: Key event.
        """
        if event.key() == Qt.Key.Key_Escape and self._is_scrubbing:
            self.cancel_scrubbing()
            event.accept()
            return
        super().keyPressEvent(event)

    def _update_tooltip_from_slider_value(self) -> None:
        """Update tooltip based on current slider value."""
        if not self._is_scrubbing:
            return

        current_value = self.value()
        tooltip_text = self._get_sample_tooltip(current_value)

        # Get mouse position for tooltip display
        if self._last_mouse_pos is not None:
            # Use stored mouse position
            local_pos = self._last_mouse_pos
        else:
            # Fallback to cursor position
            cursor = QCursor()
            local_pos = self.mapFromGlobal(cursor.pos())
            if not self.rect().contains(local_pos):
                # Fallback to center of slider if cursor is outside
                local_pos = self.rect().center()

        # Convert to global coordinates for tooltip
        global_pos = self.mapToGlobal(local_pos)
        # Offset tooltip slightly above cursor
        global_pos.setY(global_pos.y() - 30)

        QToolTip.showText(global_pos, tooltip_text, self)
