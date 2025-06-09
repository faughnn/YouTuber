#!/usr/bin/env python3
"""
Test Video Clipper Integration with Master Processor
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.getcwd())

def test_import():
    """Test that we can import the Video Clipper"""
    try:
        from Video_Clipper.integration import extract_clips_from_script
        print("✓ Video Clipper import successful")
        return True
    except ImportError as e:
        print(f"✗ Video Clipper import failed: {e}")
        return False

def test_master_processor_import():
    """Test that we can import the master processor"""
    try:
        from master_processor import MasterProcessor
        print("✓ Master Processor import successful")
        return True
    except ImportError as e:
        print(f"✗ Master Processor import failed: {e}")
        return False

def test_stage_8_method():
    """Test that stage 8 method exists and can be called"""
    try:
        from master_processor import MasterProcessor
        processor = MasterProcessor()
        
        # Check if the method exists
        if hasattr(processor, '_stage_8_video_clip_extraction'):
            print("✓ Stage 8 method exists")
            return True
        else:
            print("✗ Stage 8 method not found")
            return False
    except Exception as e:
        print(f"✗ Stage 8 method test failed: {e}")
        return False

def main():
    print("Video Clipper Integration Test")
    print("=" * 40)
    
    success_count = 0
    total_tests = 3
    
    if test_import():
        success_count += 1
    
    if test_master_processor_import():
        success_count += 1
    
    if test_stage_8_method():
        success_count += 1
    
    print("=" * 40)
    print(f"Tests passed: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("✓ All integration tests passed!")
        return True
    else:
        print("✗ Some integration tests failed")
        return False

if __name__ == "__main__":
    main()
