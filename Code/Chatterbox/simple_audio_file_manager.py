"""
Simple Audio File Manager

Simplified file manager for SimpleTTSEngine - removes complex dependencies
and focuses only on the 3 core methods needed for API-based TTS processing.
"""

import logging
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class SimpleAudioFileManager:
    """
    Simplified file manager for SimpleTTSEngine - no complex dependencies.
    
    Provides only the essential methods needed for API-based TTS processing:
    - discover_episode_from_script(): Find episode directory from script path
    - create_episode_structure(): Create Output/Audio directory structure
    - organize_audio_file(): Organize generated audio files
    """
    
    def __init__(self, content_root: str = None):
        """
        Initialize the Simple Audio File Manager.
        
        Args:
            content_root: Root directory for content (defaults to Content/)
        """
        if content_root is None:
            # Default to Content directory relative to project root
            content_root = Path(__file__).parent.parent.parent / "Content"
        
        self.content_root = Path(content_root)
        
        logger.info(f"SimpleAudioFileManager initialized with content root: {self.content_root}")
    
    def discover_episode_from_script(self, script_path: str) -> Optional[str]:
        """
        Discover episode directory from a script file path.
        
        Args:
            script_path: Path to the script file
            
        Returns:
            Path to the episode directory, or None if not found
        """
        try:
            script_path_obj = Path(script_path)
            # Look for the episode directory by traversing upward
            current_dir = script_path_obj.parent
            
            while current_dir != current_dir.parent:  # Not at root
                # Check if this looks like an episode directory
                # Skip Processing, Scripts, Output directories - go up to actual episode
                if (current_dir.name not in ["Scripts", "Output", "Processing", "Chatterbox"] and 
                    "Content" in str(current_dir) and
                    current_dir.parent.name != "Content"):  # Make sure it's an episode, not series
                    
                    # This should be the episode directory
                    logger.debug(f"Discovered episode directory: {current_dir}")
                    return str(current_dir)
                
                current_dir = current_dir.parent
            
            logger.warning(f"Could not discover episode directory from script: {script_path}")
            return None
            
        except Exception as e:
            logger.error(f"Error discovering episode from script {script_path}: {e}")
            return None
    
    def create_episode_structure(self, episode_path: str) -> str:
        """
        Create the required directory structure for an episode's audio output.
        
        Args:
            episode_path: Path to the episode directory
            
        Returns:
            Path to the Audio output directory
            
        Raises:
            OSError: If directory creation fails
        """
        try:
            episode_dir = Path(episode_path)
            
            # Create the main Output/Audio directory (matching existing pattern)
            audio_output_dir = episode_dir / "Output" / "Audio"
            audio_output_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Created episode audio structure: {audio_output_dir}")
            return str(audio_output_dir)
            
        except OSError as e:
            logger.error(f"Failed to create episode structure for {episode_path}: {e}")
            raise
    
    def organize_audio_file(self, file_path: str, metadata: Dict[str, Any]) -> str:
        """
        Organize an audio file within the episode directory structure.
        
        Args:
            file_path: Path to the generated audio file
            metadata: Metadata dictionary containing episode and section info
            
        Returns:
            Final organized file path
            
        Raises:
            OSError: If file organization fails
        """
        try:
            file_path = Path(file_path)
            
            # Extract organizational information from metadata
            episode_dir = metadata.get('episode_dir', '')
            section_id = metadata.get('section_id', 'unknown')
            
            if not episode_dir:
                # If no episode directory specified, use current location
                logger.warning("No episode directory specified in metadata, keeping file in place")
                return str(file_path)
            
            # Create episode directory structure
            audio_output_dir = self.create_episode_structure(episode_dir)
            
            # Generate organized filename
            organized_filename = self._generate_organized_filename(section_id, metadata)
            organized_path = Path(audio_output_dir) / organized_filename
              # Move file if it's not already in the right location
            if file_path != organized_path:
                # Create target directory if needed
                organized_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Remove existing target file if it exists (same behavior as original)
                if organized_path.exists():
                    organized_path.unlink()
                
                # Move/copy the file
                if file_path.exists():
                    file_path.rename(organized_path)
                    logger.debug(f"Organized audio file: {file_path} -> {organized_path}")
                else:
                    logger.warning(f"Source audio file not found: {file_path}")
                    return str(file_path)
            
            return str(organized_path)
            
        except Exception as e:
            logger.error(f"Failed to organize audio file {file_path}: {e}")
            raise OSError(f"File organization failed: {e}")
    
    def _generate_organized_filename(self, section_id: str, metadata: Dict[str, Any]) -> str:
        """
        Generate an organized filename based on section ID and metadata.
        
        Args:
            section_id: Section identifier
            metadata: Additional metadata for filename generation
            
        Returns:
            Organized filename with .wav extension
        """
        # Clean section ID for filename
        clean_section_id = section_id.replace(" ", "_").replace(":", "_")
        
        # Add timestamp if requested
        if metadata.get('include_timestamp', False):
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            return f"{clean_section_id}_{timestamp}.wav"
        
        return f"{clean_section_id}.wav"
