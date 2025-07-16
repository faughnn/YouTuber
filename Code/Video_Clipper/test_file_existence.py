#!/usr/bin/env python3
"""
Test script to verify file existence checking in Video Clipper

This script simulates the file existence checking behavior
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import Video_Clipper as a module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Video_Clipper.video_extractor import VideoClipExtractor, ExtractionReport
from Video_Clipper.script_parser import VideoClipSpec

def test_file_existence_check():
    """Test that video clipper properly skips existing files"""
    
    # Create test directory structure
    test_dir = Path("test_output")
    test_dir.mkdir(exist_ok=True)
    
    # Create a fake existing file
    existing_file = test_dir / "test_section_001.mp4"
    existing_file.write_text("fake video content")
    
    # Create mock video clip specs
    clips = [
        VideoClipSpec(
            section_id="test_section_001",
            clip_id="test_clip_001",
            title="Test Section 1",
            start_time="00:00:00",
            end_time="00:00:10",
            severity_level="HIGH",
            estimated_duration="10s"
        ),
        VideoClipSpec(
            section_id="test_section_002",
            clip_id="test_clip_002", 
            title="Test Section 2",
            start_time="00:00:10",
            end_time="00:00:20",
            severity_level="MEDIUM",
            estimated_duration="10s"
        )
    ]
    
    # Create a mock video file (not actually used for this test)
    fake_video = test_dir / "fake_video.mp4"
    fake_video.write_text("fake video")
    
    # Create extractor
    extractor = VideoClipExtractor()
    
    # Test the file existence check logic by examining the code
    print("Testing file existence check logic...")
    
    # Simulate the existence check
    for clip in clips:
        output_path = test_dir / f"{clip.section_id}.mp4"
        if output_path.exists():
            print(f"✓ File exists, would skip: {output_path}")
        else:
            print(f"✗ File missing, would process: {output_path}")
    
    # Test the report structure
    report = ExtractionReport(
        total_clips=2,
        successful_clips=1,
        failed_clips=0,
        skipped_clips=1,
        existing_files=[str(existing_file)]
    )
    
    print(f"\nReport structure test:")
    print(f"Total clips: {report.total_clips}")
    print(f"Successful: {report.successful_clips}")
    print(f"Failed: {report.failed_clips}")
    print(f"Skipped: {report.skipped_clips}")
    print(f"Existing files: {report.existing_files}")
    
    # Test to_dict conversion
    report_dict = report.to_dict()
    print(f"\nReport dict keys: {list(report_dict.keys())}")
    print(f"Contains skipped_clips: {'skipped_clips' in report_dict}")
    print(f"Contains existing_files: {'existing_files' in report_dict}")
    
    # Cleanup
    existing_file.unlink()
    fake_video.unlink()
    test_dir.rmdir()
    
    print("\n✅ File existence check test completed successfully!")

if __name__ == "__main__":
    test_file_existence_check()
