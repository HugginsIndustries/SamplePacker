"""Tests for spectrogram widget playback indicator behaviour."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication

from spectrosampler.gui.spectrogram_widget import SpectrogramWidget


def _ensure_qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_set_playback_state_throttles_updates(monkeypatch):
    """set_playback_state should avoid redundant redraws and clamp to duration."""
    app = _ensure_qapp()
    widget = SpectrogramWidget()
    widget.set_duration(5.0)

    call_count = {"value": 0}

    def fake_update() -> None:
        call_count["value"] += 1

    monkeypatch.setattr(widget, "_update_overlays_only", fake_update)

    widget.set_playback_state(0, 1.0, paused=False)
    assert call_count["value"] == 1

    # Difference within tolerance should not trigger another draw.
    widget.set_playback_state(0, 1.00001, paused=False)
    assert call_count["value"] == 1

    widget.set_playback_state(0, 2.0, paused=False)
    assert call_count["value"] == 2

    # Values beyond duration should clamp and still trigger.
    widget.set_playback_state(0, 10.0, paused=False)
    assert call_count["value"] == 3

    # Clearing indicator triggers update.
    widget.set_playback_state(None, None)
    assert call_count["value"] == 4

    widget.deleteLater()
    app.processEvents()
