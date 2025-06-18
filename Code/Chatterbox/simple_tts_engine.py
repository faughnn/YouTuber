"""
SimpleTTSEngine - Simplified API-based TTS Engine

This module provides a streamlined replacement for the complex ChatterboxBatchProcessor,
using direct API calls to process podcast audio sections sequentially.
Maintains interface compatibility with the master processor expectations.
"""

import logging
import time
import requests
import wave
import audioop
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional, Any

# PyDub imports for audio analysis and silence detection
try:
    from pydub import AudioSegment
    from pydub.silence import detect_silence
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    logging.warning("PyDub not available. Audio quality validation will be disabled.")

from .config_tts_api import (
    API_BASE_URL, EXAGGERATION, CFG_WEIGHT, TEMPERATURE,
    ENABLE_AUDIO_VALIDATION, MAX_RETRIES, SILENCE_THRESHOLD_DB,
    MIN_SILENCE_DURATION_MS, MAX_SILENCE_RATIO
)
from .json_parser import ChatterboxResponseParser, AudioSection
from .simple_audio_file_manager import SimpleAudioFileManager

logger = logging.getLogger(__name__)


@dataclass
class AudioValidationResult:
    """Result of audio quality validation"""
    is_valid: bool
    silence_duration_ms: int
    total_duration_ms: int
    silence_ratio: float
    detected_silent_ranges: List[tuple]
    validation_details: str


@dataclass
class SimpleProcessingReport:
    """Return structure compatible with master processor expectations"""
    total_sections: int           # Total audio sections found
    successful_sections: int      # Successfully processed
    failed_sections: int          # Failed to process
    generated_files: List[str]    # List of generated .wav file paths
    output_directory: str         # Path to Output/Audio/ directory
    processing_time: float        # Total processing time in seconds
    metadata_file: str = ""       # Path to metadata file (optional)


class SimpleTTSEngine:
    """Simple API-based TTS engine for sequential processing of podcast audio sections"""
    
    def __init__(self, config_path=None):
        """Initialize with API configuration"""
        self.config_path = config_path
        self.parser = ChatterboxResponseParser()
        self.file_manager = SimpleAudioFileManager()
        
        logger.info("SimpleTTSEngine initialized")
        logger.info(f"API endpoint: {API_BASE_URL}/v1/audio/speech")
        
        # Audio validation setup
        if ENABLE_AUDIO_VALIDATION:
            if PYDUB_AVAILABLE:
                logger.info("Audio quality validation enabled with PyDub")
                logger.info(f"Validation settings: threshold={SILENCE_THRESHOLD_DB}dB, "
                           f"min_duration={MIN_SILENCE_DURATION_MS}ms, max_ratio={MAX_SILENCE_RATIO}")
            else:
                logger.warning("Audio validation requested but PyDub not available - validation disabled")
        else:
            logger.info("Audio quality validation disabled")
    
    def process_episode_script(self, script_path: str) -> SimpleProcessingReport:
        """
        Main processing pipeline:
        1. Parse JSON script file
        2. Extract audio sections
        3. Discover episode directory
        4. Process each section sequentially (ONE AT A TIME)
        5. Log every API call
        6. Return compatible report
        """
        start_time = time.time()
        logger.info(f"Starting SimpleTTSEngine processing: {script_path}")
        
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
            
            # Step 3: Discover episode directory
            logger.info("Step 3: Discovering episode directory...")
            episode_dir = self.file_manager.discover_episode_from_script(script_path)
            output_dir = self.file_manager.create_episode_structure(episode_dir)
            
            logger.info(f"Episode directory: {episode_dir}")
            logger.info(f"Output directory: {output_dir}")
              # Step 4: Process each section sequentially
            logger.info("Step 4: Processing audio sections...")
            generated_files = []
            successful_count = 0
            failed_count = 0
            
            for i, section in enumerate(audio_sections, 1):
                logger.info(f"Processing section {i}/{len(audio_sections)}: {section.section_id}")
                
                try:
                    # Generate output path
                    output_filename = f"{section.section_id}.wav"
                    output_path = Path(output_dir) / output_filename
                    
                    # Generate speech with validation and retry logic
                    success = self.generate_speech_with_validation(
                        section.script_content, 
                        str(output_path), 
                        section.section_id
                    )
                    
                    if success:
                        # Organize file using file manager
                        metadata = {
                            'episode_dir': episode_dir,
                            'section_id': section.section_id,
                            'section_type': section.section_type
                        }
                        
                        organized_path = self.file_manager.organize_audio_file(output_path, metadata)
                        generated_files.append(organized_path)
                        successful_count += 1
                        
                        logger.info(f"✅ Successfully processed {section.section_id}")
                    else:
                        failed_count += 1
                        logger.error(f"❌ Failed to process {section.section_id}")
                        
                except Exception as e:
                    failed_count += 1
                    logger.error(f"❌ Error processing {section.section_id}: {e}")
                    # Fail fast - stop on any error
                    raise Exception(f"Processing failed at section {section.section_id}: {e}")
            
            processing_time = time.time() - start_time
            
            logger.info(f"Processing complete: {successful_count} successful, {failed_count} failed")
            logger.info(f"Total processing time: {processing_time:.2f}s")
            
            return SimpleProcessingReport(
                total_sections=len(audio_sections),
                successful_sections=successful_count,
                failed_sections=failed_count,
                generated_files=generated_files,
                output_directory=output_dir,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Episode processing failed: {e}")
            
            return SimpleProcessingReport(
                total_sections=0,
                successful_sections=0,
                failed_sections=1,
                generated_files=[],
                output_directory="",
                processing_time=processing_time
            )
    
    def generate_speech(self, text: str, output_path: str) -> bool:
        """Generate single audio file via API call"""
        section_start_time = time.time()
        text_length = len(text)
        
        try:
            # Prepare API payload
            payload = {
                "input": text,
                "exaggeration": EXAGGERATION,
                "cfg_weight": CFG_WEIGHT,
                "temperature": TEMPERATURE
            }
            
            logger.debug(f"Making API call for {text_length} characters")
            
            # Make API request
            response = requests.post(
                f"{API_BASE_URL}/v1/audio/speech",
                headers={"Content-Type": "application/json"},
                json=payload
            )
            
            processing_time = time.time() - section_start_time
            
            # Log API call
            response_data = {
                'status_code': response.status_code,
                'output_path': output_path,
                'processing_time': processing_time
            }
            
            section_id = Path(output_path).stem  # Extract section_id from filename
            self.log_api_call(section_id, text_length, response_data)
            
            # Handle response
            if response.status_code == 200:
                # Save audio file
                output_path_obj = Path(output_path)
                output_path_obj.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"Audio saved to: {output_path}")
                return True
            else:
                error_msg = f"API call failed for section {section_id}: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Could not connect to TTS API at {API_BASE_URL}: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
        except Exception as e:
            error_msg = f"API call failed: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def log_api_call(self, section_id: str, text_length: int, response_data: dict) -> None:
        """Log every API interaction for debugging"""
        logger.info(f"API Call - Section: {section_id}, Text Length: {text_length}, "
                    f"Status: {response_data.get('status_code')}, "
                    f"Output: {response_data.get('output_path')}, "
                    f"Duration: {response_data.get('processing_time', 0):.2f}s")
    
    def validate_audio_quality(self, audio_file_path: str, section_id: str) -> AudioValidationResult:
        """
        Validate audio quality using PyDub silence detection
        
        Args:
            audio_file_path: Path to the generated audio file
            section_id: Section identifier for logging
            
        Returns:
            AudioValidationResult with validation details
        """
        if not ENABLE_AUDIO_VALIDATION or not PYDUB_AVAILABLE:
            return AudioValidationResult(
                is_valid=True,
                silence_duration_ms=0,
                total_duration_ms=0,
                silence_ratio=0.0,
                detected_silent_ranges=[],
                validation_details="Validation disabled or PyDub unavailable"
            )
        
        try:
            # Load audio file
            audio = AudioSegment.from_wav(audio_file_path)
            total_duration_ms = len(audio)
            
            # Detect silence periods
            silent_ranges = detect_silence(
                audio,
                min_silence_len=MIN_SILENCE_DURATION_MS,
                silence_thresh=SILENCE_THRESHOLD_DB
            )
            
            # Calculate total silence duration
            total_silence_ms = sum(end - start for start, end in silent_ranges)
            silence_ratio = total_silence_ms / total_duration_ms if total_duration_ms > 0 else 0
            
            # Determine if audio is valid
            is_valid = silence_ratio <= MAX_SILENCE_RATIO
            
            validation_details = (
                f"Duration: {total_duration_ms}ms, "
                f"Silence: {total_silence_ms}ms ({silence_ratio:.1%}), "
                f"Silent ranges: {len(silent_ranges)}"
            )
            
            logger.debug(f"Audio validation for {section_id}: {validation_details}")
            
            return AudioValidationResult(
                is_valid=is_valid,
                silence_duration_ms=total_silence_ms,
                total_duration_ms=total_duration_ms,
                silence_ratio=silence_ratio,
                detected_silent_ranges=silent_ranges,
                validation_details=validation_details
            )
            
        except Exception as e:
            logger.error(f"Audio validation failed for {section_id}: {e}")
            # Return as valid to avoid blocking processing on validation errors
            return AudioValidationResult(
                is_valid=True,
                silence_duration_ms=0,
                total_duration_ms=0,
                silence_ratio=0.0,
                detected_silent_ranges=[],
                validation_details=f"Validation error: {e}"
            )
    
    def generate_speech_with_validation(self, text: str, output_path: str, section_id: str) -> bool:
        """
        Generate speech with automatic retry for silent clips
        
        Args:
            text: Text to convert to speech
            output_path: Output file path for the audio
            section_id: Section identifier for logging
            
        Returns:
            bool: True if successful, False if all retries failed
        """
        max_retries = MAX_RETRIES if ENABLE_AUDIO_VALIDATION else 1
        
        for attempt in range(1, max_retries + 1):
            logger.debug(f"Audio generation attempt {attempt}/{max_retries} for {section_id}")
            
            try:
                # Generate audio via API
                success = self.generate_speech(text, output_path)
                
                if not success:
                    logger.warning(f"API call failed for {section_id} on attempt {attempt}")
                    continue
                
                # Validate audio quality if enabled
                if ENABLE_AUDIO_VALIDATION and PYDUB_AVAILABLE:
                    validation_result = self.validate_audio_quality(output_path, section_id)
                    
                    if validation_result.is_valid:
                        if attempt > 1:
                            logger.info(f"✅ {section_id} generated successfully after {attempt} attempts")
                        logger.info(f"Audio validation passed for {section_id}: {validation_result.validation_details}")
                        return True
                    else:
                        logger.warning(f"❌ Audio validation failed for {section_id} on attempt {attempt}: "
                                     f"{validation_result.validation_details}")
                        
                        # Delete the problematic file before retry
                        if os.path.exists(output_path):
                            os.remove(output_path)
                            logger.debug(f"Deleted invalid audio file: {output_path}")
                        
                        if attempt < max_retries:
                            logger.info(f"Retrying audio generation for {section_id}...")
                            # Brief delay before retry
                            time.sleep(1)
                        continue
                else:
                    # No validation - accept the generated audio
                    return True
                    
            except Exception as e:
                logger.error(f"Error during audio generation for {section_id} on attempt {attempt}: {e}")
                
                # Clean up any partial file
                if os.path.exists(output_path):
                    os.remove(output_path)
                
                if attempt < max_retries:
                    logger.info(f"Retrying after error for {section_id}...")
                    time.sleep(2)  # Longer delay after error
                continue
        
        # All attempts failed
        logger.error(f"Failed to generate quality audio for {section_id} after {max_retries} attempts")
        return False
