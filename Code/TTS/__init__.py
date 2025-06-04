"""
TTS (Text-to-Speech) Module
Provides text-to-speech functionality using various providers.
"""

from .core.tts_generator import SimpleTTSGenerator
from .config.setup import TTSSetup

__version__ = "1.0.0"
__all__ = ["SimpleTTSGenerator", "TTSSetup"]
