"""
Main Video Compilator

Entry point that orchestrates the complete video compilation process.
"""
import logging
from pathlib import Path
from typing import Dict, Optional, NamedTuple
import time

from .script_parser import ScriptParser
from .asset_validator import AssetValidator, ValidationResult
from .background_processor import BackgroundProcessor
from .timeline_builder import TimelineBuilder
from .ffmpeg_orchestrator import FFmpegOrchestrator, CompileResult
from .config import get_temp_dir_name, should_cleanup_temp_files

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CompilationResult(NamedTuple):
    """Complete result of video compilation process"""
    success: bool
    output_path: Optional[Path]
    error_message: str
    execution_time: float
    stats: Dict


class VideoCompilator:
    """Main Video Compilator class"""
    
    def __init__(self):
        self.script_parser = ScriptParser()
        self.asset_validator = AssetValidator()
        self.background_processor = BackgroundProcessor()
        self.timeline_builder = TimelineBuilder()
        self.ffmpeg_orchestrator = FFmpegOrchestrator()
        
    def compile_episode(self, episode_path: str) -> CompilationResult:
        """
        Compile a complete episode from unified script and assets
        
        Args:
            episode_path: Path to episode directory containing Output folder
            
        Returns:
            CompilationResult with compilation status and details
        """
        start_time = time.time()
        episode_path = Path(episode_path)
        episode_name = episode_path.name
        
        logger.info(f"=== Starting Video Compilation for {episode_name} ===")
        
        try:
            # Phase 1: Validate assets
            logger.info("[1/4] Validating assets...")
            validation_result = self._validate_assets(episode_path)
            if not validation_result.is_valid:
                return CompilationResult(
                    success=False,
                    output_path=None,
                    error_message=validation_result.error_message,
                    execution_time=time.time() - start_time,
                    stats={}
                )
            logger.info("✓ All assets validated")
            
            # Phase 2: Generate narration videos
            logger.info("[2/4] Generating narration videos...")
            narration_result = self._generate_narration_videos(episode_path)
            if not narration_result:
                return CompilationResult(
                    success=False,
                    output_path=None,
                    error_message="Failed to generate narration videos",
                    execution_time=time.time() - start_time,
                    stats={}
                )
            logger.info(f"✓ {narration_result['successful_count']} narration videos created")
            
            # Phase 3: Build timeline
            logger.info("[3/4] Building timeline...")
            timeline = self._build_timeline(episode_path)
            if not timeline:
                return CompilationResult(
                    success=False,
                    output_path=None,
                    error_message="Failed to build timeline",
                    execution_time=time.time() - start_time,
                    stats={}
                )
            
            estimated_duration = self.timeline_builder.calculate_total_duration(timeline)
            logger.info(f"✓ Timeline ready - {timeline.get_segment_count()} segments, ~{self.timeline_builder._format_duration(estimated_duration)}")
            
            # Phase 4: Final compilation
            logger.info("[4/4] Compiling final video...")
            compile_result = self._compile_final_video(episode_path, timeline, episode_name)
            
            total_time = time.time() - start_time
            
            if compile_result.success:
                logger.info(f"=== Compilation Complete ===")
                logger.info(f"✓ Output: {compile_result.output_path}")
                logger.info(f"✓ Size: {compile_result.file_size_mb:.1f} MB")
                logger.info(f"✓ Total time: {total_time:.1f}s")
                  # Generate final stats
                stats = self._generate_final_stats(timeline, compile_result, narration_result, total_time)
                
                return CompilationResult(
                    success=True,
                    output_path=compile_result.output_path,
                    error_message="",
                    execution_time=total_time,
                    stats=stats
                )
            else:
                logger.error(f"=== Compilation Failed ===")
                logger.error(f"✗ Error: {compile_result.error_message}")
                
                return CompilationResult(
                    success=False,
                    output_path=None,
                    error_message=compile_result.error_message,
                    execution_time=total_time,
                    stats={}
                )
                
        except Exception as e:
            total_time = time.time() - start_time
            error_msg = f"Unexpected error during compilation: {e}"
            logger.error(error_msg)
            
            return CompilationResult(
                success=False,
                output_path=None,
                error_message=error_msg,
                execution_time=total_time,
                stats={}
            )
            
    def _validate_assets(self, episode_path: Path):
        """Phase 1: Validate all required assets"""
        
        # Define paths
        script_path = episode_path / "Output" / "Scripts" / "unified_podcast_script.json"
        audio_dir = episode_path / "Output" / "Audio"
        video_dir = episode_path / "Output" / "Video"        # Parse script
        try:
            script_data = self.script_parser.parse_script(script_path)
        except Exception as e:
            logger.error(f"Failed to parse script: {e}")
            return ValidationResult(
                success=False,
                missing_audio=[],
                missing_video=[],
                missing_background=False,
                error_message=str(e)
            )
            
        # Validate assets
        paths = {
            'script_path': script_path,
            'audio_dir': audio_dir,
            'video_dir': video_dir
        }
        
        validation_result = self.asset_validator.validate_all_assets(script_data, paths)
        
        # Check for additional validation failures
        additional_errors = []
        
        if not self.background_processor.validate_background_setup():
            additional_errors.append("FFmpeg or background image setup failed")
            
        if not self.ffmpeg_orchestrator.test_ffmpeg_availability():
            additional_errors.append("FFmpeg not available or missing required codecs")
            
        # If there are additional errors, create a new ValidationResult
        if additional_errors:
            combined_error = validation_result.error_message
            if combined_error:
                combined_error += "\n\nAdditional Issues:\n" + "\n".join(additional_errors)
            else:
                combined_error = "Additional Issues:\n" + "\n".join(additional_errors)
                
            return ValidationResult(
                success=False,
                missing_audio=validation_result.missing_audio,
                missing_video=validation_result.missing_video,
                missing_background=True,  # Set to True since we have additional background issues
                error_message=combined_error
            )
        return validation_result
        
    def _generate_narration_videos(self, episode_path: Path) -> Optional[Dict]:
        """Phase 2: Generate narration videos from static background + TTS audio"""
          # Get script sections in original sequence order
        sections = self.script_parser.get_section_sequence()
        # Filter narration sections while preserving original sequence order
        # This ensures narration videos are created in the proper alternating sequence
        narration_sections = [s for s in sections if s.get('section_type') in ['intro', 'pre_clip', 'post_clip', 'outro']]
        
        if not narration_sections:
            logger.warning("No narration sections found in script")
            return {'successful_count': 0, 'total_count': 0}
            
        # Define paths
        audio_dir = episode_path / "Output" / "Audio"
        temp_dir = episode_path / "Output" / "Video" / get_temp_dir_name()
        
        # Create narration videos
        results = self.background_processor.batch_create_narration_videos(
            narration_sections, audio_dir, temp_dir
        )
        
        successful_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        if successful_count == 0:
            logger.error("Failed to create any narration videos")
            return None
            
        if successful_count < total_count:
            logger.warning(f"Only {successful_count}/{total_count} narration videos created successfully")
            
        return {
            'successful_count': successful_count,
            'total_count': total_count,
            'results': results
        }
        
    def _build_timeline(self, episode_path: Path):
        """Phase 3: Build compilation timeline"""
        
        # Get script sections
        sections = self.script_parser.get_section_sequence()
        
        # Define paths
        audio_dir = episode_path / "Output" / "Audio"
        video_dir = episode_path / "Output" / "Video"
        temp_dir = episode_path / "Output" / "Video" / get_temp_dir_name()
        
        # Build timeline
        timeline = self.timeline_builder.build_compilation_timeline(
            sections, audio_dir, video_dir, temp_dir
        )
        
        # Validate timeline
        if not self.timeline_builder.validate_segment_order(timeline):
            logger.warning("Timeline validation issues detected")
            
        return timeline
        
    def _compile_final_video(self, episode_path: Path, timeline, episode_name: str) -> CompileResult:
        """Phase 4: Compile final video using FFmpeg"""
        
        # Define paths
        temp_dir = episode_path / "Output" / "Video" / get_temp_dir_name()
        final_dir = episode_path / "Output" / "Video" / "Final"
        output_file = final_dir / f"{episode_name}_compiled.mp4"
        
        # Create concat file
        concat_file = self.timeline_builder.create_concat_file(timeline, temp_dir)
          # Compile final video
        compile_result = self.ffmpeg_orchestrator.compile_final_video(
            concat_file, output_file
        )
        
        # Cleanup if configured
        if should_cleanup_temp_files() and compile_result.success:
            self._cleanup_temp_files(temp_dir, timeline)
            
        return compile_result
        
    def _cleanup_temp_files(self, temp_dir: Path, timeline) -> None:
        """Clean up temporary files if configured"""
        try:
            # Get list of temp files to clean
            temp_files = timeline.get_temp_files()
            
            for temp_file in temp_files:
                if temp_file.exists():
                    temp_file.unlink()
                    
            # Remove concat file
            concat_file = temp_dir / "concat_list.txt"
            if concat_file.exists():
                concat_file.unlink()
                
            # Remove temp directory if empty
            if temp_dir.exists() and not any(temp_dir.iterdir()):
                temp_dir.rmdir()
                
            logger.info("Temporary files cleaned up")
            
        except Exception as e:
            logger.warning(f"Failed to cleanup some temporary files: {e}")
            
    def _generate_final_stats(self, timeline, compile_result, narration_result, execution_time: float) -> Dict:
        """Generate comprehensive compilation statistics"""
        
        stats = {
            'episode_info': {
                'total_segments': timeline.get_segment_count(),
                'narration_segments': narration_result['total_count'],
                'video_segments': len(timeline.get_existing_files()),
                'estimated_duration': self.timeline_builder.calculate_total_duration(timeline)
            },
            'compilation': {
                'successful': compile_result.success,
                'execution_time': execution_time,
                'output_size_mb': compile_result.file_size_mb,
                'output_path': str(compile_result.output_path) if compile_result.output_path else None
            },
            'assets': {
                'narration_videos_created': narration_result['successful_count'],
                'temp_files_created': len(timeline.get_temp_files()),
                'existing_files_used': len(timeline.get_existing_files())
            }
        }
        
        return stats
        
    def get_script_summary(self) -> Dict:
        """Get summary of the currently loaded script"""
        return self.script_parser.get_script_summary()


# Convenience function for external use
def compile_episode(episode_path: str) -> CompilationResult:
    """
    Convenience function to compile an episode
    
    Args:
        episode_path: Path to episode directory
        
    Returns:
        CompilationResult with compilation status
    """
    compiler = VideoCompilator()
    return compiler.compile_episode(episode_path)
