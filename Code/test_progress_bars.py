#!/usr/bin/env python3
"""
Test Progress Bars for Video and Audio Downloads

This script demonstrates the progress bar functionality for both video and audio downloads.
Run this with a YouTube URL to see the progress bars in action.

Usage: python test_progress_bars.py <youtube_url>
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from Extraction.youtube_video_downloader import download_video
from Extraction.youtube_audio_extractor import download_audio

def test_progress_bars(video_url):
    """Test both video and audio download progress bars"""
    print("🎬 Testing Video Download Progress Bar")
    print("=" * 50)
    
    try:
        video_result = download_video(video_url)
        if video_result and not video_result.startswith("An error occurred"):
            print(f"✅ Video download successful: {video_result}")
        else:
            print(f"❌ Video download failed: {video_result}")
    except Exception as e:
        print(f"❌ Video download error: {e}")
    
    print("\n🎵 Testing Audio Download Progress Bar")
    print("=" * 50)
    
    try:
        audio_result = download_audio(video_url)
        if audio_result and not audio_result.startswith("An error occurred"):
            print(f"✅ Audio download successful: {audio_result}")
        else:
            print(f"❌ Audio download failed: {audio_result}")
    except Exception as e:
        print(f"❌ Audio download error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_progress_bars.py <youtube_url>")
        print("Example: python test_progress_bars.py https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        sys.exit(1)
    
    video_url = sys.argv[1]
    print(f"Testing progress bars with URL: {video_url}\n")
    test_progress_bars(video_url)
