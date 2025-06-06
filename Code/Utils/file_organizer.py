"""
File Organization Utilities for Master Processor

Provides file organization, path management, and cleanup functionality.
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
            base_paths: Dictionary with keys like 'episode_base', 'analysis_rules'
        """
        self.base_paths = base_paths
        self.logger = logging.getLogger(__name__)
        self.temp_files: List[str] = []  # Track temporary files for cleanup
    
    def ensure_directory_exists(self, path: str) -> bool:
        """Ensure a directory exists, creating it if necessary."""
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception as e:
            self.logger.error(f"Failed to create directory {path}: {e}")
            return False
    def get_legacy_audio_output_path(self, filename: str) -> str:
        """
        DEPRECATED: Get episode-specific audio path instead.
        Use get_audio_output_path() for new episode structure.
        """
        raise NotImplementedError("Legacy paths no longer supported. Use episode structure with get_audio_output_path()")
    
    def extract_channel_name(self, filename: str) -> str:
        """Extract channel name from audio filename."""
        # Remove file extension
        base_name = os.path.splitext(filename)[0]
        
        # Common patterns for channel extraction
        if "Joe Rogan Experience" in base_name:
            return "Joe_Rogan_Experience"
        elif "Lex Fridman" in base_name:
            return "Lex_Fridman_Podcast"
        elif "Tim Ferriss" in base_name:
            return "Tim_Ferriss_Show"
        else:
            # Extract first part before episode number or dash
            parts = base_name.split(' - ')
            if len(parts) > 1:
                return parts[0].replace(' ', '_')
            else:
                # Fallback: use first few words
                words = base_name.split()[:3]
                return '_'.join(words)
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem compatibility."""
        # Remove or replace problematic characters
        replacements = {
            ':': '',
            '"': '',
            "'": '',
            '<': '',
            '>': '',
            '|': '',
            '?': '',
            '*': '',
            '/': '_',
            '\\': '_',
            '  ': ' '  # Replace double spaces with single
        }
        
        sanitized = filename
        for old, new in replacements.items():
            sanitized = sanitized.replace(old, new)
        
        return sanitized.strip()
    def get_transcript_structure_paths(self, audio_filename: str) -> Tuple[str, str, str]:
        """
        Get the organized folder structure for transcripts using new Input/Processing/Output structure.
        
        Returns:
            Tuple of (channel_folder, episode_folder, transcript_file_path)
        """
        base_name = os.path.splitext(os.path.basename(audio_filename))[0]
        
        # Extract channel name
        channel_name = self.extract_channel_name(base_name)
        
        # Sanitize episode name
        episode_name = self.sanitize_filename(base_name)        # Build paths using new structure: Content/Series/Episode/Input/
        content_base = self.base_paths.get('episode_base', 'Content')
        channel_folder = os.path.join(content_base, channel_name)
        episode_folder = os.path.join(channel_folder, episode_name)
        input_folder = os.path.join(episode_folder, 'Input')
        transcript_file = os.path.join(input_folder, f"{base_name}_full_transcript.json")
        
        # Ensure directories exist
        self.ensure_directory_exists(input_folder)
        
        return channel_folder, episode_folder, transcript_file
    def get_analysis_output_path(self, transcript_path: str) -> str:
        """Get the analysis output path for a transcript file using new structure."""
        # Get the episode folder from transcript path (remove Input folder and file)
        transcript_dir = os.path.dirname(transcript_path)  # This is the Input folder
        episode_dir = os.path.dirname(transcript_dir)  # This is the episode folder
        
        # Create Processing folder path
        processing_dir = os.path.join(episode_dir, 'Processing')
        self.ensure_directory_exists(processing_dir)
        
        # Generate analysis filename
        transcript_base = os.path.splitext(os.path.basename(transcript_path))[0]
        return os.path.join(processing_dir, f"{transcript_base}_analysis.txt")
    
    def validate_audio_file(self, file_path: str) -> Dict[str, any]:
        """Validate an audio file."""
        result = {
            'valid': False,
            'warnings': [],
            'info': {}
        }
        
        if not os.path.exists(file_path):
            result['warnings'].append(f"File does not exist: {file_path}")
            return result
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            result['warnings'].append("File is empty")
            return result
        
        if file_size < 1024:  # Less than 1KB
            result['warnings'].append("File is very small (less than 1KB)")
        
        # Check file extension
        valid_extensions = ['.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg']
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext not in valid_extensions:
            result['warnings'].append(f"Unusual audio format: {file_ext}")
        
        # If we get here with no blocking warnings, it's valid
        result['valid'] = True
        result['info'] = {
            'size_bytes': file_size,
            'size_mb': file_size / (1024 * 1024),
            'extension': file_ext,
            'path': file_path
        }
        
        return result
    
    def check_existing_outputs(self, input_path: str) -> Dict[str, any]:
        """Check if outputs already exist for an input."""
        result = {
            'transcript_exists': False,
            'analysis_exists': False,
            'transcript_path': None,
            'analysis_path': None
        }
        
        try:
            # Get expected paths
            _, _, transcript_path = self.get_transcript_structure_paths(input_path)
            analysis_path = self.get_analysis_output_path(transcript_path)
            
            # Check if files exist
            if os.path.exists(transcript_path):
                result['transcript_exists'] = True
                result['transcript_path'] = transcript_path
            
            if os.path.exists(analysis_path):
                result['analysis_exists'] = True
                result['analysis_path'] = analysis_path
                
        except Exception as e:
            self.logger.warning(f"Error checking existing outputs: {e}")
        
        return result
    
    def add_temp_file(self, file_path: str):
        """Add a file to the temporary files list for cleanup."""
        if file_path not in self.temp_files:
            self.temp_files.append(file_path)
    
    def cleanup_temp_files(self):
        """Clean up temporary files."""
        for file_path in self.temp_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    self.logger.debug(f"Cleaned up temp file: {file_path}")
            except Exception as e:
                self.logger.warning(f"Failed to clean up temp file {file_path}: {e}")
        
        self.temp_files.clear()
    
    def create_processing_summary(self, results: Dict[str, str], session_id: str) -> str:
        """Create a processing summary file."""
        summary_data = {
            'session_id': session_id,
            'timestamp': time.time(),
            'human_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'results': results,
            'file_sizes': {}
        }
        
        # Add file size information
        for key, path in results.items():
            if os.path.exists(path):
                summary_data['file_sizes'][key] = {
                    'bytes': os.path.getsize(path),
                    'mb': round(os.path.getsize(path) / (1024 * 1024), 2)
                }
        
        # Save summary
        if 'transcript_path' in results:
            episode_dir = os.path.dirname(results['transcript_path'])
            summary_path = os.path.join(episode_dir, f"processing_summary_{session_id}.json")
            
            try:
                with open(summary_path, 'w', encoding='utf-8') as f:
                    json.dump(summary_data, f, indent=2)
                return summary_path
            except Exception as e:
                self.logger.warning(f"Failed to create processing summary: {e}")
        
        return None
    def get_episode_input_folder(self, video_title: str) -> str:
        """
        Get the Input folder path for an episode based on video title.
        Creates the necessary episode directory structure.
        
        Args:
            video_title: The title of the video/episode
            
        Returns:
            Path to the episode's Input folder
        """
        # Get episode structure using the video title as filename
        dummy_filename = f"{video_title}.mp3"
        _, episode_folder, _ = self.get_transcript_structure_paths(dummy_filename)
        
        # Return the Input folder path
        input_folder = os.path.join(episode_folder, 'Input')
        self.ensure_directory_exists(input_folder)
        
        return input_folder

    def get_episode_paths(self, audio_filename: str) -> Dict[str, str]:
        """
        Get all standard paths for an episode using new Input/Processing/Output structure.
        
        Returns:
            Dictionary with all standard episode paths
        """
        # Get base episode info
        _, episode_folder, transcript_path = self.get_transcript_structure_paths(audio_filename)
        
        paths = {
            'episode_folder': episode_folder,
            'input_folder': os.path.join(episode_folder, 'Input'),
            'processing_folder': os.path.join(episode_folder, 'Processing'),
            'processing_logs_folder': os.path.join(episode_folder, 'Processing', 'Logs'),
            'output_folder': os.path.join(episode_folder, 'Output'),
            'output_scripts_folder': os.path.join(episode_folder, 'Output', 'Scripts'),
            'output_audio_folder': os.path.join(episode_folder, 'Output', 'Audio'),
            'output_video_folder': os.path.join(episode_folder, 'Output', 'Video'),
            'output_timelines_folder': os.path.join(episode_folder, 'Output', 'Timelines'),
            'transcript_path': transcript_path
        }
        
        # Ensure all directories exist
        for folder_path in paths.values():
            if folder_path.endswith(('.json', '.txt', '.mp3', '.mp4')):                # It's a file path, create parent directory
                self.ensure_directory_exists(os.path.dirname(folder_path))
            else:
                # It's a directory path
                self.ensure_directory_exists(folder_path)
                
        return paths
    
    def get_podcast_script_output_path(self, transcript_path: str, script_name: str = "podcast_script") -> str:
        """Get the podcast script output path in the Output/Scripts folder."""
        # Get episode folder from transcript path
        transcript_dir = os.path.dirname(transcript_path)  # Input folder
        episode_dir = os.path.dirname(transcript_dir)  # Episode folder
        
        # Create Scripts output folder
        scripts_output_dir = os.path.join(episode_dir, 'Output', 'Scripts')
        self.ensure_directory_exists(scripts_output_dir)
        
        return os.path.join(scripts_output_dir, f"{script_name}.json")
    
    def get_audio_output_path(self, transcript_path: str, audio_type: str = "original") -> str:
        """Get audio file paths in Input (original) or Output/Audio (generated)."""
        transcript_dir = os.path.dirname(transcript_path)  # Input folder
        episode_dir = os.path.dirname(transcript_dir)  # Episode folder
        
        # Get base filename
        base_name = os.path.splitext(os.path.basename(transcript_path))[0]
        
        if audio_type == "original":
            # Original audio goes in Input folder
            return os.path.join(transcript_dir, f"{base_name}.mp3")
        else:
            # Generated audio goes in Output/Audio folder
            audio_output_dir = os.path.join(episode_dir, 'Output', 'Audio')
            self.ensure_directory_exists(audio_output_dir)
            return os.path.join(audio_output_dir, f"{base_name}_{audio_type}.mp3")
    
    def get_video_paths(self, transcript_path: str) -> Dict[str, str]:
        """Get video-related paths for an episode."""
        transcript_dir = os.path.dirname(transcript_path)  # Input folder
        episode_dir = os.path.dirname(transcript_dir)  # Episode folder
        
        # Get base filename
        base_name = os.path.splitext(os.path.basename(transcript_path))[0]
        
        video_input_dir = transcript_dir  # Input folder
        video_output_dir = os.path.join(episode_dir, 'Output', 'Video')
        
        self.ensure_directory_exists(video_output_dir)
        
        return {
            'original_video': os.path.join(video_input_dir, f"{base_name}.mp4"),
            'clips_folder': video_output_dir,
            'final_video': os.path.join(video_output_dir, f"{base_name}_final.mp4")
        }
