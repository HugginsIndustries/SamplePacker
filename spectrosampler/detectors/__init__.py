"""Audio event detection modules."""

from spectrosampler.detectors.base import BaseDetector, Segment
from spectrosampler.detectors.energy import NonSilenceEnergyDetector
from spectrosampler.detectors.flux import TransientFluxDetector
from spectrosampler.detectors.spectral import SpectralInterestingnessDetector
from spectrosampler.detectors.vad import VoiceVADDetector

__all__ = [
    "BaseDetector",
    "Segment",
    "VoiceVADDetector",
    "TransientFluxDetector",
    "NonSilenceEnergyDetector",
    "SpectralInterestingnessDetector",
]
