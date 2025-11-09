"""Detection manager for background sample detection."""

import logging
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, QThread, Signal

from spectrosampler.audio_io import FFmpegError
from spectrosampler.gui.pipeline_wrapper import PipelineWrapper

logger = logging.getLogger(__name__)


class DetectionWorker(QThread):
    """Legacy worker thread (unused when using process pool)."""

    progress = Signal(str)
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, pipeline_wrapper: PipelineWrapper, output_dir: Path | None = None):
        super().__init__()
        self.pipeline_wrapper = pipeline_wrapper
        self.output_dir = output_dir
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        try:
            self.progress.emit("Detecting samples...")
            result = self.pipeline_wrapper.detect_samples(self.output_dir)
            if not self._cancelled:
                self.finished.emit(result)
        except (FFmpegError, OSError, RuntimeError, ValueError) as exc:
            logger.error("Detection error: %s", exc, exc_info=exc)
            if not self._cancelled:
                self.error.emit(str(exc))


class DetectionManager(QObject):
    """Manages detection processing in background thread."""

    progress = Signal(str)  # Emitted with progress message
    finished = Signal(dict)  # Emitted with processing results
    error = Signal(str)  # Emitted with error message

    def __init__(self, parent: QObject | None = None):
        """Initialize detection manager.

        Args:
            parent: Parent QObject.
        """
        super().__init__(parent)
        self._worker: DetectionWorker | None = None
        self._future = None
        self._pipeline_wrapper: PipelineWrapper | None = None

    def set_pipeline_wrapper(self, pipeline_wrapper: PipelineWrapper) -> None:
        """Set pipeline wrapper.

        Args:
            pipeline_wrapper: PipelineWrapper instance.
        """
        self._pipeline_wrapper = pipeline_wrapper

    def start_detection(self, output_dir: Path | None = None) -> None:
        """Start detection.

        Args:
            output_dir: Optional output directory for temporary files.
        """
        if self._pipeline_wrapper is None:
            self.error.emit("No pipeline wrapper set")
            return

        # If an existing future is running, ignore or cancel
        self.progress.emit("Detecting samples...")
        try:

            def _cb(result: dict[str, Any]) -> None:
                self.finished.emit(result)

            self._future = self._pipeline_wrapper.detect_samples_async(
                output_dir=output_dir, callback=_cb
            )
        except (FFmpegError, OSError, RuntimeError, ValueError) as exc:
            logger.error("Detection start failed: %s", exc, exc_info=exc)
            self.error.emit(str(exc))

    def cancel_detection(self) -> None:
        """Cancel detection processing."""
        # ProcessPoolExecutor futures can't be easily cancelled once started; best-effort.
        if self._future:
            try:
                self._future.cancel()
            except RuntimeError as exc:
                logger.debug("Cancel detection future failed: %s", exc, exc_info=exc)

    def is_processing(self) -> bool:
        """Check if processing is in progress.

        Returns:
            True if processing.
        """
        if self._future is None:
            return False
        return not self._future.done()
