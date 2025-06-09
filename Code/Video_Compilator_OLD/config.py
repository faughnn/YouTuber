"""
Configuration settings for Video Compilator
"""
from pathlib import Path
from typing import Dict, Any

# Video Output Configuration
VIDEO_CONFIG = {
    "resolution": "1920x1080",
    "codec": "libx264",
    "preset": "medium",  # Valid x264 preset: ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
    "crf": 18,  # High quality
    "frame_rate": 30,
    "pixel_format": "yuv420p"
}

# Audio Configuration
AUDIO_CONFIG = {
    "codec": "aac",
    "bitrate": "320k",
    "sample_rate": 48000,
    "channels": 2
}

# Processing Configuration
PROCESSING_CONFIG = {
    "cleanup_temp_files": False,  # Keep temp files for inspection
    "fail_on_missing_assets": True,
    "background_image_path": "C:/Users/nfaug/OneDrive - LIR/Desktop/YouTuber/Assets/Chris_Morris_Images/bloody_hell.jpg",
    "temp_dir_name": "temp"
}

# Transitions Configuration
TRANSITIONS_CONFIG = {
    "type": "hard_cut",  # Future: crossfade, fade_in_out
    "duration": 0  # Future: configurable fade duration
}

# FFmpeg Configuration
FFMPEG_CONFIG = {
    "executable": "ffmpeg",  # Assumes ffmpeg is in PATH
    "log_level": "error",  # quiet, error, warning, info, verbose, debug
    "overwrite_output": True
}

# File Extensions
FILE_EXTENSIONS = {
    "audio": ".wav",
    "video": ".mp4",
    "script": ".json",
    "concat_file": ".txt"
}

# Section Types
SECTION_TYPES = {
    "intro": "intro",
    "pre_clip": "pre_clip", 
    "video_clip": "video_clip",
    "post_clip": "post_clip",
    "outro": "outro"
}

def get_background_image_path() -> Path:
    """Get the background image path as a Path object"""
    return Path(PROCESSING_CONFIG["background_image_path"])

def get_temp_dir_name() -> str:
    """Get the temporary directory name"""
    return PROCESSING_CONFIG["temp_dir_name"]

def should_cleanup_temp_files() -> bool:
    """Check if temporary files should be cleaned up"""
    return PROCESSING_CONFIG["cleanup_temp_files"]

def should_fail_on_missing_assets() -> bool:
    """Check if processing should fail on missing assets"""
    return PROCESSING_CONFIG["fail_on_missing_assets"]
