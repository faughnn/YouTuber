"""
Timeline Builder for Video Compilator

Orchestrates the sequence and creates FFmpeg input lists for video compilation.
"""
import logging
from pathlib import Path
from typing import List, Dict, Optional, NamedTuple
import math

from .config import FILE_EXTENSIONS, get_temp_dir_name

logger = logging.getLogger(__name__)


class TimelineSegment(NamedTuple):
    """Represents a single segment in the timeline"""
    section_id: str
    section_type: str
    file_path: Path
    is_temp: bool
    estimated_duration: float


class Timeline:
    """Represents the complete timeline of video segments"""
    
    def __init__(self):
        self.segments: List[TimelineSegment] = []
        
    def add_segment(self, segment: TimelineSegment):
        """Add a segment to the timeline"""
        self.segments.append(segment)
        
    def get_segments(self) -> List[TimelineSegment]:
        """Get all timeline segments"""
        return self.segments
        
    def get_segment_count(self) -> int:
        """Get total number of segments"""
        return len(self.segments)
        
    def get_temp_files(self) -> List[Path]:
        """Get list of temporary files in the timeline"""
        return [seg.file_path for seg in self.segments if seg.is_temp]
        
    def get_existing_files(self) -> List[Path]:
        """Get list of existing (non-temp) files in the timeline"""
        return [seg.file_path for seg in self.segments if not seg.is_temp]
        
    def get_total_duration(self) -> float:
        """Get estimated total duration in seconds"""
        return sum(seg.estimated_duration for seg in self.segments)


class TimelineBuilder:
    """Orchestrates the sequence and creates FFmpeg input lists"""
    
    def __init__(self):
        self.timeline: Optional[Timeline] = None
        
    def build_compilation_timeline(self, script_sections: List, audio_dir: Path, video_dir: Path, temp_dir: Path) -> Timeline:
        """
        Build the complete compilation timeline from script sections
        
        Args:
            script_sections: List of script section dictionaries
            audio_dir: Directory containing TTS audio files
            video_dir: Directory containing video clips
            temp_dir: Directory for temporary files
            
        Returns:
            Timeline object with all segments
        """
        logger.info("Building compilation timeline...")
        
        timeline = Timeline()
        
        for section in script_sections:
            section_id = section.get('section_id')
            section_type = section.get('section_type')
            
            if not section_id or not section_type:
                logger.warning(f"Skipping section with missing id or type: {section}")
                continue
                
            # Determine file path and type based on section type
            if section_type in ['intro', 'pre_clip', 'post_clip', 'outro']:
                # Narration segments use temp files (static bg + TTS audio)
                file_path = temp_dir / f"temp_{section_id}{FILE_EXTENSIONS['video']}"
                is_temp = True
                duration = self._estimate_narration_duration(section)
                
            elif section_type == 'video_clip':
                # Video segments use existing clip files
                file_path = video_dir / f"{section_id}{FILE_EXTENSIONS['video']}"
                is_temp = False
                duration = self._estimate_video_duration(file_path)
                
            else:
                logger.warning(f"Unknown section type: {section_type}")
                continue
                
            segment = TimelineSegment(
                section_id=section_id,
                section_type=section_type,
                file_path=file_path,
                is_temp=is_temp,
                estimated_duration=duration
            )
            
            timeline.add_segment(segment)
            
        self.timeline = timeline
        
        logger.info(f"Timeline built with {timeline.get_segment_count()} segments")
        return timeline
        
    def create_concat_file(self, timeline: Timeline, temp_dir: Path) -> Path:
        """
        Create the FFmpeg concat file for the timeline
        
        Args:
            timeline: Timeline object with segments
            temp_dir: Directory for temporary files
            
        Returns:
            Path to created concat file
        """
        concat_file = temp_dir / "concat_list.txt"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(concat_file, 'w', encoding='utf-8') as f:
                for segment in timeline.get_segments():
                    # Use forward slashes for FFmpeg compatibility
                    file_path_str = str(segment.file_path).replace('\\', '/')
                    f.write(f"file '{file_path_str}'\n")
                    
            logger.info(f"Created concat file: {concat_file}")
            return concat_file
            
        except Exception as e:
            logger.error(f"Failed to create concat file: {e}")
            raise
            
    def calculate_total_duration(self, timeline: Timeline) -> float:
        """
        Calculate the estimated total duration of the timeline
        
        Args:
            timeline: Timeline object
            
        Returns:
            Total duration in seconds
        """
        return timeline.get_total_duration()
        
    def validate_segment_order(self, timeline: Timeline) -> bool:
        """
        Validate that segments are in the correct order
        
        Args:
            timeline: Timeline object to validate
            
        Returns:
            True if order is valid
        """
        segments = timeline.get_segments()
        
        if not segments:
            logger.warning("Timeline is empty")
            return False
            
        # Check that intro comes first (if present)
        intro_segments = [s for s in segments if s.section_type == 'intro']
        if intro_segments and segments[0].section_type != 'intro':
            logger.warning("Intro segment should be first")
            return False
            
        # Check that outro comes last (if present)
        outro_segments = [s for s in segments if s.section_type == 'outro']
        if outro_segments and segments[-1].section_type != 'outro':
            logger.warning("Outro segment should be last")
            return False
            
        # Check for reasonable alternating pattern (not strict validation)
        video_clip_count = len([s for s in segments if s.section_type == 'video_clip'])
        narration_count = len([s for s in segments if s.section_type in ['pre_clip', 'post_clip']])
        
        if video_clip_count == 0:
            logger.warning("No video clips found in timeline")
            return False
            
        logger.info(f"Timeline validation passed: {video_clip_count} video clips, {narration_count} narration segments")
        return True
        
    def _estimate_narration_duration(self, section: Dict) -> float:
        """
        Estimate duration for narration sections based on script content
        
        Args:
            section: Script section dictionary
            
        Returns:
            Estimated duration in seconds
        """
        # Try to use provided duration estimate
        estimated_duration = section.get('estimated_duration', '')
        
        if estimated_duration:
            # Parse duration strings like "45s", "1min", "2min 30s"
            duration = self._parse_duration_string(estimated_duration)
            if duration > 0:
                return duration
                
        # Fallback: estimate based on script content length
        script_content = section.get('script_content', '')
        if script_content:
            # Rough estimate: ~150 words per minute, ~5 chars per word
            char_count = len(script_content)
            word_count = char_count / 5
            duration = (word_count / 150) * 60  # Convert to seconds
            return max(duration, 5.0)  # Minimum 5 seconds
            
        # Default fallback
        return 30.0
        
    def _estimate_video_duration(self, video_path: Path) -> float:
        """
        Estimate duration for video clips
        
        Args:
            video_path: Path to video file
            
        Returns:
            Estimated duration in seconds
        """
        # Try to get actual duration using ffprobe if available
        try:
            import subprocess
            
            command = [
                "ffprobe",
                "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "csv=p=0",
                str(video_path)
            ]
            
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            duration = float(result.stdout.strip())
            return duration
            
        except (subprocess.SubprocessError, ValueError, FileNotFoundError):
            # Fallback to default estimate
            logger.debug(f"Could not get duration for {video_path}, using default estimate")
            return 60.0  # Default 1 minute for video clips
            
    def _parse_duration_string(self, duration_str: str) -> float:
        """
        Parse duration strings like "45s", "1min", "2min 30s"
        
        Args:
            duration_str: Duration string to parse
            
        Returns:
            Duration in seconds, or 0 if parsing fails
        """
        try:
            duration_str = duration_str.lower().strip()
            total_seconds = 0
            
            # Handle "Xmin Ys" format
            if 'min' in duration_str and 's' in duration_str:
                parts = duration_str.split()
                for part in parts:
                    if 'min' in part:
                        minutes = float(part.replace('min', ''))
                        total_seconds += minutes * 60
                    elif 's' in part:
                        seconds = float(part.replace('s', ''))
                        total_seconds += seconds
                        
            # Handle "Xmin" format
            elif 'min' in duration_str:
                minutes = float(duration_str.replace('min', ''))
                total_seconds = minutes * 60
                
            # Handle "Xs" format  
            elif 's' in duration_str:
                seconds = float(duration_str.replace('s', ''))
                total_seconds = seconds
                
            return total_seconds
            
        except (ValueError, AttributeError):
            return 0.0
            
    def _format_duration(self, seconds: float) -> str:
        """
        Format duration in seconds to human readable string
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string
        """
        if seconds < 60:
            return f"{seconds:.0f}s"
        else:
            minutes = int(seconds // 60)
            remaining_seconds = int(seconds % 60)
            if remaining_seconds > 0:
                return f"{minutes}m {remaining_seconds}s"
            else:
                return f"{minutes}m"
                
    def get_timeline_summary(self) -> Dict:
        """
        Get a summary of the current timeline
        
        Returns:
            Dictionary with timeline statistics
        """
        if not self.timeline:
            return {}
            
        segments = self.timeline.get_segments()
        
        summary = {
            'total_segments': len(segments),
            'temp_files': len(self.timeline.get_temp_files()),
            'existing_files': len(self.timeline.get_existing_files()),
            'estimated_duration': self.calculate_total_duration(self.timeline),
            'section_counts': {}
        }
        
        # Count segments by type
        for segment in segments:
            section_type = segment.section_type
            summary['section_counts'][section_type] = summary['section_counts'].get(section_type, 0) + 1
            
        return summary