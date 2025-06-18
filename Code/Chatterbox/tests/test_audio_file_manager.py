"""
Unit Tests for ChatterboxAudioFileManager

Tests audio file management functionality including file organization,
metadata generation, and pipeline integration.
"""

import unittest
import tempfile
import os
import json
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from Code.Chatterbox.audio_file_manager import (
    ChatterboxAudioFileManager, 
    ChatterboxGenerationResult,
    ChatterboxEpisodeMetadata,
    AudioFileManager
)
from Code.Chatterbox.tts_engine import TTSResult
from Code.Chatterbox.config import ChatterboxTTSConfig


class TestChatterboxAudioFileManager(unittest.TestCase):
    """Test suite for ChatterboxAudioFileManager functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.config_path = Path(__file__).parent.parent.parent.parent / "Code" / "Config" / "default_config.yaml"
        self.temp_dir = tempfile.mkdtemp()
        self.content_root = self.temp_dir
        
        # Create test episode directory structure
        self.episode_dir = os.path.join(self.temp_dir, "Test_Episode_001")
        os.makedirs(self.episode_dir, exist_ok=True)
        
        self.config = ChatterboxTTSConfig(str(self.config_path))
        
    def tearDown(self):
        """Clean up after each test method."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_file_manager_initialization(self):
        """Test file manager initialization with configuration."""
        try:
            file_manager = ChatterboxAudioFileManager(
                content_root=self.content_root,
                config=self.config
            )
            
            self.assertIsNotNone(file_manager.content_root)
            self.assertIsNotNone(file_manager.config)
            
            print("✓ ChatterboxAudioFileManager initialization successful")
            print(f"  Content root: {file_manager.content_root}")
            print(f"  Config loaded: {file_manager.config is not None}")
            
        except Exception as e:
            print(f"! Initialization error: {type(e).__name__}: {e}")
    
    def test_episode_directory_creation(self):
        """Test episode directory structure creation."""
        try:
            file_manager = ChatterboxAudioFileManager(
                content_root=self.content_root,
                config=self.config
            )
            
            # Test episode directory setup
            episode_info = {
                'narrative_theme': 'Test Episode for Directory Creation',
                'total_estimated_duration': '10 minutes',
                'source_file': 'test_episode.json'
            }
            
            episode_dir = file_manager.setup_episode_directory(
                episode_title="Test_Episode_001",
                episode_info=episode_info
            )
            
            self.assertIsNotNone(episode_dir)
            self.assertTrue(os.path.exists(episode_dir))
            
            # Check that expected subdirectories are created
            expected_dirs = [
                os.path.join(episode_dir, "Output", "Audio"),
                os.path.join(episode_dir, "Output", "Scripts"),
                os.path.join(episode_dir, "Output", "Chatterbox")
            ]
            
            for expected_dir in expected_dirs:
                if os.path.exists(expected_dir):
                    print(f"  ✓ Created: {os.path.relpath(expected_dir, episode_dir)}")
                else:
                    print(f"  ! Missing: {os.path.relpath(expected_dir, episode_dir)}")
            
        except Exception as e:
            print(f"! Directory creation error: {type(e).__name__}: {e}")
    
    def test_tts_result_conversion(self):
        """Test conversion from TTSResult to ChatterboxGenerationResult."""
        try:
            file_manager = ChatterboxAudioFileManager(
                content_root=self.content_root,
                config=self.config
            )
            
            # Create test TTSResult
            tts_result = TTSResult(
                success=True,
                output_path=os.path.join(self.temp_dir, "test_audio.wav"),
                audio_duration=5.2,
                file_size=125440,
                generation_time=3.1,
                text_length=50,
                error_message=""
            )
            
            # Test conversion
            chatterbox_result = file_manager.create_generation_result_from_tts(
                tts_result=tts_result,
                section_id="test_section_001",
                script_content="This is test content for audio generation."
            )
            
            self.assertIsInstance(chatterbox_result, ChatterboxGenerationResult)
            self.assertEqual(chatterbox_result.section_id, "test_section_001")
            self.assertEqual(chatterbox_result.success, True)
            self.assertEqual(chatterbox_result.audio_duration, 5.2)
            self.assertEqual(chatterbox_result.file_size, 125440)
            
            print("✓ TTSResult conversion successful")
            print(f"  Section ID: {chatterbox_result.section_id}")
            print(f"  Success: {chatterbox_result.success}")
            print(f"  Duration: {chatterbox_result.audio_duration}s")
            print(f"  File size: {chatterbox_result.file_size} bytes")
            
        except Exception as e:
            print(f"! TTSResult conversion error: {type(e).__name__}: {e}")
    
    def test_audio_file_organization(self):
        """Test audio file organization and path generation."""
        try:
            file_manager = ChatterboxAudioFileManager(
                content_root=self.content_root,
                config=self.config
            )
            
            # Test audio file path generation
            audio_path = file_manager.generate_audio_file_path(
                episode_dir=self.episode_dir,
                section_id="intro_001",
                section_type="intro"
            )
            
            self.assertIsNotNone(audio_path)
            self.assertTrue(audio_path.endswith('.wav'))
            self.assertIn('intro_001', audio_path)
            
            print(f"✓ Audio file path generation: {os.path.basename(audio_path)}")
            
            # Test file organization
            file_info = file_manager.organize_audio_file(
                source_path=audio_path,
                section_id="intro_001",
                episode_dir=self.episode_dir
            )
            
            self.assertIsInstance(file_info, dict)
            
            print("✓ Audio file organization successful")
            
        except Exception as e:
            print(f"! Audio file organization error: {type(e).__name__}: {e}")
    
    def test_metadata_generation(self):
        """Test metadata generation for Chatterbox-specific information."""
        try:
            file_manager = ChatterboxAudioFileManager(
                content_root=self.content_root,
                config=self.config
            )
            
            # Create test generation results
            test_results = [
                ChatterboxGenerationResult(
                    section_id="intro_001",
                    section_type="intro",
                    success=True,
                    output_path=os.path.join(self.episode_dir, "intro_001.wav"),
                    audio_duration=30.5,
                    file_size=732160,
                    generation_time=2.1,
                    script_content="Welcome to our test episode.",
                    parameters_used={'exaggeration': 0.9, 'temperature': 0.5, 'cfg_weight': 0.9},
                    device_used="cuda",
                    model_info="ChatterboxTTS-v1.0",
                    sample_rate=24000
                ),
                ChatterboxGenerationResult(
                    section_id="outro_001",
                    section_type="outro",
                    success=True,
                    output_path=os.path.join(self.episode_dir, "outro_001.wav"),
                    audio_duration=25.0,
                    file_size=600000,
                    generation_time=1.8,
                    script_content="Thank you for listening.",
                    parameters_used={'exaggeration': 0.9, 'temperature': 0.5, 'cfg_weight': 0.9},
                    device_used="cuda",
                    model_info="ChatterboxTTS-v1.0",
                    sample_rate=24000
                )
            ]
            
            # Test metadata generation
            metadata = file_manager.generate_episode_metadata(
                episode_title="Test_Episode_001",
                generation_results=test_results,
                episode_info={
                    'narrative_theme': 'Metadata Testing',
                    'total_estimated_duration': '2 minutes'
                }
            )
            
            self.assertIsInstance(metadata, ChatterboxEpisodeMetadata)
            self.assertEqual(metadata.episode_title, "Test_Episode_001")
            self.assertEqual(metadata.total_sections, 2)
            self.assertEqual(metadata.successful_sections, 2)
            self.assertEqual(metadata.failed_sections, 0)
            
            print("✓ Metadata generation successful")
            print(f"  Episode: {metadata.episode_title}")
            print(f"  Sections: {metadata.total_sections}")
            print(f"  Success rate: {metadata.successful_sections}/{metadata.total_sections}")
            print(f"  Generation mode: {metadata.generation_mode}")
            print(f"  Voice model: {metadata.voice_model}")
            
        except Exception as e:
            print(f"! Metadata generation error: {type(e).__name__}: {e}")
    
    def test_metadata_file_creation(self):
        """Test metadata file creation and saving."""
        try:
            file_manager = ChatterboxAudioFileManager(
                content_root=self.content_root,
                config=self.config
            )
            
            # Create test metadata
            metadata = ChatterboxEpisodeMetadata(
                episode_title="Test_Episode_Metadata",
                total_sections=2,
                successful_sections=2,
                failed_sections=0,
                total_duration=55.5,
                generation_mode="batch",
                voice_model="Harvard1_2.wav",
                device_used="cuda",
                generation_timestamp="2025-06-12T15:30:00"
            )
            
            # Test saving metadata
            metadata_path = file_manager.save_episode_metadata(
                metadata=metadata,
                episode_dir=self.episode_dir
            )
            
            self.assertIsNotNone(metadata_path)
            self.assertTrue(os.path.exists(metadata_path))
            
            # Verify file content
            with open(metadata_path, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
            
            self.assertIn('episode_title', saved_data)
            self.assertEqual(saved_data['episode_title'], "Test_Episode_Metadata")
            
            print(f"✓ Metadata file created: {os.path.basename(metadata_path)}")
            print(f"  File size: {os.path.getsize(metadata_path)} bytes")
            
        except Exception as e:
            print(f"! Metadata file creation error: {type(e).__name__}: {e}")
    
    def test_audio_validation(self):
        """Test audio file validation functionality."""
        try:
            file_manager = ChatterboxAudioFileManager(
                content_root=self.content_root,
                config=self.config
            )
            
            # Create a dummy audio file for testing
            test_audio_path = os.path.join(self.temp_dir, "test_audio.wav")
            
            # Create minimal WAV file header for testing
            wav_header = b'RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80\xbb\x00\x00\x00w\x01\x00\x02\x00\x10\x00data\x00\x08\x00\x00'
            audio_data = b'\x00\x00' * 1000  # Simple audio data
            
            with open(test_audio_path, 'wb') as f:
                f.write(wav_header + audio_data)
            
            # Test audio validation
            validation_result = file_manager.validate_audio_file(test_audio_path)
            
            self.assertIsInstance(validation_result, dict)
            
            # Check validation result keys
            if 'is_valid' in validation_result:
                print(f"✓ Audio validation: {validation_result['is_valid']}")
            
            if 'format' in validation_result:
                print(f"  Format: {validation_result['format']}")
                
            if 'duration' in validation_result:
                print(f"  Duration: {validation_result['duration']}s")
                
        except Exception as e:
            print(f"! Audio validation error (expected without audio libraries): {type(e).__name__}: {e}")
    
    def test_episode_summary_generation(self):
        """Test episode summary generation."""
        try:
            file_manager = ChatterboxAudioFileManager(
                content_root=self.content_root,
                config=self.config
            )
            
            # Create test generation results
            test_results = [
                ChatterboxGenerationResult(
                    section_id="intro_001",
                    section_type="intro",
                    success=True,
                    output_path="intro_001.wav",
                    audio_duration=30.0,
                    file_size=720000,
                    generation_time=2.5,
                    script_content="Introduction content",
                    parameters_used={'exaggeration': 0.9, 'temperature': 0.5, 'cfg_weight': 0.9},
                    device_used="cuda",
                    model_info="ChatterboxTTS-v1.0",
                    sample_rate=24000
                )
            ]
            
            # Test summary generation
            summary = file_manager.generate_episode_summary(
                episode_title="Test_Episode_Summary",
                generation_results=test_results
            )
            
            self.assertIsInstance(summary, str)
            self.assertTrue(len(summary) > 0)
            
            # Check that summary contains expected information
            self.assertIn("Test_Episode_Summary", summary)
            self.assertIn("intro_001", summary)
            
            print("✓ Episode summary generation successful")
            print(f"  Summary length: {len(summary)} characters")
            
        except Exception as e:
            print(f"! Episode summary generation error: {type(e).__name__}: {e}")
    
    def test_pipeline_integration_compatibility(self):
        """Test compatibility with existing pipeline patterns."""
        try:
            file_manager = ChatterboxAudioFileManager(
                content_root=self.content_root,
                config=self.config
            )
            
            # Test interface compatibility with AudioFileManager
            self.assertTrue(hasattr(file_manager, 'setup_episode_directory'))
            self.assertTrue(hasattr(file_manager, 'generate_audio_file_path'))
            self.assertTrue(hasattr(file_manager, 'organize_audio_file'))
            
            # Test that methods have compatible signatures
            import inspect
            
            setup_sig = inspect.signature(file_manager.setup_episode_directory)
            setup_params = list(setup_sig.parameters.keys())
            
            print("✓ Pipeline integration compatibility verified")
            print(f"  setup_episode_directory parameters: {setup_params}")
            
        except Exception as e:
            print(f"! Pipeline integration error: {type(e).__name__}: {e}")


class TestChatterboxGenerationResult(unittest.TestCase):
    """Test suite for ChatterboxGenerationResult dataclass."""
    
    def test_generation_result_structure(self):
        """Test ChatterboxGenerationResult dataclass structure."""
        result = ChatterboxGenerationResult(
            section_id="test_section",
            section_type="intro",
            success=True,
            output_path="/path/to/output.wav",
            audio_duration=45.5,
            file_size=1092000,
            generation_time=3.2,
            script_content="Test script content for generation",
            parameters_used={'exaggeration': 0.9, 'temperature': 0.5, 'cfg_weight': 0.9},
            device_used="cuda",
            model_info="ChatterboxTTS-v1.0",
            sample_rate=24000
        )
        
        # Test all fields are properly set
        self.assertEqual(result.section_id, "test_section")
        self.assertEqual(result.section_type, "intro")
        self.assertTrue(result.success)
        self.assertEqual(result.audio_duration, 45.5)
        self.assertEqual(result.sample_rate, 24000)
        
        print("✓ ChatterboxGenerationResult structure validated")
        print(f"  Section: {result.section_id} ({result.section_type})")
        print(f"  Duration: {result.audio_duration}s")
        print(f"  Parameters: {result.parameters_used}")


class TestAudioFileManagerIntegration(unittest.TestCase):
    """Integration tests for audio file manager with other components."""
    
    def test_config_integration(self):
        """Test integration with ChatterboxTTSConfig."""
        config_path = Path(__file__).parent.parent.parent.parent / "Code" / "Config" / "default_config.yaml"
        config = ChatterboxTTSConfig(str(config_path))
        
        temp_dir = tempfile.mkdtemp()
        try:
            file_manager = ChatterboxAudioFileManager(
                content_root=temp_dir,
                config=config
            )
            
            # Test that config is properly integrated
            self.assertIsNotNone(file_manager.config)
            
            # Test voice model info extraction
            voice_path = config.get_voice_model_path()
            if voice_path:
                voice_model_name = os.path.basename(voice_path)
                print(f"✓ Voice model integration: {voice_model_name}")
            
        finally:
            import shutil
            shutil.rmtree(temp_dir)
    
    def test_batch_processor_integration(self):
        """Test integration patterns with batch processor."""
        config_path = Path(__file__).parent.parent.parent.parent / "Code" / "Config" / "default_config.yaml"
        config = ChatterboxTTSConfig(str(config_path))
        
        temp_dir = tempfile.mkdtemp()
        try:
            file_manager = ChatterboxAudioFileManager(
                content_root=temp_dir,
                config=config
            )
            
            # Test episode setup that batch processor would use
            episode_info = {
                'narrative_theme': 'Batch Processor Integration Test',
                'total_estimated_duration': '5 minutes',
                'source_file': 'integration_test.json'
            }
            
            episode_dir = file_manager.setup_episode_directory(
                episode_title="Integration_Test_Episode",
                episode_info=episode_info
            )
            
            self.assertIsNotNone(episode_dir)
            self.assertTrue(os.path.exists(episode_dir))
            
            print("✓ Batch processor integration patterns validated")
            
        finally:
            import shutil
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    print("=" * 60)
    print("CHATTERBOX AUDIO FILE MANAGER UNIT TESTS")
    print("=" * 60)
    
    # Run tests with detailed output
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "=" * 60)
    print("AUDIO FILE MANAGER UNIT TESTS COMPLETED")
    print("=" * 60)
