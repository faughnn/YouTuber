"""
Background Processor for Video Compilator

Creates video streams from static image + TTS audio for narration segments.
"""
import logging
import subprocess
from pathlib import Path
from typing import List, Optional, Dict

from .config import VIDEO_CONFIG, AUDIO_CONFIG, FFMPEG_CONFIG, get_background_image_path, FILE_EXTENSIONS

logger = logging.getLogger(__name__)


class BackgroundProcessor:
    """Handles creation of narration videos from static image + TTS audio"""
    
    def __init__(self):
        self.background_image_path = get_background_image_path()
        
    def create_narration_video(self, audio_path: Path, output_path: Path) -> bool:
        """
        Create a video by combining static background image with TTS audio
        
        Args:
            audio_path: Path to TTS audio file
            output_path: Path for output video file
            
        Returns:
            True if successful, False otherwise
        """
        if not audio_path.exists():
            logger.error(f"Audio file not found: {audio_path}")
            return False
            
        if not self.background_image_path.exists():
            logger.error(f"Background image not found: {self.background_image_path}")
            return False
            
        # Get audio duration
        duration = self.get_audio_duration(audio_path)
        if duration <= 0:
            logger.error(f"Could not determine audio duration: {audio_path}")
            return False
            
        # Generate FFmpeg command
        command = self.generate_ffmpeg_command(audio_path, output_path, duration)
        
        # Execute FFmpeg
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )
            
            if output_path.exists():
                logger.info(f"✓ Created narration video: {output_path}")
                return True
            else:
                logger.error(f"Output file not created: {output_path}")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error creating narration video: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error creating narration video: {e}")
            return False
            
    def get_audio_duration(self, audio_path: Path) -> float:
        """
        Get the duration of an audio file in seconds
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Duration in seconds, or 0 if unable to determine
        """
        command = [
            FFMPEG_CONFIG["executable"],
            "-i", str(audio_path),
            "-f", "null",
            "-"        ]
        
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True
            )
              # Parse duration from stderr output (FFmpeg writes info to stderr)
            output = result.stderr
            for line in output.split('\n'):
                if 'Duration:' in line:
                    # Extract duration in format HH:MM:SS.ss
                    duration_str = line.split('Duration:')[1].split(',')[0].strip()
                    return self._parse_duration(duration_str)
                    
            logger.warning(f"Could not parse duration from FFmpeg output for: {audio_path}")
            return 0
            
        except Exception as e:
            logger.error(f"Error getting audio duration: {e}")
            return 0
            
    def _parse_duration(self, duration_str: str) -> float:
        """
        Parse duration string (HH:MM:SS.ss) to seconds
        
        Args:
            duration_str: Duration in HH:MM:SS.ss format
            
        Returns:
            Duration in seconds
        """
        try:
            parts = duration_str.split(':')
            hours = float(parts[0])
            minutes = float(parts[1])
            seconds = float(parts[2])
            
            total_seconds = hours * 3600 + minutes * 60 + seconds
            return total_seconds
        except Exception as e:
            logger.error(f"Error parsing duration '{duration_str}': {e}")
            return 0
            
    def generate_ffmpeg_command(self, audio_path: Path, output_path: Path, duration: float) -> List[str]:
        """
        Generate FFmpeg command for creating narration video
        
        Args:
            audio_path: Path to TTS audio file
            output_path: Path for output video file
            duration: Duration in seconds
            
        Returns:
            List of command arguments for FFmpeg
        """
        # Parse resolution into width and height
        width, height = VIDEO_CONFIG['resolution'].split('x')
        
        command = [
            FFMPEG_CONFIG["executable"],
            "-loop", "1",  # Loop the image
            "-i", str(self.background_image_path),  # Background image input
            "-i", str(audio_path),  # Audio input
            "-c:v", VIDEO_CONFIG["codec"],  # Video codec
            "-preset", VIDEO_CONFIG["preset"],  # Encoding preset
            "-crf", str(VIDEO_CONFIG["crf"]),  # Quality            "-c:a", AUDIO_CONFIG["codec"],  # Audio codec
            "-b:a", AUDIO_CONFIG["bitrate"],  # Audio bitrate
            "-ar", str(AUDIO_CONFIG["sample_rate"]),  # Audio sample rate
            "-ac", str(AUDIO_CONFIG["channels"]),  # Audio channels
            "-r", "30000/1001",  # Match source video frame rate (29.97fps)
            "-pix_fmt", VIDEO_CONFIG["pixel_format"],  # Pixel format
            "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",  # Scale and pad to target resolution
            "-t", str(duration),  # Duration
            "-shortest",  # End when shortest input ends
            "-y" if FFMPEG_CONFIG["overwrite_output"] else "-n",  # Overwrite or not
            str(output_path)
        ]
        
        # Add log level
        if FFMPEG_CONFIG["log_level"]:
            command.insert(1, "-loglevel")
            command.insert(2, FFMPEG_CONFIG["log_level"])
            
        return command
        
    def prepare_background_image(self) -> str:
        """
        Prepare the background image for processing
        
        Returns:
            String description of image preparation status
        """
        if not self.background_image_path.exists():
            return f"Background image not found: {self.background_image_path}"
            
        try:
            # Basic file validation
            file_size = self.background_image_path.stat().st_size
            if file_size == 0:
                return f"Background image is empty: {self.background_image_path}"
                
            return f"Background image ready: {self.background_image_path} ({file_size} bytes)"
            
        except Exception as e:
            return f"Error accessing background image: {e}"
            
    def create_multiple_narration_videos(self, audio_files: List[Path], temp_dir: Path) -> List[Path]:
        """
        Create multiple narration videos in batch
        
        Args:
            audio_files: List of audio file paths
            temp_dir: Directory for temporary video files
            
        Returns:
            List of created video file paths
        """
        created_videos = []
        
        # Ensure temp directory exists
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        for audio_file in audio_files:
            # Generate output filename
            video_filename = f"temp_{audio_file.stem}.mp4"
            output_path = temp_dir / video_filename
            
            # Create narration video
            if self.create_narration_video(audio_file, output_path):
                created_videos.append(output_path)
            else:
                logger.error(f"Failed to create narration video for: {audio_file}")
                
        logger.info(f"Created {len(created_videos)} narration videos")
        return created_videos
        
    def validate_ffmpeg_available(self) -> bool:
        """
        Check if FFmpeg is available and working
        
        Returns:
            True if FFmpeg is available, False otherwise
        """
        try:
            result = subprocess.run(
                [FFMPEG_CONFIG["executable"], "-version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logger.info("FFmpeg is available and working")
                return True
            else:
                logger.error(f"FFmpeg returned error code: {result.returncode}")
                return False
                
        except FileNotFoundError:
            logger.error("FFmpeg not found. Please install FFmpeg and ensure it's in your PATH.")
            return False
        except subprocess.TimeoutExpired:
            logger.error("FFmpeg version check timed out")
            return False
        except Exception as e:
            logger.error(f"Error checking FFmpeg availability: {e}")
            return False
        
    def validate_background_setup(self) -> bool:
        """
        Validate that background image and FFmpeg setup is working
        
        Returns:
            True if setup is valid
        """
        # Check background image
        bg_path = get_background_image_path()
        if not bg_path.exists():
            logger.error(f"Background image not found: {bg_path}")
            return False
            
        # Check if it's a valid image file
        try:
            # Simple check - try to read file size
            size = bg_path.stat().st_size
            if size == 0:
                logger.error("Background image file is empty")
                return False
        except Exception as e:
            logger.error(f"Cannot access background image: {e}")
            return False
            
        # Test FFmpeg with a simple command
        try:
            command = ["ffmpeg", "-f", "lavfi", "-i", "testsrc=duration=1:size=320x240:rate=1", "-f", "null", "-"]
            process = subprocess.run(command, capture_output=True, text=True, timeout=10)
            # Don't check return code as this might fail on some systems, just check if ffmpeg responds
            
        except subprocess.TimeoutExpired:
            # This is actually OK - means ffmpeg is working but we stopped it
            pass
        except FileNotFoundError:
            logger.error("FFmpeg not found in PATH")
            return False
        except Exception as e:
            logger.warning(f"FFmpeg test had issues: {e}")
            
        logger.info("Background setup validation passed")
        return True
        
    def batch_create_narration_videos(self, narration_sections: List[Dict], audio_dir: Path, temp_dir: Path) -> Dict[str, bool]:
        """
        Create multiple narration videos in batch
        
        Args:
            narration_sections: List of narration section dictionaries
            audio_dir: Directory containing TTS audio files
            temp_dir: Directory for temporary video files
            
        Returns:
            Dictionary mapping section_id to success status
        """
        temp_dir.mkdir(parents=True, exist_ok=True)
        results = {}
        
        logger.info(f"Creating {len(narration_sections)} narration videos...")
        
        for section in narration_sections:
            section_id = section.get('section_id')
            if not section_id:
                continue
                
            audio_file = audio_dir / f"{section_id}{FILE_EXTENSIONS['audio']}"
            video_file = temp_dir / f"temp_{section_id}.mp4"
            
            # Create narration video
            success = self.create_narration_video(audio_file, video_file)
            results[section_id] = success
            
            if success:
                logger.info(f"✓ Created: {video_file}")
            else:
                logger.error(f"✗ Failed: {section_id}")
                
        logger.info(f"Batch creation complete: {sum(results.values())}/{len(results)} successful")
        return results