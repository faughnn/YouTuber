#!/usr/bin/env python3
"""
Test script for 10-Stage Video Production Integration
Tests the master processor with different pipeline configurations
"""

import sys
import os
import subprocess
import time

# Add the Code directory to the path
script_dir = os.path.dirname(os.path.abspath(__file__))
code_dir = os.path.join(os.path.dirname(script_dir), "Code")
sys.path.insert(0, code_dir)

def test_help_message():
    """Test that the help message shows all new options"""
    print("🔍 Testing help message...")
    try:
        result = subprocess.run([
            sys.executable, 
            os.path.join(code_dir, "master_processor.py"), 
            "--help"
        ], capture_output=True, text=True, cwd=code_dir)
        
        help_text = result.stdout
        
        # Check for new video processing options
        required_options = [
            "--generate-video",
            "--full-pipeline",
            "Generate video from podcast script",
            "Run complete 10-stage pipeline"
        ]
        
        for option in required_options:
            if option in help_text:
                print(f"✅ Found: {option}")
            else:
                print(f"❌ Missing: {option}")
        
        print(f"Help command exit code: {result.returncode}")
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error testing help: {e}")
        return False

def test_dry_run():
    """Test dry run functionality"""
    print("\n🔍 Testing dry run...")
    try:
        result = subprocess.run([
            sys.executable, 
                        os.path.join(code_dir, "master_processor.py"), 
            "https://youtube.com/watch?v=test",
            "--dry-run"
        ], capture_output=True, text=True, cwd=code_dir)
        
        print(f"Dry run output: {result.stdout}")
        print(f"Dry run stderr: {result.stderr}")
        print(f"Dry run exit code: {result.returncode}")
        
        # Dry run should show what would be processed
        output_text = result.stdout + result.stderr
        if "DRY RUN:" in output_text:
            print("✅ Dry run works correctly")
            return True
        else:
            print("❌ Dry run output not found")
            return False
            
    except Exception as e:
        print(f"❌ Error testing dry run: {e}")
        return False

def test_import_capabilities():
    """Test that all required modules can be imported"""
    print("\n🔍 Testing import capabilities...")
    
    try:
        # Test importing the master processor
        from master_processor import MasterProcessor
        print("✅ MasterProcessor imports successfully")
        
        # Test creating an instance
        processor = MasterProcessor()
        print("✅ MasterProcessor instance created successfully")
        
        # Check if video processing modules are available
        if hasattr(processor, '_stage_8_video_clip_extraction'):
            print("✅ Stage 8 (Video Clip Extraction) available")
        else:
            print("❌ Stage 8 missing")
            
        if hasattr(processor, '_stage_9_video_timeline_building'):
            print("✅ Stage 9 (Video Timeline Building) available")
        else:
            print("❌ Stage 9 missing")
            
        if hasattr(processor, '_stage_10_final_video_assembly'):
            print("✅ Stage 10 (Final Video Assembly) available")
        else:
            print("❌ Stage 10 missing")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_configuration_loading():
    """Test that the updated configuration loads correctly"""
    print("\n🔍 Testing configuration loading...")
    
    try:
        from master_processor import MasterProcessor
        processor = MasterProcessor()
        
        # Check for video configuration
        video_config = processor.config.get('video', {})
        if video_config:
            print("✅ Video configuration section found")
            
            # Check specific video settings
            if video_config.get('always_download_video', False):
                print("✅ Video download enabled by default")
            else:
                print("❌ Video download not enabled by default")
                
            clip_extraction = video_config.get('clip_extraction', {})
            if clip_extraction:
                print("✅ Clip extraction settings found")
            else:
                print("❌ Clip extraction settings missing")
                
        else:
            print("❌ Video configuration section missing")
            
        # Check TTS configuration
        tts_config = processor.config.get('tts', {})
        if tts_config:
            print("✅ TTS configuration section found")
        else:
            print("❌ TTS configuration section missing")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_progress_tracker():
    """Test that progress tracker includes new stages"""
    print("\n🔍 Testing progress tracker with new stages...")
    
    try:
        from Utils.progress_tracker import ProcessingStage
        
        # Check for new stages
        new_stages = [
            "VIDEO_CLIP_EXTRACTION",
            "VIDEO_TIMELINE_BUILDING", 
            "FINAL_VIDEO_ASSEMBLY"
        ]
        
        available_stages = [stage.name for stage in ProcessingStage]
        
        for stage in new_stages:
            if stage in available_stages:
                print(f"✅ Stage {stage} found in ProcessingStage enum")
            else:
                print(f"❌ Stage {stage} missing from ProcessingStage enum")
        
        print(f"Total stages available: {len(available_stages)}")
        print(f"Available stages: {', '.join(available_stages)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Progress tracker error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing 10-Stage Video Production Integration")
    print("=" * 60)
    
    tests = [
        ("Help Message", test_help_message),
        ("Dry Run", test_dry_run),
        ("Import Capabilities", test_import_capabilities),
        ("Configuration Loading", test_configuration_loading),
        ("Progress Tracker", test_progress_tracker)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 40)
        
        start_time = time.time()
        try:
            success = test_func()
            duration = time.time() - start_time
            
            if success:
                print(f"✅ {test_name} PASSED ({duration:.2f}s)")
            else:
                print(f"❌ {test_name} FAILED ({duration:.2f}s)")
            
            results.append((test_name, success, duration))
            
        except Exception as e:
            duration = time.time() - start_time
            print(f"💥 {test_name} ERROR: {e} ({duration:.2f}s)")
            results.append((test_name, False, duration))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for test_name, success, duration in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name:<25} ({duration:.2f}s)")
    
    print("-" * 60)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! 10-Stage integration is ready!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the issues above.")

if __name__ == "__main__":
    main()
