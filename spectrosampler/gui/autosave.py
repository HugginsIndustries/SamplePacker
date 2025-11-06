"""Auto-save manager for periodic automatic saves."""

import logging
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, QTimer, Signal

from spectrosampler.gui.project import save_project

logger = logging.getLogger(__name__)


class AutoSaveManager(QObject):
    """Manages automatic periodic saves to temporary files."""

    autosave_completed = Signal(Path)  # Emitted when auto-save completes successfully
    autosave_error = Signal(str)  # Emitted when auto-save fails

    def __init__(self, parent: QObject | None = None):
        """Initialize auto-save manager.

        Args:
            parent: Parent QObject.
        """
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_timer_timeout)
        self._autosave_dir = self._get_autosave_directory()
        self._autosave_dir.mkdir(parents=True, exist_ok=True)
        self._current_project_path: Path | None = None
        self._project_data_callback = None  # Callback to get current project data
        self._project_modified_callback = None  # Callback to check if project is modified

    def _get_autosave_directory(self) -> Path:
        """Get auto-save directory path.

        Returns:
            Path to auto-save directory.
        """
        temp_dir = Path(tempfile.gettempdir())
        autosave_dir = temp_dir / "spectrosampler_autosave"
        return autosave_dir

    def get_autosave_files(self) -> list[Path]:
        """Get list of all auto-save files.

        Returns:
            List of auto-save file paths, sorted by modification time (newest first).
        """
        if not self._autosave_dir.exists():
            return []

        autosave_files = [
            f
            for f in self._autosave_dir.iterdir()
            if f.is_file() and f.suffix == ".ssproj" and f.name.startswith("autosave_")
        ]
        autosave_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return autosave_files

    def start(self, interval_minutes: int = 5) -> None:
        """Start auto-save timer.

        Args:
            interval_minutes: Auto-save interval in minutes.
        """
        if not self._timer.isActive():
            interval_ms = interval_minutes * 60 * 1000
            self._timer.start(interval_ms)
            logger.debug(f"Auto-save started with interval: {interval_minutes} minutes")

    def stop(self) -> None:
        """Stop auto-save timer."""
        if self._timer.isActive():
            self._timer.stop()
            logger.debug("Auto-save stopped")

    def set_project_data_callback(self, callback: Any) -> None:
        """Set callback to get current project data.

        Args:
            callback: Callback function that returns ProjectData or None.
        """
        self._project_data_callback = callback

    def set_project_modified_callback(self, callback: Any) -> None:
        """Set callback to check if project is modified.

        Args:
            callback: Callback function that returns True if project is modified, False otherwise.
        """
        self._project_modified_callback = callback

    def save_now(self) -> bool:
        """Immediately save current project if modified.

        Returns:
            True if save was successful, False otherwise.
        """
        if not self._project_data_callback:
            return False

        # Check if project is modified
        if self._project_modified_callback:
            if not self._project_modified_callback():
                return False  # Project not modified, don't save

        project_data = self._project_data_callback()
        if project_data is None:
            return False

        # Only save if project has been loaded (has audio file)
        if not project_data.audio_path:
            return False

        try:
            # Generate auto-save filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            autosave_path = self._autosave_dir / f"autosave_{timestamp}.ssproj"

            # Save project
            save_project(project_data, autosave_path)

            # Clean up old auto-saves (keep last 3)
            self.cleanup_old_autosaves(keep_count=3)

            logger.debug(f"Auto-save completed: {autosave_path}")
            self.autosave_completed.emit(autosave_path)
            return True
        except Exception as e:
            error_msg = f"Auto-save failed: {e}"
            logger.error(error_msg, exc_info=True)
            self.autosave_error.emit(error_msg)
            return False

    def _on_timer_timeout(self) -> None:
        """Handle auto-save timer timeout."""
        self.save_now()

    def cleanup_old_autosaves(self, keep_count: int = 3) -> None:
        """Clean up old auto-save files, keeping only the most recent ones.

        Args:
            keep_count: Number of most recent auto-save files to keep.
        """
        autosave_files = self.get_autosave_files()

        if len(autosave_files) <= keep_count:
            return

        # Delete older files
        files_to_delete = autosave_files[keep_count:]
        for file_path in files_to_delete:
            try:
                file_path.unlink()
                logger.debug(f"Deleted old auto-save file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete auto-save file {file_path}: {e}")

    def cleanup_all_autosaves(self) -> None:
        """Delete all auto-save files."""
        autosave_files = self.get_autosave_files()
        for file_path in autosave_files:
            try:
                file_path.unlink()
                logger.debug(f"Deleted auto-save file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete auto-save file {file_path}: {e}")
