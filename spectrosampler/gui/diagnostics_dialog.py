"""Diagnostics dialog for surfacing environment and media tool details."""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

try:  # QtMultimedia is optional in headless test environments
    from PySide6.QtMultimedia import QAudioDevice, QMediaDevices
except ImportError:  # pragma: no cover - handled gracefully in diagnostics
    QAudioDevice = None  # type: ignore[misc]
    QMediaDevices = None  # type: ignore[misc]

if TYPE_CHECKING:  # pragma: no cover
    from spectrosampler.gui.theme import ThemeManager


@dataclass(slots=True)
class FFmpegDiagnostics:
    """Structured FFmpeg details for display and testing."""

    available: bool
    summary: str
    executable: str | None = None
    raw_output: str | None = None


def _collect_ffmpeg_details() -> FFmpegDiagnostics:
    """Return FFmpeg availability and version information."""

    exe = shutil.which("ffmpeg")
    if not exe:
        return FFmpegDiagnostics(
            available=False,
            summary="FFmpeg executable not found on PATH.",
            executable=None,
        )

    try:
        proc = subprocess.run(
            [exe, "-version"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:  # pragma: no cover - defensive
        return FFmpegDiagnostics(
            available=False,
            summary=f"Failed to launch FFmpeg: {exc}",
            executable=exe,
        )

    output = (proc.stdout or proc.stderr or "").strip()
    first_line = (
        output.splitlines()[0].strip() if output else "FFmpeg reachable (no version output)."
    )
    available = proc.returncode == 0
    summary = first_line if available else f"FFmpeg returned exit code {proc.returncode}."
    return FFmpegDiagnostics(
        available=available,
        summary=summary,
        executable=exe,
        raw_output=output or None,
    )


def _format_audio_device(device: QAudioDevice, *, default_id: bytes | None) -> dict[str, Any]:
    """Return serialisable information about an audio device."""

    preferred = device.preferredFormat()
    return {
        "name": device.description(),
        "is_default": device.id().data() == (default_id or b""),
        "sample_rate": preferred.sampleRate(),
        "channels": preferred.channelCount(),
    }


def _collect_audio_device_details() -> dict[str, Any]:
    """Return details about audio input/output availability."""

    if QMediaDevices is None or QAudioDevice is None:
        return {
            "status": "unavailable",
            "reason": "QtMultimedia modules are not available in this environment.",
            "outputs": [],
            "inputs": [],
        }

    # Qt requires an application instance; ensure one exists before probing.
    from PySide6.QtCore import QCoreApplication

    if QCoreApplication.instance() is None:
        return {
            "status": "unavailable",
            "reason": "Qt application instance not initialised.",
            "outputs": [],
            "inputs": [],
        }

    try:
        default_output = QMediaDevices.defaultAudioOutput()
        default_input = QMediaDevices.defaultAudioInput()
        default_output_id = default_output.id().data() if default_output else None  # type: ignore[attr-defined]
        default_input_id = default_input.id().data() if default_input else None  # type: ignore[attr-defined]
        outputs = [
            _format_audio_device(device, default_id=default_output_id)
            for device in QMediaDevices.audioOutputs()
        ]
        inputs = [
            _format_audio_device(device, default_id=default_input_id)
            for device in QMediaDevices.audioInputs()
        ]
    except RuntimeError as exc:  # pragma: no cover - defensive logging
        return {
            "status": "error",
            "reason": f"Failed to enumerate audio devices: {exc}",
            "outputs": [],
            "inputs": [],
        }

    return {
        "status": "ok",
        "outputs": outputs,
        "inputs": inputs,
    }


def collect_diagnostics_data() -> dict[str, Any]:
    """Gather diagnostics details for display and testing."""

    ffmpeg = _collect_ffmpeg_details()
    audio_devices = _collect_audio_device_details()

    env = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "executable": sys.executable,
    }

    try:  # PySide6 provides a version attribute on the package root
        import PySide6

        env["pyside6"] = PySide6.__version__  # type: ignore[attr-defined]
    except Exception:  # pragma: no cover - best effort only
        env["pyside6"] = "unknown"

    return {
        "ffmpeg": ffmpeg,
        "audio_devices": audio_devices,
        "environment": env,
    }


def _build_summary_text(data: dict[str, Any]) -> str:
    """Return a human-readable summary string for diagnostics."""

    lines: list[str] = []
    ffmpeg: FFmpegDiagnostics = data["ffmpeg"]

    lines.append("FFmpeg")
    status = "Available" if ffmpeg.available else "Unavailable"
    lines.append(f"  Status: {status}")
    lines.append(f"  Details: {ffmpeg.summary}")
    if ffmpeg.executable:
        lines.append(f"  Executable: {ffmpeg.executable}")
    if ffmpeg.raw_output and ffmpeg.available:
        lines.append("  Version Output:")
        for line in ffmpeg.raw_output.splitlines():
            lines.append(f"    {line}")

    lines.append("")
    lines.append("Environment")
    env: dict[str, Any] = data["environment"]
    for key in ("python", "pyside6", "platform", "executable"):
        value = env.get(key, "unknown")
        lines.append(f"  {key.capitalize()}: {value}")

    lines.append("")
    lines.append("Audio Outputs")
    devices = data["audio_devices"]
    outputs: Iterable[dict[str, Any]] = devices.get("outputs", []) or []
    if devices.get("status") != "ok":
        reason = devices.get("reason", "Audio device information unavailable.")
        lines.append(f"  Status: {devices.get('status', 'unavailable')}")
        lines.append(f"  Reason: {reason}")
    elif not outputs:
        lines.append("  None detected.")
    else:
        for device in outputs:
            default_marker = " (Default)" if device.get("is_default") else ""
            lines.append(f"  - {device.get('name', 'Unknown')}{default_marker}")
            lines.append(
                f"    {device.get('channels', '?')} channels @ {device.get('sample_rate', '?')} Hz"
            )

    inputs: Iterable[dict[str, Any]] = devices.get("inputs", []) or []
    lines.append("")
    lines.append("Audio Inputs")
    if devices.get("status") != "ok":
        reason = devices.get("reason", "Audio device information unavailable.")
        lines.append(f"  Status: {devices.get('status', 'unavailable')}")
        lines.append(f"  Reason: {reason}")
    elif not inputs:
        lines.append("  None detected.")
    else:
        for device in inputs:
            default_marker = " (Default)" if device.get("is_default") else ""
            lines.append(f"  - {device.get('name', 'Unknown')}{default_marker}")
            lines.append(
                f"    {device.get('channels', '?')} channels @ {device.get('sample_rate', '?')} Hz"
            )

    return "\n".join(lines)


class DiagnosticsDialog(QDialog):
    """Modal dialog that renders diagnostics information."""

    def __init__(self, parent: QDialog | None = None, *, theme_manager: ThemeManager | None = None):
        super().__init__(parent)
        self.setWindowTitle("Diagnostics")
        self.setModal(True)
        self.resize(640, 480)

        layout = QVBoxLayout()

        self._text_area = QPlainTextEdit()
        self._text_area.setReadOnly(True)
        self._text_area.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self._text_area)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)

        copy_button = QPushButton("Copy to Clipboard")
        copy_button.clicked.connect(self._copy_to_clipboard)

        footer = QHBoxLayout()
        footer.addWidget(copy_button)
        footer.addStretch()
        footer.addWidget(buttons)
        layout.addLayout(footer)

        self.setLayout(layout)

        if theme_manager is not None:
            self._apply_theme(theme_manager)

        self._refresh_contents()

    def _refresh_contents(self) -> None:
        """Refresh the diagnostic information presented to the user."""

        data = collect_diagnostics_data()
        self._text_area.setPlainText(_build_summary_text(data))

    def _copy_to_clipboard(self) -> None:
        """Copy the diagnostics summary to the clipboard."""

        text = self._text_area.toPlainText()
        if not text:
            return
        from PySide6.QtWidgets import QApplication

        clipboard = QApplication.clipboard()
        clipboard.setText(text, mode=clipboard.Mode.Clipboard)

    def reject(self) -> None:  # noqa: D401
        """Close the dialog when the Close button is pressed."""

        super().reject()

    @staticmethod
    def _color_to_hex(color: Any, default: str) -> str:
        """Convert a QColor or color-like object to hex for stylesheets."""

        if isinstance(color, QColor):
            return color.name()
        if isinstance(color, str) and color.startswith("#"):
            return color
        return default

    def _apply_theme(self, theme_manager: ThemeManager) -> None:
        """Apply the active theme palette to the dialog widgets."""

        palette_dict = getattr(theme_manager, "palette", {}) or {}

        bg_hex = self._color_to_hex(palette_dict.get("background"), "#1E1E1E")
        text_hex = self._color_to_hex(palette_dict.get("text"), "#CCCCCC")
        secondary_hex = self._color_to_hex(palette_dict.get("background_secondary"), bg_hex)
        border_hex = self._color_to_hex(palette_dict.get("selection_border"), text_hex)

        stylesheet = f"""
            QDialog {{
                background-color: {bg_hex};
                color: {text_hex};
            }}
            QPlainTextEdit {{
                background-color: {secondary_hex};
                color: {text_hex};
                border: 1px solid {border_hex};
            }}
            QPushButton {{
                background-color: {secondary_hex};
                color: {text_hex};
                border: 1px solid {border_hex};
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: {border_hex};
                color: #000000;
            }}
        """
        self.setStyleSheet(stylesheet)
