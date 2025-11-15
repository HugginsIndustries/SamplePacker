"""Tests for export templating helpers."""

from __future__ import annotations

from spectrosampler.detectors.base import Segment
from spectrosampler.gui.export_models import (
    DEFAULT_FILENAME_TEMPLATE,
    apply_template,
    build_template_context,
    derive_sample_title,
    render_filename_from_template,
)


def test_render_filename_supports_new_tokens() -> None:
    """Filename templates should resolve new tokens like id/title/start/duration."""

    segment = Segment(
        start=0.5,
        end=1.25,
        detector="vad",
        score=0.92,
        attrs={"name": "Lead Vox"},
    )
    rendered = render_filename_from_template(
        template="{id}_{title}_{start}_{duration}",
        base_name="session",
        sample_id="seg-002",
        index=2,
        total=20,
        segment=segment,
        fmt="wav",
        normalized=False,
        pre_pad_ms=25.0,
        post_pad_ms=10.0,
    )
    # Index=2 should map to id "0002" (0-based, zero padded) and values formatted to 3 decimals.
    # With pre_pad_ms=25.0 and post_pad_ms=10.0:
    # start_padded = max(0, 0.5 - 0.025) = 0.475
    # end_padded = 1.25 + 0.010 = 1.26
    # duration_padded = 1.26 - 0.475 = 0.785
    assert rendered == "0002_Lead Vox_0.475_0.785"


def test_template_context_exposes_metadata_and_sample_fields() -> None:
    """Token context should include metadata and sample-table values for notes/templates."""

    segment = Segment(
        start=1.0,
        end=1.5,
        detector="flux",
        score=0.5,
        attrs={"enabled": False, "take": 7},
    )
    title = derive_sample_title(0, segment, fallback="sample")
    context = build_template_context(
        base_name="source",
        sample_id="seg-000",
        index=0,
        total=1,
        segment=segment,
        fmt="flac",
        normalize=True,
        pre_pad_ms=100.0,
        post_pad_ms=50.0,
        title=title,
        artist="SpectroSampler",
        album="Field Notes",
        year=2025,
        sample_rate_hz=48000,
        bit_depth="24",
        channels="stereo",
    )

    assert context["id"] == "0000"  # 0-based indexing
    assert context["title"] == "sample"
    assert context["detector"] == "flux"
    # Attribute tokens should be namespaced with attr_ prefix.
    assert context["attr_take"] == 7

    rendered_notes = apply_template(
        "Title={title}; Artist={artist}; Start={start}; Detector={detector}; Enabled={enabled}",
        context,
    )
    # With pre_pad_ms=100.0, start_padded = max(0, 1.0 - 0.1) = 0.9
    assert (
        rendered_notes
        == "Title=sample; Artist=SpectroSampler; Start=0.900; Detector=flux; Enabled=False"
    )

    default_name = render_filename_from_template(
        template=DEFAULT_FILENAME_TEMPLATE,
        base_name="source",
        sample_id="seg-000",
        index=0,
        total=1,
        segment=segment,
        fmt="flac",
        normalized=True,
        pre_pad_ms=100.0,
        post_pad_ms=50.0,
        title=title,
        artist="SpectroSampler",
        album="Field Notes",
        year=2025,
        sample_rate_hz=48000,
        bit_depth="24",
        channels="stereo",
    )
    # With 0-based indexing, id="0000", and padded times: start=0.900, duration=0.650
    # Default template is "{id}_{title}_start-{start}s_duration-{duration}s"
    assert default_name.startswith("0000_sample_start-0.900s_duration-0.650s")
