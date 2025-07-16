#!/usr/bin/env python3
"""
Test script to demonstrate the simplified loudnorm functionality in DirectConcatenator
"""

import logging
from pathlib import Path
from concat_orchestrator import DirectConcatenator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_loudnorm_concatenation():
    """Test the concatenation with loudnorm feature"""
    
    # Initialize concatenator
    concatenator = DirectConcatenator()
    
    # Example segment paths (replace with your actual test files)
    segment_sequence = [
        Path("path/to/tts_segment_1.mp4"),
        Path("path/to/video_clip_1.mp4"), 
        Path("path/to/tts_segment_2.mp4"),
        Path("path/to/video_clip_2.mp4")
    ]
    
    output_path = Path("test_output_with_loudnorm.mp4")
    
    print("=== Testing Loudnorm Concatenation ===")
    print(f"Input segments: {len(segment_sequence)}")
    print(f"Output: {output_path}")
    print()
    
    # Test with default loudnorm settings (-16 LUFS, LRA=7, TP=-1)
    print("Testing loudnorm concatenation (default settings):")
    result = concatenator.concatenate_segments(
        segment_sequence=segment_sequence,
        output_path=output_path,
        target_lufs=-16.0  # Good for YouTube/web content
    )
    
    if result.success:
        print(f"✅ Success! Output: {result.output_path}")
        print(f"   Duration: {result.duration:.2f}s")
        print(f"   File size: {result.file_size/1024/1024:.1f}MB")
        print(f"   Audio normalized to -16 LUFS with consistent levels")
    else:
        print(f"❌ Failed: {result.error}")
    
    print()
    
    # Test with custom settings
    output_path_custom = Path("test_output_custom_settings.mp4")
    print("Testing with custom loudnorm settings:")
    result_custom = concatenator.concatenate_segments(
        segment_sequence=segment_sequence,
        output_path=output_path_custom,
        target_lufs=-14.0,  # Louder for competitive content
        loudness_range=5.0,  # More compressed
        true_peak=-1.0
    )
    
    if result_custom.success:
        print(f"✅ Success! Output: {result_custom.output_path}")
        print(f"   Duration: {result_custom.duration:.2f}s")
        print(f"   File size: {result_custom.file_size/1024/1024:.1f}MB")
        print(f"   Audio normalized to -14 LUFS with tighter dynamics")
    else:
        print(f"❌ Failed: {result_custom.error}")

def test_custom_loudnorm_settings():
    """Test custom loudnorm settings for different content types"""
    
    concatenator = DirectConcatenator()
    segment_sequence = [Path("test1.mp4"), Path("test2.mp4")]  # Replace with real files
    
    print("\n=== Testing Custom Loudnorm Settings ===")
    
    # Podcast-style settings (quieter, more dynamic)
    print("Testing podcast settings (-19 LUFS, more dynamic):")
    result = concatenator.concatenate_segments(
        segment_sequence=segment_sequence,
        output_path=Path("podcast_style.mp4"),
        target_lufs=-19.0,  # Quieter for podcast listening
        loudness_range=10.0,  # More dynamic range
        true_peak=-2.0  # Extra conservative peak limiting
    )
    
    # YouTube-optimized settings (louder, more compressed)
    print("Testing YouTube settings (-14 LUFS, compressed):")
    result = concatenator.concatenate_segments(
        segment_sequence=segment_sequence,
        output_path=Path("youtube_style.mp4"),
        target_lufs=-14.0,  # Louder for competitive loudness
        loudness_range=5.0,  # More compressed
        true_peak=-1.0  # Standard peak limiting
    )

if __name__ == "__main__":
    print("DirectConcatenator Loudnorm Test")
    print("=" * 40)
    print()
    print("Note: Replace the example paths with real video files to test")
    print()
    
    # Uncomment to run tests with real files:
    # test_loudnorm_concatenation()
    # test_custom_loudnorm_settings()
    
    print("Test script ready. Edit paths and uncomment test calls to run.")
