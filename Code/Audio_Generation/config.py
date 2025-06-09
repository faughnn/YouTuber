"""
Configuration Manager for Audio Generation System

This module handles loading and validation of configuration settings,
reusing existing API keys and settings from the main config file.
"""

import logging
import os
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


@dataclass
class GeminiConfig:
    """Configuration for Gemini TTS API."""
    model: str = "gemini-2.5-flash-preview-tts"
    voice_name: str = "Algenib"
    audio_format: str = "wav"
    sample_rate: int = 24000
    channels: int = 1
    sample_width: int = 2
    api_key: Optional[str] = None


@dataclass
class AudioSettings:
    """Audio generation processing settings."""
    max_concurrent: int = 3
    retry_attempts: int = 2
    delay_between_requests: float = 1.5
    tone_instruction_prefix: str = "Use this tone: "
    fallback_tone: str = "a natural conversational tone"
    timeout_seconds: int = 30
    max_text_length: int = 4000


@dataclass
class FileSettings:
    """File system and organization settings."""
    content_root: str = "Content"
    audio_subdir: str = "Output/Audio"
    metadata_filename: str = "generation_metadata.json"
    log_filename: str = "audio_generation.log"


@dataclass
class ConfigValidation:
    """Result of configuration validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class AudioGenerationConfig:
    """
    Configuration manager for the audio generation system.
    
    Loads configuration from the existing default_config.yaml and
    provides audio generation specific settings.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Optional path to config file. If None, uses default location.
        """
        self.logger = logging.getLogger(__name__)
        
        # Determine config file path
        if config_path is None:
            # Use default location relative to this module
            module_dir = Path(__file__).parent
            config_path = module_dir.parent / "Config" / "default_config.yaml"
        
        self.config_path = Path(config_path)
        self.raw_config = {}
        
        # Configuration objects
        self.gemini_config = GeminiConfig()
        self.audio_settings = AudioSettings()
        self.file_settings = FileSettings()
        
        # Load configuration
        self._load_configuration()

    def _load_configuration(self) -> None:
        """Load configuration from YAML file."""
        try:
            if not self.config_path.exists():
                self.logger.warning(f"Config file not found: {self.config_path}")
                self.logger.info("Using default configuration values")
                return
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.raw_config = yaml.safe_load(f) or {}
            
            self.logger.info(f"Loaded configuration from: {self.config_path}")
            
            # Extract and set configuration values
            self._extract_gemini_config()
            self._extract_audio_settings()
            self._extract_file_settings()
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            self.logger.info("Using default configuration values")

    def _extract_gemini_config(self) -> None:
        """Extract Gemini API configuration."""
        api_config = self.raw_config.get('api', {})
        
        # API Key - check environment variable first, then config file
        api_key = os.getenv('GEMINI_API_KEY') or api_config.get('gemini_api_key')
        if api_key:
            self.gemini_config.api_key = api_key
        else:
            self.logger.warning("No Gemini API key found in environment or config")
        
        # Use existing TTS config if available, otherwise defaults
        tts_config = self.raw_config.get('tts', {})
        
        # Map existing config to new structure if available
        if 'default_voice' in tts_config:
            # Convert from old format if needed
            old_voice = tts_config['default_voice']
            if old_voice == "en-US-Standard-A":
                self.gemini_config.voice_name = "Algenib"  # Default for new system
            else:
                self.gemini_config.voice_name = "Algenib"  # Use default
        
        self.logger.info(f"Gemini config: voice={self.gemini_config.voice_name}, model={self.gemini_config.model}")

    def _extract_audio_settings(self) -> None:
        """Extract audio processing settings."""
        # Check for specific Gemini TTS settings first
        gemini_tts_config = self.raw_config.get('gemini_tts', {})
        
        if 'max_concurrent' in gemini_tts_config:
            self.audio_settings.max_concurrent = gemini_tts_config['max_concurrent']
        elif 'processing' in self.raw_config and 'batch_size' in self.raw_config['processing']:
            # Use batch_size as fallback, but cap at 2 for TTS rate limits
            self.audio_settings.max_concurrent = min(self.raw_config['processing']['batch_size'], 2)
        
        if 'request_delay' in gemini_tts_config:
            self.audio_settings.delay_between_requests = float(gemini_tts_config['request_delay'])
        elif 'error_handling' in self.raw_config and 'retry_delay' in self.raw_config['error_handling']:
            # Use retry_delay as fallback, but ensure minimum for TTS rate limits
            self.audio_settings.delay_between_requests = max(
                float(self.raw_config['error_handling']['retry_delay']), 20.0
            )
        
        if 'retry_attempts' in gemini_tts_config:
            self.audio_settings.retry_attempts = gemini_tts_config['retry_attempts']
        elif 'error_handling' in self.raw_config and 'max_retries' in self.raw_config['error_handling']:
            self.audio_settings.retry_attempts = self.raw_config['error_handling']['max_retries']
        if 'timeout' in gemini_tts_config:
            self.audio_settings.timeout_seconds = gemini_tts_config['timeout']
        
        self.logger.info(f"Audio settings: concurrent={self.audio_settings.max_concurrent}, retries={self.audio_settings.retry_attempts}")
        self.logger.info(f"Audio settings: delay={self.audio_settings.delay_between_requests}s, timeout={self.audio_settings.timeout_seconds}s")

    def _extract_file_settings(self) -> None:
        """Extract file system settings."""
        paths_config = self.raw_config.get('paths', {})
        
        if 'episode_base' in paths_config:
            # Make content_root an absolute path relative to the project root
            content_root = paths_config['episode_base']
            if not Path(content_root).is_absolute():
                # Assume it's relative to the parent directory of Code/
                project_root = Path(__file__).parent.parent.parent
                content_root = str(project_root / content_root)
                self.logger.debug(f"DEBUG: project_root={project_root}, content_root={content_root}")
            self.file_settings.content_root = content_root
        
        self.logger.info(f"File settings: content_root={self.file_settings.content_root}")

    def load_gemini_config(self) -> GeminiConfig:
        """Get Gemini API configuration."""
        return self.gemini_config

    def load_api_keys(self) -> Dict[str, str]:
        """Get API keys dictionary."""
        keys = {}
        
        if self.gemini_config.api_key:
            keys['gemini'] = self.gemini_config.api_key
        
        return keys

    def get_audio_settings(self) -> AudioSettings:
        """Get audio processing settings."""
        return self.audio_settings

    def get_file_settings(self) -> FileSettings:
        """Get file system settings."""
        return self.file_settings

    def validate_configuration(self) -> ConfigValidation:
        """
        Validate the current configuration.
        
        Returns:
            ConfigValidation with validation results
        """
        errors = []
        warnings = []
        
        # Check API key
        if not self.gemini_config.api_key:
            errors.append("Gemini API key is required but not found")
        
        # Check content root path
        content_path = Path(self.file_settings.content_root)
        if not content_path.exists():
            warnings.append(f"Content root directory does not exist: {content_path}")
        
        # Validate audio settings ranges
        if self.audio_settings.max_concurrent < 1 or self.audio_settings.max_concurrent > 10:
            warnings.append(f"max_concurrent ({self.audio_settings.max_concurrent}) should be between 1-10")
        
        if self.audio_settings.retry_attempts < 0 or self.audio_settings.retry_attempts > 5:
            warnings.append(f"retry_attempts ({self.audio_settings.retry_attempts}) should be between 0-5")
        
        # Check Gemini config
        if self.gemini_config.sample_rate not in [8000, 16000, 22050, 24000, 44100, 48000]:
            warnings.append(f"Unusual sample rate: {self.gemini_config.sample_rate}")
        
        is_valid = len(errors) == 0
        
        if is_valid:
            self.logger.info("Configuration validation passed")
        else:
            self.logger.error(f"Configuration validation failed: {errors}")
        
        if warnings:
            self.logger.warning(f"Configuration warnings: {warnings}")
        
        return ConfigValidation(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings
        )

    def override_voice(self, voice_name: str) -> None:
        """Override the default voice setting."""
        self.gemini_config.voice_name = voice_name
        self.logger.info(f"Voice overridden to: {voice_name}")

    def override_concurrent_limit(self, max_concurrent: int) -> None:
        """Override the concurrent processing limit."""
        if 1 <= max_concurrent <= 10:
            self.audio_settings.max_concurrent = max_concurrent
            self.logger.info(f"Concurrent limit overridden to: {max_concurrent}")
        else:
            self.logger.warning(f"Invalid concurrent limit {max_concurrent}, keeping current value")

    def get_config_summary(self) -> Dict:
        """Get a summary of current configuration for debugging."""
        return {
            'config_file': str(self.config_path),
            'config_exists': self.config_path.exists(),
            'gemini': {
                'model': self.gemini_config.model,
                'voice': self.gemini_config.voice_name,
                'has_api_key': bool(self.gemini_config.api_key),
                'audio_format': self.gemini_config.audio_format,
                'sample_rate': self.gemini_config.sample_rate
            },
            'audio_settings': {
                'max_concurrent': self.audio_settings.max_concurrent,
                'retry_attempts': self.audio_settings.retry_attempts,
                'delay_between_requests': self.audio_settings.delay_between_requests,
                'timeout_seconds': self.audio_settings.timeout_seconds
            },
            'file_settings': {
                'content_root': self.file_settings.content_root,
                'audio_subdir': self.file_settings.audio_subdir
            }
        }
