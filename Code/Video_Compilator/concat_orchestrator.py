"""
Direct Concatenation Orchestrator

Uses the exact successful method - concatenate segments without modifying 
original video files. The concat filter handles format differences automatically.
"""

import subprocess
import logging
import json
from pathlib import Path
from typing import List, Optional, Union, NamedTuple
from dataclasses import dataclass


@dataclass
class ConcatenationResult:
    """Result of a concatenation operation"""
    success: bool
    output_path: Optional[Path] = None
    duration: Optional[float] = None
    file_size: Optional[int] = None
    error: Optional[str] = None


class DirectConcatenator:
    """
    Video concatenation with loudness normalization for consistent audio levels.
    
    This class handles concatenating video segments (TTS + video clips) while applying
    FFmpeg's loudnorm filter to ensure consistent audio loudness across all segments.
    
    Features:
    - Loudness normalization using EBU R128 standard (LUFS)
    - Individual segment audio normalization before concatenation
    - Preserves video quality (only audio is processed)
    - Prevents clipping with true peak limiting
    - Configurable settings for different content types
    
    Default settings (-16 LUFS, LRA=7, TP=-1) are optimized for YouTube/web content.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_video_duration(self, video_path: Path) -> float:
        """Get the duration of a video file using ffprobe"""
        try:
            command = [
                'ffprobe', '-v', 'quiet',
                '-show_entries', 'format=duration',
                '-of', 'csv=p=0',
                str(video_path)
            ]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return float(result.stdout.strip())
        except (subprocess.CalledProcessError, ValueError) as e:
            self.logger.error(f"Failed to get duration for {video_path}: {e}")
            raise
    
    def get_video_info(self, video_path: Path) -> dict:
        """Get comprehensive video information using ffprobe"""
        try:
            command = [                'ffprobe', '-v', 'quiet',
                '-show_format', '-show_streams',
                '-of', 'json',
                str(video_path)
            ]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)  # JSON parsing
        except Exception as e:
            self.logger.error(f"Failed to get video info for {video_path}: {e}")
            return {}
    
    def concatenate_segments(self, segment_sequence: List[Path], output_path: Path, 
                           target_lufs: float = -16.0, loudness_range: float = 7.0, 
                           true_peak: float = -1.0) -> ConcatenationResult:
        """Concatenate video segments with loudness normalization
        
        Args:
            segment_sequence: List of video segments in sequence order
            output_path: Path for the final concatenated video
            target_lufs: Target integrated loudness in LUFS (-16 good for YouTube/web)
            loudness_range: Target loudness range in LU (7 = moderate compression)
            true_peak: Maximum true peak in dBFS (-1 prevents clipping)
            
        Returns:
            ConcatenationResult with success status and metadata
        """
        try:
            # Validate all input segments exist
            for segment in segment_sequence:
                if not segment.exists():
                    error_msg = f"Input segment not found: {segment}"
                    self.logger.error(error_msg)
                    return ConcatenationResult(success=False, error=error_msg)
            
            self.logger.info(f"Concatenating {len(segment_sequence)} segments with loudnorm (target: {target_lufs} LUFS)")
            
            # Create output directory if it doesn't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Build input list
            all_inputs = []
            for input_index, segment in enumerate(segment_sequence):
                all_inputs.extend(['-i', str(segment)])
                self.logger.debug(f"Input {input_index}: {segment.name}")
            
            # Build filter complex with video scaling, audio normalization, and concatenation
            video_filters = []
            audio_filters = []
            concat_inputs = []
            
            for i in range(len(segment_sequence)):
                # Scale all videos to 1920x1080 to handle dimension mismatches
                video_filters.append(
                    f'[{i}:v:0]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black[v{i}]'
                )
                # Apply loudnorm to each segment's audio
                audio_filters.append(
                    f'[{i}:a:0]loudnorm=I={target_lufs}:LRA={loudness_range}:TP={true_peak}[a{i}]'
                )
                # Prepare for concat (scaled video + normalized audio)
                concat_inputs.append(f'[v{i}][a{i}]')
            
            # Complete filter complex: scaling + normalization + concatenation
            filter_complex = (
                ';'.join(video_filters) + ';' +   # Video scaling filters
                ';'.join(audio_filters) + ';' +   # Individual loudnorm filters
                ''.join(concat_inputs) +          # Concat inputs (scaled video + normalized audio)
                f'concat=n={len(segment_sequence)}:v=1:a=1[outv][outa]'  # Concatenation
            )
            
            # Build FFmpeg command
            command = [
                'ffmpeg', '-y',
                *all_inputs,
                '-filter_complex', filter_complex,
                '-map', '[outv]',
                '-map', '[outa]',
                str(output_path)
            ]
            
            self.logger.debug(f"Running loudnorm concatenation command: {' '.join(command[:10])}... (truncated)")
            self.logger.debug(f"Filter complex: {filter_complex[:100]}... (truncated)")
            
            # Execute FFmpeg command
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Validate output file was created
            if not output_path.exists():
                error_msg = f"Output file was not created: {output_path}"
                self.logger.error(error_msg)
                return ConcatenationResult(success=False, error=error_msg)
            
            # Get final video metadata
            try:
                duration = self.get_video_duration(output_path)
                file_size = output_path.stat().st_size
            except Exception as e:
                self.logger.warning(f"Could not get output metadata: {e}")
                duration = None
                file_size = None
            
            self.logger.info(f"Successfully concatenated {len(segment_sequence)} segments with loudnorm")
            self.logger.info(f"Output: {output_path.name} ({duration:.2f}s, {file_size/1024/1024:.1f}MB)" if duration and file_size else f"Output: {output_path.name}")
            
            return ConcatenationResult(
                success=True,
                output_path=output_path,
                duration=duration,
                file_size=file_size
            )
            
        except subprocess.CalledProcessError as e:
            error_msg = f"FFmpeg loudnorm concatenation failed: {e.stderr}"
            self.logger.error(error_msg)
            return ConcatenationResult(success=False, error=error_msg)
        except Exception as e:
            error_msg = f"Loudnorm concatenation failed: {str(e)}"
            self.logger.error(error_msg)
            return ConcatenationResult(success=False, error=error_msg)
    
    def validate_concatenation_inputs(self, segment_sequence: List[Path]) -> bool:
        """Validate that all segments are suitable for concatenation
        
        Note: This is optional validation - the concat filter can handle format differences
        """
        if not segment_sequence:
            self.logger.error("No segments provided for concatenation")
            return False
        
        valid_segments = 0
        for i, segment in enumerate(segment_sequence):
            if not segment.exists():
                self.logger.error(f"Segment {i+1} not found: {segment}")
                continue
            
            try:
                # Basic validation - can we get duration?
                duration = self.get_video_duration(segment)
                if duration > 0:
                    valid_segments += 1
                    self.logger.debug(f"Segment {i+1} valid: {segment.name} ({duration:.2f}s)")
                else:
                    self.logger.warning(f"Segment {i+1} has zero duration: {segment.name}")
            except Exception as e:
                self.logger.warning(f"Segment {i+1} validation failed: {segment.name} - {e}")
        
        success_rate = valid_segments / len(segment_sequence)
        if success_rate < 0.8:  # Allow some tolerance
            self.logger.warning(f"Low validation success rate: {valid_segments}/{len(segment_sequence)} segments valid")
        
        return success_rate >= 0.8
    
    def validate_episode_structure(self, segment_sequence: List[Path]) -> bool:
        """Validate episode follows expected structure patterns
        
        Args:
            segment_sequence: List of segment file paths in order
            
        Returns:
            True if structure is recognized and valid
        """
        if not segment_sequence:
            self.logger.warning("No segments provided for structure validation")
            return False
            
        # Check for new structure (v2)
        first_segment = segment_sequence[0].stem.lower()
        if "hook_clip" in first_segment:
            # Validate new structure: hook -> intro_plus_hook_analysis -> ...
            if len(segment_sequence) < 2:
                self.logger.warning("Hook structure detected but insufficient segments")
                return False
            second_segment = segment_sequence[1].stem.lower()
            is_valid = "intro_plus_hook_analysis" in second_segment
            if is_valid:
                self.logger.info("Valid v2 hook structure detected")
            else:
                self.logger.warning(f"Hook structure detected but second segment is not intro_plus_hook_analysis: {second_segment}")
            return is_valid
        else:
            # Validate old structure (v1): intro -> ...
            is_valid = "intro" in first_segment and "intro_plus_hook_analysis" not in first_segment
            if is_valid:
                self.logger.info("Valid v1 intro structure detected")
            else:
                self.logger.warning(f"Unknown episode structure, first segment: {first_segment}")
            return is_valid
    
    def create_concat_file_list(self, segment_sequence: List[Path], list_file_path: Path) -> bool:
        """Create a concat file list for alternative concatenation method (backup approach)
        
        This creates a text file with the format needed for FFmpeg's concat demuxer.
        Not used in the main approach but available as fallback.
        """
        try:
            with open(list_file_path, 'w') as f:
                for segment in segment_sequence:
                    # Use forward slashes for FFmpeg compatibility
                    segment_path = str(segment).replace('\\', '/')
                    f.write(f"file '{segment_path}'\n")
            
            self.logger.debug(f"Created concat file list: {list_file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create concat file list: {e}")
            return False
    
    def concatenate_with_file_list(self, list_file_path: Path, output_path: Path) -> ConcatenationResult:
        """Alternative concatenation method using file list (backup approach)
        
        This method uses FFmpeg's concat demuxer instead of the concat filter.
        Available as a fallback if the main method fails.
        """
        try:
            command = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(list_file_path),
                '-c', 'copy',
                str(output_path)
            ]
            
            self.logger.debug(f"Running file list concatenation: {' '.join(command)}")
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )
            
            if not output_path.exists():
                error_msg = f"Output file was not created: {output_path}"
                return ConcatenationResult(success=False, error=error_msg)
            
            # Get metadata
            try:
                duration = self.get_video_duration(output_path)
                file_size = output_path.stat().st_size
            except:
                duration = None
                file_size = None
            
            return ConcatenationResult(
                success=True,
                output_path=output_path,
                duration=duration,
                file_size=file_size
            )
            
        except subprocess.CalledProcessError as e:
            error_msg = f"File list concatenation failed: {e.stderr}"
            self.logger.error(error_msg)
            return ConcatenationResult(success=False, error=error_msg)
        except Exception as e:
            error_msg = f"File list concatenation failed: {str(e)}"
            self.logger.error(error_msg)
            return ConcatenationResult(success=False, error=error_msg)


def main():
    """Test the DirectConcatenator with sample video files"""
    import sys
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    concatenator = DirectConcatenator()
    
    if len(sys.argv) > 2:
        # Get input segments from command line
        segment_paths = [Path(arg) for arg in sys.argv[1:-1]]
        output_path = Path(sys.argv[-1])
        
        # Validate inputs
        if concatenator.validate_concatenation_inputs(segment_paths):
            result = concatenator.concatenate_segments(segment_paths, output_path)
            
            if result.success:
                print(f"✓ Concatenation successful: {result.output_path}")
                if result.duration:
                    print(f"  Duration: {result.duration:.2f}s")
                if result.file_size:
                    print(f"  Size: {result.file_size/1024/1024:.1f}MB")
            else:
                print(f"✗ Concatenation failed: {result.error}")
        else:
            print("✗ Input validation failed")
    else:
        print("Usage: python concat_orchestrator.py <segment1> <segment2> ... <output_file>")


if __name__ == "__main__":
    main()
