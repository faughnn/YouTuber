"""
Audio File Manager for TTS Audio Generation System

This module handles file organization, directory structure creation,
and metadata tracking for generated audio files.
"""

import json
import logging
import os
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class GenerationResult:
    """Result of a single audio section generation."""
    section_id: str
    section_type: str
    audio_file_path: str
    success: bool
    error_message: str = ""
    generation_time: float = 0.0
    file_size: int = 0
    audio_duration: float = 0.0
    text_length: int = 0
    script_content: str = ""
    audio_tone: str = ""


@dataclass
class EpisodeMetadata:
    """Metadata for an episode's audio generation."""
    episode_name: str
    episode_path: str
    script_file: str
    total_sections: int
    audio_sections: int
    video_sections: int
    generated_timestamp: str


class AudioFileManager:
    """
    Manages audio file organization and metadata for the TTS system.
    
    Handles directory structure creation, file naming, and tracking
    of generated audio files with comprehensive metadata.
    """
    
    def __init__(self, content_root: str = None):
        """
        Initialize the Audio File Manager.
        
        Args:
            content_root: Root directory for content (defaults to Content/)
        """
        if content_root is None:
            # Default to Content directory relative to project root
            content_root = Path(__file__).parent.parent.parent / "Content"
        
        self.content_root = Path(content_root)
        logger.info(f"Audio File Manager initialized with content root: {self.content_root}")
    
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
            
            # Create the main Output/Audio directory
            audio_output_dir = episode_dir / "Output" / "Audio"
            audio_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Also ensure Scripts directory exists for metadata
            scripts_dir = episode_dir / "Output" / "Scripts"
            scripts_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Created episode audio structure: {audio_output_dir}")
            return str(audio_output_dir)
            
        except OSError as e:
            logger.error(f"Failed to create episode structure for {episode_path}: {e}")
            raise
    
    def get_audio_output_path(self, episode_dir: str, section_id: str) -> str:
        """
        Generate the full output path for an audio file based on section_id.
        
        Args:
            episode_dir: Path to the episode directory
            section_id: Unique identifier for the section
            
        Returns:
            Full path where the audio file should be saved
        """
        # Ensure Audio directory exists
        audio_dir = self.create_episode_structure(episode_dir)
        
        # Generate filename with .wav extension
        filename = f"{section_id}.wav"
        output_path = Path(audio_dir) / filename
        
        logger.debug(f"Generated audio output path: {output_path}")
        return str(output_path)
    
    def validate_output_directory(self, path: str) -> bool:
        """
        Validate that an output directory exists and is writable.
        
        Args:
            path: Directory path to validate
            
        Returns:
            True if directory is valid and writable
        """
        try:
            path_obj = Path(path)
            
            # Check if directory exists
            if not path_obj.exists():
                logger.warning(f"Output directory does not exist: {path}")
                return False
            
            # Check if it's actually a directory
            if not path_obj.is_dir():
                logger.warning(f"Output path is not a directory: {path}")
                return False
            
            # Check write permissions by creating a test file
            test_file = path_obj / ".write_test"
            try:
                test_file.touch()
                test_file.unlink()  # Clean up
                logger.debug(f"Output directory is writable: {path}")
                return True
            except OSError:
                logger.warning(f"Output directory is not writable: {path}")
                return False
                
        except Exception as e:
            logger.error(f"Error validating output directory {path}: {e}")
            return False
    
    def save_generation_metadata(self, 
                                results: List[GenerationResult], 
                                episode_metadata: EpisodeMetadata,
                                output_dir: str) -> str:
        """
        Save comprehensive metadata about the audio generation process.
        
        Args:
            results: List of generation results for all sections
            episode_metadata: Episode-level metadata
            output_dir: Directory where metadata should be saved
            
        Returns:
            Path to the saved metadata file
        """
        try:
            # Create metadata structure
            metadata = {
                "episode_info": asdict(episode_metadata),
                "generation_summary": {
                    "total_sections_processed": len(results),
                    "successful_generations": sum(1 for r in results if r.success),
                    "failed_generations": sum(1 for r in results if not r.success),
                    "total_generation_time": sum(r.generation_time for r in results),
                    "total_audio_duration": sum(r.audio_duration for r in results),
                    "total_file_size": sum(r.file_size for r in results),
                    "generated_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                },
                "section_results": [asdict(result) for result in results],
                "successful_files": [r.audio_file_path for r in results if r.success],
                "failed_sections": [
                    {"section_id": r.section_id, "error": r.error_message} 
                    for r in results if not r.success
                ]
            }
            
            # Save JSON metadata
            metadata_path = Path(output_dir) / "tts_generation_report.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # Save human-readable summary
            summary_path = Path(output_dir) / "tts_generation_summary.txt"
            self._save_human_readable_summary(metadata, summary_path)
            logger.info(f"Saved generation metadata to: {metadata_path}")
            return str(metadata_path)
            
        except Exception as e:
            logger.error(f"Failed to save generation metadata: {e}")
            raise
    
    def _save_human_readable_summary(self, metadata: Dict[str, Any], summary_path: Path) -> None:
        """Save a human-readable summary of the generation process."""
        try:
            summary = metadata["generation_summary"]
            episode_info = metadata["episode_info"]
            
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write("TTS AUDIO GENERATION SUMMARY\n")
                f.write("=" * 50 + "\n\n")
                
                f.write(f"Episode: {episode_info['episode_name']}\n")
                f.write(f"Generated: {summary['generated_timestamp']}\n")
                f.write(f"Script File: {episode_info['script_file']}\n\n")
                
                f.write("PROCESSING SUMMARY:\n")
                f.write(f"• Total sections processed: {summary['total_sections_processed']}\n")
                f.write(f"• Successful generations: {summary['successful_generations']}\n")
                f.write(f"• Failed generations: {summary['failed_generations']}\n")
                f.write(f"• Total generation time: {summary['total_generation_time']:.2f} seconds\n")
                f.write(f"• Total audio duration: {summary['total_audio_duration']:.2f} seconds\n")
                f.write(f"• Total file size: {summary['total_file_size']:,} bytes\n\n")
                
                if metadata["successful_files"]:
                    f.write("GENERATED FILES:\n")
                    for file_path in metadata["successful_files"]:
                        filename = Path(file_path).name
                        f.write(f"• {filename}\n")
                    f.write("\n")
                
                if metadata["failed_sections"]:
                    f.write("FAILED SECTIONS:\n")
                    for failed in metadata["failed_sections"]:
                        f.write(f"• {failed['section_id']}: {failed['error']}\n")
                    f.write("\n")
                
                f.write(f"Full details saved to: tts_generation_report.json\n")
                
            logger.debug(f"Saved human-readable summary to: {summary_path}")
            
        except Exception as e:
            logger.error(f"Failed to save human-readable summary: {e}")
    
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
                if (current_dir.name not in ["Scripts", "Output", "Processing"] and 
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
    
    def get_relative_audio_path(self, audio_file_path: str, episode_dir: str) -> str:
        """
        Get relative path for audio file within episode structure.
        
        Args:
            audio_file_path: Full path to audio file
            episode_dir: Episode directory path
            
        Returns:
            Relative path from episode directory
        """
        try:
            audio_path = Path(audio_file_path)
            episode_path = Path(episode_dir)
            
            relative_path = audio_path.relative_to(episode_path)
            return str(relative_path)
            
        except ValueError:
            # If relative path calculation fails, return just the filename
            return Path(audio_file_path).name
    
    def cleanup_temp_files(self, temp_dir: str) -> None:
        """
        Clean up temporary files and directories.
        
        Args:
            temp_dir: Temporary directory to clean up
        """
        try:
            temp_path = Path(temp_dir)
            if temp_path.exists() and temp_path.is_dir():
                # Remove all files in temp directory
                for file_path in temp_path.iterdir():
                    if file_path.is_file():
                        file_path.unlink()
                        logger.debug(f"Cleaned up temp file: {file_path}")
                
                # Remove temp directory if empty
                try:
                    temp_path.rmdir()
                    logger.debug(f"Cleaned up temp directory: {temp_path}")
                except OSError:
                    # Directory not empty, that's okay
                    pass
                    
        except Exception as e:
            logger.warning(f"Error cleaning up temp files in {temp_dir}: {e}")
