"""
Integration Module for Video Clipper

This module provides the main interface for master processor integration
and high-level clip extraction functionality.
"""

import os
import json
import logging
from typing import Dict, Optional
from pathlib import Path

from .script_parser import UnifiedScriptParser
from .video_extractor import VideoClipExtractor


def extract_clips_from_script(episode_dir: str, 
                             script_filename: str = "unified_podcast_script.json",
                             start_buffer: float = 0.0,
                             end_buffer: float = 0.0) -> Dict:
    """
    Main function called by master processor to extract video clips from script.
    
    Args:
        episode_dir: Full path to episode directory
        script_filename: Name of script file in Output/Scripts/
        start_buffer: Buffer time (seconds) to add before clip start
        end_buffer: Buffer time (seconds) to add after clip end
    
    Returns:
        Dict with success status, clip count, output directory, and details
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Convert to Path objects
        episode_path = Path(episode_dir)
        
        # Define paths
        video_path = episode_path / "Input" / "original_video.mp4"
        script_path = episode_path / "Output" / "Scripts" / script_filename
        output_dir = episode_path / "Output" / "Video"
        
        logger.info(f"Starting video clip extraction for episode: {episode_path.name}")
        logger.info(f"Video source: {video_path}")
        logger.info(f"Script source: {script_path}")
        logger.info(f"Output directory: {output_dir}")
        
        # Validate inputs
        if not video_path.exists():
            return {
                'success': False,
                'error': f'Original video file not found: {video_path}',
                'clips_created': 0,
                'output_directory': None
            }
        
        if not script_path.exists():
            return {
                'success': False,
                'error': f'Script file not found: {script_path}',
                'clips_created': 0,
                'output_directory': None
            }
        
        # Parse script to extract video clip specifications
        parser = UnifiedScriptParser()
        clips = parser.parse_script_file(str(script_path))
        
        if not clips:
            logger.info("No video clips found in script - extraction complete")
            return {
                'success': True,
                'message': 'No video clips found in script',
                'clips_created': 0,
                'output_directory': str(output_dir)
            }
        
        logger.info(f"Found {len(clips)} video clips to extract")
        
        # Create video extractor and extract clips
        extractor = VideoClipExtractor()
        report = extractor.extract_clips(
            video_path=video_path,
            clips=clips,
            output_dir=output_dir,
            start_buffer=start_buffer,
            end_buffer=end_buffer
        )
        
        # Save extraction report
        _save_extraction_report(output_dir, report)
        
        # Generate summary
        _save_extraction_summary(output_dir, report)
        
        # Return result
        if report.successful_clips > 0:
            return {
                'success': True,
                'clips_created': report.successful_clips,
                'clips_failed': report.failed_clips,
                'clips_skipped': report.skipped_clips,
                'total_clips': report.total_clips,
                'output_directory': str(output_dir),
                'extraction_time': report.total_time,
                'success_rate': f"{(report.successful_clips / report.total_clips * 100):.1f}%"
            }
        else:
            return {
                'success': False,
                'error': f'All {report.total_clips} clips failed to extract',
                'clips_created': 0,
                'clips_failed': report.failed_clips,
                'clips_skipped': report.skipped_clips,
                'total_clips': report.total_clips,
                'output_directory': str(output_dir),
                'errors': report.errors
            }
    
    except Exception as e:
        logger.error(f"Unexpected error in extract_clips_from_script: {e}")
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}',
            'clips_created': 0,
            'output_directory': None
        }


def _save_extraction_report(output_dir: Path, report) -> None:
    """Save detailed extraction report as JSON"""
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / "extraction_report.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
        
        logging.getLogger(__name__).info(f"Saved extraction report: {report_path}")
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to save extraction report: {e}")


def _save_extraction_summary(output_dir: Path, report) -> None:
    """Save human-readable extraction summary"""
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        summary_path = output_dir / "extraction_summary.txt"
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("Video Clip Extraction Summary\n")
            f.write("=" * 40 + "\n\n")
            
            f.write(f"Total clips processed: {report.total_clips}\n")
            f.write(f"Successfully extracted: {report.successful_clips}\n")
            f.write(f"Failed extractions: {report.failed_clips}\n")
            f.write(f"Skipped (already exist): {report.skipped_clips}\n")
            f.write(f"Success rate: {(report.successful_clips / report.total_clips * 100):.1f}%\n" if report.total_clips > 0 else "Success rate: 0%\n")
            f.write(f"Total processing time: {report.total_time:.2f} seconds\n")
            f.write(f"Output directory: {report.output_directory}\n\n")
            
            if report.successful_clips > 0:
                f.write("Successfully Extracted Clips:\n")
                f.write("-" * 30 + "\n")
                for result in report.results:
                    if result.success and result.output_path in report.existing_files:
                        # This was skipped (already existed)
                        continue
                    elif result.success:
                        f.write(f"✓ {result.clip_spec.section_id}: {result.clip_spec.title}\n")
                        f.write(f"  File: {Path(result.output_path).name}\n")
                        f.write(f"  Size: {result.file_size_bytes / 1024 / 1024:.2f} MB\n")
                        f.write(f"  Time: {result.extraction_time:.2f}s\n\n")
            
            if report.skipped_clips > 0:
                f.write("Skipped Clips (Already Exist):\n")
                f.write("-" * 30 + "\n")
                for result in report.results:
                    if result.success and result.output_path in report.existing_files:
                        f.write(f"↻ {result.clip_spec.section_id}: {result.clip_spec.title}\n")
                        f.write(f"  File: {Path(result.output_path).name}\n")
                        f.write(f"  Size: {result.file_size_bytes / 1024 / 1024:.2f} MB\n\n")
            
            if report.failed_clips > 0:
                f.write("Failed Extractions:\n")
                f.write("-" * 20 + "\n")
                for result in report.results:
                    if not result.success:
                        f.write(f"✗ {result.clip_spec.section_id}: {result.clip_spec.title}\n")
                        f.write(f"  Error: {result.error_message}\n\n")
            
            if report.errors:
                f.write("General Errors:\n")
                f.write("-" * 15 + "\n")
                for error in report.errors:
                    f.write(f"• {error}\n")
        
        logging.getLogger(__name__).info(f"Saved extraction summary: {summary_path}")
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to save extraction summary: {e}")


def get_video_clips_info(script_path: str) -> Dict:
    """
    Get information about video clips in a script without extracting.
    
    Args:
        script_path: Path to unified podcast script file
        
    Returns:
        Dict with clip information and statistics
    """
    try:
        parser = UnifiedScriptParser()
        clips = parser.parse_script_file(script_path)
        
        clip_info = []
        total_duration = 0.0
        
        for clip in clips:
            try:
                start_seconds = parser.parse_timestamp(clip.start_time)
                end_seconds = parser.parse_timestamp(clip.end_time)
                duration = end_seconds - start_seconds
                total_duration += duration
                
                clip_info.append({
                    'section_id': clip.section_id,
                    'clip_id': clip.clip_id,
                    'title': clip.title,
                    'start_time': clip.start_time,
                    'end_time': clip.end_time,
                    'duration_seconds': duration,
                    'severity_level': clip.severity_level
                })
            except Exception as e:
                logging.getLogger(__name__).warning(f"Could not parse timestamps for clip {clip.clip_id}: {e}")
        
        return {
            'success': True,
            'total_clips': len(clips),
            'total_duration_seconds': total_duration,
            'total_duration_formatted': f"{total_duration / 60:.1f} minutes",
            'clips': clip_info
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'total_clips': 0,
            'clips': []
        }
