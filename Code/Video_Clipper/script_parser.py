"""
Script Parser Module for Video Clipper

This module handles parsing of unified podcast script files to extract
video clip specifications for video extraction.
"""

import json
import re
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class VideoClipSpec:
    """Data structure for video clip specifications"""
    section_id: str          # e.g., "video_clip_001"
    clip_id: str            # e.g., "covid_censorship_001"
    start_time: str         # e.g., "1:03:55.06"
    end_time: str           # e.g., "1:04:11.28"
    title: str              # Human-readable title
    severity_level: str     # HIGH, MEDIUM, LOW
    estimated_duration: str # e.g., "16s"
    selection_reason: Optional[str] = None
    key_claims: Optional[List[str]] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'section_id': self.section_id,
            'clip_id': self.clip_id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'title': self.title,
            'severity_level': self.severity_level,
            'estimated_duration': self.estimated_duration,
            'selection_reason': self.selection_reason,
            'key_claims': self.key_claims
        }


class UnifiedScriptParser:
    """Parser for unified podcast script files to extract video clip specifications"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def parse_script_file(self, script_path: str) -> List[VideoClipSpec]:
        """
        Parse unified podcast script file and extract video clip specifications.
        
        Args:
            script_path: Path to the unified_podcast_script.json file
            
        Returns:
            List of VideoClipSpec objects for video clips found in script
            
        Raises:
            FileNotFoundError: If script file doesn't exist
            json.JSONDecodeError: If script file is not valid JSON
            ValueError: If required fields are missing
        """
        try:
            script_path = Path(script_path)
            if not script_path.exists():
                raise FileNotFoundError(f"Script file not found: {script_path}")
            
            self.logger.info(f"Parsing script file: {script_path}")
            
            with open(script_path, 'r', encoding='utf-8') as f:
                script_data = json.load(f)
            
            # Extract podcast_sections array
            podcast_sections = script_data.get('podcast_sections', [])
            if not podcast_sections:
                self.logger.warning("No podcast_sections found in script file")
                return []
            
            # Extract video clips from sections
            video_clips = self.extract_video_clips(podcast_sections)
            
            self.logger.info(f"Found {len(video_clips)} video clips in script")
            return video_clips
            
        except Exception as e:
            self.logger.error(f"Error parsing script file {script_path}: {e}")
            raise
    
    def extract_video_clips(self, podcast_sections: List[Dict]) -> List[VideoClipSpec]:
        """
        Extract video clip specifications from podcast sections.
        
        Args:
            podcast_sections: List of podcast section dictionaries
            
        Returns:
            List of VideoClipSpec objects for video clips        """
        video_clips = []
        
        for section in podcast_sections:
            # Support both video_clip and hook_clip section types
            if section.get('section_type') in ['video_clip', 'hook_clip']:
                try:
                    clip_spec = self._parse_video_clip_section(section)
                    if self.validate_clip_data(clip_spec):
                        video_clips.append(clip_spec)                    
                    else:
                        self.logger.warning(f"Invalid clip data for section: {section.get('section_id', 'unknown')}")
                except Exception as e:
                    self.logger.error(f"Error parsing video clip section: {e}")
                    continue
        
        return video_clips
    
    def _parse_video_clip_section(self, section: Dict) -> VideoClipSpec:
        """Parse a single video clip section into VideoClipSpec"""
        # Check for basic required fields
        basic_required_fields = ['section_id', 'clip_id', 'title']
        for field in basic_required_fields:
            if field not in section:
                raise ValueError(f"Missing required field: {field}")
        
        # Determine start_time and end_time
        start_time, end_time = self._extract_clip_times(section)
        
        return VideoClipSpec(
            section_id=section['section_id'],
            clip_id=section['clip_id'],
            start_time=start_time,
            end_time=end_time,
            title=section['title'],
            severity_level=section.get('severity_level', 'MEDIUM'),
            estimated_duration=section.get('estimated_duration', 'Unknown'),
            selection_reason=section.get('selection_reason'),
            key_claims=section.get('key_claims', [])
        )
    
    def _extract_clip_times(self, section: Dict) -> tuple[str, str]:
        """
        Extract start and end times from a video clip section.
        
        Priority order:
        1. If start_time and end_time are explicitly provided, use them
        2. If suggestedClip array exists, calculate from timestamps
        3. Otherwise, raise an error
        
        Args:
            section: Video clip section dictionary
            
        Returns:
            Tuple of (start_time, end_time) as strings
            
        Raises:
            ValueError: If neither explicit times nor suggestedClip are available
        """
        # Option 1: Explicit start_time and end_time
        if 'start_time' in section and 'end_time' in section:
            return section['start_time'], section['end_time']
        
        # Option 2: Calculate from suggestedClip array
        if 'suggestedClip' in section:
            suggested_clip = section['suggestedClip']
            if not isinstance(suggested_clip, list) or not suggested_clip:
                raise ValueError("suggestedClip must be a non-empty list")
            
            # Extract all timestamps
            timestamps = []
            for i, clip_entry in enumerate(suggested_clip):
                if not isinstance(clip_entry, dict):
                    raise ValueError(f"suggestedClip entry {i} must be a dictionary")
                if 'timestamp' not in clip_entry:
                    raise ValueError(f"suggestedClip entry {i} missing 'timestamp' field")
                
                timestamp_str = str(clip_entry['timestamp'])
                try:
                    # Convert to float for comparison
                    timestamp_float = float(timestamp_str)
                    timestamps.append((timestamp_float, timestamp_str))
                except ValueError:
                    raise ValueError(f"Invalid timestamp format in suggestedClip entry {i}: {timestamp_str}")
            
            # Find min and max timestamps
            min_timestamp = min(timestamps, key=lambda x: x[0])
            max_timestamp = max(timestamps, key=lambda x: x[0])
            
            self.logger.info(f"Calculated clip times from suggestedClip: {min_timestamp[1]} to {max_timestamp[1]}")
            return min_timestamp[1], max_timestamp[1]
        
        # Option 3: Neither available
        raise ValueError("Section must have either explicit start_time/end_time or suggestedClip array")
    
    def validate_clip_data(self, clip_spec: VideoClipSpec) -> bool:
        """
        Validate video clip specification data.
        
        Args:
            clip_spec: VideoClipSpec object to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Validate required fields are not empty
            if not all([clip_spec.section_id, clip_spec.clip_id, 
                       clip_spec.start_time, clip_spec.end_time, clip_spec.title]):
                return False
            
            # Validate timestamp formats
            start_seconds = self.parse_timestamp(clip_spec.start_time)
            end_seconds = self.parse_timestamp(clip_spec.end_time)
            
            # Check that end time is after start time
            if end_seconds <= start_seconds:
                self.logger.error(f"End time ({clip_spec.end_time}) is not after start time ({clip_spec.start_time}) for clip {clip_spec.clip_id}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Validation error for clip {clip_spec.clip_id}: {e}")
            return False
    
    def parse_timestamp(self, timestamp: str) -> float:
        """
        Parse timestamp string to seconds (float).
        
        Supported formats:
        - H:MM:SS.MS (1:03:55.06)
        - MM:SS.MS (03:55.06)
        - H:MM:SS (1:03:55)
        - MM:SS (03:55)
        - Decimal seconds (64.821, 3846.508)
        - Integer seconds (64, 3846)
        
        Args:
            timestamp: Timestamp string to parse
            
        Returns:
            Time in seconds as float
            
        Raises:
            ValueError: If timestamp format is not supported
        """
        if not timestamp:
            raise ValueError("Empty timestamp")
        
        # Remove any whitespace
        timestamp = timestamp.strip()
        
        # Check for decimal seconds format first (64.821, 3846.508)
        try:
            # If it's a simple number (integer or float), convert directly
            return float(timestamp)
        except ValueError:
            pass
        
        # Pattern for H:MM:SS.MS or MM:SS.MS format
        pattern_with_ms = r'^(?:(\d+):)?(\d{1,2}):(\d{1,2})\.(\d+)$'
        match = re.match(pattern_with_ms, timestamp)
        
        if match:
            hours, minutes, seconds, milliseconds = match.groups()
            hours = int(hours) if hours else 0
            minutes = int(minutes)
            seconds = int(seconds)
            # Handle variable length milliseconds (06 = 60ms, 123 = 123ms)
            ms_str = milliseconds.ljust(3, '0')[:3]  # Pad or truncate to 3 digits
            milliseconds = int(ms_str)
            
            total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
            return total_seconds
        
        # Pattern for H:MM:SS or MM:SS format (no milliseconds)
        pattern_no_ms = r'^(?:(\d+):)?(\d{1,2}):(\d{1,2})$'
        match = re.match(pattern_no_ms, timestamp)
        
        if match:
            hours, minutes, seconds = match.groups()
            hours = int(hours) if hours else 0
            minutes = int(minutes)
            seconds = int(seconds)
            
            total_seconds = hours * 3600 + minutes * 60 + seconds
            return float(total_seconds)
        
        raise ValueError(f"Unsupported timestamp format: {timestamp}")
    
    def format_timestamp_for_ffmpeg(self, timestamp: str) -> str:
        """
        Convert timestamp to FFmpeg format (HH:MM:SS.mmm).
        
        Args:
            timestamp: Original timestamp string
            
        Returns:
            Timestamp in FFmpeg format
        """
        seconds = self.parse_timestamp(timestamp)
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
    
    def detect_episode_version(self, podcast_sections: List[Dict]) -> str:
        """Detect episode structure version for compatibility
        
        Args:
            podcast_sections: List of podcast section dictionaries
            
        Returns:
            Version string: 'v2_hook_structure', 'v1_intro_structure', or 'unknown'
        """
        if not podcast_sections:
            return "unknown"
            
        first_section = podcast_sections[0]
        section_type = first_section.get('section_type', '')
        
        if section_type == 'hook_clip':
            return "v2_hook_structure"
        elif section_type == 'intro':
            return "v1_intro_structure"
        else:
            self.logger.warning(f"Unknown episode structure, first section type: {section_type}")
            return "unknown"
