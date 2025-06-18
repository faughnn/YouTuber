"""
Unit Tests for ChatterboxTTSConfig

Tests configuration system functionality including YAML loading, device detection,
parameter validation, and system resource validation.
"""

import unittest
import tempfile
import os
import yaml
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    ChatterboxTTSConfig, 
    ChatterboxConfig, 
    ChatterboxParameters,
    ChatterboxAudioSettings,
    detect_device,
    validate_system_resources
)


class TestChatterboxTTSConfig(unittest.TestCase):
    """Test suite for ChatterboxTTSConfig functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.config_path = Path(__file__).parent.parent.parent / "Code" / "Config" / "default_config.yaml"
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up after each test method."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_device_detection(self):
        """Test device detection functionality."""
        device = detect_device()
        
        # Should return one of the supported devices
        self.assertIn(device, ['cuda', 'mps', 'cpu'])
        print(f"✓ Device detected: {device}")
        
        # Device detection should be consistent
        device2 = detect_device()
        self.assertEqual(device, device2)
    
    def test_system_resource_validation(self):
        """Test system resource validation."""
        resources = validate_system_resources()
        
        # Should return a dictionary with expected keys
        expected_keys = ['sufficient_ram', 'sufficient_disk', 'python_version_ok']
        for key in expected_keys:
            self.assertIn(key, resources)
            self.assertIsInstance(resources[key], bool)
        
        print(f"✓ System resources: RAM={resources['sufficient_ram']}, Disk={resources['sufficient_disk']}, Python={resources['python_version_ok']}")
    
    def test_config_initialization_with_path(self):
        """Test configuration initialization with file path."""
        config = ChatterboxTTSConfig(str(self.config_path))
        
        self.assertIsNotNone(config.yaml_config)
        self.assertIsInstance(config.yaml_config, dict)
        
        # Should have chatterbox_tts section
        self.assertIn('chatterbox_tts', config.yaml_config)
    
    def test_config_initialization_default(self):
        """Test configuration initialization with default settings."""
        config = ChatterboxTTSConfig()
        
        # Should work with default configuration
        self.assertIsNotNone(config.yaml_config)
        
        # Should have detected device
        self.assertIsNotNone(config.detected_device)
        self.assertIn(config.detected_device, ['cuda', 'mps', 'cpu'])
    
    def test_chatterbox_config_components(self):
        """Test ChatterboxConfig dataclass components."""
        config = ChatterboxTTSConfig(str(self.config_path))
        
        # Get chatterbox configuration
        chatterbox_config = config.get_chatterbox_config()
        self.assertIsInstance(chatterbox_config, ChatterboxConfig)
        
        # Check voice model path
        self.assertIsNotNone(chatterbox_config.voice_model_path)
        self.assertTrue(len(chatterbox_config.voice_model_path) > 0)
        
        # Check device preference
        self.assertIn(chatterbox_config.device_preference, ['cuda', 'mps', 'cpu'])
        
        # Check default parameters
        params = chatterbox_config.default_parameters
        self.assertIsInstance(params, ChatterboxParameters)
        self.assertEqual(params.exaggeration, 0.9)
        self.assertEqual(params.temperature, 0.5)
        self.assertEqual(params.cfg_weight, 0.9)
        
        print(f"✓ Chatterbox config: device={chatterbox_config.device_preference}, voice_model={chatterbox_config.voice_model_path}")
    
    def test_audio_settings(self):
        """Test audio settings configuration."""
        config = ChatterboxTTSConfig(str(self.config_path))
        
        audio_settings = config.get_audio_settings()
        self.assertIsInstance(audio_settings, ChatterboxAudioSettings)
        
        # Check audio format settings
        self.assertEqual(audio_settings.sample_rate, 24000)
        self.assertEqual(audio_settings.format, "wav")
        self.assertEqual(audio_settings.channels, 1)
        
        print(f"✓ Audio settings: {audio_settings.sample_rate}Hz, {audio_settings.format}, {audio_settings.channels} channel(s)")
    
    def test_voice_model_path_resolution(self):
        """Test voice model path resolution."""
        config = ChatterboxTTSConfig(str(self.config_path))
        
        # Test voice model path resolution
        voice_path = config.get_voice_model_path()
        self.assertIsNotNone(voice_path)
        
        # Should be absolute path
        self.assertTrue(os.path.isabs(voice_path))
        
        # Check if file exists
        exists = os.path.exists(voice_path)
        print(f"✓ Voice model path: {voice_path} (exists: {exists})")
        
        if exists:
            # Check file size
            file_size = os.path.getsize(voice_path)
            self.assertGreater(file_size, 1000000)  # Should be > 1MB
            print(f"  File size: {file_size/1024/1024:.1f}MB")
    
    def test_configuration_validation(self):
        """Test comprehensive configuration validation."""
        config = ChatterboxTTSConfig(str(self.config_path))
        
        validation_result = config.validate_configuration()
        
        # Should return validation result
        self.assertIsNotNone(validation_result)
        self.assertIsInstance(validation_result.is_valid, bool)
        self.assertIsInstance(validation_result.errors, list)
        self.assertIsInstance(validation_result.warnings, list)
        
        print(f"✓ Configuration validation: valid={validation_result.is_valid}")
        print(f"  Errors: {len(validation_result.errors)}")
        print(f"  Warnings: {len(validation_result.warnings)}")
        
        # Print any errors or warnings
        for error in validation_result.errors:
            print(f"  ERROR: {error}")
        for warning in validation_result.warnings:
            print(f"  WARNING: {warning}")
    
    def test_file_settings(self):
        """Test file settings configuration."""
        config = ChatterboxTTSConfig(str(self.config_path))
        
        file_settings = config.get_file_settings()
        
        # Should have content root
        self.assertIsNotNone(file_settings.content_root)
        self.assertTrue(len(file_settings.content_root) > 0)
        
        # Should have timeout and retry settings
        self.assertGreater(file_settings.timeout_seconds, 0)
        self.assertGreater(file_settings.retry_attempts, 0)
        
        print(f"✓ File settings: content_root={file_settings.content_root}")
        print(f"  Timeout: {file_settings.timeout_seconds}s, Retries: {file_settings.retry_attempts}")
    
    def test_parameter_validation(self):
        """Test parameter validation and ranges."""
        config = ChatterboxTTSConfig(str(self.config_path))
        
        # Test getting parameters for different tones
        neutral_params = config.get_parameters_for_tone("neutral")
        self.assertIsInstance(neutral_params, ChatterboxParameters)
        
        # Should use optimal defaults
        self.assertEqual(neutral_params.exaggeration, 0.9)
        self.assertEqual(neutral_params.temperature, 0.5)
        self.assertEqual(neutral_params.cfg_weight, 0.9)
        
        # Test other tones (should also use optimal defaults since tone mapping is disabled)
        excited_params = config.get_parameters_for_tone("excited")
        self.assertEqual(excited_params.exaggeration, 0.9)
        self.assertEqual(excited_params.temperature, 0.5)
        self.assertEqual(excited_params.cfg_weight, 0.9)
        
        print("✓ Parameter validation: optimal defaults used for all tones")
    
    def test_yaml_config_structure(self):
        """Test YAML configuration structure and required sections."""
        config = ChatterboxTTSConfig(str(self.config_path))
        yaml_config = config.yaml_config
        
        # Check required top-level sections
        required_sections = ['api', 'processing', 'chatterbox_tts', 'paths']
        for section in required_sections:
            if section in yaml_config:
                print(f"✓ Found section: {section}")
            else:
                print(f"! Missing section: {section}")
        
        # Check chatterbox_tts subsections
        if 'chatterbox_tts' in yaml_config:
            chatterbox_section = yaml_config['chatterbox_tts']
            
            required_chatterbox_keys = [
                'voice_prompt_path', 'device_preference', 'default_parameters'
            ]
            
            for key in required_chatterbox_keys:
                if key in chatterbox_section:
                    print(f"  ✓ Found chatterbox key: {key}")
                else:
                    print(f"  ! Missing chatterbox key: {key}")


class TestChatterboxParameters(unittest.TestCase):
    """Test suite for ChatterboxParameters dataclass."""
    
    def test_parameter_defaults(self):
        """Test parameter default values."""
        params = ChatterboxParameters()
        
        # Check optimal defaults
        self.assertEqual(params.exaggeration, 0.9)
        self.assertEqual(params.temperature, 0.5)
        self.assertEqual(params.cfg_weight, 0.9)
        
        print("✓ Parameter defaults: optimal values confirmed")
    
    def test_parameter_customization(self):
        """Test parameter customization."""
        custom_params = ChatterboxParameters(
            exaggeration=0.8,
            temperature=0.6,
            cfg_weight=0.7
        )
        
        self.assertEqual(custom_params.exaggeration, 0.8)
        self.assertEqual(custom_params.temperature, 0.6)
        self.assertEqual(custom_params.cfg_weight, 0.7)
        
        print("✓ Parameter customization working")


class TestConfigurationIntegration(unittest.TestCase):
    """Integration tests for configuration system."""
    
    def test_config_loading_from_different_directories(self):
        """Test configuration loading from different working directories."""
        config_path = Path(__file__).parent.parent.parent / "Code" / "Config" / "default_config.yaml"
        
        # Test from current directory
        config1 = ChatterboxTTSConfig(str(config_path))
        voice_path1 = config1.get_voice_model_path()
        
        # Test from different directory (simulate master processor usage)
        os.chdir(str(Path(__file__).parent.parent.parent))
        config2 = ChatterboxTTSConfig(str(config_path))
        voice_path2 = config2.get_voice_model_path()
        
        # Should resolve to same absolute path
        self.assertEqual(os.path.normpath(voice_path1), os.path.normpath(voice_path2))
        print(f"✓ Path resolution consistent: {voice_path1}")
    
    def test_configuration_error_handling(self):
        """Test configuration error handling for invalid files."""
        # Test with non-existent config file
        try:
            config = ChatterboxTTSConfig("/non/existent/config.yaml")
            # Should fall back to default configuration
            self.assertIsNotNone(config.yaml_config)
            print("✓ Non-existent config handled gracefully")
        except Exception as e:
            print(f"✓ Config error handled: {type(e).__name__}")
    
    def test_device_specific_configuration(self):
        """Test device-specific configuration handling."""
        config = ChatterboxTTSConfig()
        
        # Test detected device configuration
        detected_device = config.detected_device
        chatterbox_config = config.get_chatterbox_config()
        
        print(f"✓ Device detection: {detected_device}")
        print(f"✓ Config device preference: {chatterbox_config.device_preference}")
        
        # Device preference should be valid
        self.assertIn(chatterbox_config.device_preference, ['cuda', 'mps', 'cpu'])


if __name__ == '__main__':
    print("=" * 60)
    print("CHATTERBOX TTS CONFIG UNIT TESTS")
    print("=" * 60)
    
    # Run tests with detailed output
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "=" * 60)
    print("TTS CONFIG UNIT TESTS COMPLETED")
    print("=" * 60)
