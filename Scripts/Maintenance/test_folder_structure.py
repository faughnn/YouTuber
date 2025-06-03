#!/usr/bin/env python3
"""
Test script to verify the audio_diarizer.py folder structure logic works correctly.
"""

import sys
import os
import re

# Add the extraction script directory to path so we can import functions
script_dir = os.path.dirname(os.path.abspath(__file__))
extraction_dir = os.path.join(os.path.dirname(script_dir), "Extraction")
sys.path.insert(0, extraction_dir)

# Import the functions we want to test
from audio_diarizer import sanitize_audio_filename, extract_channel_name

def test_folder_structure():
    """Test the folder structure creation logic."""
    
    test_files = [
        "Joe Rogan Experience 2325 - Aaron Rodgers.mp3",
        "Joe Rogan Experience 2330 - Bono_1min_test.mp3", 
        "The Daily Show 2024-05-15 - Guest Interview.wav",
        "Saturday Night Live Best Of 2024.mp3",
        "Some Random Podcast Episode 42.mp3"
    ]
    
    print("🧪 Testing folder structure logic...")
    print("=" * 60)
    
    # Get the transcripts folder path (like the audio_diarizer.py script does)
    TRANSCRIPTS_FOLDER = os.path.join(os.path.dirname(os.path.dirname(script_dir)), "Transcripts")
    print(f"📁 Base Transcripts folder: {TRANSCRIPTS_FOLDER}")
    print()
    
    for audio_file in test_files:
        print(f"🎵 Audio file: {audio_file}")
        
        # Extract base name for creating subfolder structure: Channel/Episode/
        audio_base_name, _ = os.path.splitext(os.path.basename(audio_file))
        
        # Extract channel name and create episode folder name
        channel_name = extract_channel_name(audio_base_name)
        episode_folder_name = sanitize_audio_filename(audio_base_name)
        
        # Create the full path: Transcripts/Channel/Episode/
        channel_folder = os.path.join(TRANSCRIPTS_FOLDER, channel_name)
        audio_transcript_folder = os.path.join(channel_folder, episode_folder_name)
        
        print(f"  📺 Channel: {channel_name}")
        print(f"  📁 Episode folder: {episode_folder_name}")
        print(f"  🗂️  Full path: {audio_transcript_folder}")
        print()

if __name__ == "__main__":
    test_folder_structure()
