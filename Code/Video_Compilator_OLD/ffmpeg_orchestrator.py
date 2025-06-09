"""
FFmpeg Orchestrator for Video Compilator

Executes the final video compilation using FFmpeg commands.
"""
import subprocess
import logging
from pathlib import Path
from typing import List, Optional, NamedTuple
import shlex

from .config import VIDEO_CONFIG, AUDIO_CONFIG, FFMPEG_CONFIG

logger = logging.getLogger(__name__)


class CompileResult(NamedTuple):
    """Result of FFmpeg compilation"""
    success: bool
    output_path: Optional[Path]
    error_message: str
    stderr: str
    file_size_mb: float


class FFmpegOrchestrator:
    """Executes final video compilation using FFmpeg"""
    
    def __init__(self):
        self.ffmpeg_executable = FFMPEG_CONFIG["executable"]
        
    def compile_final_video(self, concat_file: Path, output_path: Path) -> CompileResult:
        """
        Compile the final video using FFmpeg concat demuxer
        
        Args:
            concat_file: Path to the concat list file
            output_path: Path for the final compiled video
            
        Returns:
            CompileResult with success status and details
        """
        logger.info(f"Starting final video compilation...")
        logger.info(f"Concat file: {concat_file}")
        logger.info(f"Output path: {output_path}")
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Build FFmpeg command
        command = self._build_ffmpeg_command(concat_file, output_path)
        
        try:
            result = self.execute_ffmpeg_command(command)
            
            if result.success:
                # Verify output file was created and get size
                if output_path.exists():
                    file_size_mb = output_path.stat().st_size / (1024 * 1024)
                    logger.info(f"Compilation successful! Output size: {file_size_mb:.1f} MB")
                    
                    # Optional: Verify output quality
                    if self.verify_output_quality(output_path):
                        return CompileResult(
                            success=True,
                            output_path=output_path,
                            error_message="",
                            stderr=result.stderr,
                            file_size_mb=file_size_mb
                        )
                    else:
                        return CompileResult(
                            success=False,
                            output_path=None,
                            error_message="Output quality verification failed",
                            stderr=result.stderr,
                            file_size_mb=0.0
                        )
                else:
                    return CompileResult(
                        success=False,
                        output_path=None,
                        error_message="Output file was not created",
                        stderr=result.stderr,
                        file_size_mb=0.0
                    )
            else:
                return CompileResult(
                    success=False,
                    output_path=None,
                    error_message=result.error_message,
                    stderr=result.stderr,
                    file_size_mb=0.0
                )
                
        except Exception as e:
            logger.error(f"Compilation failed with exception: {e}")
            return CompileResult(
                success=False,
                output_path=None,
                error_message=f"Exception during compilation: {str(e)}",
                stderr="",
                file_size_mb=0.0
            )
            
    def execute_ffmpeg_command(self, command: List[str]) -> CompileResult:
        """
        Execute an FFmpeg command and capture output
        
        Args:
            command: List of command arguments
            
        Returns:
            CompileResult with execution details
        """
        logger.info(f"Executing FFmpeg command: {' '.join(command)}")
        
        try:
            # Run FFmpeg command
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False
            )
            
            if process.returncode == 0:
                logger.info("FFmpeg command executed successfully")
                return CompileResult(
                    success=True,
                    output_path=None,  # Will be set by caller
                    error_message="",
                    stderr=process.stderr,
                    file_size_mb=0.0
                )
            else:
                error_msg = self.handle_compilation_errors(process.stderr)
                logger.error(f"FFmpeg command failed: {error_msg}")
                return CompileResult(
                    success=False,
                    output_path=None,
                    error_message=error_msg,
                    stderr=process.stderr,
                    file_size_mb=0.0
                )
                
        except subprocess.SubprocessError as e:
            error_msg = f"Subprocess error: {str(e)}"
            logger.error(error_msg)
            return CompileResult(
                success=False,
                output_path=None,
                error_message=error_msg,
                stderr="",
                file_size_mb=0.0
            )
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return CompileResult(
                success=False,
                output_path=None,
                error_message=error_msg,
                stderr="",
                file_size_mb=0.0
            )
            
    def _build_ffmpeg_command(self, concat_file: Path, output_path: Path) -> List[str]:
        """
        Build the FFmpeg command for final compilation
        
        Args:
            concat_file: Path to concat list file
            output_path: Output video path
            
        Returns:
            List of command arguments
        """
        command = [
            self.ffmpeg_executable,
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),            "-c:v", VIDEO_CONFIG["codec"],
            "-preset", VIDEO_CONFIG["preset"], 
            "-crf", str(VIDEO_CONFIG["crf"]),
            "-r", "30000/1001",  # Match source video frame rate (29.97fps)
            "-pix_fmt", VIDEO_CONFIG["pixel_format"],
            "-c:a", AUDIO_CONFIG["codec"],
            "-b:a", AUDIO_CONFIG["bitrate"],
            "-ar", str(AUDIO_CONFIG["sample_rate"]),
            "-ac", str(AUDIO_CONFIG["channels"]),
            "-loglevel", FFMPEG_CONFIG["log_level"]
        ]
        
        # Add overwrite option if configured
        if FFMPEG_CONFIG.get("overwrite_output", True):
            command.append("-y")
            
        # Add output path
        command.append(str(output_path))
        
        return command
        
    def handle_compilation_errors(self, stderr: str) -> str:
        """
        Parse FFmpeg stderr output for meaningful error messages
        
        Args:
            stderr: FFmpeg stderr output
            
        Returns:
            Processed error message
        """
        if not stderr:
            return "Unknown FFmpeg error (no stderr output)"
            
        # Common FFmpeg error patterns
        error_patterns = {
            "No such file or directory": "Input file not found",
            "Invalid data found": "Corrupted or invalid input file",
            "Permission denied": "Insufficient permissions to write output file",
            "No space left on device": "Insufficient disk space",
            "codec not currently supported": "Unsupported codec or format",
            "Unable to find a suitable output format": "Invalid output format"
        }
        
        stderr_lower = stderr.lower()
        for pattern, message in error_patterns.items():
            if pattern.lower() in stderr_lower:
                return f"{message}: {pattern}"
                
        # If no specific pattern matches, return the last few lines of stderr
        stderr_lines = stderr.strip().split('\n')
        if len(stderr_lines) > 3:
            return "FFmpeg error: " + " | ".join(stderr_lines[-3:])
        else:
            return f"FFmpeg error: {stderr.strip()}"
            
    def verify_output_quality(self, output_path: Path) -> bool:
        """
        Verify the output video meets quality standards
        
        Args:
            output_path: Path to the compiled video
            
        Returns:
            True if quality verification passes
        """
        if not output_path.exists():
            logger.error("Output file does not exist for quality verification")
            return False
            
        try:
            # Use ffprobe to check video properties
            probe_command = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                str(output_path)
            ]
            
            process = subprocess.run(
                probe_command,
                capture_output=True,
                text=True,
                check=True
            )
            
            import json
            probe_data = json.loads(process.stdout)
            
            # Check for video and audio streams
            video_streams = [s for s in probe_data.get('streams', []) if s.get('codec_type') == 'video']
            audio_streams = [s for s in probe_data.get('streams', []) if s.get('codec_type') == 'audio']
            
            if not video_streams:
                logger.error("No video stream found in output")
                return False
                
            if not audio_streams:
                logger.error("No audio stream found in output")
                return False
                
            # Check video resolution
            video_stream = video_streams[0]
            width = int(video_stream.get('width', 0))
            height = int(video_stream.get('height', 0))
            
            expected_width, expected_height = map(int, VIDEO_CONFIG["resolution"].split('x'))
            
            if width != expected_width or height != expected_height:
                logger.warning(f"Resolution mismatch: expected {expected_width}x{expected_height}, got {width}x{height}")
                # Don't fail for resolution mismatch, just warn
                
            # Check duration (should be > 0)
            duration = float(probe_data.get('format', {}).get('duration', 0))
            if duration <= 0:
                logger.error("Output video has zero or invalid duration")
                return False
                
            logger.info(f"Quality verification passed: {width}x{height}, {duration:.1f}s duration")
            return True
            
        except subprocess.SubprocessError as e:
            logger.error(f"Failed to run ffprobe for quality verification: {e}")
            return False
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse ffprobe output: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during quality verification: {e}")
            return False
            
    def create_preview_video(self, concat_file: Path, output_path: Path, duration: int = 30) -> CompileResult:
        """
        Create a preview version of the video (first N seconds)
        
        Args:
            concat_file: Path to concat list file
            output_path: Output path for preview
            duration: Preview duration in seconds
            
        Returns:
            CompileResult with preview creation status
        """
        logger.info(f"Creating {duration}s preview video...")
        
        command = [
            self.ffmpeg_executable,
            "-f", "concat",
            "-safe", "0", 
            "-i", str(concat_file),
            "-t", str(duration),
            "-c:v", VIDEO_CONFIG["codec"],
            "-preset", "fast",  # Faster preset for preview
            "-crf", "23",  # Lower quality for preview
            "-c:a", AUDIO_CONFIG["codec"],
            "-loglevel", FFMPEG_CONFIG["log_level"],
            "-y",
            str(output_path)
        ]
        
        return self.execute_ffmpeg_command(command)
    
    def test_ffmpeg_availability(self) -> bool:
        """
        Test if FFmpeg is available and has required codecs
        
        Returns:
            True if FFmpeg is available and functional
        """
        try:
            # Test FFmpeg availability
            command = [self.ffmpeg_executable, "-version"]
            process = subprocess.run(command, capture_output=True, text=True, check=True)
            
            if "ffmpeg version" not in process.stdout.lower():
                logger.error("FFmpeg not properly installed")
                return False
                
            # Test required codecs
            command = [self.ffmpeg_executable, "-codecs"]
            process = subprocess.run(command, capture_output=True, text=True, check=True)
            codecs_output = process.stdout.lower()
            
            required_codecs = ["libx264", "aac"]
            for codec in required_codecs:
                if codec not in codecs_output:
                    logger.error(f"Required codec not available: {codec}")
                    return False
                    
            logger.info("FFmpeg availability test passed")
            return True
            
        except subprocess.SubprocessError as e:
            logger.error(f"FFmpeg availability test failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error testing FFmpeg: {e}")
            return False