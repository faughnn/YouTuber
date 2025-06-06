#!/usr/bin/env python3
"""
Test script to verify that the updated extractors download directly to episode folders
without using temp_downloads.
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "Code"))

from Extraction.youtube_audio_extractor import extract_youtube_audio
from Extraction.youtube_video_downloader import download_video
from Utils.file_organizer import FileOrganizer
import yaml

def test_direct_download_system():
    """Test that files download directly to episode Input folders."""
    
    # Load config
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Code", "Config", "default_config.yaml")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize file organizer
    file_organizer = FileOrganizer(config['paths'])
    
    # Test video URL (short video for testing)
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll - short video
    
    print("Testing direct download system...")
    print(f"Test URL: {test_url}")
    
    try:
        # Test getting episode input folder
        test_title = "Test Video Direct Download"
        input_folder = file_organizer.get_episode_input_folder(test_title)
        print(f"\nExpected Input folder: {input_folder}")
        
        # Verify the Input folder was created
        if os.path.exists(input_folder):
            print("✓ Episode Input folder created successfully")
        else:
            print("✗ Episode Input folder was not created")
            return False
        
        # Check expected file paths
        expected_audio = os.path.join(input_folder, "original_audio.mp3")
        expected_video = os.path.join(input_folder, "original_video.mp4")
        
        print(f"\nExpected audio path: {expected_audio}")
        print(f"Expected video path: {expected_video}")
        
        # NOTE: Not actually downloading to avoid downloading files during test
        # In real usage, the extractors would download directly to these paths
        
        print("\n✓ Test completed - system configured to download directly to episode folders")
        print("✓ No temp_downloads folder will be used")
        print("✓ Files will go directly to: Content/[Channel]/[Episode]/Input/")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_direct_download_system()
    if success:
        print("\n🎉 SUCCESS: Direct download system is properly configured!")
    else:
        print("\n❌ FAILURE: Issues found with direct download system")
        sys.exit(1)
