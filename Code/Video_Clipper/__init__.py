"""
Video Clipper Module for Script-Based Video Extraction

This module provides script-based video clip extraction functionality
that reads video clip specifications from unified podcast script files
and extracts corresponding segments from original video files.
"""

from .script_parser import UnifiedScriptParser, VideoClipSpec
from .video_extractor import VideoClipExtractor
from .integration import extract_clips_from_script

__all__ = [
    'UnifiedScriptParser',
    'VideoClipSpec', 
    'VideoClipExtractor',
    'extract_clips_from_script'
]
