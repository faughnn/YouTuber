#!/usr/bin/env python3
"""
Reorganize existing transcript files in the main Transcripts folder
into channel-specific subfolders.
"""

import os
import shutil
import re
from pathlib import Path

# Configuration
TRANSCRIPTS_FOLDER = r"c:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Transcripts"
DRY_RUN = False  # Set to False to actually move files

def sanitize_audio_filename(name: str) -> str:
    """
    Cleans a string to be suitable for use as a folder/filename.
    This is copied from the audio_diarizer.py script to maintain consistency.
    """
    name = name.strip()
    # Replace problematic characters often found in titles
    name = name.replace(":", "_")
    name = name.replace("/", "_")
    name = name.replace("\\", "_")
    name = name.replace("\"", "'")  # Replace double quotes with single

    # Remove characters forbidden in Windows filenames
    name = re.sub(r'[<>|?*]', '', name)
    
    # Replace multiple spaces/underscores with a single underscore
    name = re.sub(r'[\s_]+', '_', name)
    
    # Remove leading/trailing underscores or periods that might result from replacements
    name = name.strip('_.')
    
    # Limit length to avoid issues (e.g. 150 chars for the base name)
    max_len = 150
    if len(name) > max_len:
        name_part = name[:max_len]
        if '_' in name_part:
            name = name_part.rsplit('_', 1)[0]
        else:
            name = name_part

    return name if name else "untitled_audio"

def extract_channel_name(filename: str) -> str:
    """
    Extract channel name from filename using common patterns.
    Returns the channel name that should be used for the subfolder.
    """
    # Remove file extension
    base_name = os.path.splitext(filename)[0]
    
    # Common patterns for YouTube channel names
    patterns = [
        # "Joe Rogan Experience 2325 - Title" -> "Joe Rogan Experience"
        r'^(Joe Rogan Experience)',
        # "Channel Name Episode 123 - Title" -> "Channel Name"
        r'^([A-Za-z\s]+?)(?:\s+(?:Episode|#|\d+))',
        # "Channel Name - Episode Title" -> "Channel Name"
        r'^([^-]+?)\s*-\s*',
        # "Channel Name S01E01 Title" -> "Channel Name"
        r'^([A-Za-z\s]+?)(?:\s+S\d+E\d+)',
    ]
    
    for pattern in patterns:
        match = re.match(pattern, base_name, re.IGNORECASE)
        if match:
            channel_name = match.group(1).strip()
            return sanitize_audio_filename(channel_name)
    
    # Fallback: use the entire base name (like the original script does)
    return sanitize_audio_filename(base_name)

def get_files_to_reorganize():
    """
    Get list of files in the main Transcripts folder that need to be reorganized.
    """
    files_to_move = []
    
    if not os.path.exists(TRANSCRIPTS_FOLDER):
        print(f"Error: Transcripts folder not found: {TRANSCRIPTS_FOLDER}")
        return files_to_move
    
    # Get all files in the main transcripts folder (not in subfolders)
    for item in os.listdir(TRANSCRIPTS_FOLDER):
        item_path = os.path.join(TRANSCRIPTS_FOLDER, item)
        
        # Skip directories and focus on transcript files
        if os.path.isfile(item_path):
            # Skip system files and focus on transcript-related files
            if item.lower().endswith(('.json', '.txt', '.srt')):
                # Skip obviously sample/test files
                if not item.lower().startswith(('sample_', 'segments_', 'test')):
                    files_to_move.append(item)
                else:
                    print(f"Skipping sample/test file: {item}")
            else:
                print(f"Skipping non-transcript file: {item}")
    
    return files_to_move

def create_channel_folder(channel_name: str) -> str:
    """
    Create channel subfolder if it doesn't exist.
    Returns the path to the channel folder.
    """
    channel_folder = os.path.join(TRANSCRIPTS_FOLDER, channel_name)
    
    if not os.path.exists(channel_folder):
        if not DRY_RUN:
            os.makedirs(channel_folder, exist_ok=True)
            print(f"Created folder: {channel_folder}")
        else:
            print(f"[DRY RUN] Would create folder: {channel_folder}")
    
    return channel_folder

def move_file(source_path: str, destination_path: str):
    """
    Move a file from source to destination.
    """
    if not DRY_RUN:
        try:
            shutil.move(source_path, destination_path)
            print(f"Moved: {os.path.basename(source_path)} -> {os.path.dirname(destination_path)}")
        except Exception as e:
            print(f"Error moving {source_path}: {e}")
    else:
        print(f"[DRY RUN] Would move: {os.path.basename(source_path)} -> {os.path.dirname(destination_path)}")

def main():
    """
    Main function to reorganize transcript files.
    """
    print("=== Transcript Reorganization Script ===")
    print(f"Working directory: {TRANSCRIPTS_FOLDER}")
    print(f"Dry run mode: {'ON' if DRY_RUN else 'OFF'}")
    print()
    
    # Get files that need to be reorganized
    files_to_move = get_files_to_reorganize()
    
    if not files_to_move:
        print("No files found to reorganize.")
        return
    
    print(f"Found {len(files_to_move)} files to reorganize:")
    for file in files_to_move:
        print(f"  - {file}")
    print()
    
    # Group files by channel
    channel_groups = {}
    for filename in files_to_move:
        channel_name = extract_channel_name(filename)
        if channel_name not in channel_groups:
            channel_groups[channel_name] = []
        channel_groups[channel_name].append(filename)
    
    print("Channel groupings:")
    for channel, files in channel_groups.items():
        print(f"  {channel}: {len(files)} files")
        for file in files:
            print(f"    - {file}")
    print()
    
    # Reorganize files
    total_moved = 0
    for channel_name, files in channel_groups.items():
        print(f"Processing channel: {channel_name}")
        
        # Create channel folder
        channel_folder = create_channel_folder(channel_name)
        
        # Move files
        for filename in files:
            source_path = os.path.join(TRANSCRIPTS_FOLDER, filename)
            destination_path = os.path.join(channel_folder, filename)
            
            # Check if destination already exists
            if os.path.exists(destination_path):
                print(f"Warning: Destination already exists: {destination_path}")
                continue
            
            move_file(source_path, destination_path)
            total_moved += 1
        
        print()
    
    print(f"Reorganization complete. {'Would move' if DRY_RUN else 'Moved'} {total_moved} files.")
    
    if DRY_RUN:
        print("\nTo actually perform the reorganization, set DRY_RUN = False in the script.")

if __name__ == "__main__":
    main()
