#!/usr/bin/env python3
"""
Test the new episode structure creation and path management.
"""

import sys
import os
import yaml
from pathlib import Path

# Add Code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Code'))

from Utils.file_organizer import FileOrganizer

def test_episode_structure():
    """Test that the FileOrganizer creates proper episode structure."""
    
    # Load config
    config_path = os.path.join('Code', 'Config', 'default_config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize FileOrganizer
    file_organizer = FileOrganizer(config['paths'])
    
    # Test audio filename
    test_audio = "Joe_Rogan_Experience_2331_Jesse_Michels.mp3"
    
    print("🧪 Testing Episode Structure Creation")
    print("=" * 50)
    
    # Test transcript structure paths
    channel_folder, episode_folder, transcript_path = file_organizer.get_transcript_structure_paths(test_audio)
    
    print(f"📁 Channel Folder: {channel_folder}")
    print(f"📁 Episode Folder: {episode_folder}")
    print(f"📄 Transcript Path: {transcript_path}")
    print()
    
    # Test all episode paths
    episode_paths = file_organizer.get_episode_paths(test_audio)
    
    print("📋 All Episode Paths:")
    for path_name, path_value in episode_paths.items():
        print(f"  {path_name}: {path_value}")
    print()
    
    # Test specific path methods
    analysis_path = file_organizer.get_analysis_output_path(transcript_path)
    script_path = file_organizer.get_podcast_script_output_path(transcript_path)
    audio_path = file_organizer.get_audio_output_path(transcript_path, "tts_generated")
    video_paths = file_organizer.get_video_paths(transcript_path)
    
    print("🎯 Specific Path Tests:")
    print(f"  Analysis: {analysis_path}")
    print(f"  Script: {script_path}")
    print(f"  Audio: {audio_path}")
    print(f"  Video Original: {video_paths['original_video']}")
    print(f"  Video Clips: {video_paths['clips_folder']}")
    print(f"  Final Video: {video_paths['final_video']}")
    print()
    
    # Verify directory structure exists
    print("📂 Directory Structure Created:")
    if os.path.exists(episode_folder):
        for root, dirs, files in os.walk(episode_folder):
            level = root.replace(episode_folder, '').count(os.sep)
            indent = '  ' * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = '  ' * (level + 1)
            for file in files:
                print(f"{subindent}{file}")
    else:
        print("  Episode folder not yet created (will be created during processing)")
    
    print("\n✅ Episode structure test completed!")

if __name__ == "__main__":
    test_episode_structure()
