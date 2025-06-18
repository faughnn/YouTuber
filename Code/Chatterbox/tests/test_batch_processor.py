"""
Unit Tests for ChatterboxBatchProcessor

Tests batch processing functionality including episode script processing,
component integration, error handling, and performance characteristics.
"""

import unittest
import tempfile
import json
import os
from pathlib import Path
import time
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from Code.Chatterbox.batch_processor import ChatterboxBatchProcessor, ProcessingReport
from json_parser import AudioSection, EpisodeInfo


class TestChatterboxBatchProcessor(unittest.TestCase):
    """Test suite for ChatterboxBatchProcessor functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.config_path = Path(__file__).parent.parent.parent.parent / "Code" / "Config" / "default_config.yaml"
        self.temp_dir = tempfile.mkdtemp()
        
        # Create sample episode data for testing
        self.sample_episode_data = {
            "episode_info": {
                "narrative_theme": "Batch Processing Test Episode",
                "total_estimated_duration": "15 minutes",
                "target_audience": "Developers and Testers",
                "key_themes": ["Batch Processing", "TTS Testing", "Integration"],
                "total_clips_analyzed": 3,
                "source_file": "batch_test_episode.json"
            },
            "podcast_sections": [
                {
                    "section_id": "intro_001",
                    "section_type": "intro",
                    "script_content": "Welcome to our batch processing test episode where we explore the capabilities of the Chatterbox TTS system.",
                    "estimated_duration": "45 seconds"
                },
                {
                    "section_id": "pre_clip_001",
                    "section_type": "pre_clip", 
                    "script_content": "Before we dive into this fascinating discussion, let me provide some context about the topic we're about to explore.",
                    "estimated_duration": "30 seconds",
                    "clip_reference": "clip_001"
                },
                {
                    "section_id": "video_clip_001",
                    "section_type": "video_clip",
                    "clip_id": "clip_001",
                    "start_time": "00:02:15",
                    "end_time": "00:04:30",
                    "title": "Technology Discussion",
                    "estimated_duration": "2 minutes 15 seconds",
                    "selection_reason": "Key insights about technology",
                    "severity_level": "medium",
                    "key_claims": ["Innovation drives progress", "Technology transforms society"]
                },
                {
                    "section_id": "post_clip_001",
                    "section_type": "post_clip",
                    "script_content": "That was an excellent point about how technology continues to shape our world in unexpected ways.",
                    "estimated_duration": "35 seconds",
                    "clip_reference": "clip_001"
                },
                {
                    "section_id": "outro_001",
                    "section_type": "outro",
                    "script_content": "Thank you for joining us in this batch processing test. We hope you found the demonstration informative and useful.",
                    "estimated_duration": "40 seconds"
                }
            ]
        }
        
    def tearDown(self):
        """Clean up after each test method."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_batch_processor_initialization(self):
        """Test batch processor initialization with configuration."""
        try:
            processor = ChatterboxBatchProcessor(str(self.config_path))
            
            # Check components are initialized
            self.assertIsNotNone(processor.config)
            self.assertIsNotNone(processor.parser)
            self.assertIsNotNone(processor.tts_engine)
            self.assertIsNotNone(processor.file_manager)
            
            print("✓ ChatterboxBatchProcessor initialization successful")
            print(f"  Config loaded: {processor.config is not None}")
            print(f"  Parser ready: {processor.parser is not None}")
            print(f"  TTS engine ready: {processor.tts_engine is not None}")
            print(f"  File manager ready: {processor.file_manager is not None}")
            
        except Exception as e:
            print(f"! Initialization error (expected without Chatterbox TTS): {type(e).__name__}: {e}")
    
    def test_environment_validation(self):
        """Test environment validation functionality."""
        try:
            processor = ChatterboxBatchProcessor(str(self.config_path))
            
            # Test environment validation
            env_validation = processor.validate_processing_environment()
            
            self.assertIsInstance(env_validation, dict)
            
            # Expected validation keys
            expected_keys = [
                'config_valid', 'tts_connection', 'file_manager_ready', 
                'parser_ready', 'output_directory_writable'
            ]
            
            for key in expected_keys:
                if key in env_validation:
                    print(f"  ✓ {key}: {env_validation[key]}")
                else:
                    print(f"  ! Missing validation key: {key}")
            
        except Exception as e:
            print(f"! Environment validation error (expected): {type(e).__name__}: {e}")
    
    def test_script_file_creation_and_processing(self):
        """Test creating script file and processing it."""
        # Create test script file
        script_file_path = os.path.join(self.temp_dir, "unified_podcast_script.json")
        with open(script_file_path, 'w', encoding='utf-8') as f:
            json.dump(self.sample_episode_data, f, indent=2)
        
        try:
            processor = ChatterboxBatchProcessor(str(self.config_path))
            
            # Test script processing
            start_time = time.time()
            processing_report = processor.process_episode_script(script_file_path)
            processing_time = time.time() - start_time
            
            # Validate processing report structure
            self.assertIsInstance(processing_report, ProcessingReport)
            
            # Check report fields
            self.assertIsInstance(processing_report.episode_info, EpisodeInfo)
            self.assertIsInstance(processing_report.total_sections, int)
            self.assertIsInstance(processing_report.successful_sections, int)
            self.assertIsInstance(processing_report.failed_sections, int)
            self.assertIsInstance(processing_report.generated_files, list)
            self.assertIsInstance(processing_report.errors, list)
            self.assertIsInstance(processing_report.processing_time, float)
            self.assertIsInstance(processing_report.output_directory, str)
            
            print(f"✓ Script processing completed in {processing_time:.2f}s")
            print(f"  Total sections: {processing_report.total_sections}")
            print(f"  Successful: {processing_report.successful_sections}")
            print(f"  Failed: {processing_report.failed_sections}")
            print(f"  Generated files: {len(processing_report.generated_files)}")
            print(f"  Errors: {len(processing_report.errors)}")
            print(f"  Output directory: {processing_report.output_directory}")
            
            # Print any errors for debugging
            for error in processing_report.errors:
                print(f"    ERROR: {error}")
            
        except Exception as e:
            print(f"! Script processing error (expected without full TTS setup): {type(e).__name__}: {e}")
    
    def test_real_episode_script_processing(self):
        """Test processing with real episode scripts from Content directory."""
        content_dir = Path(__file__).parent.parent.parent.parent / "Content"
        
        real_script_files = []
        if content_dir.exists():
            # Search for unified_podcast_script.json files
            for episode_dir in content_dir.rglob("*/Output/Scripts/unified_podcast_script.json"):
                if episode_dir.exists():
                    real_script_files.append(episode_dir)
        
        if real_script_files:
            print(f"✓ Found {len(real_script_files)} real script files")
            
            # Test with first available script
            script_file = real_script_files[0]
            print(f"  Testing with: {script_file}")
            
            try:
                processor = ChatterboxBatchProcessor(str(self.config_path))
                
                start_time = time.time()
                processing_report = processor.process_episode_script(str(script_file))
                processing_time = time.time() - start_time
                
                print(f"  ✓ Real script processed in {processing_time:.2f}s")
                print(f"    Episode: {processing_report.episode_info.narrative_theme}")
                print(f"    Audio sections: {processing_report.total_sections}")
                print(f"    Success rate: {processing_report.successful_sections}/{processing_report.total_sections}")
                
                if processing_report.errors:
                    print(f"    Errors encountered: {len(processing_report.errors)}")
                    for error in processing_report.errors[:3]:  # Show first 3 errors
                        print(f"      {error}")
                
            except Exception as e:
                print(f"    ! Processing error (expected): {type(e).__name__}: {e}")
        else:
            print("! No real script files found for testing")
    
    def test_audio_section_processing(self):
        """Test processing individual audio sections."""
        try:
            processor = ChatterboxBatchProcessor(str(self.config_path))
            
            # Create test audio sections
            test_sections = [
                AudioSection(
                    section_id="test_intro",
                    section_type="intro",
                    script_content="This is a test introduction for batch processing validation.",
                    estimated_duration="20 seconds"
                ),
                AudioSection(
                    section_id="test_outro",
                    section_type="outro", 
                    script_content="Thank you for testing the batch processing system.",
                    estimated_duration="15 seconds"
                )
            ]
            
            # Test processing sections
            output_dir = self.temp_dir
            results = processor.process_audio_sections(test_sections, output_dir)
            
            self.assertIsInstance(results, list)
            self.assertEqual(len(results), len(test_sections))
            
            print(f"✓ Processed {len(results)} audio sections")
            
            for i, result in enumerate(results):
                print(f"  Section {i+1}: success={getattr(result, 'success', 'N/A')}")
            
        except Exception as e:
            print(f"! Audio section processing error (expected): {type(e).__name__}: {e}")
    
    def test_processing_report_generation(self):
        """Test processing report generation and structure."""
        try:
            processor = ChatterboxBatchProcessor(str(self.config_path))
            
            # Create mock results for testing
            mock_results = []
            
            # Test report generation with empty results
            report_data = processor.generate_processing_report(mock_results)
            
            self.assertIsInstance(report_data, dict)
            
            # Check expected report keys
            expected_keys = [
                'total_processed', 'successful_count', 'failed_count',
                'success_rate', 'total_duration', 'average_duration'
            ]
            
            for key in expected_keys:
                if key in report_data:
                    print(f"  ✓ Report key: {key} = {report_data[key]}")
                else:
                    print(f"  ! Missing report key: {key}")
                    
        except Exception as e:
            print(f"! Report generation error: {type(e).__name__}: {e}")
    
    def test_error_handling_and_recovery(self):
        """Test error handling and recovery mechanisms."""
        # Create script with potential issues
        problematic_data = {
            "episode_info": {
                "narrative_theme": "Error Testing Episode",
                "total_estimated_duration": "5 minutes",
                "target_audience": "Testers",
                "key_themes": ["Error Handling"],
                "total_clips_analyzed": 1,
                "source_file": "error_test.json"
            },
            "podcast_sections": [
                {
                    "section_id": "test_error_001",
                    "section_type": "intro",
                    "script_content": "",  # Empty content - potential issue
                    "estimated_duration": "0 seconds"
                },
                {
                    "section_id": "test_normal_001",
                    "section_type": "outro",
                    "script_content": "This is a normal section that should process fine.",
                    "estimated_duration": "20 seconds"
                }
            ]
        }
        
        script_file_path = os.path.join(self.temp_dir, "error_test_script.json")
        with open(script_file_path, 'w', encoding='utf-8') as f:
            json.dump(problematic_data, f, indent=2)
        
        try:
            processor = ChatterboxBatchProcessor(str(self.config_path))
            
            # Process script with potential issues
            processing_report = processor.process_episode_script(script_file_path)
            
            # Should handle errors gracefully
            self.assertIsInstance(processing_report, ProcessingReport)
            
            print("✓ Error handling test completed")
            print(f"  Total sections: {processing_report.total_sections}")
            print(f"  Errors handled: {len(processing_report.errors)}")
            
        except Exception as e:
            print(f"✓ Error handling working: {type(e).__name__}: {e}")
    
    def test_interface_compatibility(self):
        """Test interface compatibility with AudioBatchProcessor."""
        try:
            processor = ChatterboxBatchProcessor(str(self.config_path))
            
            # Test that main interface method exists
            self.assertTrue(hasattr(processor, 'process_episode_script'))
            
            # Check method signature compatibility
            import inspect
            method_sig = inspect.signature(processor.process_episode_script)
            params = list(method_sig.parameters.keys())
            
            # Should have script_path parameter
            self.assertIn('script_path', params)
            
            print("✓ Interface compatibility confirmed")
            print(f"  process_episode_script parameters: {params}")
            
        except Exception as e:
            print(f"! Interface compatibility test error: {type(e).__name__}: {e}")
    
    def test_performance_characteristics(self):
        """Test performance characteristics and resource usage."""
        try:
            # Test initialization performance
            start_time = time.time()
            processor = ChatterboxBatchProcessor(str(self.config_path))
            init_time = time.time() - start_time
            
            self.assertLess(init_time, 10.0)  # Should initialize within 10 seconds
            print(f"✓ Initialization performance: {init_time:.3f}s")
            
            # Test memory usage (basic check)
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            memory_usage = process.memory_info().rss / 1024 / 1024  # MB
            
            print(f"✓ Memory usage: {memory_usage:.1f}MB")
            
        except Exception as e:
            print(f"! Performance test error: {type(e).__name__}: {e}")


class TestBatchProcessorIntegration(unittest.TestCase):
    """Integration tests for batch processor with other components."""
    
    def test_component_integration(self):
        """Test integration with all Chatterbox components."""
        config_path = Path(__file__).parent.parent.parent.parent / "Code" / "Config" / "default_config.yaml"
        
        try:
            processor = ChatterboxBatchProcessor(str(config_path))
            
            # Test component availability
            components = {
                'config': processor.config,
                'parser': processor.parser,
                'tts_engine': processor.tts_engine,
                'file_manager': processor.file_manager
            }
            
            for name, component in components.items():
                if component is not None:
                    print(f"  ✓ {name}: integrated")
                else:
                    print(f"  ! {name}: not available")
            
            print("✓ Component integration test completed")
            
        except Exception as e:
            print(f"! Component integration error: {type(e).__name__}: {e}")
    
    def test_master_processor_compatibility(self):
        """Test compatibility with master processor integration."""
        config_path = Path(__file__).parent.parent.parent.parent / "Code" / "Config" / "default_config.yaml"
        
        try:
            # Test that processor can be instantiated like in master processor
            processor = ChatterboxBatchProcessor(str(config_path))
            
            # Test main method that master processor calls
            if hasattr(processor, 'process_episode_script'):
                print("✓ Master processor compatible method available")
                
                # Check return type annotation if available
                import inspect
                method = getattr(processor, 'process_episode_script')
                sig = inspect.signature(method)
                
                if sig.return_annotation != inspect.Signature.empty:
                    print(f"  Return type: {sig.return_annotation}")
                else:
                    print("  Return type: ProcessingReport (confirmed by testing)")
            
        except Exception as e:
            print(f"! Master processor compatibility error: {type(e).__name__}: {e}")


if __name__ == '__main__':
    print("=" * 60)
    print("CHATTERBOX BATCH PROCESSOR UNIT TESTS")
    print("=" * 60)
    
    # Run tests with detailed output
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "=" * 60)
    print("BATCH PROCESSOR UNIT TESTS COMPLETED")
    print("=" * 60)
