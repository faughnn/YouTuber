"""
Batch Processor for TTS Audio Generation System

This module orchestrates the full audio generation pipeline,
processing multiple sections and coordinating all components.
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Optional, Any
import json

from .json_parser import GeminiResponseParser, AudioSection, EpisodeInfo
from .config import AudioGenerationConfig
from .tts_engine import GeminiTTSEngine, TTSResult
from .audio_file_manager import AudioFileManager, GenerationResult, EpisodeMetadata

logger = logging.getLogger(__name__)


@dataclass
class ProcessingReport:
    """Comprehensive report of audio generation processing."""
    episode_info: EpisodeInfo
    total_sections: int
    successful_sections: int
    failed_sections: int
    generated_files: List[str]
    errors: List[str]
    processing_time: float
    output_directory: str
    metadata_file: str = ""


class AudioBatchProcessor:
    """
    Orchestrates the full audio generation pipeline.
    
    Coordinates JSON parsing, TTS generation, file management,
    and provides comprehensive error handling and reporting.
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the batch processor.
        
        Args:
            config_path: Optional path to configuration file
        """        # Initialize components
        self.config = AudioGenerationConfig(config_path)
        self.parser = GeminiResponseParser()
        self.tts_engine = GeminiTTSEngine(self.config)
        self.file_manager = AudioFileManager(self.config.file_settings.content_root)
        
        logger.info("Audio Batch Processor initialized")
        
        # Validate configuration
        validation = self.config.validate_configuration()
        if not validation.is_valid:
            logger.error(f"Configuration validation failed: {validation.errors}")
            for error in validation.errors:
                logger.error(f"Config error: {error}")
    
    def process_episode_script(self, script_path: str) -> ProcessingReport:
        """
        Process a complete episode script and generate all audio files.
        
        Args:
            script_path: Path to the Gemini response script file
            
        Returns:
            Comprehensive processing report
        """
        start_time = time.time()
        logger.info(f"Starting episode processing: {script_path}")
        
        try:            # Step 1: Parse and validate the script
            logger.info("Step 1: Parsing script file...")
            json_data = self.parser.parse_response_file(script_path)
            parse_result = self.parser.validate_podcast_sections(json_data)
            
            if not parse_result.is_valid:
                error_msg = f"Script parsing failed: {'; '.join(parse_result.errors)}"
                logger.error(error_msg)
                return self._create_failed_report(script_path, error_msg, start_time)
            
            episode_info = parse_result.episode_info
            audio_sections = self.parser.extract_audio_sections(json_data.get('podcast_sections', []))
            
            logger.info(f"Parsed {len(audio_sections)} audio sections for processing")
            
            # Step 2: Determine output directory
            logger.info("Step 2: Setting up output directory...")
            episode_dir = self.file_manager.discover_episode_from_script(script_path)
            if not episode_dir:
                error_msg = "Could not determine episode directory from script path"
                logger.error(error_msg)
                return self._create_failed_report(script_path, error_msg, start_time)
            
            output_dir = self.file_manager.create_episode_structure(episode_dir)
            logger.info(f"Audio output directory: {output_dir}")
            
            # Step 3: Process all audio sections
            logger.info("Step 3: Generating audio files...")
            generation_results = self.process_audio_sections(audio_sections, output_dir)
              # Step 4: Save metadata and generate report
            logger.info("Step 4: Saving metadata and generating report...")
            episode_metadata = EpisodeMetadata(
                episode_name=Path(episode_dir).name,
                episode_path=episode_dir,
                script_file=script_path,
                total_sections=parse_result.audio_section_count + parse_result.video_section_count,
                audio_sections=parse_result.audio_section_count,
                video_sections=parse_result.video_section_count,
                generated_timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
            )
            
            metadata_file = self.file_manager.save_generation_metadata(
                generation_results, episode_metadata, output_dir
            )
            
            # Step 5: Create final report
            processing_time = time.time() - start_time
            report = self._create_success_report(
                episode_info, generation_results, output_dir, metadata_file, processing_time
            )
            
            logger.info(f"Episode processing completed in {processing_time:.2f} seconds")
            logger.info(f"Generated {report.successful_sections}/{report.total_sections} audio files")
            
            return report
            
        except Exception as e:
            error_msg = f"Unexpected error during episode processing: {e}"
            logger.error(error_msg, exc_info=True)
            return self._create_failed_report(script_path, error_msg, start_time)
    
    def process_audio_sections(self, sections: List[AudioSection], output_dir: str) -> List[GenerationResult]:
        """
        Process multiple audio sections with concurrent generation.
        
        Args:
            sections: List of audio sections to process
            output_dir: Directory for output files
            
        Returns:
            List of generation results for all sections
        """
        results = []
        max_workers = min(self.config.audio_settings.max_concurrent, len(sections))
        
        logger.info(f"Processing {len(sections)} sections with {max_workers} concurrent workers")
        
        if max_workers == 1:
            # Sequential processing
            for i, section in enumerate(sections, 1):
                logger.info(f"Processing section {i}/{len(sections)}: {section.section_id}")
                result = self._process_single_section(section, output_dir)
                results.append(result)
                
                # Add delay between requests to respect rate limits
                if i < len(sections):
                    time.sleep(self.config.audio_settings.delay_between_requests)
        else:
            # Concurrent processing
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks
                future_to_section = {
                    executor.submit(self._process_single_section, section, output_dir): section
                    for section in sections
                }
                
                # Process completed tasks
                for future in as_completed(future_to_section):
                    section = future_to_section[future]
                    try:
                        result = future.result()
                        results.append(result)
                        logger.info(f"Completed section: {section.section_id} - {'SUCCESS' if result.success else 'FAILED'}")
                    except Exception as e:
                        logger.error(f"Error processing section {section.section_id}: {e}")
                        # Create failed result
                        failed_result = GenerationResult(
                            section_id=section.section_id,
                            section_type=section.section_type,
                            audio_file_path="",
                            success=False,
                            error_message=str(e),
                            generation_time=0.0,
                            file_size=0,
                            audio_duration=0.0,
                            text_length=len(section.script_content)
                        )
                        results.append(failed_result)
        
        # Sort results by section_id for consistent ordering
        results.sort(key=lambda r: r.section_id)
        
        successful = sum(1 for r in results if r.success)
        logger.info(f"Section processing completed: {successful}/{len(results)} successful")
        
        return results
    
    def _process_single_section(self, section: AudioSection, output_dir: str) -> GenerationResult:
        """
        Process a single audio section and generate the audio file.
        
        Args:
            section: Audio section to process
            output_dir: Directory for output files
            
        Returns:
            Generation result for this section
        """
        start_time = time.time()
        
        try:
            # Generate output path
            output_path = Path(output_dir) / f"{section.section_id}.wav"
            
            logger.debug(f"Generating audio for {section.section_id}: {section.section_type}")
            
            # Generate audio using TTS engine
            tts_result = self.tts_engine.generate_audio_with_retry(
                text=section.script_content,
                tone=section.audio_tone,
                output_path=str(output_path)
            )
              # Create generation result
            generation_time = time.time() - start_time
            
            if tts_result.success:
                result = GenerationResult(
                    section_id=section.section_id,
                    section_type=section.section_type,
                    audio_file_path=str(output_path),
                    success=True,
                    error_message="",
                    generation_time=generation_time,
                    file_size=tts_result.file_size,
                    audio_duration=tts_result.audio_duration,
                    text_length=len(section.script_content),
                    script_content=section.script_content,
                    audio_tone=section.audio_tone
                )
                logger.debug(f"Successfully generated audio for {section.section_id}")
            else:
                result = GenerationResult(
                    section_id=section.section_id,
                    section_type=section.section_type,
                    audio_file_path="",
                    success=False,
                    error_message=tts_result.error_message,
                    generation_time=generation_time,
                    file_size=0,
                    audio_duration=0.0,
                    text_length=len(section.script_content),
                    script_content=section.script_content,
                    audio_tone=section.audio_tone
                )
                logger.warning(f"Failed to generate audio for {section.section_id}: {tts_result.error_message}")
            return result
            
        except Exception as e:
            generation_time = time.time() - start_time
            error_msg = f"Error processing section {section.section_id}: {e}"
            logger.error(error_msg)
            
            return GenerationResult(
                section_id=section.section_id,
                section_type=section.section_type,
                audio_file_path="",
                success=False,
                error_message=error_msg,
                generation_time=generation_time,
                file_size=0,
                audio_duration=0.0,
                text_length=len(section.script_content),
                script_content=section.script_content,
                audio_tone=section.audio_tone
            )
    
    def generate_processing_report(self, results: List[GenerationResult]) -> Dict[str, Any]:
        """
        Generate a detailed processing report from results.
        
        Args:
            results: List of generation results
            
        Returns:
            Detailed report dictionary
        """
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]
        
        report = {
            "summary": {
                "total_sections": len(results),
                "successful_sections": len(successful_results),
                "failed_sections": len(failed_results),
                "success_rate": len(successful_results) / len(results) if results else 0,
                "total_generation_time": sum(r.generation_time for r in results),
                "average_generation_time": sum(r.generation_time for r in results) / len(results) if results else 0
            },
            "successful_sections": [
                {
                    "section_id": r.section_id,
                    "section_type": r.section_type,
                    "file_path": r.audio_file_path,
                    "duration": r.audio_duration,
                    "file_size": r.file_size
                }
                for r in successful_results
            ],
            "failed_sections": [
                {
                    "section_id": r.section_id,
                    "section_type": r.section_type,
                    "error": r.error_message
                }
                for r in failed_results
            ]
        }
        
        return report
    
    def _create_success_report(self, 
                              episode_info: EpisodeInfo,
                              results: List[GenerationResult], 
                              output_dir: str,
                              metadata_file: str,
                              processing_time: float) -> ProcessingReport:
        """Create a successful processing report."""
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]
        
        return ProcessingReport(
            episode_info=episode_info,
            total_sections=len(results),
            successful_sections=len(successful_results),
            failed_sections=len(failed_results),
            generated_files=[r.audio_file_path for r in successful_results],
            errors=[r.error_message for r in failed_results if r.error_message],
            processing_time=processing_time,
            output_directory=output_dir,
            metadata_file=metadata_file
        )
    
    def _create_failed_report(self, script_path: str, error_message: str, start_time: float) -> ProcessingReport:
        """Create a failed processing report."""
        processing_time = time.time() - start_time
          # Create minimal episode info from script path
        episode_info = EpisodeInfo(
            narrative_theme="Processing failed",
            total_estimated_duration="0 minutes",
            target_audience="Unknown",
            key_themes=[],
            total_clips_analyzed=0,
            source_file=script_path
        )
        
        return ProcessingReport(
            episode_info=episode_info,
            total_sections=0,
            successful_sections=0,
            failed_sections=1,
            generated_files=[],
            errors=[error_message],
            processing_time=processing_time,
            output_directory="",
            metadata_file=""
        )
    
    def validate_processing_environment(self) -> Dict[str, bool]:
        """
        Validate that the processing environment is ready.
        
        Returns:
            Dictionary of validation results
        """
        validation = {
            "config_valid": False,
            "tts_connection": False,
            "content_root_exists": False,
            "write_permissions": False
        }
        
        try:
            # Check configuration
            config_validation = self.config.validate_configuration()
            validation["config_valid"] = config_validation.is_valid
            
            # Check TTS connection
            validation["tts_connection"] = self.tts_engine.test_connection()
            
            # Check content root
            validation["content_root_exists"] = self.file_manager.content_root.exists()
            
            # Check write permissions (try to create a temp directory)
            if validation["content_root_exists"]:
                test_dir = self.file_manager.content_root / ".write_test"
                try:
                    test_dir.mkdir(exist_ok=True)
                    test_dir.rmdir()
                    validation["write_permissions"] = True
                except OSError:
                    validation["write_permissions"] = False
            
        except Exception as e:
            logger.error(f"Error validating processing environment: {e}")
        
        return validation
    
    def process_script_file(self, script_path: str, force_regenerate: bool = False) -> ProcessingReport:
        """
        Process a script file and generate audio files.
        
        This is an alias for process_episode_script with additional force_regenerate option.
        
        Args:
            script_path: Path to the script file
            force_regenerate: Whether to regenerate existing audio files
            
        Returns:
            Processing report with results
        """
        # TODO: Implement force_regenerate functionality in future iteration
        # For now, just call the main processing method
        return self.process_episode_script(script_path)
    
    def save_batch_report(self, report: ProcessingReport, output_path: str) -> str:
        """
        Save a batch processing report to file.
        
        Args:
            report: Processing report to save
            output_path: Path where to save the report
            
        Returns:
            Path to saved report file
        """
        try:
            report_data = {
                "batch_report": {
                    "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "total_files": report.total_sections,
                    "successful_files": report.successful_sections,
                    "failed_files": report.failed_sections,
                    "success_rate": report.successful_sections / report.total_sections if report.total_sections > 0 else 0,
                    "total_time": report.processing_time
                },
                "file_results": [
                    {
                        "section_id": result.section_id,
                        "section_type": result.section_type,
                        "audio_file_path": result.audio_file_path,
                        "success": result.success,
                        "error_message": result.error_message,
                        "generation_time": result.generation_time,
                        "file_size": result.file_size,
                        "audio_duration": result.audio_duration,
                        "text_length": result.text_length
                    }
                    for result in report.generated_files
                ],
                "episode_reports": {
                    path: {
                        "total_files": ep_report.total_sections,
                        "successful_files": ep_report.successful_sections,
                        "failed_files": ep_report.failed_sections,
                        "success_rate": ep_report.successful_sections / ep_report.total_sections if ep_report.total_sections > 0 else 0,
                        "total_time": ep_report.processing_time
                    }
                    for path, ep_report in report.episode_reports.items()
                }
            }
            
            output_path = Path(output_path)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Batch report saved to: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Failed to save batch report: {e}")
            raise
