"""
Episode Management Service
==========================

Provides episode discovery, metadata extraction, status tracking, and directory management
for the YouTube video processing pipeline. Integrates with the existing pipeline controller
and database models to provide comprehensive episode selection and management capabilities.

Created: June 20, 2025
Agent: Implementation Agent
Task Reference: Phase 2, Task 2.2 - Episode Management System
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import re

# Import database models
from database.models import db, PipelineSession
from database.utils import SessionManager


@dataclass
class EpisodeMetadata:
    """Represents metadata and status information for a single episode."""
    episode_id: str
    show_name: str
    episode_title: str
    episode_number: Optional[str]
    full_path: str
    processing_path: str
    input_path: str
    output_path: str
    
    # Processing status
    stages_completed: List[int]
    stages_total: int = 7
    processing_status: str = "Not Started"  # Not Started, In Progress, Completed, Error
    last_processed: Optional[str] = None
    duration: Optional[str] = None
    
    # File existence tracking
    has_audio_analysis: bool = False
    has_transcript: bool = False
    has_final_output: bool = False
    
    # Session information
    active_sessions: List[str] = None
    last_session_id: Optional[str] = None

    def __post_init__(self):
        if self.active_sessions is None:
            self.active_sessions = []


class EpisodeManager:
    """
    Manages episode discovery, metadata extraction, and status tracking.
    
    Provides functionality to:
    - Scan Content directory for available episodes
    - Extract episode metadata from directory structure
    - Determine processing status and stage completion
    - Integrate with database session tracking
    - Provide episode filtering and search capabilities
    """
    
    def __init__(self, content_dir: str, session_manager: SessionManager = None):
        """
        Initialize the Episode Manager.
        
        Args:
            content_dir: Path to the Content directory containing shows/episodes
            session_manager: Database session manager for tracking pipeline sessions
        """
        self.content_dir = Path(content_dir)
        self.session_manager = session_manager or SessionManager()
        self.logger = logging.getLogger(__name__)
        
        # Define the 7 pipeline stages and their expected output files
        self.pipeline_stages = {
            1: ["original_audio.wav", "original_audio.mp3"],  # Audio extraction
            2: ["original_audio_transcript.json"],  # Transcription
            3: ["original_audio_analysis_results.json"],  # Analysis
            4: ["segments.json", "selected_segments.json"],  # Segment selection
            5: ["compiled_segments.json"],  # Compilation
            6: ["preset_audio.wav", "preset_audio.mp3"],  # Audio generation
            7: ["final_video.mp4", "final_output.mp4"]  # Final video
        }
    
    def discover_episodes(self) -> List[EpisodeMetadata]:
        """
        Scan the Content directory and discover all available episodes.
        
        Returns:
            List of EpisodeMetadata objects for all discovered episodes
        """
        episodes = []
        
        if not self.content_dir.exists():
            self.logger.warning(f"Content directory does not exist: {self.content_dir}")
            return episodes
        
        try:
            # Scan each show directory
            for show_dir in self.content_dir.iterdir():
                if not show_dir.is_dir():
                    continue
                    
                show_name = show_dir.name
                self.logger.info(f"Scanning show: {show_name}")
                
                # Scan each episode directory within the show
                for episode_dir in show_dir.iterdir():
                    if not episode_dir.is_dir():
                        continue
                    
                    try:
                        episode_metadata = self._extract_episode_metadata(episode_dir, show_name)
                        if episode_metadata:
                            episodes.append(episode_metadata)
                    except Exception as e:
                        self.logger.error(f"Error processing episode {episode_dir}: {e}")
                        continue
            
            self.logger.info(f"Discovered {len(episodes)} episodes across all shows")
            return episodes
            
        except Exception as e:
            self.logger.error(f"Error discovering episodes: {e}")
            return episodes
    
    def _extract_episode_metadata(self, episode_dir: Path, show_name: str) -> Optional[EpisodeMetadata]:
        """
        Extract metadata from an episode directory.
        
        Args:
            episode_dir: Path to the episode directory
            show_name: Name of the show
            
        Returns:
            EpisodeMetadata object or None if invalid episode
        """
        episode_title = episode_dir.name
        
        # Extract episode number if present (e.g., "Joe Rogan Experience #2339")
        episode_number = self._extract_episode_number(episode_title)
        
        # Define paths
        processing_path = episode_dir / "Processing"
        input_path = episode_dir / "Input"
        output_path = episode_dir / "Output"
        
        # Generate unique episode ID
        episode_id = f"{show_name}_{episode_title}".replace(" ", "_").replace("#", "")
        
        # Check processing status
        stages_completed = self._check_stage_completion(processing_path)
        processing_status = self._determine_processing_status(stages_completed)
        
        # Check for key files
        has_audio_analysis = (processing_path / "original_audio_analysis_results.json").exists()
        has_transcript = (processing_path / "original_audio_transcript.json").exists()
        has_final_output = any((output_path / f).exists() for f in ["final_video.mp4", "final_output.mp4"])
        
        # Get duration if available from analysis
        duration = self._extract_duration(processing_path)
        
        # Get last processed timestamp
        last_processed = self._get_last_processed_time(processing_path)
        
        # Check for active sessions
        active_sessions = self._get_active_sessions(str(episode_dir))
        last_session_id = active_sessions[0] if active_sessions else None
        
        return EpisodeMetadata(
            episode_id=episode_id,
            show_name=show_name,
            episode_title=episode_title,
            episode_number=episode_number,
            full_path=str(episode_dir),
            processing_path=str(processing_path),
            input_path=str(input_path),
            output_path=str(output_path),
            stages_completed=stages_completed,
            processing_status=processing_status,
            last_processed=last_processed,
            duration=duration,
            has_audio_analysis=has_audio_analysis,
            has_transcript=has_transcript,
            has_final_output=has_final_output,
            active_sessions=active_sessions,
            last_session_id=last_session_id
        )
    
    def _extract_episode_number(self, episode_title: str) -> Optional[str]:
        """Extract episode number from title (e.g., #2339 from 'Joe Rogan Experience #2339 - Guest')."""
        match = re.search(r'#(\d+)', episode_title)
        return match.group(1) if match else None
    
    def _check_stage_completion(self, processing_path: Path) -> List[int]:
        """
        Check which pipeline stages have been completed for an episode.
        
        Args:
            processing_path: Path to the episode's Processing directory
            
        Returns:
            List of completed stage numbers
        """
        completed_stages = []
        
        if not processing_path.exists():
            return completed_stages
        
        for stage_num, expected_files in self.pipeline_stages.items():
            # Check if any of the expected files for this stage exist
            stage_completed = any((processing_path / file).exists() for file in expected_files)
            if stage_completed:
                completed_stages.append(stage_num)
        
        return completed_stages
    
    def _determine_processing_status(self, stages_completed: List[int]) -> str:
        """Determine overall processing status based on completed stages."""
        if not stages_completed:
            return "Not Started"
        elif len(stages_completed) == 7:
            return "Completed"
        else:
            return "In Progress"
    
    def _extract_duration(self, processing_path: Path) -> Optional[str]:
        """Extract episode duration from analysis results if available."""
        analysis_file = processing_path / "original_audio_analysis_results.json"
        
        if not analysis_file.exists():
            return None
        
        try:
            with open(analysis_file, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)
                
            # Look for duration in common locations
            duration = None
            if isinstance(analysis_data, dict):
                # Check various possible keys
                for key in ['duration', 'length', 'total_duration', 'audio_duration']:
                    if key in analysis_data:
                        duration = analysis_data[key]
                        break
                
                # If duration is numeric, format it
                if isinstance(duration, (int, float)):
                    hours = int(duration // 3600)
                    minutes = int((duration % 3600) // 60)
                    return f"{hours:02d}:{minutes:02d}"
                elif isinstance(duration, str):
                    return duration
            
        except Exception as e:
            self.logger.warning(f"Error extracting duration from {analysis_file}: {e}")
        
        return None
    
    def _get_last_processed_time(self, processing_path: Path) -> Optional[str]:
        """Get the timestamp of the most recent processing activity."""
        if not processing_path.exists():
            return None
        
        try:
            # Find the most recently modified file in the processing directory
            most_recent = None
            most_recent_time = 0
            
            for file_path in processing_path.rglob('*'):
                if file_path.is_file():
                    mtime = file_path.stat().st_mtime
                    if mtime > most_recent_time:
                        most_recent_time = mtime
                        most_recent = file_path
            
            if most_recent_time > 0:
                return datetime.fromtimestamp(most_recent_time).strftime('%Y-%m-%d %H:%M:%S')
                
        except Exception as e:
            self.logger.warning(f"Error getting last processed time: {e}")
        
        return None
    
    def _get_active_sessions(self, episode_path: str) -> List[str]:
        """Get list of active pipeline sessions for an episode."""
        try:
            sessions = self.session_manager.get_sessions_by_episode(episode_path)
            active_sessions = []
            
            for session in sessions:
                if session.status in ['running', 'paused', 'waiting']:
                    active_sessions.append(session.session_id)
            
            return active_sessions
            
        except Exception as e:
            self.logger.warning(f"Error getting active sessions for {episode_path}: {e}")
            return []
    
    def get_episodes_by_show(self, show_name: str) -> List[EpisodeMetadata]:
        """Get all episodes for a specific show."""
        all_episodes = self.discover_episodes()
        return [ep for ep in all_episodes if ep.show_name == show_name]
    
    def get_episodes_by_status(self, status: str) -> List[EpisodeMetadata]:
        """Get all episodes with a specific processing status."""
        all_episodes = self.discover_episodes()
        return [ep for ep in all_episodes if ep.processing_status == status]
    
    def search_episodes(self, query: str) -> List[EpisodeMetadata]:
        """Search episodes by title, show name, or episode number."""
        all_episodes = self.discover_episodes()
        query_lower = query.lower()
        
        matching_episodes = []
        for episode in all_episodes:
            if (query_lower in episode.episode_title.lower() or
                query_lower in episode.show_name.lower() or
                (episode.episode_number and query_lower in episode.episode_number)):
                matching_episodes.append(episode)
        
        return matching_episodes
    
    def get_episode_by_id(self, episode_id: str) -> Optional[EpisodeMetadata]:
        """Get a specific episode by its ID."""
        all_episodes = self.discover_episodes()
        for episode in all_episodes:
            if episode.episode_id == episode_id:
                return episode
        return None
    
    def validate_episode_path(self, episode_path: str) -> Tuple[bool, str]:
        """
        Validate that an episode path is valid for pipeline processing.
        
        Args:
            episode_path: Path to the episode directory
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        episode_dir = Path(episode_path)
        
        if not episode_dir.exists():
            return False, f"Episode directory does not exist: {episode_path}"
        
        if not episode_dir.is_dir():
            return False, f"Episode path is not a directory: {episode_path}"
        
        # Check for required subdirectories
        required_dirs = ['Processing', 'Input', 'Output']
        for req_dir in required_dirs:
            dir_path = episode_dir / req_dir
            if not dir_path.exists():
                # Create missing directories
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    self.logger.info(f"Created missing directory: {dir_path}")
                except Exception as e:
                    return False, f"Cannot create required directory {req_dir}: {e}"
        
        return True, "Episode path is valid"
    
    def get_episode_statistics(self) -> Dict:
        """Get statistics about episodes across all shows."""
        episodes = self.discover_episodes()
        
        shows = {}
        status_counts = {"Not Started": 0, "In Progress": 0, "Completed": 0}
        
        for episode in episodes:
            # Count by show
            if episode.show_name not in shows:
                shows[episode.show_name] = 0
            shows[episode.show_name] += 1
            
            # Count by status
            if episode.processing_status in status_counts:
                status_counts[episode.processing_status] += 1
        
        return {
            "total_episodes": len(episodes),
            "total_shows": len(shows),
            "shows": shows,
            "status_counts": status_counts,
            "episodes_by_show": shows
        }
    
    def cleanup_episode_data(self, episode_path: str, stages_to_clean: List[int] = None) -> bool:
        """
        Clean up processing data for an episode.
        
        Args:
            episode_path: Path to the episode directory
            stages_to_clean: List of stage numbers to clean (default: all stages)
            
        Returns:
            True if cleanup was successful
        """
        try:
            processing_dir = Path(episode_path) / "Processing"
            
            if not processing_dir.exists():
                return True  # Nothing to clean
            
            stages_to_clean = stages_to_clean or list(self.pipeline_stages.keys())
            
            files_removed = 0
            for stage_num in stages_to_clean:
                if stage_num in self.pipeline_stages:
                    for filename in self.pipeline_stages[stage_num]:
                        file_path = processing_dir / filename
                        if file_path.exists():
                            file_path.unlink()
                            files_removed += 1
            
            self.logger.info(f"Cleaned up {files_removed} files from episode: {episode_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cleaning up episode {episode_path}: {e}")
            return False
