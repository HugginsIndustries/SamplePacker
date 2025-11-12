"""Tests for settings persistence helpers and validation."""

from spectrosampler.gui.settings import SettingsManager
from spectrosampler.pipeline_settings import ProcessingSettings


def test_detection_max_samples_persistent_and_clamped(tmp_path, monkeypatch):
    """Max samples should persist between manager instances and stay within 1-10,000."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    manager = SettingsManager()
    manager.set_detection_max_samples(10_000)
    assert manager.get_detection_max_samples() == 10_000

    # Values outside the allowed range should clamp.
    manager.set_detection_max_samples(0)
    assert manager.get_detection_max_samples() == 1

    manager.set_detection_max_samples(15_000)
    assert manager.get_detection_max_samples() == 10_000

    manager.set_detection_max_samples(5_432)

    # A fresh manager should read the persisted value.
    other_manager = SettingsManager()
    assert other_manager.get_detection_max_samples() == 5_432


def test_processing_settings_validation_defaults_are_valid():
    """Default settings should produce no validation issues."""
    settings = ProcessingSettings()
    assert settings.validate() == []


def test_processing_settings_validation_detects_duration_order():
    """Validation should fail when min duration exceeds max duration."""
    settings = ProcessingSettings(min_dur_ms=5000.0, max_dur_ms=1000.0)
    issues = settings.validate()
    assert issues
    assert any("Minimum duration" in issue.message for issue in issues)


def test_processing_settings_validation_detects_filter_bounds():
    """High-pass filter must be lower than low-pass filter."""
    settings = ProcessingSettings(hp=5000.0, lp=2000.0)
    issues = settings.validate()
    assert issues
    assert any("High-pass frequency must be lower" in issue.message for issue in issues)
