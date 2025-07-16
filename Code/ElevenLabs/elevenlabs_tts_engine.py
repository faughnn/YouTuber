"""
ElevenLabsTTSEngine - ElevenLabs API-based TTS Engine

This module provides ElevenLabs TTS integration for the podcast audio generation pipeline.
Maintains interface compatibility with SimpleTTSEngine for seamless pipeline integration.
"""

import logging
import time
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional, Any

from elevenlabs import VoiceSettings, save
from elevenlabs.client import ElevenLabs

# Import shared components from Chatterbox
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Chatterbox.json_parser import ChatterboxResponseParser, AudioSection
from Chatterbox.simple_audio_file_manager import SimpleAudioFileManager

logger = logging.getLogger(__name__)


@dataclass
class SimpleProcessingReport:
    """Return structure compatible with master processor expectations"""
    total_sections: int           # Total audio sections found
    successful_sections: int      # Successfully processed
    failed_sections: int          # Failed to process
    skipped_sections: int = 0     # Existing files that were skipped
    generated_files: List[str] = None    # List of generated .mp3 file paths
    existing_files: List[str] = None     # List of existing .mp3 file paths
    output_directory: str = ""    # Path to Output/Audio/ directory
    processing_time: float = 0.0  # Total processing time in seconds
    metadata_file: str = ""       # Path to metadata file (optional)


class ElevenLabsTTSEngine:
    """ElevenLabs API-based TTS engine for sequential processing of podcast audio sections"""
    
    def __init__(self, config_path=None):
        """Initialize with ElevenLabs API configuration"""
        self.config_path = config_path
        self.parser = ChatterboxResponseParser()
        self.file_manager = SimpleAudioFileManager()
        
        # ElevenLabs configuration
        self.api_key = os.getenv('ELEVENLABS_API_KEY')
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY environment variable not set")
        
        # Hardcoded voice ID and settings as per requirements
        self.voice_id = "0DxQtWphUO5YNcF7UOm1"  # Aria voice
        self.voice_settings = VoiceSettings(
            stability=0.5,           # 50%
            similarity_boost=0.75,   # 75%
            style=0.0,               # Default
            use_speaker_boost=True
        )
        
        # Initialize ElevenLabs client
        self.client = ElevenLabs(api_key=self.api_key)
        
        logger.info("ElevenLabsTTSEngine initialized")
        logger.info(f"Voice ID: {self.voice_id}")
        logger.info(f"Voice settings: Stability=50%, Similarity=75%, Style=0%")
    
    def process_episode_script(self, script_path: str, progress_callback=None) -> SimpleProcessingReport:
        """
        Main processing pipeline:
        1. Parse JSON script file
        2. Extract audio sections
        3. Discover episode directory
        4. Process each section sequentially with ElevenLabs API
        5. Log every API call
        6. Return compatible report
        
        Args:
            script_path: Path to script file
            progress_callback: Optional callback function(section_id, is_success, is_existing)
        """
        start_time = time.time()
        logger.info(f"Starting ElevenLabsTTSEngine processing: {script_path}")
        
        try:
            # Step 1: Parse JSON script file
            logger.info("Step 1: Parsing script file...")
            json_data = self.parser.parse_response_file(script_path)
            
            # Step 2: Extract audio sections
            logger.info("Step 2: Extracting audio sections...")
            all_sections = json_data.get('podcast_sections', [])
            audio_sections = self.parser.extract_audio_sections(all_sections)
            
            if not audio_sections:
                logger.warning("No audio sections found in script")
                return SimpleProcessingReport(
                    total_sections=0,
                    successful_sections=0,
                    failed_sections=0,
                    generated_files=[],
                    output_directory="",
                    processing_time=time.time() - start_time
                )
            
            logger.info(f"Found {len(audio_sections)} audio sections to process")
            
            # Step 3: Discover episode directory structure
            logger.info("Step 3: Discovering episode directory...")
            episode_dir = self.file_manager.discover_episode_from_script(script_path)
            audio_output_dir = self.file_manager.create_episode_structure(episode_dir)
            
            logger.info(f"Episode directory: {episode_dir}")
            logger.info(f"Audio output directory: {audio_output_dir}")
            
            # Step 4: Process sections sequentially
            logger.info("Step 4: Processing audio sections with ElevenLabs...")
            results = self._process_sections_sequentially(audio_sections, audio_output_dir, progress_callback)
            
            # Step 5: Compile results
            processing_time = time.time() - start_time
            
            report = SimpleProcessingReport(
                total_sections=len(audio_sections),
                successful_sections=results['successful'],
                failed_sections=results['failed'],
                skipped_sections=results['skipped'],
                generated_files=results['generated_files'],
                existing_files=results['existing_files'],
                output_directory=str(audio_output_dir),
                processing_time=processing_time
            )
            
            logger.info(f"Processing complete: {report.successful_sections}/{report.total_sections} successful")
            logger.info(f"Total processing time: {processing_time:.2f} seconds")
            
            return report
            
        except Exception as e:
            logger.error(f"Critical error in ElevenLabsTTSEngine: {e}")
            return SimpleProcessingReport(
                total_sections=0,
                successful_sections=0,
                failed_sections=1,
                generated_files=[],
                output_directory="",
                processing_time=time.time() - start_time
            )
    
    def _process_sections_sequentially(self, audio_sections: List[AudioSection], 
                                     audio_output_dir: str, progress_callback=None) -> Dict[str, Any]:
        """Process audio sections one at a time using ElevenLabs API
        
        Args:
            audio_sections: List of AudioSection objects to process
            audio_output_dir: Output directory for audio files
            progress_callback: Optional callback function(section_id, is_success, is_existing)
        """
        
        # Convert string path to Path object for consistent path operations
        audio_output_dir = Path(audio_output_dir)
        
        results = {
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'generated_files': [],
            'existing_files': []
        }
        
        for i, section in enumerate(audio_sections, 1):
            logger.info(f"Processing section {i}/{len(audio_sections)}: {section.section_id}")
            
            try:
                # Generate output file path (MP3 format)
                mp3_filename = f"{section.section_id}.mp3"
                output_file = audio_output_dir / mp3_filename
                
                # Check if file already exists
                if output_file.exists():
                    logger.info(f"File already exists, skipping: {output_file}")
                    results['skipped'] += 1
                    results['existing_files'].append(str(output_file))
                    # Notify progress callback about existing file
                    if progress_callback:
                        progress_callback(section.section_id, True, is_existing=True)
                    continue
                
                # Make ElevenLabs API call
                logger.info(f"Making ElevenLabs API call for: {section.script_content[:100]}...")
                logger.info(f"Using voice ID: {self.voice_id}")
                
                audio_data = self.client.text_to_speech.convert(
                    voice_id=self.voice_id,
                    text=section.script_content,
                    voice_settings=self.voice_settings
                )
                
                # Save audio file
                save(audio_data, str(output_file))
                
                logger.info(f"✅ Successfully generated: {output_file}")
                results['successful'] += 1
                results['generated_files'].append(str(output_file))
                # Notify progress callback about success
                if progress_callback:
                    progress_callback(section.section_id, True, is_existing=False)
                
            except Exception as e:
                logger.error(f"❌ Failed to process section {section.section_id}: {e}")
                results['failed'] += 1
                # Notify progress callback about failure
                if progress_callback:
                    progress_callback(section.section_id, False, is_existing=False)
                # Re-raise the exception to fail the pipeline as required
                raise Exception(f"ElevenLabs API error for section {section.section_id}: {e}")
        
        return results

    def check_existing_audio_files(self, audio_sections: List[AudioSection], output_dir: str) -> tuple:
        """
        Check which audio files already exist
        
        Args:
            audio_sections: List of audio sections from script
            output_dir: Output directory path
            
        Returns:
            Tuple of (existing_sections, missing_sections, existing_files)
        """
        existing_sections = []
        missing_sections = []
        existing_files = []
        
        for section in audio_sections:
            audio_file_path = Path(output_dir) / f"{section.section_id}.mp3"  # ElevenLabs uses MP3
            
            # Check if file exists and has reasonable size (min 1KB to avoid empty files)
            if audio_file_path.exists() and audio_file_path.stat().st_size > 1024:
                existing_sections.append(section)
                existing_files.append(str(audio_file_path))
                logger.debug(f"✓ Found existing file: {section.section_id}.mp3 ({audio_file_path.stat().st_size} bytes)")
            else:
                missing_sections.append(section)
                if audio_file_path.exists():
                    logger.warning(f"⚠ File too small, will regenerate: {section.section_id}.mp3 ({audio_file_path.stat().st_size} bytes)")
                else:
                    logger.debug(f"⚠ Missing file: {section.section_id}.mp3")
        
        return existing_sections, missing_sections, existing_files
