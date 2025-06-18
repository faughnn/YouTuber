"""
Chatterbox TTS Module

A streamlined Text-to-Speech module for YouTube video processing pipeline.
This module provides SimpleTTSEngine for direct TTS API integration.

Main Components:
- SimpleTTSEngine: Streamlined TTS engine with direct API integration
- SimpleAudioFileManager: Optimized file management for generated audio
- JSONParser: Processes video content data for TTS generation
- API Configuration: TTS API server configuration and parameters

Usage:
    from Code.Chatterbox import SimpleTTSEngine, SimpleAudioFileManager
    
    engine = SimpleTTSEngine()
    results = engine.process_episode_script(script_path)
"""

__version__ = "2.0.0"
__author__ = "YouTuber Project - APM Implementation"

# Import SimpleTTSEngine (new streamlined engine)
from .simple_tts_engine import SimpleTTSEngine

# Import SimpleAudioFileManager (optimized file manager)
from .simple_audio_file_manager import SimpleAudioFileManager

# Import JSON Parser
from .json_parser import ChatterboxResponseParser

# Import API Configuration
from .config_tts_api import API_BASE_URL, TEMPERATURE, CFG_WEIGHT, EXAGGERATION

# Export all main components
__all__ = [
    # Core TTS Components
    'SimpleTTSEngine',
    'SimpleAudioFileManager',
    
    # JSON Processing
    'ChatterboxResponseParser',
    
    # API Configuration
    'API_BASE_URL', 'TEMPERATURE', 'CFG_WEIGHT', 'EXAGGERATION'
]
