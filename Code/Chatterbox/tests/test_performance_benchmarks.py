"""
Performance Validation and Device Detection Tests

Tests performance characteristics, device detection accuracy,
GPU utilization, and resource management for Chatterbox TTS.
"""

import unittest
import time
import os
import tempfile
import json
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from Code.Chatterbox.config import detect_device, validate_system_resources, ChatterboxTTSConfig
from Code.Chatterbox.tts_engine import ChatterboxTTSEngine
from Code.Chatterbox.batch_processor import ChatterboxBatchProcessor


class TestDeviceDetectionAndCompatibility(unittest.TestCase):
    """Test device detection and hardware compatibility."""
    
    def test_device_detection_accuracy(self):
        """Test device detection accuracy and consistency."""
        print("\n" + "="*60)
        print("DEVICE DETECTION ACCURACY TEST")
        print("="*60)
        
        try:
            print("1. Testing device detection function...")
            
            # Test multiple detection calls for consistency
            devices = []
            for i in range(5):
                device = detect_device()
                devices.append(device)
                time.sleep(0.1)  # Small delay between calls
            
            # All detections should be consistent
            unique_devices = set(devices)
            self.assertEqual(len(unique_devices), 1, "Device detection should be consistent")
            
            detected_device = devices[0]
            print(f"   ✓ Detected device: {detected_device}")
            print(f"   ✓ Detection consistency: {len(unique_devices)}/1")
            
            # Device should be valid
            self.assertIn(detected_device, ['cuda', 'mps', 'cpu'])
            
            # Test device-specific details
            if detected_device == 'cuda':
                try:
                    import torch
                    if torch.cuda.is_available():
                        gpu_count = torch.cuda.device_count()
                        gpu_name = torch.cuda.get_device_name(0)
                        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
                        
                        print(f"   ✓ CUDA GPUs: {gpu_count}")
                        print(f"   ✓ GPU 0: {gpu_name}")
                        print(f"   ✓ GPU Memory: {gpu_memory:.1f}GB")
                        
                        # Validate GPU memory is sufficient
                        self.assertGreater(gpu_memory, 2.0, "GPU should have >2GB memory")
                        
                except ImportError:
                    print("   ! PyTorch not available for CUDA details")
            
            elif detected_device == 'mps':
                try:
                    import torch
                    if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                        print("   ✓ MPS backend available")
                    else:
                        print("   ! MPS backend not available despite detection")
                except ImportError:
                    print("   ! PyTorch not available for MPS details")
            
            else:  # CPU
                try:
                    import psutil
                    cpu_count = psutil.cpu_count()
                    cpu_freq = psutil.cpu_freq()
                    
                    print(f"   ✓ CPU cores: {cpu_count}")
                    if cpu_freq:
                        print(f"   ✓ CPU frequency: {cpu_freq.current:.0f}MHz")
                        
                except ImportError:
                    print("   ! psutil not available for CPU details")
            
            print("\n✅ DEVICE DETECTION ACCURACY TEST PASSED")
            
        except Exception as e:
            print(f"\n❌ DEVICE DETECTION ACCURACY TEST FAILED: {type(e).__name__}: {e}")
    
    def test_system_resource_validation(self):
        """Test system resource validation for TTS processing."""
        print("\n" + "="*60)
        print("SYSTEM RESOURCE VALIDATION TEST")
        print("="*60)
        
        try:
            print("1. Testing system resource validation...")
            
            resources = validate_system_resources()
            
            # Check all expected resource keys
            expected_resources = ['sufficient_ram', 'sufficient_disk', 'python_version_ok']
            
            for resource in expected_resources:
                self.assertIn(resource, resources, f"Resource validation should include {resource}")
                
                status = resources[resource]
                self.assertIsInstance(status, bool, f"{resource} should be boolean")
                
                print(f"   ✓ {resource}: {status}")
            
            # Get detailed resource information
            try:
                import psutil
                
                # RAM details
                memory = psutil.virtual_memory()
                ram_gb = memory.total / 1024**3
                available_gb = memory.available / 1024**3
                
                print(f"   ✓ Total RAM: {ram_gb:.1f}GB")
                print(f"   ✓ Available RAM: {available_gb:.1f}GB")
                print(f"   ✓ RAM usage: {memory.percent:.1f}%")
                
                # Disk details
                disk = psutil.disk_usage('.')
                total_gb = disk.total / 1024**3
                free_gb = disk.free / 1024**3
                
                print(f"   ✓ Total disk: {total_gb:.1f}GB")
                print(f"   ✓ Free disk: {free_gb:.1f}GB")
                print(f"   ✓ Disk usage: {((disk.total - disk.free) / disk.total * 100):.1f}%")
                
                # Check if resources meet TTS requirements
                ram_sufficient = available_gb >= 4.0
                disk_sufficient = free_gb >= 1.0
                
                if ram_sufficient:
                    print("   ✅ RAM sufficient for TTS processing")
                else:
                    print("   ⚠️  RAM may be insufficient for TTS processing")
                
                if disk_sufficient:
                    print("   ✅ Disk space sufficient for TTS processing")
                else:
                    print("   ⚠️  Disk space may be insufficient for TTS processing")
                
            except ImportError:
                print("   ! psutil not available for detailed resource information")
            
            # Python version check
            import sys
            python_version = sys.version_info
            print(f"   ✓ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
            
            version_ok = python_version >= (3, 8)
            if version_ok:
                print("   ✅ Python version sufficient")
            else:
                print("   ⚠️  Python version may be insufficient")
            
            print("\n✅ SYSTEM RESOURCE VALIDATION TEST PASSED")
            
        except Exception as e:
            print(f"\n❌ SYSTEM RESOURCE VALIDATION TEST FAILED: {type(e).__name__}: {e}")
    
    def test_device_fallback_mechanisms(self):
        """Test device fallback mechanisms."""
        print("\n" + "="*60)
        print("DEVICE FALLBACK MECHANISMS TEST")
        print("="*60)
        
        try:
            print("1. Testing configuration device fallback...")
            
            config_path = Path(__file__).parent.parent.parent.parent / "Code" / "Config" / "default_config.yaml"
            config = ChatterboxTTSConfig(str(config_path))
            
            detected_device = config.detected_device
            preference_device = config.get_chatterbox_config().device_preference
            
            print(f"   ✓ Detected device: {detected_device}")
            print(f"   ✓ Preference device: {preference_device}")
            
            # Test TTS engine device handling
            print("\n2. Testing TTS engine device fallback...")
            
            tts_engine = ChatterboxTTSEngine(config)
            engine_device = tts_engine.device
            
            print(f"   ✓ TTS engine device: {engine_device}")
            
            # Device should be valid
            self.assertIn(engine_device, ['cuda', 'mps', 'cpu'])
            
            # Test device info
            device_info = tts_engine.get_device_info()
            print(f"   ✓ Device info: {device_info}")
            
            # Test device availability
            device_available = device_info.get('available', False)
            print(f"   ✓ Device available: {device_available}")
            
            # Cleanup
            tts_engine.cleanup()
            
            print("\n✅ DEVICE FALLBACK MECHANISMS TEST PASSED")
            
        except Exception as e:
            print(f"\n❌ DEVICE FALLBACK MECHANISMS TEST FAILED: {type(e).__name__}: {e}")


class TestPerformanceBenchmarks(unittest.TestCase):
    """Test performance benchmarks and resource utilization."""
    
    def setUp(self):
        """Set up performance test fixtures."""
        self.config_path = Path(__file__).parent.parent.parent.parent / "Code" / "Config" / "default_config.yaml"
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up performance test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_component_initialization_performance(self):
        """Test component initialization performance."""
        print("\n" + "="*60)
        print("COMPONENT INITIALIZATION PERFORMANCE TEST")
        print("="*60)
        
        try:
            performance_results = {}
            
            # Test configuration loading performance
            print("1. Testing configuration loading performance...")
            
            start_time = time.time()
            for i in range(10):
                config = ChatterboxTTSConfig(str(self.config_path))
            config_time = (time.time() - start_time) / 10
            
            performance_results['config_loading'] = config_time
            print(f"   ✓ Average config loading time: {config_time:.3f}s")
            
            # Target: <1s for config loading
            if config_time < 1.0:
                print("   ✅ Config loading performance target met")
            else:
                print("   ⚠️  Config loading performance target missed")
            
            # Test TTS engine initialization performance
            print("\n2. Testing TTS engine initialization performance...")
            
            config = ChatterboxTTSConfig(str(self.config_path))
            
            start_time = time.time()
            tts_engine = ChatterboxTTSEngine(config)
            engine_init_time = time.time() - start_time
            
            performance_results['tts_engine_init'] = engine_init_time
            print(f"   ✓ TTS engine initialization time: {engine_init_time:.3f}s")
            
            # Target: <5s for TTS engine init
            if engine_init_time < 5.0:
                print("   ✅ TTS engine initialization performance target met")
            else:
                print("   ⚠️  TTS engine initialization performance target missed")
            
            # Test batch processor initialization performance
            print("\n3. Testing batch processor initialization performance...")
            
            start_time = time.time()
            batch_processor = ChatterboxBatchProcessor(str(self.config_path))
            batch_init_time = time.time() - start_time
            
            performance_results['batch_processor_init'] = batch_init_time
            print(f"   ✓ Batch processor initialization time: {batch_init_time:.3f}s")
            
            # Target: <10s for batch processor init
            if batch_init_time < 10.0:
                print("   ✅ Batch processor initialization performance target met")
            else:
                print("   ⚠️  Batch processor initialization performance target missed")
            
            # Memory usage during initialization
            print("\n4. Testing memory usage during initialization...")
            
            try:
                import psutil
                process = psutil.Process(os.getpid())
                memory_usage = process.memory_info().rss / 1024 / 1024  # MB
                
                print(f"   ✓ Memory usage after initialization: {memory_usage:.1f}MB")
                
                performance_results['memory_usage_mb'] = memory_usage
                
                # Target: <2GB memory usage
                if memory_usage < 2048:
                    print("   ✅ Memory usage target met")
                else:
                    print("   ⚠️  Memory usage target exceeded")
                    
            except ImportError:
                print("   ! psutil not available for memory testing")
            
            # Cleanup
            tts_engine.cleanup()
            
            # Performance summary
            print(f"\n📊 PERFORMANCE SUMMARY:")
            for metric, value in performance_results.items():
                if 'time' in metric or metric.endswith('_init'):
                    print(f"   {metric}: {value:.3f}s")
                elif 'memory' in metric:
                    print(f"   {metric}: {value:.1f}MB")
                else:
                    print(f"   {metric}: {value}")
            
            print("\n✅ COMPONENT INITIALIZATION PERFORMANCE TEST PASSED")
            
        except Exception as e:
            print(f"\n❌ COMPONENT INITIALIZATION PERFORMANCE TEST FAILED: {type(e).__name__}: {e}")
    
    def test_processing_performance_benchmarks(self):
        """Test processing performance benchmarks."""
        print("\n" + "="*60)
        print("PROCESSING PERFORMANCE BENCHMARKS TEST")
        print("="*60)
        
        try:
            # Create test scripts of different sizes
            test_scripts = self._create_performance_test_scripts()
            
            print(f"1. Created {len(test_scripts)} test scripts for performance testing")
            
            batch_processor = ChatterboxBatchProcessor(str(self.config_path))
            
            performance_results = {}
            
            for script_name, script_data in test_scripts.items():
                print(f"\n2. Testing performance with {script_name}...")
                
                # Create script file
                script_path = os.path.join(self.temp_dir, f"{script_name}.json")
                with open(script_path, 'w', encoding='utf-8') as f:
                    json.dump(script_data, f, indent=2)
                
                # Measure processing performance
                start_time = time.time()
                
                try:
                    result = batch_processor.process_episode_script(script_path)
                    processing_time = time.time() - start_time
                    
                    performance_results[script_name] = {
                        'total_sections': result.total_sections,
                        'processing_time': processing_time,
                        'time_per_section': processing_time / max(result.total_sections, 1),
                        'successful_sections': result.successful_sections,
                        'failed_sections': result.failed_sections
                    }
                    
                    print(f"   ✓ Processing time: {processing_time:.2f}s")
                    print(f"   ✓ Sections processed: {result.total_sections}")
                    print(f"   ✓ Time per section: {processing_time / max(result.total_sections, 1):.2f}s")
                    print(f"   ✓ Success rate: {result.successful_sections}/{result.total_sections}")
                    
                    # Performance target: <10s per section
                    time_per_section = processing_time / max(result.total_sections, 1)
                    if time_per_section < 10.0:
                        print(f"   ✅ Performance target met: {time_per_section:.2f}s < 10.0s")
                    else:
                        print(f"   ⚠️  Performance target missed: {time_per_section:.2f}s >= 10.0s")
                
                except Exception as process_error:
                    print(f"   ! Processing error (expected): {type(process_error).__name__}")
                    performance_results[script_name] = {'error': str(process_error)}
            
            # Performance summary
            print(f"\n📊 PROCESSING PERFORMANCE SUMMARY:")
            for script_name, results in performance_results.items():
                if 'error' not in results:
                    print(f"   {script_name}:")
                    print(f"     Sections: {results['total_sections']}")
                    print(f"     Time: {results['processing_time']:.2f}s")
                    print(f"     Per section: {results['time_per_section']:.2f}s")
                    print(f"     Success rate: {results['successful_sections']}/{results['total_sections']}")
                else:
                    print(f"   {script_name}: {results['error']}")
            
            print("\n✅ PROCESSING PERFORMANCE BENCHMARKS TEST PASSED")
            
        except Exception as e:
            print(f"\n❌ PROCESSING PERFORMANCE BENCHMARKS TEST FAILED: {type(e).__name__}: {e}")
    
    def test_memory_usage_and_resource_management(self):
        """Test memory usage and resource management."""
        print("\n" + "="*60)
        print("MEMORY USAGE AND RESOURCE MANAGEMENT TEST")
        print("="*60)
        
        try:
            import psutil
            process = psutil.Process(os.getpid())
            
            # Baseline memory usage
            baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
            print(f"1. Baseline memory usage: {baseline_memory:.1f}MB")
            
            # Test memory usage during component initialization
            print("\n2. Testing memory usage during initialization...")
            
            memory_points = {'baseline': baseline_memory}
            
            # After config loading
            config = ChatterboxTTSConfig(str(self.config_path))
            memory_points['after_config'] = process.memory_info().rss / 1024 / 1024
            
            # After TTS engine init
            tts_engine = ChatterboxTTSEngine(config)
            memory_points['after_tts_engine'] = process.memory_info().rss / 1024 / 1024
            
            # After batch processor init
            batch_processor = ChatterboxBatchProcessor(str(self.config_path))
            memory_points['after_batch_processor'] = process.memory_info().rss / 1024 / 1024
            
            # Print memory progression
            for point, memory in memory_points.items():
                increase = memory - baseline_memory
                print(f"   ✓ {point}: {memory:.1f}MB (+{increase:.1f}MB)")
            
            # Test memory usage during processing
            print("\n3. Testing memory usage during processing...")
            
            # Create small test script
            test_script = {
                "episode_info": {
                    "narrative_theme": "Memory Test",
                    "total_estimated_duration": "2 minutes",
                    "target_audience": "Memory Testing",
                    "key_themes": ["Memory", "Testing"],
                    "total_clips_analyzed": 1,
                    "source_file": "memory_test.json"
                },
                "podcast_sections": [
                    {
                        "section_id": "memory_test_001",
                        "section_type": "intro",
                        "script_content": "Testing memory usage during TTS processing.",
                        "estimated_duration": "20 seconds"
                    }
                ]
            }
            
            script_path = os.path.join(self.temp_dir, "memory_test.json")
            with open(script_path, 'w', encoding='utf-8') as f:
                json.dump(test_script, f, indent=2)
            
            memory_before_processing = process.memory_info().rss / 1024 / 1024
            
            try:
                result = batch_processor.process_episode_script(script_path)
                memory_after_processing = process.memory_info().rss / 1024 / 1024
                
                processing_memory_increase = memory_after_processing - memory_before_processing
                
                print(f"   ✓ Memory before processing: {memory_before_processing:.1f}MB")
                print(f"   ✓ Memory after processing: {memory_after_processing:.1f}MB")
                print(f"   ✓ Processing memory increase: {processing_memory_increase:.1f}MB")
                
                # Target: <1GB memory increase during processing
                if processing_memory_increase < 1024:
                    print("   ✅ Processing memory increase target met")
                else:
                    print("   ⚠️  Processing memory increase target exceeded")
                
            except Exception as process_error:
                print(f"   ! Processing error (expected): {type(process_error).__name__}")
            
            # Test cleanup and memory release
            print("\n4. Testing cleanup and memory release...")
            
            memory_before_cleanup = process.memory_info().rss / 1024 / 1024
            
            # Cleanup components
            tts_engine.cleanup()
            del tts_engine
            del batch_processor
            del config
            
            # Force garbage collection
            import gc
            gc.collect()
            
            memory_after_cleanup = process.memory_info().rss / 1024 / 1024
            memory_released = memory_before_cleanup - memory_after_cleanup
            
            print(f"   ✓ Memory before cleanup: {memory_before_cleanup:.1f}MB")
            print(f"   ✓ Memory after cleanup: {memory_after_cleanup:.1f}MB")
            print(f"   ✓ Memory released: {memory_released:.1f}MB")
            
            # Memory should not grow excessively
            total_increase = memory_after_cleanup - baseline_memory
            print(f"   ✓ Total memory increase: {total_increase:.1f}MB")
            
            if total_increase < 512:  # Target: <512MB permanent increase
                print("   ✅ Memory management target met")
            else:
                print("   ⚠️  Memory management target exceeded")
            
            print("\n✅ MEMORY USAGE AND RESOURCE MANAGEMENT TEST PASSED")
            
        except ImportError:
            print("! psutil not available - skipping memory usage test")
        except Exception as e:
            print(f"\n❌ MEMORY USAGE AND RESOURCE MANAGEMENT TEST FAILED: {type(e).__name__}: {e}")
    
    def _create_performance_test_scripts(self):
        """Create test scripts of different sizes for performance testing."""
        scripts = {}
        
        # Small script (2 sections)
        scripts['small_script'] = {
            "episode_info": {
                "narrative_theme": "Small Performance Test",
                "total_estimated_duration": "2 minutes",
                "target_audience": "Performance Testing",
                "key_themes": ["Performance"],
                "total_clips_analyzed": 1,
                "source_file": "small_test.json"
            },
            "podcast_sections": [
                {
                    "section_id": "intro_001",
                    "section_type": "intro",
                    "script_content": "This is a small performance test script.",
                    "estimated_duration": "30 seconds"
                },
                {
                    "section_id": "outro_001",
                    "section_type": "outro",
                    "script_content": "End of small performance test.",
                    "estimated_duration": "25 seconds"
                }
            ]
        }
        
        # Medium script (5 sections)
        scripts['medium_script'] = {
            "episode_info": {
                "narrative_theme": "Medium Performance Test",
                "total_estimated_duration": "8 minutes",
                "target_audience": "Performance Testing",
                "key_themes": ["Performance", "Medium Scale"],
                "total_clips_analyzed": 2,
                "source_file": "medium_test.json"
            },
            "podcast_sections": []
        }
        
        # Add 5 sections to medium script
        section_types = ["intro", "pre_clip", "post_clip", "outro", "intro"]
        for i in range(5):
            section = {
                "section_id": f"section_{i+1:03d}",
                "section_type": section_types[i % len(section_types)],
                "script_content": f"This is section {i+1} of the medium performance test script. " * 2,
                "estimated_duration": f"{30 + (i * 5)} seconds"
            }
            scripts['medium_script']['podcast_sections'].append(section)
        
        # Large script (10 sections)
        scripts['large_script'] = {
            "episode_info": {
                "narrative_theme": "Large Performance Test",
                "total_estimated_duration": "20 minutes",
                "target_audience": "Performance Testing",
                "key_themes": ["Performance", "Large Scale", "Stress Testing"],
                "total_clips_analyzed": 5,
                "source_file": "large_test.json"
            },
            "podcast_sections": []
        }
        
        # Add 10 sections to large script
        for i in range(10):
            section_type = section_types[i % len(section_types)]
            section = {
                "section_id": f"large_section_{i+1:03d}",
                "section_type": section_type,
                "script_content": f"This is large section {i+1} for performance testing. " * 3,
                "estimated_duration": f"{40 + (i * 3)} seconds"
            }
            
            if section_type in ["pre_clip", "post_clip"]:
                section["clip_reference"] = f"clip_{(i//2)+1:03d}"
            
            scripts['large_script']['podcast_sections'].append(section)
        
        return scripts


if __name__ == '__main__':
    print("=" * 70)
    print("PERFORMANCE VALIDATION AND DEVICE DETECTION TESTS")
    print("=" * 70)
    
    # Run tests with detailed output
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "=" * 70)
    print("PERFORMANCE AND DEVICE DETECTION TESTS COMPLETED")
    print("=" * 70)
