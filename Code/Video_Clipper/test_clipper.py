"""
Test Module for Video Clipper

This module provides test functions to validate the video clipper implementation.
"""

import os
import json
import tempfile
import logging
import sys
from pathlib import Path
from typing import Dict, List

# Add the Code directory to the path for testing
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Video_Clipper.script_parser import UnifiedScriptParser, VideoClipSpec
from Video_Clipper.video_extractor import VideoClipExtractor
from Video_Clipper.integration import extract_clips_from_script, get_video_clips_info
from Video_Clipper.config import get_default_config, validate_config


def test_timestamp_parsing():
    """Test timestamp parsing functionality"""
    print("Testing timestamp parsing...")
    
    parser = UnifiedScriptParser()
    
    test_cases = [
        ("1:03:55.06", 3835.06),
        ("03:55.06", 235.06),
        ("1:03:55", 3835.0),
        ("03:55", 235.0),
        ("0:00:30.5", 30.5),
        ("2:30", 150.0)
    ]
    
    for timestamp, expected in test_cases:
        try:
            result = parser.parse_timestamp(timestamp)
            if abs(result - expected) < 0.001:
                print(f"✓ {timestamp} -> {result}s (expected {expected}s)")
            else:
                print(f"✗ {timestamp} -> {result}s (expected {expected}s)")
        except Exception as e:
            print(f"✗ {timestamp} -> Error: {e}")
    
    print()


def test_script_parsing_with_sample():
    """Test script parsing with a sample unified script"""
    print("Testing script parsing...")
    
    # Create sample script data
    sample_script = {
        "narrative_theme": "Test Theme",
        "podcast_sections": [
            {
                "section_type": "intro",
                "section_id": "intro_001",
                "script_content": "Test intro",
                "estimated_duration": "30s",
                "audio_tone": "enthusiastic"
            },
            {
                "section_type": "video_clip",
                "section_id": "video_clip_001",
                "clip_id": "test_clip_001",
                "start_time": "1:03:55.06",
                "end_time": "1:04:11.28",
                "title": "Test Video Clip",
                "selection_reason": "Test reason",
                "severity_level": "HIGH",
                "key_claims": ["Test claim 1", "Test claim 2"],
                "estimated_duration": "16s"
            },
            {
                "section_type": "post_clip",
                "section_id": "post_clip_001",
                "clip_reference": "test_clip_001",
                "script_content": "Test analysis",
                "estimated_duration": "2min",
                "audio_tone": "analytical"
            }
        ]
    }
    
    # Create temporary script file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_script, f, indent=2)
        temp_script_path = f.name
    
    try:
        parser = UnifiedScriptParser()
        clips = parser.parse_script_file(temp_script_path)
        
        if len(clips) == 1:
            clip = clips[0]
            print(f"✓ Found 1 video clip: {clip.section_id}")
            print(f"  Title: {clip.title}")
            print(f"  Time: {clip.start_time} - {clip.end_time}")
            print(f"  Severity: {clip.severity_level}")
            
            # Test validation
            if parser.validate_clip_data(clip):
                print("✓ Clip validation passed")
            else:
                print("✗ Clip validation failed")
        else:
            print(f"✗ Expected 1 clip, found {len(clips)}")
    
    except Exception as e:
        print(f"✗ Script parsing failed: {e}")
    
    finally:
        # Clean up
        os.unlink(temp_script_path)
    
    print()


def test_config_validation():
    """Test configuration validation"""
    print("Testing configuration validation...")
    
    # Test default config
    try:
        default_config = get_default_config()
        validated = validate_config(default_config)
        print("✓ Default configuration validation passed")
    except Exception as e:
        print(f"✗ Default configuration validation failed: {e}")
    
    # Test custom config
    custom_config = {
        "start_buffer_seconds": 5.0,
        "video_quality": {
            "crf": 20,
            "preset": "medium"
        }
    }
    
    try:
        validated = validate_config(custom_config)
        print("✓ Custom configuration validation passed")
        print(f"  Start buffer: {validated['start_buffer_seconds']}s")
        print(f"  CRF: {validated['video_quality']['crf']}")
    except Exception as e:
        print(f"✗ Custom configuration validation failed: {e}")
    
    print()


def test_ffmpeg_availability():
    """Test FFmpeg availability"""
    print("Testing FFmpeg availability...")
    
    extractor = VideoClipExtractor()
    if extractor._check_ffmpeg():
        print("✓ FFmpeg is available")
    else:
        print("✗ FFmpeg is not available")
        print("  Please install FFmpeg and ensure it's in your PATH")
    
    print()


def test_integration_with_missing_files():
    """Test integration function with missing files"""
    print("Testing integration with missing files...")
    
    # Test with non-existent directory
    result = extract_clips_from_script("non_existent_directory")
    if not result['success'] and 'not found' in result['error']:
        print("✓ Correctly handled missing video file")
    else:
        print("✗ Did not handle missing video file correctly")
    
    print()


def run_all_tests():
    """Run all available tests"""
    print("=" * 50)
    print("Video Clipper Test Suite")
    print("=" * 50)
    print()
    
    test_timestamp_parsing()
    test_script_parsing_with_sample()
    test_config_validation()
    test_ffmpeg_availability()
    test_integration_with_missing_files()
    
    print("=" * 50)
    print("Test suite completed")
    print("=" * 50)


def test_with_real_episode(episode_path: str):
    """
    Test with a real episode directory.
    
    Args:
        episode_path: Path to episode directory with Input/original_video.mp4 
                     and Output/Scripts/unified_podcast_script.json
    """
    print(f"Testing with real episode: {episode_path}")
    print("-" * 40)
    
    episode_dir = Path(episode_path)
    
    # Check if required files exist
    video_path = episode_dir / "Input" / "original_video.mp4"
    script_path = episode_dir / "Output" / "Scripts" / "unified_podcast_script.json"
    
    print(f"Video file: {video_path}")
    print(f"Exists: {video_path.exists()}")
    
    print(f"Script file: {script_path}")
    print(f"Exists: {script_path.exists()}")
    
    if not script_path.exists():
        print("✗ Script file not found - cannot test")
        return
    
    # Test getting clip info without extraction
    print("\nGetting clip information...")
    info_result = get_video_clips_info(str(script_path))
    
    if info_result['success']:
        print(f"✓ Found {info_result['total_clips']} video clips")
        print(f"  Total duration: {info_result['total_duration_formatted']}")
        
        for clip in info_result['clips']:
            print(f"  - {clip['section_id']}: {clip['title']}")
            print(f"    Time: {clip['start_time']} - {clip['end_time']} ({clip['duration_seconds']:.1f}s)")
            print(f"    Severity: {clip['severity_level']}")
    else:
        print(f"✗ Failed to get clip info: {info_result['error']}")
        return
    
    if not video_path.exists():
        print("\n✗ Video file not found - cannot test extraction")
        return
    
    # Test actual extraction (dry run - don't actually extract)
    print(f"\nWould extract {info_result['total_clips']} clips from video")
    print("To actually extract, call extract_clips_from_script() function")


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Run tests
    run_all_tests()
