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
import os

from .audio_to_video import AudioToVideoConverter
from .concat_orchestrator import DirectConcatenator, ConcatenationResult


class EpisodeFileRegistry:
    """Centralized file discovery and resolution for episode directories
    
    Scans episode directory once and provides O(1) file lookups by name or section ID.
    Eliminates path duplication bugs by maintaining single source of truth for file locations.
    """
    
    def __init__(self, episode_path: Path):
        self.episode_path = Path(episode_path)
        self.logger = logging.getLogger(f"{__name__}.EpisodeFileRegistry")
        self.file_map = self._build_file_index()
        self.logger.info(f"Registry initialized with {len(self.file_map)} files")
    
    def _build_file_index(self) -> Dict[str, Path]:
        """Scan all relevant directories once and build filename -> absolute_path map"""
        file_map = {}
        
        # Define search directories in priority order
        search_dirs = [
            self.episode_path / 'Output' / 'Audio',
            self.episode_path / 'Output' / 'Video',
            self.episode_path / 'Audio',
            self.episode_path / 'Video'
        ]
        
        for search_dir in search_dirs:
            if search_dir.exists():
                self.logger.debug(f"Scanning directory: {search_dir}")
                for file_path in search_dir.rglob('*'):
                    if file_path.is_file():
                        filename = file_path.name
                        # Only add if not already found (priority order)
                        if filename not in file_map:
                            file_map[filename] = file_path
                            self.logger.debug(f"Registered: {filename} -> {file_path}")
        
        return file_map
    
    def resolve_file(self, identifier: str) -> Optional[Path]:
        """Convert any identifier to actual file path
        
        Args:
            identifier: Can be filename, section_id, or relative path
            
        Returns:
            Absolute path to file if found, None otherwise
        """
        # Handle different input formats
        identifier = str(identifier).replace('\\', '/').strip('/')
        
        # Case 1: Direct filename match
        if identifier in self.file_map:
            return self.file_map[identifier]
        
        # Case 2: Extract filename from path-like identifier
        if '/' in identifier:
            filename = Path(identifier).name
            if filename in self.file_map:
                return self.file_map[filename]
        
        # Case 3: Try as section_id with extensions (for audio files)
        if not Path(identifier).suffix:  # No extension, treat as section_id
            return self.find_audio_file(identifier)
        
        return None
    
    def find_audio_file(self, section_id: str) -> Optional[Path]:
        """Find audio file with extension priority: .wav > .m4a > .mp3 > .aac"""
        audio_extensions = ['.wav', '.m4a', '.mp3', '.aac']
        
        for ext in audio_extensions:
            filename = f"{section_id}{ext}"
            if filename in self.file_map:
                return self.file_map[filename]
        
        return None
    
    def find_video_file(self, section_id: str) -> Optional[Path]:
        """Find video file, typically .mp4"""
        video_extensions = ['.mp4', '.mov', '.avi', '.mkv']
        
        for ext in video_extensions:
            filename = f"{section_id}{ext}"
            if filename in self.file_map:
                return self.file_map[filename]
        
        return None
    
    def get_relative_path(self, file_path: Path) -> str:
        """Convert absolute path back to episode-relative path"""
        try:
            return os.path.relpath(file_path, self.episode_path).replace('\\', '/')
        except ValueError:
            # Path is not relative to episode_path
            return str(file_path)
    
    def list_files_by_pattern(self, pattern: str) -> List[Path]:
        """List all files matching a pattern (e.g., 'pre_clip_*', '*.wav')"""
        import fnmatch
        matching_files = []
        
        for filename, file_path in self.file_map.items():
            if fnmatch.fnmatch(filename, pattern):
                matching_files.append(file_path)
        
        return sorted(matching_files)
    
    def get_file_stats(self) -> Dict[str, int]:
        """Get statistics about discovered files"""
        stats = {'total': len(self.file_map)}
        
        # Count by extension
        for filename in self.file_map.keys():
            ext = Path(filename).suffix.lower()
            if ext:
                key = f"{ext[1:]}_files"  # Remove the dot
                stats[key] = stats.get(key, 0) + 1
        
        return stats


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
    segments_skipped: int = 0
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
        
        # File registry will be initialized per episode
        self.file_registry: Optional[EpisodeFileRegistry] = None
    
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
            
            # Initialize file registry if not already done
            if not self.file_registry:
                self.file_registry = EpisodeFileRegistry(episode_path)
            
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
                
                # Process segments using registry
                for i, segment_data in enumerate(segment_list):
                    if isinstance(segment_data, dict):
                        # Extract segment information
                        segment_id = segment_data.get('id', f'segment_{i+1:03d}')
                        segment_type = segment_data.get('type', 'unknown')
                        
                        # Try to find file path using registry
                        file_path = None
                        for path_key in ['file', 'path', 'filename', 'audio_file', 'video_file']:
                            if path_key in segment_data:
                                identifier = segment_data[path_key]
                                file_path = self.file_registry.resolve_file(identifier)
                                if file_path:
                                    break
                        
                        # If no file path found in segment data, try to resolve by segment_id
                        if not file_path:
                            if segment_type == 'audio' or segment_type == 'unknown':
                                file_path = self.file_registry.find_audio_file(segment_id)
                            elif segment_type == 'video':
                                file_path = self.file_registry.find_video_file(segment_id)
                        
                        if file_path:
                            # Determine segment type if unknown
                            if segment_type == 'unknown':
                                if file_path.suffix.lower() in ['.mp3', '.wav', '.aac', '.m4a']:
                                    segment_type = 'audio'
                                elif file_path.suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv']:
                                    segment_type = 'video'
                            
                            # Ensure metadata always contains section_type
                            metadata = segment_data.get('metadata', segment_data)
                            segments.append(SegmentInfo(
                                segment_id=segment_id,
                                segment_type=segment_type,
                                file_path=file_path,
                                order=i,
                                metadata=metadata
                            ))
                            self.logger.debug(f"Found file for {segment_id}: {file_path}")
                        else:
                            self.logger.warning(f"Could not find file for segment {segment_id}")
            
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
        self.logger.info(f"[UPDATED] Parsing {len(podcast_sections)} podcast sections with intro_plus_hook_analysis support")
        segment_list = []
        
        for section in podcast_sections:
            section_type = section.get('section_type')
            section_id = section.get('section_id')
            self.logger.debug(f"Processing section: {section_id} with type: {section_type}")
            if section_type in ['intro', 'intro_plus_hook_analysis', 'pre_clip', 'post_clip', 'outro']:
                # Audio segment - use section_id to let registry find the file
                self.logger.debug(f"Adding audio segment: {section_id}")
                segment_list.append({
                    'id': section_id,
                    'type': 'audio',
                    'metadata': section
                })
            elif section_type in ['video_clip', 'hook_clip']:
                # Video segment - use section_id to let registry find the file
                self.logger.debug(f"Adding video segment: {section_id}")
                segment_list.append({
                    'id': section_id,
                    'type': 'video', 
                    'metadata': section
                })
            else:
                self.logger.warning(f"Unknown section_type '{section_type}' for section '{section_id}' - skipping")
        
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
            audio_files = []
            # Priority: .wav, .m4a, then others
            for ext in ['*.wav', '*.m4a', '*.mp3', '*.aac']:
                audio_files.extend(audio_dir.glob(ext))
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
            
            # Extract section_type from metadata for random image selection
            section_type = None
            if segment.metadata and isinstance(segment.metadata, dict):
                section_type = segment.metadata.get('section_type')            # Fallback: infer section_type from filename if not present
            if not section_type and segment.file_path:
                fname = segment.file_path.name.lower()
                if 'post_clip' in fname:
                    section_type = 'post_clip'
                elif 'pre_clip' in fname:
                    section_type = 'pre_clip'
                elif 'intro_plus_hook_analysis' in fname:
                    section_type = 'intro_plus_hook_analysis'
                elif 'intro' in fname:
                    section_type = 'intro'
                elif 'outro' in fname:
                    section_type = 'outro'
            
            self.logger.info(f"Converting {segment.file_path.name} → {output_filename} (section_type: {section_type})")
            
            # Convert audio to video with segment type for random background image selection
            if self.audio_converter.convert_audio_segment(segment.file_path, output_path, section_type):
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
                # Use original video file (UNTOUCHED!) - but check if it exists
                if segment.file_path.exists():
                    sequence.append(segment.file_path)
                    self.logger.debug(f"Sequence {len(sequence)}: Original Video - {segment.file_path.name}")
                else:
                    self.logger.warning(f"Skipping missing video file: {segment.file_path}")
                    self.logger.warning(f"Video segment {segment.segment_id} was not successfully extracted during Stage 6")
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

            # Initialize file registry for this episode
            self.file_registry = EpisodeFileRegistry(episode_path)

            # Set working directory to episode_path for correct relative path resolution
            os.chdir(episode_path)

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
            
            # Save directly to episode root directory for easy access
            output_path = episode_path / output_filename
              # Create debugging file with clip order before concatenation
            self._create_clip_order_debug_file(episode_path, output_filename, segments, sequence, converted_audio_videos)
            
            self.logger.info(f"Starting concatenation of {len(sequence)} segments...")
            concat_result = self.concatenator.concatenate_segments(sequence, output_path)
            
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
                    audio_segments_converted=len(converted_audio_videos)                )
            
        except Exception as e:
            error_msg = f"Compilation failed: {str(e)}"
            self.logger.error(error_msg)
            return CompilationResult(success=False, error=error_msg)

    def _create_clip_order_debug_file(self, final_dir: Path, output_filename: str, segments: List[SegmentInfo], 
                                     sequence: List[Path], converted_audio_videos: Dict[str, Path]) -> None:
        """Create a text file documenting the order of clips in the final video for debugging purposes.
        
        Args:
            final_dir: Directory where the final video will be saved
            output_filename: Name of the output video file
            segments: Original segment information
            sequence: Final sequence of video files to be concatenated
            converted_audio_videos: Mapping of audio segment IDs to converted video paths
        """
        import datetime
        
        # Create debug filename based on output video name
        debug_filename = output_filename.replace('.mp4', '_clip_order.txt')
        debug_path = final_dir / debug_filename
        
        try:
            with open(debug_path, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("FINAL VIDEO CLIP ORDER DEBUG FILE\n")
                f.write("=" * 80 + "\n")
                f.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Video File: {output_filename}\n")
                f.write(f"Total Segments: {len(sequence)}\n")
                f.write(f"Audio Segments Converted: {len(converted_audio_videos)}\n")
                f.write(f"Video Segments: {len([s for s in segments if s.segment_type == 'video'])}\n")
                f.write("\n")
                
                f.write("SEGMENT ORDER IN FINAL VIDEO:\n")
                f.write("-" * 50 + "\n")
                
                for i, video_path in enumerate(sequence, 1):
                    # Find the corresponding segment info
                    segment_info = None
                    segment_type = None
                    segment_id = None
                    original_file = None
                    
                    # Check if this is a converted audio file
                    for seg_id, converted_path in converted_audio_videos.items():
                        if converted_path == video_path:
                            segment_type = "AUDIO→VIDEO"
                            segment_id = seg_id
                            # Find original audio file
                            for seg in segments:
                                if seg.segment_id == seg_id:
                                    original_file = seg.file_path.name
                                    segment_info = seg
                                    break
                            break
                    
                    # If not converted audio, check if it's an original video
                    if segment_type is None:
                        for seg in segments:
                            if seg.file_path == video_path:
                                segment_type = "ORIGINAL VIDEO"
                                segment_id = seg.segment_id
                                original_file = seg.file_path.name
                                segment_info = seg
                                break
                    
                    # If still not found, it's an unknown file
                    if segment_type is None:
                        segment_type = "UNKNOWN"
                        segment_id = "unknown"
                        original_file = video_path.name
                    
                    f.write(f"{i:2d}. [{segment_type:15}] {segment_id}\n")
                    f.write(f"    Original: {original_file}\n")
                    f.write(f"    Final:    {video_path.name}\n")
                    
                    # Add metadata if available
                    if segment_info and segment_info.metadata:
                        metadata = segment_info.metadata
                        if 'start_time' in metadata or 'duration' in metadata:
                            f.write(f"    Timing:   ")
                            if 'start_time' in metadata:
                                f.write(f"Start: {metadata['start_time']}")
                            if 'duration' in metadata:
                                f.write(f", Duration: {metadata['duration']}")
                            f.write("\n")
                    f.write("\n")
                
                f.write("-" * 50 + "\n")
                f.write("FILE PATHS:\n")
                f.write("-" * 50 + "\n")
                
                for i, video_path in enumerate(sequence, 1):
                    f.write(f"{i:2d}. {video_path}\n")
                
                f.write("\n")
                f.write("=" * 80 + "\n")
                f.write("END OF DEBUG FILE\n")
                f.write("=" * 80 + "\n")
            
            self.logger.info(f"Created clip order debug file: {debug_filename}")
            
        except Exception as e:
            self.logger.warning(f"Failed to create debug file: {e}")


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
