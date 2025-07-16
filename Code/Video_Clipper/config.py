"""
Configuration Module for Video Clipper

This module provides configuration management and default settings
for the video clipper system.
"""

from typing import Dict, Any


# Default configuration settings
DEFAULT_CONFIG = {
    "start_buffer_seconds": 0.0,
    "end_buffer_seconds": 0.0,
    "video_quality": {
        "codec": "libx264",
        "crf": 23,
        "preset": "fast"
    },
    "audio_quality": {
        "codec": "aac",
        "bitrate": "128k"
    },
    "processing": {
        "max_retries": 2,
        "timeout_seconds": 300,
        "continue_on_error": True
    },
    "output": {
        "naming_pattern": "{section_id}.mp4",
        "create_reports": True,
        "create_summary": True
    }
}


def get_default_config() -> Dict[str, Any]:
    """
    Get the default configuration dictionary.
    
    Returns:
        Default configuration settings
    """
    return DEFAULT_CONFIG.copy()


def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and normalize configuration settings.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        Validated and normalized configuration
        
    Raises:
        ValueError: If configuration contains invalid values
    """
    validated = get_default_config()
    
    if not isinstance(config, dict):
        raise ValueError("Configuration must be a dictionary")
    
    # Validate buffer settings
    if "start_buffer_seconds" in config:
        value = config["start_buffer_seconds"]
        if not isinstance(value, (int, float)) or value < 0:
            raise ValueError("start_buffer_seconds must be a non-negative number")
        validated["start_buffer_seconds"] = float(value)
    
    if "end_buffer_seconds" in config:
        value = config["end_buffer_seconds"]
        if not isinstance(value, (int, float)) or value < 0:
            raise ValueError("end_buffer_seconds must be a non-negative number")
        validated["end_buffer_seconds"] = float(value)
    
    # Validate video quality settings
    if "video_quality" in config:
        vq = config["video_quality"]
        if isinstance(vq, dict):
            if "codec" in vq and isinstance(vq["codec"], str):
                validated["video_quality"]["codec"] = vq["codec"]
            
            if "crf" in vq:
                crf = vq["crf"]
                if isinstance(crf, (int, float)) and 0 <= crf <= 51:
                    validated["video_quality"]["crf"] = int(crf)
                else:
                    raise ValueError("CRF must be between 0 and 51")
            
            if "preset" in vq and isinstance(vq["preset"], str):
                valid_presets = ["ultrafast", "superfast", "veryfast", "faster", 
                               "fast", "medium", "slow", "slower", "veryslow"]
                if vq["preset"] in valid_presets:
                    validated["video_quality"]["preset"] = vq["preset"]
                else:
                    raise ValueError(f"Preset must be one of: {valid_presets}")
    
    # Validate audio quality settings
    if "audio_quality" in config:
        aq = config["audio_quality"]
        if isinstance(aq, dict):
            if "codec" in aq and isinstance(aq["codec"], str):
                validated["audio_quality"]["codec"] = aq["codec"]
            
            if "bitrate" in aq and isinstance(aq["bitrate"], str):
                validated["audio_quality"]["bitrate"] = aq["bitrate"]
    
    # Validate processing settings
    if "processing" in config:
        proc = config["processing"]
        if isinstance(proc, dict):
            if "max_retries" in proc:
                retries = proc["max_retries"]
                if isinstance(retries, int) and retries >= 0:
                    validated["processing"]["max_retries"] = retries
                else:
                    raise ValueError("max_retries must be a non-negative integer")
            
            if "timeout_seconds" in proc:
                timeout = proc["timeout_seconds"]
                if isinstance(timeout, (int, float)) and timeout > 0:
                    validated["processing"]["timeout_seconds"] = timeout
                else:
                    raise ValueError("timeout_seconds must be a positive number")
            
            if "continue_on_error" in proc:
                continue_on_error = proc["continue_on_error"]
                if isinstance(continue_on_error, bool):
                    validated["processing"]["continue_on_error"] = continue_on_error
                else:
                    raise ValueError("continue_on_error must be a boolean")
    
    # Validate output settings
    if "output" in config:
        output = config["output"]
        if isinstance(output, dict):
            if "naming_pattern" in output and isinstance(output["naming_pattern"], str):
                validated["output"]["naming_pattern"] = output["naming_pattern"]
            
            if "create_reports" in output and isinstance(output["create_reports"], bool):
                validated["output"]["create_reports"] = output["create_reports"]
            
            if "create_summary" in output and isinstance(output["create_summary"], bool):
                validated["output"]["create_summary"] = output["create_summary"]
    
    return validated


def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two configuration dictionaries, with override taking precedence.
    
    Args:
        base_config: Base configuration dictionary
        override_config: Override configuration dictionary
        
    Returns:
        Merged configuration dictionary
    """
    merged = base_config.copy()
    
    for key, value in override_config.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = {**merged[key], **value}
        else:
            merged[key] = value
    
    return merged
