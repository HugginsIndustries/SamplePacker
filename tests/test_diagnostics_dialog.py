"""Diagnostics dialog data collection tests."""

from __future__ import annotations

from types import SimpleNamespace

from spectrosampler.gui.diagnostics_dialog import collect_diagnostics_data


def test_collect_diagnostics_handles_missing_ffmpeg(monkeypatch):
    """collect_diagnostics_data should report FFmpeg absence gracefully."""

    monkeypatch.setattr("spectrosampler.gui.diagnostics_dialog.shutil.which", lambda exe: None)

    data = collect_diagnostics_data()
    ffmpeg = data["ffmpeg"]

    assert not ffmpeg.available
    assert "not found" in ffmpeg.summary.lower()

    devices = data["audio_devices"]
    assert "status" in devices
    assert isinstance(devices.get("outputs"), list)
    assert isinstance(devices.get("inputs"), list)


def test_collect_diagnostics_returns_ffmpeg_summary(monkeypatch):
    """collect_diagnostics_data should capture FFmpeg version output."""

    monkeypatch.setattr(
        "spectrosampler.gui.diagnostics_dialog.shutil.which", lambda exe: "/usr/bin/ffmpeg"
    )

    def fake_run(cmd, capture_output, text, check):
        return SimpleNamespace(returncode=0, stdout="ffmpeg version 6.0-abc\nCopyright")

    monkeypatch.setattr("spectrosampler.gui.diagnostics_dialog.subprocess.run", fake_run)

    data = collect_diagnostics_data()
    ffmpeg = data["ffmpeg"]

    assert ffmpeg.available
    assert ffmpeg.summary.startswith("ffmpeg version")
    assert "ffmpeg version 6.0-abc" in (ffmpeg.raw_output or "")
