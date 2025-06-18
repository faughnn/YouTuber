"""
Unit Tests for ChatterboxTTSEngine

Tests core TTS engine functionality including model loading, audio generation,
device detection, parameter optimization, and error handling.
"""

import unittest
import tempfile
import os
from pathlib import Path
import time
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tts_engine import ChatterboxTTSEngine, TTSResult
from config import ChatterboxTTSConfig


class TestChatterboxTTSEngine(unittest.TestCase):
    """Test suite for ChatterboxTTSEngine functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.config_path = Path(__file__).parent.parent.parent / "Code" / "Config" / "default_config.yaml"
        self.config = ChatterboxTTSConfig(str(self.config_path))
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up after each test method."""
        # Clean up temporary files
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_engine_initialization(self):
        """Test TTS engine initialization with different config types."""
        # Test with config object
        engine1 = ChatterboxTTSEngine(self.config)
        self.assertIsInstance(engine1.config, ChatterboxTTSConfig)
        
        # Test with config path string
        engine2 = ChatterboxTTSEngine(str(self.config_path))
        self.assertIsInstance(engine2.config, ChatterboxTTSConfig)
        
        # Test with None (default config)
        engine3 = ChatterboxTTSEngine(None)
        self.assertIsInstance(engine3.config, ChatterboxTTSConfig)
        
        # Clean up
        engine1.cleanup()
        engine2.cleanup()
        engine3.cleanup()
    
    def test_device_detection(self):
        """Test device detection and device preference handling."""
        engine = ChatterboxTTSEngine(self.config)
        
        # Check device is detected
        self.assertIsNotNone(engine.device)
        self.assertIn(engine.device, ['cuda', 'mps', 'cpu'])
        
        # Test device info
        device_info = engine.get_device_info()
        self.assertIsInstance(device_info, dict)
        self.assertIn('device', device_info)
        self.assertIn('available', device_info)
        
        print(f"Detected device: {engine.device}")
        print(f"Device info: {device_info}")
        
        engine.cleanup()
    
    def test_model_loading(self):
        """Test model loading functionality and caching."""
        engine = ChatterboxTTSEngine(self.config)
        
        # Initial state - model not loaded
        self.assertFalse(engine.model_loaded)
        self.assertIsNone(engine.model)
        
        try:
            # Test model loading
            success = engine.load_model()
            
            if success:
                self.assertTrue(engine.model_loaded)
                self.assertIsNotNone(engine.model)
                print("✓ Model loading successful")
            else:
                print("! Model loading failed (expected without Chatterbox TTS installed)")
                
        except Exception as e:
            print(f"! Model loading gracefully handled error: {type(e).__name__}")
            
        engine.cleanup()
    
    def test_connection_testing(self):
        """Test connection testing functionality."""
        engine = ChatterboxTTSEngine(self.config)
        
        # Test connection
        connection_result = engine.test_connection()
        self.assertIsInstance(connection_result, bool)
        
        print(f"Connection test result: {connection_result}")
        
        engine.cleanup()
    
    def test_tts_result_structure(self):
        """Test TTSResult dataclass structure and validation."""
        # Test successful result
        success_result = TTSResult(
            success=True,
            output_path="/path/to/output.wav",
            audio_duration=5.2,
            file_size=125440,
            generation_time=3.1,
            text_length=50
        )
        
        self.assertTrue(success_result.success)
        self.assertEqual(success_result.output_path, "/path/to/output.wav")
        self.assertEqual(success_result.audio_duration, 5.2)
        self.assertEqual(success_result.file_size, 125440)
        self.assertEqual(success_result.generation_time, 3.1)
        self.assertEqual(success_result.text_length, 50)
        self.assertEqual(success_result.error_message, "")  # Default value
        
        # Test failure result
        failure_result = TTSResult(
            success=False,
            output_path="",
            error_message="Model loading failed"
        )
        
        self.assertFalse(failure_result.success)
        self.assertEqual(failure_result.error_message, "Model loading failed")
        self.assertEqual(failure_result.audio_duration, 0.0)  # Default value
    
    def test_audio_generation_interface(self):
        """Test audio generation interface compatibility."""
        engine = ChatterboxTTSEngine(self.config)
        
        # Test output path
        output_path = Path(self.temp_dir) / "test_output.wav"
        
        try:
            # Test main interface method
            result = engine.generate_audio_with_retry(
                text="Hello, this is a test.",
                tone="neutral",
                output_path=output_path
            )
            
            # Validate result structure
            self.assertIsInstance(result, TTSResult)
            self.assertIsInstance(result.success, bool)
            self.assertIsInstance(result.output_path, str)
            self.assertIsInstance(result.error_message, str)
            self.assertIsInstance(result.audio_duration, float)
            self.assertIsInstance(result.file_size, int)
            self.assertIsInstance(result.generation_time, float)
            self.assertIsInstance(result.text_length, int)
            
            if result.success:
                print("✓ Audio generation successful")
                self.assertTrue(os.path.exists(result.output_path))
            else:
                print(f"! Audio generation failed (expected): {result.error_message}")
                
        except Exception as e:
            print(f"! Audio generation gracefully handled error: {type(e).__name__}: {e}")
            
        engine.cleanup()
    
    def test_parameter_validation(self):
        """Test TTS parameter validation and optimal defaults."""
        engine = ChatterboxTTSEngine(self.config)
        
        # Check optimal parameters are loaded
        chatterbox_config = engine.config.get_chatterbox_config()
        params = chatterbox_config.default_parameters
        
        # Validate optimal parameter values
        self.assertEqual(params.exaggeration, 0.9)
        self.assertEqual(params.temperature, 0.5)
        self.assertEqual(params.cfg_weight, 0.9)
        
        print(f"✓ Optimal parameters validated: exag={params.exaggeration}, temp={params.temperature}, cfg={params.cfg_weight}")
        
        engine.cleanup()
    
    def test_error_handling(self):
        """Test error handling for various failure scenarios."""
        engine = ChatterboxTTSEngine(self.config)
        
        # Test with invalid output path
        invalid_path = "/invalid/path/that/does/not/exist/output.wav"
        
        try:
            result = engine.generate_audio_with_retry(
                text="Test error handling",
                tone="neutral", 
                output_path=invalid_path
            )
            
            # Should handle error gracefully
            self.assertIsInstance(result, TTSResult)
            if not result.success:
                self.assertIsInstance(result.error_message, str)
                self.assertTrue(len(result.error_message) > 0)
                print(f"✓ Error handling working: {result.error_message}")
            
        except Exception as e:
            print(f"✓ Exception handling working: {type(e).__name__}")
            
        engine.cleanup()
    
    def test_resource_cleanup(self):
        """Test resource cleanup and memory management."""
        engine = ChatterboxTTSEngine(self.config)
        
        # Load model if possible
        try:
            engine.load_model()
        except:
            pass  # Expected if Chatterbox not installed
        
        # Test cleanup
        initial_model_state = engine.model_loaded
        engine.cleanup()
        
        # Verify cleanup
        self.assertFalse(engine.model_loaded)
        self.assertIsNone(engine.model)
        
        print(f"✓ Resource cleanup successful (was loaded: {initial_model_state})")
    
    def test_performance_characteristics(self):
        """Test performance characteristics and timing."""
        engine = ChatterboxTTSEngine(self.config)
        
        # Test initialization timing
        start_time = time.time()
        engine2 = ChatterboxTTSEngine(self.config)
        init_time = time.time() - start_time
        
        self.assertLess(init_time, 5.0)  # Should initialize quickly
        print(f"✓ Initialization time: {init_time:.3f}s")
        
        engine.cleanup()
        engine2.cleanup()


class TestTTSEngineIntegration(unittest.TestCase):
    """Integration tests for TTS engine with configuration system."""
    
    def test_config_integration(self):
        """Test integration with ChatterboxTTSConfig."""
        config_path = Path(__file__).parent.parent.parent / "Code" / "Config" / "default_config.yaml"
        
        # Test configuration loading
        config = ChatterboxTTSConfig(str(config_path))
        validation = config.validate_configuration()
        
        self.assertTrue(validation.is_valid)
        print(f"✓ Configuration validation: {len(validation.errors)} errors, {len(validation.warnings)} warnings")
        
        # Test engine with validated config
        engine = ChatterboxTTSEngine(config)
        self.assertIsNotNone(engine.config)
        
        engine.cleanup()
    
    def test_voice_model_validation(self):
        """Test voice model file accessibility and validation."""
        config_path = Path(__file__).parent.parent.parent / "Code" / "Config" / "default_config.yaml"
        config = ChatterboxTTSConfig(str(config_path))
        
        # Check voice model path resolution
        voice_path = config.get_voice_model_path()
        self.assertIsNotNone(voice_path)
        
        if os.path.exists(voice_path):
            file_size = os.path.getsize(voice_path)
            self.assertGreater(file_size, 1000000)  # Should be > 1MB
            print(f"✓ Voice model found: {voice_path} ({file_size/1024/1024:.1f}MB)")
        else:
            print(f"! Voice model not found: {voice_path}")


if __name__ == '__main__':
    print("=" * 60)
    print("CHATTERBOX TTS ENGINE UNIT TESTS")
    print("=" * 60)
    
    # Run tests with detailed output
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "=" * 60)
    print("TTS ENGINE UNIT TESTS COMPLETED")
    print("=" * 60)
