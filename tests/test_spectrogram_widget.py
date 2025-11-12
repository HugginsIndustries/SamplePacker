"""Tests for spectrogram widget playback indicator behaviour."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from spectrosampler.detectors.base import Segment
from spectrosampler.gui.spectrogram_widget import SpectrogramWidget

pytestmark = [
    pytest.mark.filterwarnings("ignore:Attempting to set identical low and high xlims"),
]


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


def test_fit_selection_frames_current_segment():
    """fit_selection should zoom to the selected segment range with margin."""

    app = _ensure_qapp()
    widget = SpectrogramWidget()
    widget.set_duration(30.0)

    segments = [
        Segment(start=5.0, end=10.0, detector="vad", score=0.9),
        Segment(start=14.0, end=20.0, detector="vad", score=0.5),
    ]
    widget.set_segments(segments)
    widget.set_selected_index(0)

    assert widget.fit_selection()
    assert widget._start_time <= 5.0
    assert widget._end_time >= 10.0

    # Multiple selections should cover the entire combined range.
    assert widget.fit_selection([0, 1])
    assert widget._start_time <= 5.0
    assert widget._end_time >= 20.0

    widget.deleteLater()
    app.processEvents()


def test_set_selected_indexes_emits_and_filters():
    """set_selected_indexes should emit selection_changed with sanitized indexes."""

    app = _ensure_qapp()
    widget = SpectrogramWidget()
    widget.set_duration(15.0)

    segments = [
        Segment(start=0.0, end=2.0, detector="a", score=0.5),
        Segment(start=2.5, end=5.0, detector="b", score=0.6),
        Segment(start=6.0, end=8.0, detector="c", score=0.7),
    ]
    widget.set_segments(segments)

    selection_events: list[list[int]] = []
    active_events: list[int] = []

    widget.selection_changed.connect(selection_events.append)
    widget.sample_selected.connect(active_events.append)

    widget.set_selected_indexes([0, 2, 5, -1])
    assert selection_events[-1] == [0, 2]
    assert widget._selected_indexes == {0, 2}
    assert active_events[-1] == 2

    widget.set_selected_indexes([])
    assert selection_events[-1] == []

    widget.deleteLater()
    app.processEvents()


def test_selection_anchor_tracks_latest_active():
    """Anchor should follow the latest selected sample for subsequent shift operations."""

    app = _ensure_qapp()
    widget = SpectrogramWidget()
    widget.set_duration(20.0)

    segments = [
        Segment(start=idx * 2.0, end=(idx + 1) * 2.0 - 0.1, detector="t", score=0.5)
        for idx in range(5)
    ]
    widget.set_segments(segments)

    widget.set_selected_indexes([1])
    assert widget._selection_anchor == 1

    widget.set_selected_indexes([1, 2, 3], anchor=3)
    assert widget._selection_anchor == 3

    widget.set_selected_indexes([1, 2], anchor=None)
    assert widget._selection_anchor == 2

    widget.set_selected_indexes([])
    assert widget._selection_anchor is None

    widget.deleteLater()
    app.processEvents()


def test_ctrl_shift_sequence_uses_latest_anchor():
    """Ctrl/Shift selection should extend from the most recently focused sample."""

    app = _ensure_qapp()
    widget = SpectrogramWidget()
    widget.set_duration(30.0)

    segments = [
        Segment(start=float(i * 2), end=float(i * 2 + 1), detector="t", score=0.5) for i in range(8)
    ]
    widget.set_segments(segments)

    widget.handle_selection_click(1, ctrl=False, shift=False)
    widget.handle_selection_click(6, ctrl=True, shift=False)
    widget.handle_selection_click(3, ctrl=True, shift=False)
    widget.handle_selection_click(5, ctrl=False, shift=True)

    assert sorted(widget._selected_indexes) == [1, 3, 4, 5, 6]
    assert widget._selection_anchor == 5
    assert widget._selected_index == 5

    widget.deleteLater()
    app.processEvents()
