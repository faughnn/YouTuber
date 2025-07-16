"""
ElevenLabs TTS Integration Package

This package provides ElevenLabs Text-to-Speech integration for the YouTuber pipeline.
"""

from .elevenlabs_tts_engine import ElevenLabsTTSEngine
from .config_elevenlabs import VOICE_ID, VOICE_SETTINGS, OUTPUT_FORMAT

__all__ = ['ElevenLabsTTSEngine', 'VOICE_ID', 'VOICE_SETTINGS', 'OUTPUT_FORMAT']
