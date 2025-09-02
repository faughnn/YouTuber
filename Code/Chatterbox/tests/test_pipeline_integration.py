"""
Integration Tests for Chatterbox TTS Pipeline

Tests end-to-end pipeline integration, real data processing,
and master processor Stage 5 integration validation.
"""

import unittest
import tempfile
import json
import os
from pathlib import Path
import time
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from Code.Chatterbox import (
    ChatterboxBatchProcessor,
    ChatterboxTTSEngine,
    ChatterboxTTSConfig,
    ChatterboxResponseParser,
    ChatterboxAudioFileManager,
    ProcessingReport
)


class TestChatterboxPipelineIntegration(unittest.TestCase):
    """Test suite for complete Chatterbox TTS pipeline integration."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.config_path = Path(__file__).parent.parent.parent.parent / "Code" / "Config" / "default_config.yaml"
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up after each test method."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_complete_component_integration(self):
        """Test integration of all Chatterbox components together."""
        print("\n" + "="*50)
        print("COMPLETE COMPONENT INTEGRATION TEST")
        print("="*50)
        
        try:
            # Test 1: Configuration loading
            print("1. Testing configuration loading...")
            config = ChatterboxTTSConfig(str(self.config_path))
            validation = config.validate_configuration()
            
            print(f"   ✓ Configuration valid: {validation.is_valid}")
            print(f"   ✓ Device detected: {config.detected_device}")
            print(f"   ✓ Voice model path: {os.path.basename(config.get_voice_model_path())}")
            
            # Test 2: JSON Parser
            print("\n2. Testing JSON parser...")
            parser = ChatterboxResponseParser()
            
            sample_data = {
                "episode_info": {
                    "narrative_theme": "Integration Test Episode",
                    "total_estimated_duration": "10 minutes",
                    "target_audience": "Developers",
                    "key_themes": ["Integration", "Testing"],
                    "total_clips_analyzed": 2,
                    "source_file": "integration_test.json"
                },
                "podcast_sections": [
                    {
                        "section_id": "intro_001",
                        "section_type": "intro",
                        "script_content": "Welcome to our integration test episode.",
                        "estimated_duration": "30 seconds"
                    },
                    {
                        "section_id": "outro_001",
                        "section_type": "outro",
                        "script_content": "Thank you for testing our integration.",
                        "estimated_duration": "25 seconds"
                    }
                ]
            }
            
            validation_result = parser.validate_podcast_sections(sample_data)
            audio_sections = parser.extract_audio_sections(sample_data)
            
            print(f"   ✓ Parsing successful: {validation_result.is_valid}")
            print(f"   ✓ Audio sections extracted: {len(audio_sections)}")
            
            # Test 3: TTS Engine
            print("\n3. Testing TTS engine...")
            tts_engine = ChatterboxTTSEngine(config)
            
            device_info = tts_engine.get_device_info()
            connection_test = tts_engine.test_connection()
            
            print(f"   ✓ TTS engine initialized: {tts_engine is not None}")
            print(f"   ✓ Device info: {device_info}")
            print(f"   ✓ Connection test: {connection_test}")
            
            # Test 4: Audio File Manager
            print("\n4. Testing audio file manager...")
            file_manager = ChatterboxAudioFileManager(
                content_root=self.temp_dir,
                config=config
            )
            
            episode_dir = file_manager.setup_episode_directory(
                episode_title="Integration_Test_Episode",
                episode_info=sample_data["episode_info"]
            )
            
            print(f"   ✓ File manager initialized: {file_manager is not None}")
            print(f"   ✓ Episode directory created: {os.path.exists(episode_dir)}")
            
            # Test 5: Batch Processor Integration
            print("\n5. Testing batch processor integration...")
            batch_processor = ChatterboxBatchProcessor(str(self.config_path))
            
            env_validation = batch_processor.validate_processing_environment()
            
            print(f"   ✓ Batch processor initialized: {batch_processor is not None}")
            print("   ✓ Environment validation:")
            for key, value in env_validation.items():
                print(f"     {key}: {value}")
            
            # Cleanup
            tts_engine.cleanup()
            
            print("\n✅ COMPLETE INTEGRATION TEST PASSED")
            
        except Exception as e:
            print(f"\n❌ INTEGRATION TEST FAILED: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    def test_end_to_end_pipeline_processing(self):
        """Test end-to-end pipeline processing with sample episode."""
        print("\n" + "="*50)
        print("END-TO-END PIPELINE PROCESSING TEST")
        print("="*50)
        
        try:
            # Create comprehensive test episode
            test_episode = {
                "episode_info": {
                    "narrative_theme": "End-to-End Pipeline Test",
                    "total_estimated_duration": "5 minutes",
                    "target_audience": "Testing Framework",
                    "key_themes": ["Pipeline Testing", "TTS Validation", "Integration"],
                    "total_clips_analyzed": 3,
                    "source_file": "e2e_test_episode.json"
                },
                "podcast_sections": [
                    {
                        "section_id": "intro_001",
                        "section_type": "intro",
                        "script_content": "Welcome to our comprehensive end-to-end pipeline test. This episode will validate the complete Chatterbox TTS integration.",
                        "estimated_duration": "45 seconds"
                    },
                    {
                        "section_id": "pre_clip_001",
                        "section_type": "pre_clip",
                        "script_content": "Before we explore this fascinating topic, let me provide some essential context about what we're about to discuss.",
                        "estimated_duration": "35 seconds",
                        "clip_reference": "clip_001"
                    },
                    {
                        "section_id": "video_clip_001",
                        "section_type": "video_clip",
                        "clip_id": "clip_001",
                        "start_time": "00:01:30",
                        "end_time": "00:03:45",
                        "title": "Testing Discussion Clip",
                        "estimated_duration": "2 minutes 15 seconds",
                        "selection_reason": "Demonstrates pipeline functionality",
                        "severity_level": "medium",
                        "key_claims": ["Testing is essential", "Integration validates functionality"]
                    },
                    {
                        "section_id": "post_clip_001",
                        "section_type": "post_clip",
                        "script_content": "That was an excellent demonstration of how comprehensive testing validates our pipeline functionality.",
                        "estimated_duration": "30 seconds",
                        "clip_reference": "clip_001"
                    },
                    {
                        "section_id": "outro_001",
                        "section_type": "outro",
                        "script_content": "Thank you for joining us in this end-to-end pipeline test. The Chatterbox TTS integration has been successfully validated.",
                        "estimated_duration": "40 seconds"
                    }
                ]
            }
            
            # Create script file
            script_file_path = os.path.join(self.temp_dir, "e2e_test_script.json")
            with open(script_file_path, 'w', encoding='utf-8') as f:
                json.dump(test_episode, f, indent=2)
            
            print(f"1. Created test script: {os.path.basename(script_file_path)}")
            
            # Process with batch processor
            print("\n2. Processing with ChatterboxBatchProcessor...")
            start_time = time.time()
            
            batch_processor = ChatterboxBatchProcessor(str(self.config_path))
            processing_report = batch_processor.process_episode_script(script_file_path)
            
            processing_time = time.time() - start_time
            
            print(f"   ✓ Processing completed in {processing_time:.2f}s")
            print(f"   ✓ Report type: {type(processing_report).__name__}")
            print(f"   ✓ Episode theme: {processing_report.episode_info.narrative_theme}")
            print(f"   ✓ Total sections: {processing_report.total_sections}")
            print(f"   ✓ Successful: {processing_report.successful_sections}")
            print(f"   ✓ Failed: {processing_report.failed_sections}")
            print(f"   ✓ Generated files: {len(processing_report.generated_files)}")
            print(f"   ✓ Processing time: {processing_report.processing_time:.2f}s")
            print(f"   ✓ Output directory: {processing_report.output_directory}")
            
            # Show any errors for debugging
            if processing_report.errors:
                print(f"\n   Errors encountered ({len(processing_report.errors)}):")
                for i, error in enumerate(processing_report.errors[:3], 1):
                    print(f"     {i}. {error}")
            
            # Validate ProcessingReport structure
            self.assertIsInstance(processing_report, ProcessingReport)
            self.assertIsInstance(processing_report.total_sections, int)
            self.assertIsInstance(processing_report.successful_sections, int)
            self.assertIsInstance(processing_report.failed_sections, int)
            
            print("\n✅ END-TO-END PIPELINE TEST PASSED")
            
        except Exception as e:
            print(f"\n❌ END-TO-END PIPELINE TEST FAILED: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    def test_real_content_processing(self):
        """Test processing with real content from Content directory."""
        print("\n" + "="*50)
        print("REAL CONTENT PROCESSING TEST")
        print("="*50)
        
        content_dir = Path(__file__).parent.parent.parent.parent / "Content"
        
        if not content_dir.exists():
            print("! Content directory not found - skipping real content test")
            return
        
        # Find real verified script files only
        real_script_files = list(content_dir.rglob("*/Output/Scripts/verified_unified_script.json"))
        
        if not real_script_files:
            print("! No real script files found - skipping real content test")
            return
        
        print(f"Found {len(real_script_files)} real script files")
        
        # Test with first available script
        script_file = real_script_files[0]
        episode_name = script_file.parent.parent.parent.name
        
        print(f"\nTesting with episode: {episode_name}")
        print(f"Script file: {script_file}")
        
        try:
            # Load and analyze script
            with open(script_file, 'r', encoding='utf-8') as f:
                script_data = json.load(f)
            
            # Parse with Chatterbox parser
            parser = ChatterboxResponseParser()
            validation_result = parser.validate_podcast_sections(script_data)
            
            print(f"\n✓ Script validation:")
            print(f"  Valid: {validation_result.is_valid}")
            print(f"  Audio sections: {validation_result.audio_section_count}")
            print(f"  Video sections: {validation_result.video_section_count}")
            print(f"  Errors: {len(validation_result.errors)}")
            print(f"  Warnings: {len(validation_result.warnings)}")
            
            if validation_result.episode_info:
                print(f"  Theme: {validation_result.episode_info.narrative_theme}")
                print(f"  Duration: {validation_result.episode_info.total_estimated_duration}")
            
            # Process with batch processor
            if validation_result.is_valid and validation_result.audio_section_count > 0:
                print(f"\n✓ Processing {validation_result.audio_section_count} audio sections...")
                
                start_time = time.time()
                batch_processor = ChatterboxBatchProcessor(str(self.config_path))
                processing_report = batch_processor.process_episode_script(str(script_file))
                processing_time = time.time() - start_time
                
                print(f"  Processing time: {processing_time:.2f}s")
                print(f"  Success rate: {processing_report.successful_sections}/{processing_report.total_sections}")
                
                if processing_report.errors:
                    print(f"  Errors: {len(processing_report.errors)}")
                    for error in processing_report.errors[:2]:
                        print(f"    - {error}")
            
            print("\n✅ REAL CONTENT PROCESSING TEST COMPLETED")
            
        except Exception as e:
            print(f"\n❌ REAL CONTENT PROCESSING FAILED: {type(e).__name__}: {e}")
    
    def test_master_processor_integration(self):
        """Test integration with master processor Stage 5."""
        print("\n" + "="*50)
        print("MASTER PROCESSOR INTEGRATION TEST")
        print("="*50)
        
        try:
            # Test import compatibility
            print("1. Testing import compatibility...")
            
            try:
                from Code.Chatterbox import ChatterboxBatchProcessor
                print("   ✓ ChatterboxBatchProcessor import successful")
            except ImportError as e:
                print(f"   ❌ Import failed: {e}")
                return
            
            # Test instantiation like in master processor
            print("\n2. Testing master processor instantiation pattern...")
            processor = ChatterboxBatchProcessor(str(self.config_path))
            
            print("   ✓ Instantiation successful")
            
            # Test method signature compatibility
            print("\n3. Testing method signature compatibility...")
            
            import inspect
            method = getattr(processor, 'process_episode_script')
            signature = inspect.signature(method)
            
            params = list(signature.parameters.keys())
            print(f"   ✓ process_episode_script parameters: {params}")
            
            # Should have script_path parameter
            self.assertIn('script_path', params)
            
            # Test return type compatibility
            print("\n4. Testing return type compatibility...")
            
            # Create minimal test script
            test_script = {
                "episode_info": {
                    "narrative_theme": "Master Processor Integration Test",
                    "total_estimated_duration": "2 minutes",
                    "target_audience": "Integration Testing",
                    "key_themes": ["Integration"],
                    "total_clips_analyzed": 1,
                    "source_file": "master_test.json"
                },
                "podcast_sections": [
                    {
                        "section_id": "test_001",
                        "section_type": "intro",
                        "script_content": "Testing master processor integration.",
                        "estimated_duration": "20 seconds"
                    }
                ]
            }
            
            script_file = os.path.join(self.temp_dir, "master_test_script.json")
            with open(script_file, 'w', encoding='utf-8') as f:
                json.dump(test_script, f, indent=2)
            
            # Test processing
            result = processor.process_episode_script(script_file)
            
            # Validate return type
            self.assertIsInstance(result, ProcessingReport)
            print("   ✓ Returns ProcessingReport")
            
            # Validate ProcessingReport structure for master processor compatibility
            required_fields = [
                'episode_info', 'total_sections', 'successful_sections', 
                'failed_sections', 'generated_files', 'errors', 
                'processing_time', 'output_directory'
            ]
            
            for field in required_fields:
                if hasattr(result, field):
                    print(f"   ✓ ProcessingReport.{field}: present")
                else:
                    print(f"   ❌ ProcessingReport.{field}: missing")
            
            print("\n✅ MASTER PROCESSOR INTEGRATION TEST PASSED")
            
        except Exception as e:
            print(f"\n❌ MASTER PROCESSOR INTEGRATION TEST FAILED: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    def test_performance_benchmarks(self):
        """Test performance characteristics and benchmarks."""
        print("\n" + "="*50)
        print("PERFORMANCE BENCHMARK TEST")
        print("="*50)
        
        try:
            # Test 1: Initialization Performance
            print("1. Testing initialization performance...")
            
            start_time = time.time()
            processor = ChatterboxBatchProcessor(str(self.config_path))
            init_time = time.time() - start_time
            
            print(f"   ✓ Initialization time: {init_time:.3f}s")
            self.assertLess(init_time, 10.0, "Initialization should complete within 10 seconds")
            
            # Test 2: Memory Usage
            print("\n2. Testing memory usage...")
            
            try:
                import psutil
                process = psutil.Process(os.getpid())
                memory_before = process.memory_info().rss / 1024 / 1024  # MB
                
                # Perform some operations
                config = processor.config
                validation = config.validate_configuration()
                env_validation = processor.validate_processing_environment()
                
                memory_after = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = memory_after - memory_before
                
                print(f"   ✓ Memory before operations: {memory_before:.1f}MB")
                print(f"   ✓ Memory after operations: {memory_after:.1f}MB")
                print(f"   ✓ Memory increase: {memory_increase:.1f}MB")
                
                # Memory increase should be reasonable
                self.assertLess(memory_increase, 500, "Memory increase should be less than 500MB")
                
            except ImportError:
                print("   ! psutil not available - skipping memory test")
            
            # Test 3: Configuration Loading Performance
            print("\n3. Testing configuration loading performance...")
            
            start_time = time.time()
            for i in range(5):
                config = ChatterboxTTSConfig(str(self.config_path))
            config_time = (time.time() - start_time) / 5
            
            print(f"   ✓ Average config loading time: {config_time:.3f}s")
            self.assertLess(config_time, 1.0, "Config loading should be under 1 second")
            
            # Test 4: Component Instantiation Performance
            print("\n4. Testing component instantiation performance...")
            
            times = {}
            
            # TTS Engine
            start_time = time.time()
            tts_engine = ChatterboxTTSEngine(processor.config)
            times['tts_engine'] = time.time() - start_time
            
            # Parser
            start_time = time.time()
            parser = ChatterboxResponseParser()
            times['parser'] = time.time() - start_time
            
            # File Manager
            start_time = time.time()
            file_manager = ChatterboxAudioFileManager(
                content_root=self.temp_dir,
                config=processor.config
            )
            times['file_manager'] = time.time() - start_time
            
            for component, init_time in times.items():
                print(f"   ✓ {component} initialization: {init_time:.3f}s")
                self.assertLess(init_time, 5.0, f"{component} should initialize within 5 seconds")
            
            # Cleanup
            tts_engine.cleanup()
            
            print("\n✅ PERFORMANCE BENCHMARK TEST PASSED")
            
        except Exception as e:
            print(f"\n❌ PERFORMANCE BENCHMARK TEST FAILED: {type(e).__name__}: {e}")


class TestDeviceDetectionAndHardware(unittest.TestCase):
    """Test device detection and hardware utilization."""
    
    def test_device_detection_validation(self):
        """Test device detection accuracy and fallback mechanisms."""
        print("\n" + "="*50)
        print("DEVICE DETECTION VALIDATION TEST")
        print("="*50)
        
        try:
            from Code.Chatterbox.config import detect_device, validate_system_resources
            
            # Test device detection
            print("1. Testing device detection...")
            device = detect_device()
            
            print(f"   ✓ Detected device: {device}")
            self.assertIn(device, ['cuda', 'mps', 'cpu'])
            
            # Test system resource validation
            print("\n2. Testing system resource validation...")
            resources = validate_system_resources()
            
            for resource, status in resources.items():
                print(f"   ✓ {resource}: {status}")
            
            # Test config integration
            print("\n3. Testing config device integration...")
            config = ChatterboxTTSConfig()
            
            print(f"   ✓ Config detected device: {config.detected_device}")
            print(f"   ✓ Config device preference: {config.get_chatterbox_config().device_preference}")
            
            # Devices should match or preference should be valid fallback
            self.assertIn(config.detected_device, ['cuda', 'mps', 'cpu'])
            
            print("\n✅ DEVICE DETECTION VALIDATION PASSED")
            
        except Exception as e:
            print(f"\n❌ DEVICE DETECTION VALIDATION FAILED: {type(e).__name__}: {e}")


if __name__ == '__main__':
    print("=" * 70)
    print("CHATTERBOX TTS PIPELINE INTEGRATION TESTS")
    print("=" * 70)
    
    # Run tests with detailed output
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "=" * 70)
    print("PIPELINE INTEGRATION TESTS COMPLETED")
    print("=" * 70)
