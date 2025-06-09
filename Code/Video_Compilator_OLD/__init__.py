"""
Video Compilator Package

Takes unified podcast scripts and combines audio/video assets to create 
final seamless video compilations using FFmpeg.
"""

from .main import VideoCompilator, compile_episode
from .script_parser import ScriptParser
from .asset_validator import AssetValidator
from .background_processor import BackgroundProcessor
from .timeline_builder import TimelineBuilder
from .ffmpeg_orchestrator import FFmpegOrchestrator

__version__ = "1.0.0"
__author__ = "YouTuber Project"

__all__ = [
    "VideoCompilator",
    "compile_episode",
    "ScriptParser", 
    "AssetValidator",
    "BackgroundProcessor",
    "TimelineBuilder",
    "FFmpegOrchestrator"
]
