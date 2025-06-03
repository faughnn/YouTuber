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
            base_paths: Dictionary with keys like 'audio_output', 'transcript_output'
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
    
    def get_audio_output_path(self, filename: str) -> str:
        """Get the full path for an audio file in the audio output directory."""
        audio_dir = self.base_paths.get('audio_output', 'Audio Rips')
        self.ensure_directory_exists(audio_dir)
        return os.path.join(audio_dir, filename)
    
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
        Get the organized folder structure for transcripts.
        
        Returns:
            Tuple of (channel_folder, episode_folder, transcript_file_path)
        """
        base_name = os.path.splitext(os.path.basename(audio_filename))[0]
        
        # Extract channel name
        channel_name = self.extract_channel_name(base_name)
        
        # Sanitize episode name
        episode_name = self.sanitize_filename(base_name)
        
        # Build paths
        transcript_base = self.base_paths.get('transcript_output', 'Transcripts')
        channel_folder = os.path.join(transcript_base, channel_name)
        episode_folder = os.path.join(channel_folder, episode_name)
        transcript_file = os.path.join(episode_folder, f"{base_name}.json")
        
        # Ensure directories exist
        self.ensure_directory_exists(episode_folder)
        
        return channel_folder, episode_folder, transcript_file
    
    def get_analysis_output_path(self, transcript_path: str) -> str:
        """Get the analysis output path for a transcript file."""
        transcript_dir = os.path.dirname(transcript_path)
        transcript_base = os.path.splitext(os.path.basename(transcript_path))[0]
        return os.path.join(transcript_dir, f"{transcript_base}_analysis.txt")
    
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
