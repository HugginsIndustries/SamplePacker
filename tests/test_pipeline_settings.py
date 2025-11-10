"""Tests for processing settings behaviour."""

from spectrosampler.pipeline_settings import ProcessingSettings


def test_processing_settings_clamps_max_samples_upper_bound() -> None:
    """Ensure max_samples never exceeds the UI-supported limit."""
    settings = ProcessingSettings(max_samples=20000)
    assert settings.max_samples == 10000


def test_processing_settings_allows_zero_max_samples() -> None:
    """Zero should still disable the cap after clamping logic runs."""
    settings = ProcessingSettings(max_samples=-5)
    assert settings.max_samples == 0
