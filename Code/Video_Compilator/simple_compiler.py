"""
Simple Compiler - Main Orchestration

Executes the exact workflow from successful testing:
1. Parse script and identify segments
2. Convert ONLY audio segments to video (leave video files alone!)
3. Build sequence with converted audio-videos + original videos
4. Direct concatenation (no normalization!)
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, NamedTuple
from dataclasses import dataclass

from .audio_to_video import AudioToVideoConverter
from .concat_orchestrator import DirectConcatenator, ConcatenationResult


@dataclass
class SegmentInfo:
    """Information about a segment in the episode script"""
    segment_id: str
    segment_type: str  # 'audio' or 'video'
    file_path: Path
    order: int
    metadata: Dict[str, Any] = None


@dataclass
class CompilationResult:
    """Result of a complete episode compilation"""
    success: bool
    output_path: Optional[Path] = None
    duration: Optional[float] = None
    file_size: Optional[int] = None
    segments_processed: int = 0
    audio_segments_converted: int = 0
    error: Optional[str] = None


class SimpleCompiler:
    """Main orchestration using the EXACT proven workflow"""
    
    def __init__(self, keep_temp_files: bool = True, validate_segments: bool = True):
        self.keep_temp_files = keep_temp_files
        self.validate_segments = validate_segments
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.audio_converter = AudioToVideoConverter()
        self.concatenator = DirectConcatenator()
    
    def parse_script(self, script_path: Path) -> List[SegmentInfo]:
        """Parse unified podcast script and identify segments
        
        Args:
            script_path: Path to unified_podcast_script.json
            
        Returns:
            List of SegmentInfo objects in sequence order
        """
        try:
            if not script_path.exists():
                raise FileNotFoundError(f"Script file not found: {script_path}")
            
            with open(script_path, 'r', encoding='utf-8') as f:
                script_data = json.load(f)
            
            segments = []
            episode_path = script_path.parent.parent  # Go up from Scripts/ to episode directory
              # Parse segments based on the script structure
            if isinstance(script_data, dict):
                # Handle unified podcast script structure
                if 'podcast_sections' in script_data:
                    # This is a unified podcast script with podcast_sections
                    podcast_sections = script_data['podcast_sections']
                    segment_list = self._parse_podcast_sections(podcast_sections, episode_path)
                elif 'segments' in script_data:
                    # Direct segments array (legacy format)
                    segment_list = script_data['segments']
                elif 'episode' in script_data and 'segments' in script_data['episode']:
                    # Nested structure (legacy format)
                    segment_list = script_data['episode']['segments']
                else:
                    # Try to find any list of segments
                    segment_list = []
                    for key, value in script_data.items():
                        if isinstance(value, list) and len(value) > 0:
                            # Check if this looks like a segment list
                            first_item = value[0]
                            if isinstance(first_item, dict) and ('type' in first_item or 'file' in first_item or 'path' in first_item):
                                segment_list = value
                                break
                
                # Process segments
                for i, segment_data in enumerate(segment_list):
                    if isinstance(segment_data, dict):
                        # Extract segment information
                        segment_id = segment_data.get('id', f'segment_{i+1:03d}')
                        segment_type = segment_data.get('type', 'unknown')
                        
                        # Try to find file path
                        file_path = None
                        for path_key in ['file', 'path', 'filename', 'audio_file', 'video_file']:
                            if path_key in segment_data:
                                file_path = segment_data[path_key]
                                break
                        
                        if file_path:
                            # Convert to absolute path
                            if not Path(file_path).is_absolute():
                                # Try different possible locations
                                possible_paths = [
                                    episode_path / 'Audio' / file_path,
                                    episode_path / 'Video' / file_path,
                                    episode_path / 'Output' / 'Audio' / file_path,
                                    episode_path / 'Output' / 'Video' / file_path,
                                    episode_path / file_path
                                ]
                                
                                actual_path = None
                                for possible_path in possible_paths:
                                    if possible_path.exists():
                                        actual_path = possible_path
                                        break
                                
                                if actual_path:
                                    file_path = actual_path
                                else:
                                    self.logger.warning(f"Could not find file for segment {segment_id}: {file_path}")
                                    continue
                            else:
                                file_path = Path(file_path)
                            
                            # Determine segment type from file extension if not specified
                            if segment_type == 'unknown':
                                if file_path.suffix.lower() in ['.mp3', '.wav', '.aac', '.m4a']:
                                    segment_type = 'audio'
                                elif file_path.suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv']:
                                    segment_type = 'video'
                            
                            segments.append(SegmentInfo(
                                segment_id=segment_id,
                                segment_type=segment_type,
                                file_path=file_path,
                                order=i,
                                metadata=segment_data
                            ))
            
            self.logger.info(f"Parsed {len(segments)} segments from script")
            for segment in segments:
                self.logger.debug(f"  {segment.order}: {segment.segment_type} - {segment.file_path.name}")
            
            return segments
            
        except Exception as e:
            self.logger.error(f"Failed to parse script {script_path}: {e}")
            raise
    
    def _parse_podcast_sections(self, podcast_sections: List[Dict], episode_path: Path) -> List[Dict]:
        """Parse podcast_sections from unified podcast script to build ordered segment list
        
        Args:
            podcast_sections: List of sections from unified_podcast_script.json
            episode_path: Path to episode directory
            
        Returns:
            List of segment dictionaries in the correct order
        """
        segment_list = []
        
        for section in podcast_sections:
            section_type = section.get('section_type')
            section_id = section.get('section_id')
            if section_type in ['intro', 'pre_clip', 'post_clip', 'outro']:
                # Audio segment - map to corresponding audio file
                audio_filename = f"{section_id}.wav"
                segment_list.append({
                    'id': section_id,
                    'type': 'audio',
                    'file': audio_filename,
                    'metadata': section
                })
                
            elif section_type == 'video_clip':
                # Video segment - map to corresponding video file using section_id (e.g., video_clip_001.mp4)
                video_filename = f"{section_id}.mp4"
                segment_list.append({
                    'id': section_id,
                    'type': 'video', 
                    'file': video_filename,
                    'metadata': section
                })
        
        self.logger.info(f"Parsed {len(segment_list)} segments from podcast_sections in correct order")
        return segment_list
    
    def discover_episode_files(self, episode_path: Path) -> List[SegmentInfo]:
        """Fallback method to discover audio/video files when script parsing fails
        
        This method scans the episode directory for audio and video files
        and creates a basic segment sequence.
        """
        segments = []
        
        # Look for audio files
        audio_dir = episode_path / 'Output' / 'Audio'
        if not audio_dir.exists():
            audio_dir = episode_path / 'Audio'
        
        if audio_dir.exists():
            audio_files = list(audio_dir.glob('*.wav')) + list(audio_dir.glob('*.mp3'))
            audio_files.sort()  # Sort alphabetically
            
            for i, audio_file in enumerate(audio_files):
                segments.append(SegmentInfo(
                    segment_id=f'audio_{i+1:03d}',
                    segment_type='audio',
                    file_path=audio_file,
                    order=len(segments)
                ))
        
        # Look for video files
        video_dir = episode_path / 'Output' / 'Video'
        if not video_dir.exists():
            video_dir = episode_path / 'Video'
        
        if video_dir.exists():
            video_files = list(video_dir.glob('*.mp4')) + list(video_dir.glob('*.mov'))
            video_files.sort()  # Sort alphabetically
            
            for i, video_file in enumerate(video_files):
                segments.append(SegmentInfo(
                    segment_id=f'video_{i+1:03d}',
                    segment_type='video',
                    file_path=video_file,
                    order=len(segments)
                ))
        
        # Sort by order
        segments.sort(key=lambda x: x.order)
        
        self.logger.info(f"Discovered {len(segments)} files in episode directory")
        return segments
    
    def convert_audio_to_video(self, audio_segments: List[SegmentInfo], temp_dir: Path) -> List[Path]:
        """Convert ONLY audio segments to video (leave video files alone!)
        
        Args:
            audio_segments: List of audio SegmentInfo objects
            temp_dir: Directory to store converted video segments
            
        Returns:
            List of paths to converted video segments
        """
        temp_dir.mkdir(parents=True, exist_ok=True)
        converted_videos = []
        
        self.logger.info(f"Converting {len(audio_segments)} audio segments to video...")
        
        for segment in audio_segments:
            if segment.segment_type != 'audio':
                continue
            
            # Generate output filename
            output_filename = f"seg_{segment.order+1:03d}_{segment.segment_id}.mp4"
            output_path = temp_dir / output_filename
            
            self.logger.info(f"Converting {segment.file_path.name} → {output_filename}")
            
            # Convert audio to video
            if self.audio_converter.convert_audio_segment(segment.file_path, output_path):
                converted_videos.append(output_path)
                self.logger.info(f"✓ Converted: {segment.file_path.name}")
            else:
                self.logger.error(f"✗ Failed to convert: {segment.file_path.name}")
                raise RuntimeError(f"Audio conversion failed for {segment.file_path}")
        
        self.logger.info(f"Audio conversion complete: {len(converted_videos)} segments converted")
        return converted_videos
    
    def build_sequence(self, segments: List[SegmentInfo], converted_audio_videos: Dict[str, Path]) -> List[Path]:
        """Build sequence with converted audio-videos + original videos
        
        Args:
            segments: All segments in order
            converted_audio_videos: Mapping of segment_id to converted video path
            
        Returns:
            List of video file paths in sequence order
        """
        sequence = []
        
        for segment in sorted(segments, key=lambda x: x.order):
            if segment.segment_type == 'audio':
                # Use converted audio-to-video file
                if segment.segment_id in converted_audio_videos:
                    sequence.append(converted_audio_videos[segment.segment_id])
                    self.logger.debug(f"Sequence {len(sequence)}: Audio→Video - {converted_audio_videos[segment.segment_id].name}")
                else:
                    self.logger.error(f"Missing converted video for audio segment: {segment.segment_id}")
                    raise RuntimeError(f"Missing converted video for segment: {segment.segment_id}")
            elif segment.segment_type == 'video':
                # Use original video file (UNTOUCHED!)
                sequence.append(segment.file_path)
                self.logger.debug(f"Sequence {len(sequence)}: Original Video - {segment.file_path.name}")
            else:
                self.logger.warning(f"Unknown segment type '{segment.segment_type}' for segment {segment.segment_id}")
        
        self.logger.info(f"Built sequence with {len(sequence)} segments")
        return sequence
    
    def compile_episode(self, episode_path: Path, output_filename: Optional[str] = None) -> CompilationResult:
        """Execute the exact workflow from our successful test
        Args:
            episode_path: Path to episode directory
            output_filename: Optional custom output filename
            
        Returns:
            CompilationResult with success status and metadata
        """
        try:
            episode_path = Path(episode_path)
            if not episode_path.exists():
                raise FileNotFoundError(f"Episode directory not found: {episode_path}")
            
            self.logger.info(f"Starting compilation for episode: {episode_path.name}")
            
            # Step 1: Parse script and identify segments
            script_path = episode_path / "Output" / "Scripts" / "unified_podcast_script.json"
            
            try:
                segments = self.parse_script(script_path)
            except Exception as e:
                self.logger.warning(f"Script parsing failed, falling back to file discovery: {e}")
                segments = self.discover_episode_files(episode_path)
            
            if not segments:
                raise RuntimeError("No segments found in episode")
            
            # Separate audio and video segments
            audio_segments = [s for s in segments if s.segment_type == 'audio']
            video_segments = [s for s in segments if s.segment_type == 'video']
            
            self.logger.info(f"Found {len(audio_segments)} audio segments and {len(video_segments)} video segments")
              # Step 2: Convert ONLY audio segments to video (leave video files alone!)
            temp_dir = episode_path / "Output" / "Video" / "temp"
            converted_audio_videos = {}
            
            if audio_segments:
                converted_paths = self.convert_audio_to_video(audio_segments, temp_dir)
                
                # Map segment IDs to converted video paths
                for segment, converted_path in zip(audio_segments, converted_paths):
                    converted_audio_videos[segment.segment_id] = converted_path
            
            # Step 3: Build sequence with converted audio-videos + original videos
            sequence = self.build_sequence(segments, converted_audio_videos)
            
            if not sequence:
                raise RuntimeError("No segments in final sequence")
              # Step 4: Direct concatenation (no normalization!)
            if not output_filename:
                output_filename = f"{episode_path.name}_compiled.mp4"
            
            # Ensure Final directory exists
            final_dir = episode_path / "Output" / "Video" / "Final"
            final_dir.mkdir(parents=True, exist_ok=True)
            output_path = final_dir / output_filename
            
            self.logger.info(f"Starting concatenation of {len(sequence)} segments...")
            concat_result = self.concatenator.concatenate_mixed_segments(sequence, output_path)
            
            # Cleanup temp files if requested
            if not self.keep_temp_files and temp_dir.exists():
                import shutil
                shutil.rmtree(temp_dir)
                self.logger.info("Cleaned up temporary files")
            
            if concat_result.success:
                self.logger.info(f"✓ Compilation successful: {output_path.name}")
                return CompilationResult(
                    success=True,
                    output_path=concat_result.output_path,
                    duration=concat_result.duration,
                    file_size=concat_result.file_size,
                    segments_processed=len(sequence),
                    audio_segments_converted=len(converted_audio_videos)
                )
            else:
                return CompilationResult(
                    success=False,
                    error=concat_result.error,
                    segments_processed=len(sequence),
                    audio_segments_converted=len(converted_audio_videos)
                )
            
        except Exception as e:
            error_msg = f"Compilation failed: {str(e)}"
            self.logger.error(error_msg)
            return CompilationResult(success=False, error=error_msg)


def main():
    """Test the SimpleCompiler with an episode directory"""
    import sys
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    compiler = SimpleCompiler()
    
    if len(sys.argv) > 1:
        episode_path = Path(sys.argv[1])
        output_filename = sys.argv[2] if len(sys.argv) > 2 else None
        
        result = compiler.compile_episode(episode_path, output_filename)
        
        if result.success:
            print(f"✓ Compilation successful: {result.output_path}")
            print(f"  Segments processed: {result.segments_processed}")
            print(f"  Audio segments converted: {result.audio_segments_converted}")
            if result.duration:
                print(f"  Duration: {result.duration:.2f}s")
            if result.file_size:
                print(f"  Size: {result.file_size/1024/1024:.1f}MB")
        else:
            print(f"✗ Compilation failed: {result.error}")
    else:
        print("Usage: python simple_compiler.py <episode_directory> [output_filename]")


if __name__ == "__main__":
    main()
