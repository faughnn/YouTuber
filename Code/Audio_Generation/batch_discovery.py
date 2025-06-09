"""
Batch Discovery Module for TTS Audio Generation System

Automatically discovers episodes and script files in the Content directory,
identifies which episodes need audio generation, and provides batch processing capabilities.
"""

import json
import logging
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Optional, Set

from .json_parser import GeminiResponseParser

logger = logging.getLogger(__name__)


@dataclass
class EpisodeInfo:
    """Information about a discovered episode."""
    episode_name: str
    episode_path: str
    script_files: List[str]
    audio_files: List[str]
    has_existing_audio: bool
    last_modified: float
    total_sections: int = 0
    audio_sections: int = 0


@dataclass
class DiscoveryResult:
    """Results of episode discovery process."""
    episodes: List[EpisodeInfo]
    script_files: List[str]
    completed_episodes: List[EpisodeInfo]
    pending_episodes: List[EpisodeInfo]
    discovery_time: float
    content_root: str
    total_episodes: int
    
    def __post_init__(self):
        """Calculate derived fields after initialization."""
        self.total_episodes = len(self.episodes)


class BatchDiscovery:
    """
    Discovers episodes and script files for batch processing.
    
    Scans the Content directory structure to find episodes that need
    audio generation and provides filtering capabilities.
    """
    
    def __init__(self, content_root: str = None):
        """
        Initialize batch discovery.
        
        Args:
            content_root: Root directory for content (defaults to Content/)
        """
        if content_root is None:
            # Default to Content directory relative to project root
            content_root = Path(__file__).parent.parent.parent / "Content"
        
        self.content_root = Path(content_root)
        self.parser = GeminiResponseParser()
        
        logger.info(f"Batch Discovery initialized with content root: {self.content_root}")
    
    def discover_episodes(self, 
                         require_gemini_format: bool = True,
                         include_completed: bool = False) -> DiscoveryResult:
        """
        Discover all episodes in the content directory.
        
        Args:
            require_gemini_format: Only include scripts in Gemini response format
            include_completed: Include episodes that already have audio files
            
        Returns:
            Discovery results with found episodes and categorization
        """
        start_time = time.time()
        logger.info("Starting episode discovery...")
        
        episodes = []
        all_script_files = []
        
        try:
            # Scan content root for episodes
            if not self.content_root.exists():
                logger.warning(f"Content root does not exist: {self.content_root}")
                return DiscoveryResult(
                    episodes=[],
                    script_files=[],
                    completed_episodes=[],
                    pending_episodes=[],
                    discovery_time=time.time() - start_time,
                    content_root=str(self.content_root),
                    total_episodes=0
                )
            
            # Find all potential episode directories
            for series_dir in self.content_root.iterdir():
                if not series_dir.is_dir():
                    continue
                
                # Look for episode directories within series
                for episode_dir in series_dir.iterdir():
                    if not episode_dir.is_dir():
                        continue
                    
                    episode_info = self._analyze_episode(
                        episode_dir, 
                        require_gemini_format
                    )
                    
                    if episode_info and episode_info.script_files:
                        episodes.append(episode_info)
                        all_script_files.extend(episode_info.script_files)
            
            # Categorize episodes
            completed_episodes = [ep for ep in episodes if ep.has_existing_audio]
            pending_episodes = [ep for ep in episodes if not ep.has_existing_audio]
            
            # Apply include_completed filter
            if not include_completed:
                episodes = pending_episodes
            
            discovery_time = time.time() - start_time
            
            logger.info(f"Discovery completed in {discovery_time:.2f}s")
            logger.info(f"Found {len(episodes)} episodes, {len(all_script_files)} script files")
            
            return DiscoveryResult(
                episodes=episodes,
                script_files=all_script_files,
                completed_episodes=completed_episodes,
                pending_episodes=pending_episodes,
                discovery_time=discovery_time,
                content_root=str(self.content_root),
                total_episodes=len(episodes) + len(completed_episodes)
            )
            
        except Exception as e:
            logger.error(f"Discovery failed: {e}")
            raise
    
    def _analyze_episode(self, episode_dir: Path, require_gemini_format: bool) -> Optional[EpisodeInfo]:
        """
        Analyze a single episode directory for script files and audio.
        
        Args:
            episode_dir: Path to episode directory
            require_gemini_format: Only include Gemini format scripts
            
        Returns:
            Episode info if valid, None otherwise
        """
        try:
            logger.debug(f"Analyzing episode: {episode_dir}")
            
            # Look for script files
            script_files = []
            audio_files = []
            
            # Check Output/Scripts directory for Gemini format files
            output_scripts_dir = episode_dir / "Output" / "Scripts"
            if output_scripts_dir.exists():
                for script_file in output_scripts_dir.glob("*.json"):
                    if self._is_valid_script_file(script_file, require_gemini_format):
                        script_files.append(str(script_file))
            
            # Also check root episode directory for script files
            for script_file in episode_dir.glob("*.json"):
                if self._is_valid_script_file(script_file, require_gemini_format):
                    script_files.append(str(script_file))
            
            # If no script files found, skip this episode
            if not script_files:
                return None
            
            # Check for existing audio files
            audio_dir = episode_dir / "Output" / "Audio"
            if audio_dir.exists():
                audio_files = [str(f) for f in audio_dir.glob("*.wav")]
            
            # Calculate episode metrics
            total_sections = 0
            audio_sections = 0
            
            for script_file in script_files:
                try:
                    sections = self._count_audio_sections(script_file)
                    total_sections += sections
                except Exception as e:
                    logger.warning(f"Could not analyze script {script_file}: {e}")
            
            # Count existing audio sections
            audio_sections = len(audio_files)
            
            # Determine if episode has existing audio
            has_existing_audio = audio_sections > 0 and audio_sections >= total_sections * 0.8  # 80% threshold
            
            # Get last modified time
            last_modified = max(
                Path(script_file).stat().st_mtime 
                for script_file in script_files
            )
            
            return EpisodeInfo(
                episode_name=episode_dir.name,
                episode_path=str(episode_dir),
                script_files=script_files,
                audio_files=audio_files,
                has_existing_audio=has_existing_audio,
                last_modified=last_modified,
                total_sections=total_sections,
                audio_sections=audio_sections
            )
            
        except Exception as e:
            logger.warning(f"Failed to analyze episode {episode_dir}: {e}")
            return None
    
    def _is_valid_script_file(self, script_file: Path, require_gemini_format: bool) -> bool:
        """
        Check if a script file is valid for processing.
        
        Args:
            script_file: Path to script file
            require_gemini_format: Whether to require Gemini response format
            
        Returns:
            True if file is valid for processing
        """
        try:
            # Check file exists and is readable
            if not script_file.exists() or script_file.stat().st_size == 0:
                return False
            
            # If not requiring Gemini format, accept any JSON
            if not require_gemini_format:
                try:
                    with open(script_file, 'r', encoding='utf-8') as f:
                        json.load(f)
                    return True
                except json.JSONDecodeError:
                    return False
            
            # Check if it's a valid Gemini response format
            try:
                response_data = self.parser.load_response_file(str(script_file))
                # Must have podcast_sections to be valid
                return response_data.get('podcast_sections') is not None
            except Exception:
                return False
                
        except Exception as e:
            logger.debug(f"Error validating script file {script_file}: {e}")
            return False
    
    def _count_audio_sections(self, script_file: str) -> int:
        """
        Count the number of audio sections in a script file.
        
        Args:
            script_file: Path to script file
            
        Returns:
            Number of audio sections found
        """
        try:
            response_data = self.parser.load_response_file(script_file)
            audio_sections = self.parser.extract_audio_sections(response_data)
            return len(audio_sections)
        except Exception as e:
            logger.debug(f"Could not count sections in {script_file}: {e}")
            return 0
    
    def filter_by_modification_time(self, 
                                  episodes: List[EpisodeInfo], 
                                  since_hours: float) -> List[EpisodeInfo]:
        """
        Filter episodes by modification time.
        
        Args:
            episodes: List of episodes to filter
            since_hours: Only include episodes modified within this many hours
            
        Returns:
            Filtered list of episodes
        """
        cutoff_time = time.time() - (since_hours * 3600)
        
        filtered = [
            ep for ep in episodes 
            if ep.last_modified >= cutoff_time
        ]
        
        logger.info(f"Filtered {len(episodes)} episodes to {len(filtered)} modified within {since_hours} hours")
        return filtered
    
    def filter_by_episode_names(self, 
                               episodes: List[EpisodeInfo], 
                               patterns: List[str]) -> List[EpisodeInfo]:
        """
        Filter episodes by name patterns.
        
        Args:
            episodes: List of episodes to filter
            patterns: List of patterns to match against episode names
            
        Returns:
            Filtered list of episodes
        """
        filtered = []
        
        for episode in episodes:
            for pattern in patterns:
                if pattern.lower() in episode.episode_name.lower():
                    filtered.append(episode)
                    break
        
        logger.info(f"Filtered {len(episodes)} episodes to {len(filtered)} matching patterns")
        return filtered
    
    def get_statistics(self, episodes: List[EpisodeInfo]) -> Dict[str, any]:
        """
        Get statistics about discovered episodes.
        
        Args:
            episodes: List of episodes to analyze
            
        Returns:
            Dictionary with various statistics
        """
        if not episodes:
            return {
                "total_episodes": 0,
                "total_script_files": 0,
                "total_audio_files": 0,
                "completed_episodes": 0,
                "pending_episodes": 0
            }
        
        return {
            "total_episodes": len(episodes),
            "total_script_files": sum(len(ep.script_files) for ep in episodes),
            "total_audio_files": sum(len(ep.audio_files) for ep in episodes),
            "completed_episodes": sum(1 for ep in episodes if ep.has_existing_audio),
            "pending_episodes": sum(1 for ep in episodes if not ep.has_existing_audio),
            "total_sections": sum(ep.total_sections for ep in episodes),
            "total_audio_sections": sum(ep.audio_sections for ep in episodes),
            "avg_sections_per_episode": sum(ep.total_sections for ep in episodes) / len(episodes),
            "completion_rate": sum(1 for ep in episodes if ep.has_existing_audio) / len(episodes) * 100
        }
    
    def save_discovery_report(self, 
                            results: DiscoveryResult, 
                            output_path: str) -> str:
        """
        Save discovery results to a JSON report file.
        
        Args:
            results: Discovery results to save
            output_path: Path where to save the report
            
        Returns:
            Path to saved report file
        """
        try:
            report_data = {
                "discovery_report": {
                    "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "content_root": results.content_root,
                    "discovery_time": results.discovery_time,
                    "statistics": self.get_statistics(results.episodes)
                },
                "episodes": [asdict(ep) for ep in results.episodes],
                "script_files": results.script_files,
                "completed_episodes": [asdict(ep) for ep in results.completed_episodes],
                "pending_episodes": [asdict(ep) for ep in results.pending_episodes]
            }
            
            output_path = Path(output_path)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Discovery report saved to: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Failed to save discovery report: {e}")
            raise
