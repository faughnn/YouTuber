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
import random

# Video Standards (proven working)
VIDEO_SPECS = {
    "width": 1920,
    "height": 1080,
    "fps": "29.97",
    "codec": "libx264",
    "random_backgrounds": True,  # New option
    "background_change_points": ["post_clip"]  # Configurable
}

# Audio Standards (proven working)
AUDIO_SPECS = {
    "sample_rate": 44100,
    "channels": 2,
    "codec": "aac"
}


class SimpleImageManager:
    """Manages background image selection for TTS segments"""
    
    def __init__(self, assets_directory):
        self.assets_directory = Path(assets_directory)
        self.bloody_hell_path = self.assets_directory / "bloody_hell.jpg"
        self.random_images = []
        self.current_image = str(self.bloody_hell_path)  # Start with bloody_hell
        self.load_random_images()
    
    def load_random_images(self):
        """Load all images except bloody_hell.jpg for random selection"""
        image_extensions = {'.jpg', '.jpeg', '.png'}
        self.random_images = [
            str(img_path) for img_path in self.assets_directory.iterdir()
            if img_path.suffix.lower() in image_extensions
            and img_path.name != "bloody_hell.jpg"  # Exclude the intro image
        ]
        print(f"[DEBUG] Random images loaded (excluding bloody_hell.jpg): {self.random_images}")
        if not self.random_images:
            print(f"WARNING: No random images found in {self.assets_directory}")
            # Fallback to bloody_hell if no other images available            self.random_images = [str(self.bloody_hell_path)]
    
    def get_image_for_segment(self, segment_type):
        print(f"[DEBUG] get_image_for_segment called with segment_type: '{segment_type}'")
        if segment_type == "intro" or segment_type == "intro_plus_hook_analysis":
            # Both intro and intro_plus_hook_analysis ALWAYS use bloody_hell.jpg
            self.current_image = str(self.bloody_hell_path)
        elif segment_type == "post_clip":
            # Post-clip gets a NEW random image
            self.current_image = random.choice(self.random_images)
            print(f"[DEBUG] post_clip: selected image {self.current_image}")
        # For pre_clip, outro, and hook_clip: keep current_image (inherit from previous)
        # Note: hook_clip sections should be video, not audio, so this shouldn't be called for them
        
        return self.current_image


class AudioToVideoConverter:
    """Convert TTS audio files to video segments with random Chris Morris background images"""
    
    def __init__(self):
        # Initialize with Chris Morris Images folder
        assets_path = r"C:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Assets\Chris_Morris_Images"
        self.image_manager = SimpleImageManager(assets_path)
        self.logger = logging.getLogger(__name__)
    
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
    
    def convert_audio_segment(self, audio_path: Path, output_path: Path, segment_type: Optional[str] = None) -> bool:
        """Convert audio to video with appropriate background image"""
        try:
            if not audio_path.exists():
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            # Use new image selection logic
            background_image = self.image_manager.get_image_for_segment(segment_type)
            duration = self.get_audio_duration(audio_path)
            self.logger.info(f"Converting {audio_path.name} (duration: {duration:.2f}s) to video using {Path(background_image).name}")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            command = [
                'ffmpeg', '-y',
                '-loop', '1',
                '-i', str(background_image),
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
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )
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
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    converter = AudioToVideoConverter()
    if len(sys.argv) > 1:
        audio_path = Path(sys.argv[1])
        output_path = Path(sys.argv[1]).with_suffix('.mp4')
        segment_type = sys.argv[2] if len(sys.argv) > 2 else None
        success = converter.convert_audio_segment(audio_path, output_path, segment_type)
        print(f"Conversion {'successful' if success else 'failed'}")
    else:
        print("Usage: python audio_to_video.py <audio_file> [segment_type]")


if __name__ == "__main__":
    main()
