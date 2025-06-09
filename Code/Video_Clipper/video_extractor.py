"""
Video Extractor Module for Video Clipper

This module handles the actual video clip extraction using FFmpeg
with optimized settings and comprehensive error handling.
"""

import os
import subprocess
import logging
import time
import json
from typing import List, Dict, Optional
from pathlib import Path
from dataclasses import dataclass, asdict

from .script_parser import VideoClipSpec, UnifiedScriptParser


@dataclass
class ExtractionResult:
    """Result of a single clip extraction"""
    success: bool
    clip_spec: VideoClipSpec
    output_path: Optional[str] = None
    error_message: Optional[str] = None
    extraction_time: Optional[float] = None
    file_size_bytes: Optional[int] = None


@dataclass
class ExtractionReport:
    """Comprehensive report of the extraction process"""
    total_clips: int
    successful_clips: int
    failed_clips: int
    total_time: float
    output_directory: str
    results: List[ExtractionResult]
    errors: List[str]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'total_clips': self.total_clips,
            'successful_clips': self.successful_clips,
            'failed_clips': self.failed_clips,
            'success_rate': f"{(self.successful_clips / self.total_clips * 100):.1f}%" if self.total_clips > 0 else "0%",
            'total_time_seconds': self.total_time,
            'total_time_formatted': f"{self.total_time:.2f}s",
            'output_directory': self.output_directory,
            'results': [asdict(result) for result in self.results],
            'errors': self.errors,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }


class VideoClipExtractor:
    """Main video clip extraction class using FFmpeg"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize video extractor with configuration.
        
        Args:
            config: Configuration dictionary with quality and processing settings
        """
        self.logger = logging.getLogger(__name__)
        self.parser = UnifiedScriptParser()
        
        # Default configuration
        self.config = {
            "start_buffer_seconds": 3.0,
            "end_buffer_seconds": 0.0,
            "video_quality": {
                "codec": "libx264",
                "crf": 23,
                "preset": "fast"
            },
            "audio_quality": {
                "codec": "aac",
                "bitrate": "128k"
            },
            "processing": {
                "max_retries": 2,
                "timeout_seconds": 300,
                "continue_on_error": True
            }
        }
        
        # Update with user config if provided
        if config:
            self._update_config(config)
    
    def _update_config(self, user_config: Dict):
        """Update configuration with user-provided settings"""
        for key, value in user_config.items():
            if key in self.config:
                if isinstance(value, dict) and isinstance(self.config[key], dict):
                    self.config[key].update(value)
                else:
                    self.config[key] = value
    
    def extract_clips(self, video_path: Path, clips: List[VideoClipSpec], 
                     output_dir: Path, start_buffer: Optional[float] = None,
                     end_buffer: Optional[float] = None) -> ExtractionReport:
        """
        Extract multiple video clips from a source video.
        
        Args:
            video_path: Path to source video file
            clips: List of VideoClipSpec objects to extract
            output_dir: Directory to save extracted clips
            start_buffer: Buffer time (seconds) to add before clip start
            end_buffer: Buffer time (seconds) to add after clip end
            
        Returns:
            ExtractionReport with detailed results
        """
        start_time = time.time()
        results = []
        errors = []
        
        # Use provided buffers or config defaults
        if start_buffer is None:
            start_buffer = self.config["start_buffer_seconds"]
        if end_buffer is None:
            end_buffer = self.config["end_buffer_seconds"]
        
        self.logger.info(f"Starting extraction of {len(clips)} clips from {video_path}")
        self.logger.info(f"Using buffers: start={start_buffer}s, end={end_buffer}s")
        
        # Validate inputs
        if not video_path.exists():
            error_msg = f"Source video file not found: {video_path}"
            self.logger.error(error_msg)
            errors.append(error_msg)
            return self._create_error_report(clips, output_dir, errors, time.time() - start_time)
        
        # Ensure output directory exists
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            error_msg = f"Failed to create output directory {output_dir}: {e}"
            self.logger.error(error_msg)
            errors.append(error_msg)
            return self._create_error_report(clips, output_dir, errors, time.time() - start_time)
        
        # Check FFmpeg availability
        if not self._check_ffmpeg():
            error_msg = "FFmpeg not found in PATH"
            self.logger.error(error_msg)
            errors.append(error_msg)
            return self._create_error_report(clips, output_dir, errors, time.time() - start_time)
        
        # Extract each clip
        for i, clip in enumerate(clips, 1):
            self.logger.info(f"Processing clip {i}/{len(clips)}: {clip.section_id}")
            
            try:
                result = self.extract_single_clip(
                    video_path, clip, output_dir, start_buffer, end_buffer
                )
                results.append(result)
                
                if result.success:
                    self.logger.info(f"Successfully extracted {clip.section_id}")
                else:
                    self.logger.error(f"Failed to extract {clip.section_id}: {result.error_message}")
                    if not self.config["processing"]["continue_on_error"]:
                        break
                        
            except Exception as e:
                error_msg = f"Unexpected error extracting {clip.section_id}: {e}"
                self.logger.error(error_msg)
                errors.append(error_msg)
                
                # Create failed result
                result = ExtractionResult(
                    success=False,
                    clip_spec=clip,
                    error_message=error_msg
                )
                results.append(result)
                
                if not self.config["processing"]["continue_on_error"]:
                    break
        
        total_time = time.time() - start_time
        successful_count = sum(1 for r in results if r.success)
        
        report = ExtractionReport(
            total_clips=len(clips),
            successful_clips=successful_count,
            failed_clips=len(clips) - successful_count,
            total_time=total_time,
            output_directory=str(output_dir),
            results=results,
            errors=errors
        )
        
        self.logger.info(f"Extraction completed: {successful_count}/{len(clips)} clips in {total_time:.2f}s")
        return report
    
    def extract_single_clip(self, video_path: Path, clip: VideoClipSpec, 
                           output_dir: Path, start_buffer: float = 0.0,
                           end_buffer: float = 0.0) -> ExtractionResult:
        """
        Extract a single video clip.
        
        Args:
            video_path: Path to source video file
            clip: VideoClipSpec with clip information
            output_dir: Directory to save extracted clip
            start_buffer: Buffer time (seconds) to add before clip start
            end_buffer: Buffer time (seconds) to add after clip end
            
        Returns:
            ExtractionResult with detailed result information
        """
        start_time = time.time()
        
        try:
            # Calculate actual start and end times with buffers
            start_seconds = self.parser.parse_timestamp(clip.start_time) - start_buffer
            end_seconds = self.parser.parse_timestamp(clip.end_time) + end_buffer
            
            # Ensure start time is not negative
            start_seconds = max(0, start_seconds)
            
            # Calculate duration
            duration = end_seconds - start_seconds
            
            # Generate output filename
            output_path = output_dir / f"{clip.section_id}.mp4"
            
            # Build and execute FFmpeg command
            success = self._execute_ffmpeg_extraction(
                video_path, output_path, start_seconds, duration
            )
            
            extraction_time = time.time() - start_time
            
            if success and output_path.exists():
                file_size = output_path.stat().st_size
                return ExtractionResult(
                    success=True,
                    clip_spec=clip,
                    output_path=str(output_path),
                    extraction_time=extraction_time,
                    file_size_bytes=file_size
                )
            else:
                return ExtractionResult(
                    success=False,
                    clip_spec=clip,
                    error_message="FFmpeg extraction failed or output file not created",
                    extraction_time=extraction_time
                )
                
        except Exception as e:
            return ExtractionResult(
                success=False,
                clip_spec=clip,
                error_message=str(e),
                extraction_time=time.time() - start_time
            )
    
    def _execute_ffmpeg_extraction(self, video_path: Path, output_path: Path,
                                  start_seconds: float, duration: float) -> bool:
        """
        Execute FFmpeg command to extract video clip.
        
        Args:
            video_path: Source video file path
            output_path: Output clip file path
            start_seconds: Start time in seconds
            duration: Duration in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Build FFmpeg command
            cmd = self._build_ffmpeg_command(video_path, output_path, start_seconds, duration)
            
            self.logger.debug(f"FFmpeg command: {' '.join(cmd)}")
            
            # Execute command with timeout
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config["processing"]["timeout_seconds"]
            )
            
            if result.returncode == 0:
                return True
            else:
                self.logger.error(f"FFmpeg error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"FFmpeg command timed out after {self.config['processing']['timeout_seconds']}s")
            return False
        except Exception as e:
            self.logger.error(f"Error executing FFmpeg: {e}")
            return False
    
    def _build_ffmpeg_command(self, video_path: Path, output_path: Path,
                             start_seconds: float, duration: float) -> List[str]:
        """
        Build FFmpeg command with optimized settings.
        
        Args:
            video_path: Source video file path
            output_path: Output clip file path
            start_seconds: Start time in seconds
            duration: Duration in seconds
            
        Returns:
            FFmpeg command as list of strings
        """
        cmd = [
            "ffmpeg",
            "-ss", f"{start_seconds:.3f}",  # Seek to start time
            "-i", str(video_path),          # Input file
            "-t", f"{duration:.3f}",        # Duration
            "-c:v", self.config["video_quality"]["codec"],      # Video codec
            "-crf", str(self.config["video_quality"]["crf"]),   # Quality setting
            "-preset", self.config["video_quality"]["preset"],  # Encoding preset
            "-c:a", self.config["audio_quality"]["codec"],      # Audio codec
            "-b:a", self.config["audio_quality"]["bitrate"],    # Audio bitrate
            "-avoid_negative_ts", "make_zero",  # Handle timing edge cases
            "-y",                               # Overwrite output files
            str(output_path)                    # Output file
        ]
        
        return cmd
    
    def _check_ffmpeg(self) -> bool:
        """Check if FFmpeg is available in PATH"""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _create_error_report(self, clips: List[VideoClipSpec], output_dir: Path,
                           errors: List[str], total_time: float) -> ExtractionReport:
        """Create an error report when extraction cannot proceed"""
        results = [
            ExtractionResult(
                success=False,
                clip_spec=clip,
                error_message="Extraction failed due to setup errors"
            )
            for clip in clips
        ]
        
        return ExtractionReport(
            total_clips=len(clips),
            successful_clips=0,
            failed_clips=len(clips),
            total_time=total_time,
            output_directory=str(output_dir),
            results=results,
            errors=errors
        )
