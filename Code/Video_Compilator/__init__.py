"""
Video Compilator - Simple Concatenation Approach

A streamlined video compilation system that converts audio segments to video
(with static backgrounds) and seamlessly concatenates them with video clips.

Based on successful testing of the simple FFmpeg concatenation technique.
"""

from .simple_compiler import SimpleCompiler
from .audio_to_video import AudioToVideoConverter
from .concat_orchestrator import DirectConcatenator

__version__ = "1.0.0"
__all__ = ["SimpleCompiler", "AudioToVideoConverter", "DirectConcatenator"]
