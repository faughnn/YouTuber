"""
File Organization Utilities for Master Processor

Provides file organization, path management, and cleanup functionality.
This module is responsible for creating the standardized directory structure
for each episode based on the provided host and guest names.
"""

import os
import shutil
import json
import time
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging

class FileOrganizer:
    """Handles file organization and path management for the master processor."""
    def __init__(self, base_paths: Dict[str, str]):
        """
        Initialize with base paths for different file types.
        
        Args:
            base_paths: Dictionary with keys like 'episode_base'.
        """
        self.base_paths = base_paths
        self.logger = logging.getLogger(__name__)

    def ensure_directory_exists(self, path: str) -> bool:
        """Ensure a directory exists, creating it if necessary."""
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception as e:
            self.logger.error(f"Failed to create directory {path}: {e}")
            return False

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize a string to be a valid filename."""
        if not filename:
            return ""
        # Replace spaces and problematic characters with an underscore
        sanitized = filename.replace(' ', '_')
        sanitized = "".join([c for c in sanitized if c.isalnum() or c in ('_', '-')]).rstrip()
        return sanitized

    def get_episode_paths(self, original_video_title: str, host_name: str, guest_name: str) -> Dict[str, str]:
        """
        Get all standard paths for an episode using the finalized host and guest names.
        This is the primary method for creating the directory structure.

        Args:
            original_video_title (str): The original title of the video.
            host_name (str): The finalized host/show name.
            guest_name (str): The finalized guest name.

        Returns:
            Dictionary with all standard episode paths.
        """
        sanitized_host = self.sanitize_filename(host_name)
        sanitized_guest = self.sanitize_filename(guest_name)
        
        # Create a descriptive episode folder name
        # Always use host_guest format for consistency in name extraction
        episode_folder_name = f"{sanitized_host}_{sanitized_guest}"

        content_base = self.base_paths.get('episode_base', 'Content')
        
        # Define the main episode folder
        episode_folder = os.path.join(content_base, sanitized_host, episode_folder_name)

        # Define all standard sub-folders and file paths
        paths = {
            'episode_folder': episode_folder,
            'input_folder': os.path.join(episode_folder, 'Input'),
            'processing_folder': os.path.join(episode_folder, 'Processing'),
            'output_folder': os.path.join(episode_folder, 'Output'),
            'scripts_folder': os.path.join(episode_folder, 'Output', 'Scripts'),
            'audio_folder': os.path.join(episode_folder, 'Output', 'Audio'),
            'video_folder': os.path.join(episode_folder, 'Output', 'Video'),
            'timelines_folder': os.path.join(episode_folder, 'Output', 'Timelines'),
            'original_audio': os.path.join(episode_folder, 'Input', 'original_audio.mp3'),
            'original_video': os.path.join(episode_folder, 'Input', 'original_video.mp4'),
            'transcript_path': os.path.join(episode_folder, 'Processing', 'transcript.json'),
            'analysis_path': os.path.join(episode_folder, 'Processing', 'analysis.json'),
        }
        
        # Ensure all directories exist
        for key, folder_path in paths.items():
            if 'folder' in key:
                self.ensure_directory_exists(folder_path)
                
        return paths

# Example usage
if __name__ == '__main__':
    print("Running FileOrganizer example...")
    # Define dummy base paths for testing
    # In a real scenario, this would come from the main config
    test_base_paths = {'episode_base': os.path.abspath('./Content')}
    
    organizer = FileOrganizer(test_base_paths)

    # --- Test Case 1: With a guest ---
    print("\n--- Test Case 1: With Guest ---")
    title1 = "The Cool Podcast #123 - Dr. Jane Smith"
    host1 = "The Cool Podcast"
    guest1 = "Dr. Jane Smith"
    
    paths1 = organizer.get_episode_paths(title1, host1, guest1)
    
    print(f"Host: {host1}, Guest: {guest1}")
    print(f"Episode Folder: {paths1['episode_folder']}")
    print(f"Input Folder: {paths1['input_folder']}")
    print(f"Original Video Path: {paths1['original_video']}")

    # --- Test Case 2: No guest ---
    print("\n--- Test Case 2: No Guest ---")
    title2 = "A Solo Stream About Tech"
    host2 = "My Tech Channel"
    guest2 = "No Guest"

    paths2 = organizer.get_episode_paths(title2, host2, guest2)
    print(f"Host: {host2}, Guest: {guest2}")
    print(f"Episode Folder: {paths2['episode_folder']}")
    print(f"Input Folder: {paths2['input_folder']}")
    print(f"Original Video Path: {paths2['original_video']}")
