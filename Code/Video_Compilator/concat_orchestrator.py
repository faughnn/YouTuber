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
    """Use the exact method from our successful test - direct concatenation with concat filter"""
    
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
    
    def concatenate_mixed_segments(self, segment_sequence: List[Path], output_path: Path) -> ConcatenationResult:
        """Use the exact method from our successful test
        
        Args:
            segment_sequence: List of video segments in sequence order (mix of audio-videos and original videos)
            output_path: Path for the final concatenated video
            
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
            
            self.logger.info(f"Concatenating {len(segment_sequence)} segments using direct concat filter")
            
            # Create output directory if it doesn't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Build input list and filter components (exactly like our successful test)
            all_inputs = []
            filter_parts = []
            
            # Add all files as inputs in sequence order
            for input_index, segment in enumerate(segment_sequence):
                all_inputs.extend(['-i', str(segment)])
                filter_parts.append(f'[{input_index}:v:0][{input_index}:a:0]')
                self.logger.debug(f"Input {input_index}: {segment.name}")
            
            # Build concat filter (exactly like our successful test)
            filter_complex = ''.join(filter_parts) + f'concat=n={len(segment_sequence)}:v=1:a=1[outv][outa]'
            
            # Build FFmpeg command using exact proven method
            command = [
                'ffmpeg', '-y',
                *all_inputs,
                '-filter_complex', filter_complex,
                '-map', '[outv]',
                '-map', '[outa]',
                str(output_path)
            ]
            
            self.logger.debug(f"Running concatenation command: {' '.join(command[:10])}... (truncated)")
            
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
            
            self.logger.info(f"Successfully concatenated {len(segment_sequence)} segments")
            self.logger.info(f"Output: {output_path.name} ({duration:.2f}s, {file_size/1024/1024:.1f}MB)" if duration and file_size else f"Output: {output_path.name}")
            
            return ConcatenationResult(
                success=True,
                output_path=output_path,
                duration=duration,
                file_size=file_size
            )
            
        except subprocess.CalledProcessError as e:
            error_msg = f"FFmpeg concatenation failed: {e.stderr}"
            self.logger.error(error_msg)
            return ConcatenationResult(success=False, error=error_msg)
        except Exception as e:
            error_msg = f"Concatenation failed: {str(e)}"
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
        
        return valid_segments > 0
    
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
            result = concatenator.concatenate_mixed_segments(segment_paths, output_path)
            
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
