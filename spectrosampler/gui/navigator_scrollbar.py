"""Navigator scrollbar widget (Bitwig-style) showing spectrogram overview."""

import numpy as np
from PySide6.QtCore import QRect, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen
from PySide6.QtWidgets import QWidget

from spectrosampler.gui.spectrogram_tiler import SpectrogramTile


class NavigatorScrollbar(QWidget):
    """Navigator scrollbar widget with spectrogram preview."""

    view_changed = Signal(float, float)  # Emitted when view changes (start_time, end_time)
    view_resized = Signal(float, float)  # Emitted when view is resized (start_time, end_time)

    def __init__(self, parent: QWidget | None = None):
        """Initialize navigator scrollbar.

        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        self.setMinimumHeight(40)
        # Enable hover cursor updates without mouse press
        self.setMouseTracking(True)
        self._duration = 0.0
        self._view_start_time = 0.0
        self._view_end_time = 0.0
        self._overview_tile: SpectrogramTile | None = None
        self._overview_image: QImage | None = None
        self._sample_markers: list[tuple[float, float, QColor]] = []  # (start, end, color)
        self._dragging = False
        self._drag_start_x = 0
        self._drag_start_view_start = 0.0
        self._resizing_left = False
        self._resizing_right = False
        self._resize_handle_width = 8
        self._theme_colors = {
            "background": QColor(0x1E, 0x1E, 0x1E),
            "overview": QColor(0x25, 0x25, 0x26),
            "view_indicator": QColor(0xFF, 0xFF, 0xFF, 0x40),  # Semi-transparent white
            "view_border": QColor(0xFF, 0xFF, 0xFF, 0x80),
            "handle": QColor(0xFF, 0xFF, 0xFF, 0xA0),
            "marker": QColor(0x00, 0xFF, 0x6A, 0x80),
        }
        self._show_disabled: bool = True
        # Independent navigator display window (visual zoom only)
        self._nav_start_time = 0.0
        self._nav_end_time = 0.0

    def set_duration(self, duration: float) -> None:
        """Set total audio duration.

        Args:
            duration: Duration in seconds.
        """
        self._duration = max(0.0, duration)
        # Reset navigator window to full range
        self._nav_start_time = 0.0
        self._nav_end_time = self._duration
        self.update()

    def set_view_range(self, start_time: float, end_time: float) -> None:
        """Set visible view range.

        Args:
            start_time: Start time in seconds.
            end_time: End time in seconds.
        """
        self._view_start_time = max(0.0, min(start_time, self._duration))
        self._view_end_time = max(self._view_start_time, min(end_time, self._duration))
        self.update()

    def set_overview_tile(self, tile: SpectrogramTile | None) -> None:
        """Set overview spectrogram tile.

        Args:
            tile: SpectrogramTile with overview data.
        """
        self._overview_tile = tile
        self._update_overview_image()
        self.update()

    def _update_overview_image(self) -> None:
        """Update overview image from tile.

        Uses precomputed RGBA if available and scales with QImage for speed.
        """
        if self._overview_tile is None:
            self._overview_image = None
            return

        tile = self._overview_tile
        rgba = getattr(tile, "rgba", None)
        if rgba is None or rgba.size == 0:
            # Fallback to placeholder when no rgba present
            self._overview_image = None
            return
        # rgba is (freq x time x 4). Flip vertically so low freq at bottom.
        arr = np.flip(rgba, axis=0)  # (freq, time, 4)
        # Ensure C-contiguous buffer in (height, width, 4)
        arr = np.ascontiguousarray(arr)
        h = int(arr.shape[0])  # freq
        w = int(arr.shape[1])  # time
        bytes_per_line = 4 * w
        image = QImage(arr.data, w, h, bytes_per_line, QImage.Format.Format_RGBA8888)
        # Detach from numpy buffer
        self._overview_image = image.copy()

    def set_sample_markers(self, markers: list[tuple[float, float, QColor]]) -> None:
        """Set sample markers to display.

        Args:
            markers: List of (start_time, end_time, color) tuples.
        """
        self._sample_markers = markers
        self.update()

    def set_show_disabled(self, show: bool) -> None:
        """Set whether disabled markers should be drawn when provided by caller."""
        self._show_disabled = bool(show)
        self.update()

    def set_theme_colors(self, colors: dict[str, QColor]) -> None:
        """Set theme colors.

        Args:
            colors: Dictionary with color definitions.
        """
        self._theme_colors.update(colors)
        self.update()

    def paintEvent(self, event) -> None:
        """Paint navigator scrollbar."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        # Fill background
        painter.fillRect(self.rect(), self._theme_colors["background"])

        if self._duration <= 0:
            return

        # Draw overview spectrogram (respect navigator window zoom)
        if self._overview_image and not self._overview_image.isNull():
            # Source rect corresponds to [nav_start, nav_end] over full duration
            img_w = self._overview_image.width()
            img_h = self._overview_image.height()
            if self._duration > 0 and img_w > 0 and img_h > 0:
                nav_start = max(0.0, min(self._nav_start_time, self._duration))
                nav_end = max(nav_start, min(self._nav_end_time, self._duration))
                src_x = int((nav_start / self._duration) * img_w)
                src_w = max(1, int(((nav_end - nav_start) / self._duration) * img_w))
                src_rect = QRectF(src_x, 0, src_w, img_h)
                dst_rect = QRectF(0, 0, width, height)
                painter.drawImage(dst_rect, self._overview_image, src_rect)
            else:
                image_rect = QRectF(0, 0, width, height)
                painter.drawImage(image_rect, self._overview_image)
        else:
            # Draw placeholder
            painter.fillRect(self.rect(), self._theme_colors["overview"])

        # Draw sample markers (map times through navigator window)
        if self._sample_markers:
            nav_duration = max(
                1e-6, (self._nav_end_time - self._nav_start_time) if self._duration > 0 else 0.0
            )
            pixels_per_second = width / nav_duration if nav_duration > 0 else 0
            marker_pen = QPen()
            marker_pen.setWidth(2)
            for start_time, end_time, color in self._sample_markers:
                # Map to navigator-local coordinates
                x1 = int((start_time - self._nav_start_time) * pixels_per_second)
                x2 = int((end_time - self._nav_start_time) * pixels_per_second)
                # Clamp to viewport
                x1 = max(0, min(x1, max(0, width - 1)))
                x2 = max(0, min(x2, width))
                # Ensure at least 1px width so markers never disappear
                if x2 <= x1:
                    x2 = min(width, x1 + 1)
                painter.setPen(color)
                painter.drawRect(x1, 0, max(1, x2 - x1), height)

        # Draw view indicator using navigator window mapping
        nav_duration = max(
            1e-6, (self._nav_end_time - self._nav_start_time) if self._duration > 0 else 0.0
        )
        pixels_per_second = width / nav_duration if nav_duration > 0 else 0
        view_x1 = int((self._view_start_time - self._nav_start_time) * pixels_per_second)
        view_x2 = int((self._view_end_time - self._nav_start_time) * pixels_per_second)
        view_x1 = max(0, min(view_x1, width))
        view_x2 = max(view_x1, min(view_x2, width))

        if view_x2 > view_x1:
            # Draw view indicator rectangle
            view_rect = QRect(view_x1, 0, view_x2 - view_x1, height)
            painter.fillRect(view_rect, self._theme_colors["view_indicator"])
            painter.setPen(QPen(self._theme_colors["view_border"], 2))
            painter.drawRect(view_rect)

    def mousePressEvent(self, event) -> None:
        """Handle mouse press for dragging/resizing."""
        if event.button() != Qt.MouseButton.LeftButton:
            return

        x = int(event.position().x())
        width = self.width()
        nav_duration = max(
            1e-6, (self._nav_end_time - self._nav_start_time) if self._duration > 0 else 0.0
        )
        pixels_per_second = width / nav_duration if nav_duration > 0 else 0

        view_x1 = int((self._view_start_time - self._nav_start_time) * pixels_per_second)
        view_x2 = int((self._view_end_time - self._nav_start_time) * pixels_per_second)
        handle_width = self._resize_handle_width

        # Check if clicking on resize handles
        if abs(x - view_x1) < handle_width:
            self._resizing_left = True
            self._dragging = False
            self._drag_start_x = x
            self._drag_start_view_start = self._view_start_time
        elif abs(x - view_x2) < handle_width:
            self._resizing_right = True
            self._dragging = False
            self._drag_start_x = x
            self._drag_start_view_start = self._view_end_time
        elif view_x1 <= x <= view_x2:
            # Clicking in view indicator - drag view
            self._dragging = True
            self._resizing_left = False
            self._resizing_right = False
            self._drag_start_x = x
            self._drag_start_view_start = self._view_start_time
        else:
            # Clicking outside view - jump to position within navigator window
            local_time = (x / pixels_per_second) if pixels_per_second > 0 else 0.0
            time = self._nav_start_time + local_time
            time = max(0.0, min(time, self._duration))
            view_duration = self._view_end_time - self._view_start_time
            new_start = max(0.0, min(time - view_duration / 2, self._duration - view_duration))
            new_end = new_start + view_duration
            self.set_view_range(new_start, new_end)
            self.view_changed.emit(new_start, new_end)

    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move for dragging/resizing and hover cursor updates."""
        x = int(event.position().x())
        width = self.width()
        nav_duration = max(
            1e-6, (self._nav_end_time - self._nav_start_time) if self._duration > 0 else 0.0
        )
        pixels_per_second = width / nav_duration if nav_duration > 0 else 0

        # When not dragging/resizing, update cursor to indicate resizable edges
        if not (self._dragging or self._resizing_left or self._resizing_right):
            if pixels_per_second > 0:
                view_x1 = int((self._view_start_time - self._nav_start_time) * pixels_per_second)
                view_x2 = int((self._view_end_time - self._nav_start_time) * pixels_per_second)
                handle_width = self._resize_handle_width
                if abs(x - view_x1) < handle_width or abs(x - view_x2) < handle_width:
                    self.setCursor(Qt.CursorShape.SizeHorCursor)
                else:
                    self.setCursor(Qt.CursorShape.ArrowCursor)
            return

        if pixels_per_second <= 0:
            return

        dx = x - self._drag_start_x
        dt = dx / pixels_per_second

        if self._resizing_left:
            # Resize left edge
            new_start = max(0.0, min(self._drag_start_view_start + dt, self._view_end_time - 0.1))
            self.set_view_range(new_start, self._view_end_time)
            self.view_resized.emit(new_start, self._view_end_time)
        elif self._resizing_right:
            # Resize right edge
            new_end = max(
                self._view_start_time + 0.1, min(self._drag_start_view_start + dt, self._duration)
            )
            self.set_view_range(self._view_start_time, new_end)
            self.view_resized.emit(self._view_start_time, new_end)
        elif self._dragging:
            # Drag view
            view_duration = self._view_end_time - self._view_start_time
            new_start = max(
                0.0, min(self._drag_start_view_start + dt, self._duration - view_duration)
            )
            new_end = new_start + view_duration
            self.set_view_range(new_start, new_end)
            self.view_changed.emit(new_start, new_end)

    def mouseReleaseEvent(self, event) -> None:
        """Handle mouse release."""
        self._dragging = False
        self._resizing_left = False
        self._resizing_right = False
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def leaveEvent(self, event) -> None:
        """Reset cursor when leaving the widget."""
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def resizeEvent(self, event) -> None:
        """Handle widget resize."""
        super().resizeEvent(event)
        # Only scale existing image; avoid recomputing or re-colormapping
        if self._overview_tile is not None and self._overview_image is None:
            self._update_overview_image()
        self.update()

    def sizeHint(self):
        """Return preferred size."""
        from PySide6.QtCore import QSize

        return QSize(100, 80)

    # Helper to map x to absolute time using navigator window
    def _time_from_x(self, x: float) -> float:
        width = max(1, self.width())
        rel = max(0.0, min(1.0, x / float(width)))
        nav_duration = max(0.0, self._nav_end_time - self._nav_start_time)
        return self._nav_start_time + rel * nav_duration

    def wheelEvent(self, event) -> None:
        """Zoom the navigator window visually around the mouse cursor.

        Does not change the main view; no signals emitted.
        """
        if self._duration <= 0:
            return
        dy = 0
        dx = 0
        try:
            ad = event.angleDelta()
            dy = int(ad.y()) if hasattr(ad, "y") else int(ad.y())
            dx = int(ad.x()) if hasattr(ad, "x") else int(ad.x())
        except Exception:
            dy = dy or 0
            dx = dx or 0
        if dy == 0 and dx == 0:
            try:
                pd = event.pixelDelta()
                dy = int(pd.y()) if hasattr(pd, "y") else int(pd.y())
                dx = int(pd.x()) if hasattr(pd, "x") else int(pd.x())
            except Exception:
                pass
        if dy == 0 and dx == 0:
            return
        # ALT-held: horizontal pan
        if event.modifiers() & Qt.KeyboardModifier.AltModifier:
            nav_start = self._nav_start_time
            nav_end = (
                self._nav_end_time
                if self._nav_end_time > self._nav_start_time
                else max(self._nav_start_time, self._duration)
            )
            nav_dur = max(1e-6, nav_end - nav_start)
            # Determine left/right: prefer vertical delta; fallback to horizontal
            if dy != 0:
                direction = -1 if dy > 0 else 1  # wheel up = pan left
            else:
                direction = 1 if dx > 0 else -1  # right = pan right
            delta = 0.1 * nav_dur * direction
            new_start = max(0.0, min(nav_start + delta, max(0.0, self._duration - nav_dur)))
            self._nav_start_time = new_start
            self._nav_end_time = new_start + nav_dur
            self.update()
            event.accept()
            return

        # Default: zoom around cursor
        step = 1.2
        # Use vertical delta for zoom direction; if zero, use horizontal
        primary = dy if dy != 0 else dx
        zoom = step if primary > 0 else 1.0 / step

        cursor_x = float(event.position().x())
        cursor_time = self._time_from_x(cursor_x)

        nav_start = self._nav_start_time
        nav_end = (
            self._nav_end_time
            if self._nav_end_time > self._nav_start_time
            else max(self._nav_start_time, self._duration)
        )
        nav_dur = max(1e-6, nav_end - nav_start)

        new_dur = max(0.5, min(self._duration, nav_dur / zoom))
        rel = (cursor_time - nav_start) / nav_dur
        rel = max(0.0, min(1.0, rel))
        new_start = cursor_time - rel * new_dur
        new_start = max(0.0, min(new_start, max(0.0, self._duration - new_dur)))
        new_end = new_start + new_dur

        self._nav_start_time = new_start
        self._nav_end_time = new_end
        self.update()
        event.accept()
