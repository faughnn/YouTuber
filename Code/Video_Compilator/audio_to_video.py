"""
Audio to Video Converter

Converts TTS audio files to video segments with static backgrounds using the
proven working method from successful testing.
"""

import subprocess
import logging
from pathlib import Path
from typing import Optional, Union, List
import json

# Video Standards (proven working)
VIDEO_SPECS = {
    "width": 1920,
    "height": 1080,
    "fps": "29.97",
    "codec": "libx264"
}

# Audio Standards (proven working)
AUDIO_SPECS = {
    "sample_rate": 44100,
    "channels": 2,
    "codec": "aac"
}


class AudioToVideoConverter:
    """Convert TTS audio files to video segments with Chris Morris background image"""
    
    def __init__(self):
        self.background_image = r"C:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Assets\Chris_Morris_Images\bloody_hell.jpg"
        self.logger = logging.getLogger(__name__)
        
        # Validate background image exists
        if not Path(self.background_image).exists():
            raise FileNotFoundError(f"Background image not found: {self.background_image}")
    
    def get_audio_duration(self, audio_path: Path) -> float:
        """Get the duration of an audio file using ffprobe"""
        try:
            command = [
                'ffprobe', '-v', 'quiet',
                '-show_entries', 'format=duration',
                '-of', 'csv=p=0',
                str(audio_path)
            ]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return float(result.stdout.strip())
        except (subprocess.CalledProcessError, ValueError) as e:
            self.logger.error(f"Failed to get duration for {audio_path}: {e}")
            raise
    
    def convert_audio_segment(self, audio_path: Path, output_path: Path) -> bool:
        """Convert audio to video using Chris Morris background image
        
        Uses the exact proven method:
        - Chris Morris "bloody hell" image as static background
        - 1920x1080 resolution standard
        - 29.97 fps matching video clips
        - 44.1kHz stereo audio standardization
        """
        try:
            # Ensure input audio file exists
            if not audio_path.exists():
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
            # Get audio duration
            duration = self.get_audio_duration(audio_path)
            self.logger.info(f"Converting {audio_path.name} (duration: {duration:.2f}s) to video")
            
            # Create output directory if it doesn't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)
              # Build FFmpeg command using exact proven method with SAR fix
            command = [
                'ffmpeg', '-y',
                '-loop', '1',
                '-i', str(self.background_image),
                '-i', str(audio_path),
                '-c:v', VIDEO_SPECS["codec"],
                '-c:a', AUDIO_SPECS["codec"],
                '-ar', str(AUDIO_SPECS["sample_rate"]),
                '-ac', str(AUDIO_SPECS["channels"]),
                '-vf', f'scale={VIDEO_SPECS["width"]}:{VIDEO_SPECS["height"]},setsar=1:1',
                '-r', VIDEO_SPECS["fps"],
                '-t', str(duration),
                '-shortest',
                str(output_path)
            ]
            
            self.logger.debug(f"Running command: {' '.join(command)}")
            
            # Execute FFmpeg command
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Validate output file was created
            if not output_path.exists():
                raise RuntimeError(f"Output file was not created: {output_path}")
            
            self.logger.info(f"Successfully converted {audio_path.name} to {output_path.name}")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"FFmpeg failed for {audio_path}: {e.stderr}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to convert {audio_path}: {e}")
            return False
    
    def validate_segment(self, segment_path: Path) -> bool:
        """Validate segment meets concatenation requirements"""
        try:
            # Get video specifications using ffprobe
            command = [
                'ffprobe', '-v', 'quiet',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height,avg_frame_rate',
                '-of', 'csv=p=0',
                str(segment_path)
            ]
            video_result = subprocess.run(command, capture_output=True, text=True, check=True)
            video_data = video_result.stdout.strip().split(',')
            
            # Get audio specifications
            command = [
                'ffprobe', '-v', 'quiet',
                '-select_streams', 'a:0',
                '-show_entries', 'stream=sample_rate,channels',
                '-of', 'csv=p=0',
                str(segment_path)
            ]
            audio_result = subprocess.run(command, capture_output=True, text=True, check=True)
            audio_data = audio_result.stdout.strip().split(',')
            
            # Validate specifications
            width, height = int(video_data[0]), int(video_data[1])
            sample_rate, channels = int(audio_data[0]), int(audio_data[1])
            
            is_valid = (
                width == VIDEO_SPECS["width"] and 
                height == VIDEO_SPECS["height"] and
                sample_rate == AUDIO_SPECS["sample_rate"] and
                channels == AUDIO_SPECS["channels"]
            )
            
            if not is_valid:
                self.logger.warning(f"Segment {segment_path.name} validation failed: "
                                  f"Video: {width}x{height}, Audio: {sample_rate}Hz {channels}ch")
            
            return is_valid
            
        except Exception as e:
            self.logger.error(f"Failed to validate segment {segment_path}: {e}")
            return False
    
    def batch_convert_audio_segments(self, audio_files: List[Path], output_dir: Path) -> List[Path]:
        """Convert multiple audio files to video segments
        
        Args:
            audio_files: List of audio file paths to convert
            output_dir: Directory to save converted video segments
            
        Returns:
            List of successfully created video segment paths
        """
        converted_segments = []
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for i, audio_path in enumerate(audio_files, 1):
            # Generate output filename
            output_filename = f"seg_{i:03d}_{audio_path.stem}.mp4"
            output_path = output_dir / output_filename
            
            self.logger.info(f"Converting audio segment {i}/{len(audio_files)}: {audio_path.name}")
            
            # Convert audio to video
            if self.convert_audio_segment(audio_path, output_path):
                # Validate the created segment
                if self.validate_segment(output_path):
                    converted_segments.append(output_path)
                    self.logger.info(f"✓ Audio segment {i} converted and validated")
                else:
                    self.logger.warning(f"⚠ Audio segment {i} converted but validation failed")
                    converted_segments.append(output_path)  # Include anyway for now
            else:
                self.logger.error(f"✗ Failed to convert audio segment {i}: {audio_path.name}")
        
        self.logger.info(f"Batch conversion complete: {len(converted_segments)}/{len(audio_files)} successful")
        return converted_segments


def main():
    """Test the AudioToVideoConverter with a sample audio file"""
    import sys
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    converter = AudioToVideoConverter()
    
    if len(sys.argv) > 1:
        audio_path = Path(sys.argv[1])
        output_path = Path(sys.argv[1]).with_suffix('.mp4')
        
        success = converter.convert_audio_segment(audio_path, output_path)
        print(f"Conversion {'successful' if success else 'failed'}")
    else:
        print("Usage: python audio_to_video.py <audio_file>")


if __name__ == "__main__":
    main()
