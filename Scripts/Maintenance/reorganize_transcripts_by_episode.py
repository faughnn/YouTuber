#!/usr/bin/env python3
"""
Reorganize transcript files into channel/episode-specific subfolders.

This script moves transcript files from the main Transcripts folder into 
a hierarchical structure: Transcripts/[Channel]/[Episode]/files

Structure:
- Transcripts/
  - Joe_Rogan_Experience/
    - Joe_Rogan_Experience_2325_Aaron_Rodgers/
      - Joe Rogan Experience 2325 - Aaron Rodgers.json
      - Joe Rogan Experience 2325 - Aaron Rodgers.txt
      - Joe Rogan Experience 2325 - Aaron Rodgers_analysis.txt
    - Joe_Rogan_Experience_2330_Bono_1min_test/
      - Joe Rogan Experience 2330 - Bono_1min_test.json
      - Joe Rogan Experience 2330 - Bono_1min_test.txt
      - Joe Rogan Experience 2330 - Bono_1min_test_analysis.txt
"""

import os
import shutil
import re
from pathlib import Path

def sanitize_filename(name: str) -> str:
    """Cleans a string to be suitable for use as a folder/filename."""
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

    return name if name else "untitled"

def extract_channel_name(filename: str) -> str:
    """Extract channel name from filename."""
    # Remove file extension
    base_name = os.path.splitext(filename)[0]
    
    # Remove analysis suffix if present
    if base_name.endswith('_analysis'):
        base_name = base_name[:-9]
    
    # Common channel patterns
    channel_patterns = [
        r'^(Joe Rogan Experience)',
        r'^(The Daily Show)',
        r'^(Saturday Night Live)',
        r'^(Conan)',
        r'^(The Tonight Show)',
        r'^(Late Night)',
        r'^(Jimmy Kimmel Live)',
        r'^([A-Za-z\s&]+)\s+\d+',  # Channel name followed by episode number
        r'^([A-Za-z\s&]+)\s+-',    # Channel name followed by dash
    ]
    
    for pattern in channel_patterns:
        match = re.match(pattern, base_name, re.IGNORECASE)
        if match:
            return sanitize_filename(match.group(1))
    
    # If no pattern matches, use the first few words
    words = base_name.split()
    if len(words) >= 2:
        return sanitize_filename(' '.join(words[:2]))
    
    return sanitize_filename(base_name)

def get_episode_base_name(filename: str) -> str:
    """Get the base episode name (without extension and analysis suffix)."""
    base_name = os.path.splitext(filename)[0]
    
    # Remove analysis suffix if present
    if base_name.endswith('_analysis'):
        base_name = base_name[:-9]
    
    return base_name

def reorganize_transcripts(transcripts_folder: str, dry_run: bool = True):
    """
    Reorganize transcript files into channel/episode-specific subfolders.
    """
    transcripts_path = Path(transcripts_folder)
    
    if not transcripts_path.exists():
        print(f"❌ Transcripts folder not found: {transcripts_folder}")
        return
    
    print(f"🔍 Scanning transcript files in: {transcripts_folder}")
    print(f"📋 Mode: {'DRY RUN' if dry_run else 'ACTUAL MOVE'}")
    print("=" * 60)
      # Get all files in the transcripts folder and its immediate subfolders
    transcript_files = []
      # Check files in the main transcripts folder
    for file_path in transcripts_path.iterdir():
        if file_path.is_file() and not file_path.name.startswith('.'):
            # Skip sample/test files (but not episode files that happen to contain "test" in the title)
            filename_lower = file_path.name.lower()
            if (filename_lower.startswith('sample') or 
                filename_lower.startswith('test.') or 
                filename_lower.startswith('example') or
                'segments_example' in filename_lower or
                'sample_diarization' in filename_lower):
                print(f"⏭️  Skipping sample/test file: {file_path.name}")
                continue
            transcript_files.append(file_path)
      # Check files in immediate subfolders (like Joe_Rogan_Experience)
    for subfolder_path in transcripts_path.iterdir():
        if subfolder_path.is_dir() and not subfolder_path.name.startswith('.'):
            for file_path in subfolder_path.iterdir():
                if file_path.is_file() and not file_path.name.startswith('.'):
                    # Skip sample/test files (but not episode files that happen to contain "test" in the title)
                    filename_lower = file_path.name.lower()
                    if (filename_lower.startswith('sample') or 
                        filename_lower.startswith('test.') or 
                        filename_lower.startswith('example') or
                        'segments_example' in filename_lower or
                        'sample_diarization' in filename_lower):
                        print(f"⏭️  Skipping sample/test file: {file_path.name}")
                        continue
                    transcript_files.append(file_path)
    
    if not transcript_files:
        print("ℹ️  No transcript files found to reorganize.")
        return
    
    # Group files by episode
    episodes = {}
    for file_path in transcript_files:
        filename = file_path.name
        channel_name = extract_channel_name(filename)
        episode_base = get_episode_base_name(filename)
        episode_folder = sanitize_filename(episode_base)
        
        if channel_name not in episodes:
            episodes[channel_name] = {}
        
        if episode_folder not in episodes[channel_name]:
            episodes[channel_name][episode_folder] = []
        
        episodes[channel_name][episode_folder].append(file_path)
    
    # Display organization plan
    total_files = 0
    for channel, channel_episodes in episodes.items():
        print(f"📺 Channel: {channel}")
        for episode, files in channel_episodes.items():
            print(f"  📁 Episode: {episode}")
            for file_path in files:
                print(f"    📄 {file_path.name}")
                total_files += 1
        print()
    
    print(f"📊 Total files to organize: {total_files}")
    print("=" * 60)
    
    if dry_run:
        print("🔍 This was a dry run. No files were moved.")
        print("💡 Run with dry_run=False to actually move the files.")
        return
    
    # Actually move the files
    moved_count = 0
    for channel, channel_episodes in episodes.items():
        channel_path = transcripts_path / channel
        
        for episode, files in channel_episodes.items():
            episode_path = channel_path / episode
            
            # Create the episode directory
            episode_path.mkdir(parents=True, exist_ok=True)
            print(f"📁 Created directory: {episode_path}")
            
            # Move all files for this episode
            for file_path in files:
                destination = episode_path / file_path.name
                try:
                    shutil.move(str(file_path), str(destination))
                    print(f"✅ Moved: {file_path.name} -> {channel}/{episode}/")
                    moved_count += 1
                except Exception as e:
                    print(f"❌ Error moving {file_path.name}: {e}")
    
    print("=" * 60)
    print(f"🎉 Successfully moved {moved_count} files!")
    print("✅ Transcript reorganization complete!")

if __name__ == "__main__":
    import sys
    
    # Get the transcripts folder path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    transcripts_folder = os.path.join(os.path.dirname(os.path.dirname(script_dir)), "Transcripts")
    
    # Check for dry-run argument
    dry_run = True
    if len(sys.argv) > 1 and sys.argv[1].lower() in ['--execute', '--run', '--actual']:
        dry_run = False
        print("⚠️  ACTUAL MOVE MODE - Files will be moved!")
    else:
        print("🔍 DRY RUN MODE - No files will be moved")
        print("💡 Use --execute to actually move files")
    
    reorganize_transcripts(transcripts_folder, dry_run=dry_run)
