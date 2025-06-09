"""
Audio Generation Module

A modern TTS system for generating audio files from Gemini response scripts.
Designed specifically for the new podcast_sections[] JSON format.

Modules:
- config: Configuration management and validation
- json_parser: Parse and validate Gemini response files
- tts_engine: Core TTS functionality using Gemini API
- audio_file_manager: Manage audio file organization and metadata
- batch_processor: Process multiple sections and coordinate pipeline
- cli: Command-line interface for manual and batch processing
"""

__version__ = "1.0.0"
__author__ = "Audio Generation System"

# Public API exports
from .json_parser import GeminiResponseParser, AudioSection, ValidationResult, EpisodeInfo
from .config import AudioGenerationConfig, GeminiConfig, AudioSettings, ConfigValidation
from .tts_engine import GeminiTTSEngine, TTSResult
from .audio_file_manager import AudioFileManager, GenerationResult, EpisodeMetadata
from .batch_processor import AudioBatchProcessor, ProcessingReport

__all__ = [
    "GeminiResponseParser",
    "AudioSection", 
    "ValidationResult",
    "EpisodeInfo",
    "AudioGenerationConfig",
    "GeminiConfig",
    "AudioSettings",
    "ConfigValidation",
    "GeminiTTSEngine",
    "TTSResult",
    "AudioFileManager",
    "GenerationResult", 
    "EpisodeMetadata",
    "AudioBatchProcessor",
    "ProcessingReport"
]
