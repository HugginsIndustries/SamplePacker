"""Overview manager for background spectrogram overview generation."""

import logging
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal

from spectrosampler.gui.spectrogram_tiler import SpectrogramTile, SpectrogramTiler

logger = logging.getLogger(__name__)


class OverviewWorker(QThread):
    """Worker thread for generating spectrogram overview."""

    progress = Signal(str)  # Emitted with progress message
    finished = Signal(SpectrogramTile)  # Emitted with generated tile
    error = Signal(str)  # Emitted with error message

    def __init__(
        self,
        tiler: SpectrogramTiler,
        audio_path: Path,
        duration: float,
        sample_rate: int | None = None,
        parent: QObject | None = None,
    ):
        """Initialize overview worker.

        Args:
            tiler: SpectrogramTiler instance.
            audio_path: Path to audio file.
            duration: Audio file duration in seconds.
            sample_rate: Target sample rate. If None, uses file's sample rate.
            parent: Parent QObject.
        """
        super().__init__(parent)
        self._tiler = tiler
        self._audio_path = audio_path
        self._duration = duration
        self._sample_rate = sample_rate
        self._cancelled = False

    def cancel(self) -> None:
        """Cancel overview generation."""
        self._cancelled = True

    def run(self) -> None:
        """Run overview generation in background thread."""
        try:
            if self._cancelled:
                return

            self.progress.emit("Loading spectrogram...")

            if self._cancelled:
                return

            # Generate overview in background thread
            overview = self._tiler.generate_overview(
                self._audio_path, self._duration, sample_rate=self._sample_rate
            )

            if not self._cancelled:
                self.finished.emit(overview)
        except (RuntimeError, ValueError, OSError) as e:
            logger.error("Overview generation error: %s", e, exc_info=e)
            if not self._cancelled:
                self.error.emit(str(e))


class OverviewManager(QObject):
    """Manages overview generation in background thread."""

    progress = Signal(str)  # Emitted with progress message
    finished = Signal(SpectrogramTile)  # Emitted with generated tile
    error = Signal(str)  # Emitted with error message

    def __init__(self, parent: QObject | None = None):
        """Initialize overview manager.

        Args:
            parent: Parent QObject.
        """
        super().__init__(parent)
        self._worker: OverviewWorker | None = None
        self._tiler: SpectrogramTiler | None = None

    def start_generation(
        self,
        tiler: SpectrogramTiler,
        audio_path: Path,
        duration: float,
        sample_rate: int | None = None,
    ) -> None:
        """Start overview generation.

        Args:
            tiler: SpectrogramTiler instance.
            audio_path: Path to audio file.
            duration: Audio file duration in seconds.
            sample_rate: Target sample rate. If None, uses file's sample rate.
        """
        # Cancel any existing generation
        if self._worker and self._worker.isRunning():
            self.cancel()

        # Store tiler reference
        self._tiler = tiler

        # Create and start worker thread
        self._worker = OverviewWorker(tiler, audio_path, duration, sample_rate, self)
        self._worker.progress.connect(self.progress.emit)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.error.connect(self._on_worker_error)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.error.connect(self._worker.deleteLater)

        # Start worker thread
        self._worker.start()

    def cancel(self) -> None:
        """Cancel overview generation."""
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            # Wait for thread to finish, but don't block indefinitely
            if not self._worker.wait(2000):  # Wait up to 2 seconds
                logger.warning("Overview worker thread did not finish in time, terminating")
                self._worker.terminate()
                self._worker.wait(1000)  # Wait for termination
            # Clean up worker
            self._worker.deleteLater()
            self._worker = None

    def is_generating(self) -> bool:
        """Check if overview generation is in progress.

        Returns:
            True if generation is in progress, False otherwise.
        """
        return self._worker is not None and self._worker.isRunning()

    def _on_worker_finished(self, tile: SpectrogramTile) -> None:
        """Handle worker finished signal.

        Args:
            tile: Generated overview tile.
        """
        # Clean up worker reference
        self._worker = None
        # Emit finished signal (worker will be deleted via deleteLater)
        self.finished.emit(tile)

    def _on_worker_error(self, error_msg: str) -> None:
        """Handle worker error signal.

        Args:
            error_msg: Error message.
        """
        # Clean up worker reference
        self._worker = None
        # Emit error signal (worker will be deleted via deleteLater)
        self.error.emit(error_msg)
