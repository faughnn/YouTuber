"""
EdgeTTS TTS Integration Package

This package provides Microsoft Edge TTS integration for the YouTuber pipeline.
Edge TTS is a free, high-quality neural TTS service that doesn't require an API key.
"""

from .edge_tts_engine import EdgeTTSEngine
from .config_edge_tts import (
    DEFAULT_VOICE,
    VOICE_RATE,
    VOICE_VOLUME,
    VOICE_PITCH,
    OUTPUT_FORMAT
)

__all__ = [
    'EdgeTTSEngine',
    'DEFAULT_VOICE',
    'VOICE_RATE',
    'VOICE_VOLUME',
    'VOICE_PITCH',
    'OUTPUT_FORMAT'
]
