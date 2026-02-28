"""
EdgeTTSEngine - Microsoft Edge TTS Engine

This module provides Edge TTS integration for the podcast audio generation pipeline.
Uses Microsoft Edge's free neural TTS service without requiring an API key.
Maintains interface compatibility with SimpleTTSEngine and ElevenLabsTTSEngine.
"""

import logging
import time
import os
import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any

import edge_tts

# Import shared components from Chatterbox
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Chatterbox.json_parser import ChatterboxResponseParser, AudioSection
from Chatterbox.simple_audio_file_manager import SimpleAudioFileManager

from .config_edge_tts import DEFAULT_VOICE, VOICE_RATE, VOICE_VOLUME, VOICE_PITCH, OUTPUT_FORMAT

logger = logging.getLogger(__name__)


@dataclass
class SimpleProcessingReport:
    """Return structure compatible with master processor expectations"""
    total_sections: int
    successful_sections: int
    failed_sections: int
    skipped_sections: int = 0
    generated_files: List[str] = None
    existing_files: List[str] = None
    output_directory: str = ""
    processing_time: float = 0.0
    metadata_file: str = ""


class EdgeTTSEngine:
    """Microsoft Edge TTS engine for sequential processing of podcast audio sections"""

    def __init__(self, config_path=None):
        """Initialize with Edge TTS configuration"""
        self.config_path = config_path
        self.parser = ChatterboxResponseParser()
        self.file_manager = SimpleAudioFileManager()

        # Edge TTS configuration (no API key required)
        self.voice = DEFAULT_VOICE
        self.rate = VOICE_RATE
        self.volume = VOICE_VOLUME
        self.pitch = VOICE_PITCH
        self.output_format = OUTPUT_FORMAT

        logger.info("EdgeTTSEngine initialized")
        logger.info(f"Voice: {self.voice}")
        logger.info(f"Settings: Rate={self.rate}, Volume={self.volume}, Pitch={self.pitch}")

    def process_episode_script(self, script_path: str, progress_callback=None) -> SimpleProcessingReport:
        """
        Main processing pipeline:
        1. Parse JSON script file
        2. Extract audio sections
        3. Discover episode directory
        4. Process each section sequentially with Edge TTS
        5. Return compatible report

        Args:
            script_path: Path to script file
            progress_callback: Optional callback function(section_id, is_success, is_existing)

        Returns:
            SimpleProcessingReport with processing results
        """
        start_time = time.time()
        logger.info(f"Starting EdgeTTSEngine processing: {script_path}")

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
            logger.info("Step 4: Processing audio sections with Edge TTS...")
            results = self._process_sections_sequentially(
                audio_sections, audio_output_dir, progress_callback
            )

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
            logger.error(f"Critical error in EdgeTTSEngine: {e}")
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
        """Process audio sections one at a time using Edge TTS

        Args:
            audio_sections: List of AudioSection objects to process
            audio_output_dir: Output directory for audio files
            progress_callback: Optional callback function(section_id, is_success, is_existing)
        """
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
                mp3_filename = f"{section.section_id}.{self.output_format}"
                output_file = audio_output_dir / mp3_filename

                # Check if file already exists
                if output_file.exists():
                    logger.info(f"File already exists, skipping: {output_file}")
                    results['skipped'] += 1
                    results['existing_files'].append(str(output_file))
                    if progress_callback:
                        progress_callback(section.section_id, True, is_existing=True)
                    continue

                # Generate audio using Edge TTS (async wrapped in sync)
                logger.info(f"Generating audio for: {section.script_content[:100]}...")
                self._generate_audio_sync(section.script_content, str(output_file))

                logger.info(f"Successfully generated: {output_file}")
                results['successful'] += 1
                results['generated_files'].append(str(output_file))
                if progress_callback:
                    progress_callback(section.section_id, True, is_existing=False)

            except Exception as e:
                logger.error(f"Failed to process section {section.section_id}: {e}")
                results['failed'] += 1
                if progress_callback:
                    progress_callback(section.section_id, False, is_existing=False)
                raise Exception(f"Edge TTS error for section {section.section_id}: {e}")

        return results

    def _generate_audio_sync(self, text: str, output_path: str) -> None:
        """Synchronous wrapper for async Edge TTS generation"""
        asyncio.run(self._generate_audio_async(text, output_path))

    async def _generate_audio_async(self, text: str, output_path: str) -> None:
        """Generate audio using Edge TTS async API"""
        communicate = edge_tts.Communicate(
            text,
            self.voice,
            rate=self.rate,
            volume=self.volume,
            pitch=self.pitch
        )
        await communicate.save(output_path)

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
            audio_file_path = Path(output_dir) / f"{section.section_id}.{self.output_format}"

            if audio_file_path.exists() and audio_file_path.stat().st_size > 1024:
                existing_sections.append(section)
                existing_files.append(str(audio_file_path))
                logger.debug(f"Found existing file: {section.section_id}.{self.output_format}")
            else:
                missing_sections.append(section)
                if audio_file_path.exists():
                    logger.warning(f"File too small, will regenerate: {section.section_id}.{self.output_format}")
                else:
                    logger.debug(f"Missing file: {section.section_id}.{self.output_format}")

        return existing_sections, missing_sections, existing_files
