"""Edge-case regression tests covering audio I/O boundary conditions."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from spectrosampler.audio_io import FFmpegError, get_audio_info
from spectrosampler.detectors.base import Segment
from spectrosampler.export import export_sample


def _write_sine_wave(path: Path, duration_sec: float, sample_rate: int = 16_000) -> None:
    """Generate a deterministic sine wave for testing."""

    samples = max(1, int(sample_rate * duration_sec))
    timeline = np.arange(samples, dtype=np.float64) / sample_rate
    wave = 0.1 * np.sin(2 * np.pi * 440.0 * timeline)
    sf.write(path, wave, sample_rate)


def test_export_sample_supports_sub_10ms_segments(tmp_path: Path) -> None:
    """Ensure export_sample can extract extremely short slices without errors."""

    src = tmp_path / "micro.wav"
    _write_sine_wave(src, duration_sec=0.02)

    segment = Segment(start=0.001, end=0.009, detector="test", score=0.5)
    out = tmp_path / "micro_out.wav"

    export_sample(src, out, segment, format="wav")

    assert out.exists()
    data, sr = sf.read(out)
    assert sr == 16_000
    assert data.size > 0
    duration = data.size / sr
    assert duration == pytest.approx(segment.duration(), abs=0.004)


def test_export_sample_trims_padding_to_audio_duration(tmp_path: Path) -> None:
    """Confirm padding requests never exceed the available audio bounds."""

    src = tmp_path / "padded.wav"
    _write_sine_wave(src, duration_sec=3.0)

    segment = Segment(start=0.5, end=2.9, detector="test", score=0.75)
    out = tmp_path / "padded_out.wav"

    export_sample(
        src,
        out,
        segment,
        pre_pad_ms=800,
        post_pad_ms=800,
        format="wav",
    )

    data, sr = sf.read(out)
    duration = data.size / sr
    # The output should never exceed the total source length of 3 seconds.
    assert duration <= 3.0 + 0.01
    # Padding should still extend the clip beyond the original segment duration.
    assert duration > segment.duration()


def test_get_audio_info_reports_long_duration(tmp_path: Path) -> None:
    """Validate ffprobe metadata for long-form recordings stays accurate."""

    src = tmp_path / "long.wav"
    _write_sine_wave(src, duration_sec=45.0)

    info = get_audio_info(src)

    assert info["duration"] == pytest.approx(45.0, rel=0.02)
    assert info["sample_rate"] == 16_000
    assert info["channels"] == 1


def test_get_audio_info_rejects_corrupt_file(tmp_path: Path) -> None:
    """Confirm ffprobe failures result in FFmpegError for caller handling."""

    bogus = tmp_path / "corrupt.wav"
    bogus.write_text("not an audio file", encoding="utf-8")

    with pytest.raises(FFmpegError):
        get_audio_info(bogus)
