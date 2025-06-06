#!/usr/bin/env python3
"""
Master Processing Script for YouTube Content Processing

This script orchestrates the complete workflow from YouTube URL or audio file
to final transcript analysis, integrating all existing processing components.

USAGE EXAMPLES:
    # Basic YouTube video processing (Stages 1-5: Download → Transcript → Analysis)
    python master_processor.py "https://www.youtube.com/watch?v=VIDEO_ID"
    
    # Process local audio file
    python master_processor.py "path/to/audio/file.mp3"
    
    # Full 10-stage pipeline (includes video generation)
    python master_processor.py --full-pipeline "https://www.youtube.com/watch?v=VIDEO_ID"
    
    # Generate podcast script and audio only
    python master_processor.py --generate-podcast --generate-audio "YOUTUBE_URL"
    
    # Use custom analysis rules
    python master_processor.py --analysis-rules "custom_rules.txt" "YOUTUBE_URL"
    
    # Batch processing from file
    python master_processor.py --batch urls.txt
    
    # Skip existing files and use verbose logging
    python master_processor.py --skip-existing --verbose "YOUTUBE_URL"
    
    # Dry run to see what would be processed
    python master_processor.py --dry-run "YOUTUBE_URL"

PIPELINE STAGES:
    Stages 1-4 (Default):   Input → Download → Transcript → Analysis
    Stages 5-6 (Podcast):   + Script Generation → Audio Generation  
    Stages 7-9 (Video):     + Video Clips → Timeline → Final Assembly

Created: June 3, 2025
Author: Master Processor Development Plan
"""

import sys
import os
import argparse
import logging
import time
import yaml
import uuid
import re
import json
import importlib.util
import subprocess
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add the Code directory to the path so we can import our modules
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# Import our utility modules
from Utils.progress_tracker import ProgressTracker, ProcessingStage
from Utils.error_handler import ErrorHandler, ErrorCategory
from Utils.file_organizer import FileOrganizer

# Import existing processing modules
try:
    from Extraction.youtube_audio_extractor import download_audio
    from Extraction.youtube_video_downloader import download_video as download_youtube_video
    from Extraction.youtube_url_utils import YouTubeUrlUtils
    from Extraction.audio_diarizer import diarize_audio, sanitize_audio_filename, extract_channel_name
    # Import from Content_Analysis directory
    import importlib.util
    content_analysis_path = os.path.join(script_dir, "Content_Analysis", "transcript_analyzer.py")
    spec = importlib.util.spec_from_file_location("transcript_analyzer", content_analysis_path)
    transcript_analyzer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(transcript_analyzer)
    # Extract the functions we need
    load_transcript = transcript_analyzer.load_transcript
    analyze_with_gemini = transcript_analyzer.analyze_with_gemini
    load_analysis_rules = transcript_analyzer.load_analysis_rules
    configure_gemini = transcript_analyzer.configure_gemini
      # Import podcast narrative generator
    podcast_generator_path = os.path.join(script_dir, "Content_Analysis", "podcast_narrative_generator.py")
    spec = importlib.util.spec_from_file_location("podcast_narrative_generator", podcast_generator_path)
    podcast_generator_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(podcast_generator_module)
    PodcastNarrativeGenerator = podcast_generator_module.PodcastNarrativeGenerator
      # Import TTS processor
    tts_processor_path = os.path.join(script_dir, "TTS", "core", "podcast_tts_processor.py")
    spec = importlib.util.spec_from_file_location("podcast_tts_processor", tts_processor_path)
    tts_processor_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tts_processor_module)
    PodcastTTSProcessor = tts_processor_module.PodcastTTSProcessor
    
    # Import video processing modules
    video_clipper_path = os.path.join(script_dir, "Video_Clipper", "analysis_video_clipper.py")
    spec = importlib.util.spec_from_file_location("analysis_video_clipper", video_clipper_path)
    video_clipper_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(video_clipper_module)
    AnalysisVideoClipper = video_clipper_module
    
    # Import video editor modules
    timeline_builder_path = os.path.join(script_dir, "Video_Editor", "timeline_builder.py")
    spec = importlib.util.spec_from_file_location("timeline_builder", timeline_builder_path)
    timeline_builder_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(timeline_builder_module)
    TimelineBuilder = timeline_builder_module.TimelineBuilder
    
    video_assembler_path = os.path.join(script_dir, "Video_Editor", "video_assembler.py")
    spec = importlib.util.spec_from_file_location("video_assembler", video_assembler_path)
    video_assembler_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(video_assembler_module)
    VideoAssembler = video_assembler_module.VideoAssembler
      # Import TTS generator from the new TTS module
    try:
        from TTS.core.tts_generator import SimpleTTSGenerator
    except ImportError:
        # Fallback to legacy import location
        tts_generator_path = os.path.join(script_dir, "Content_Analysis", "simple_tts_generator.py")
        if os.path.exists(tts_generator_path):
            spec = importlib.util.spec_from_file_location("simple_tts_generator", tts_generator_path)
            tts_generator_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(tts_generator_module)
            SimpleTTSGenerator = tts_generator_module.SimpleTTSGenerator
        else:
            SimpleTTSGenerator = None
except ImportError as e:
    print(f"Error importing processing modules: {e}")
    print("Make sure you're running this script from the Code directory.")
    sys.exit(1)


class MasterProcessor:
    """Main orchestrator for the YouTube content processing pipeline."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the master processor with configuration."""
        self.session_id = self._generate_session_id()
        self.config = self._load_config(config_path)
        self.progress_tracker = ProgressTracker()
        self.error_handler = ErrorHandler(
            max_retries=self.config['error_handling']['max_retries'],
            retry_delay=self.config['error_handling']['retry_delay']
        )
        self.file_organizer = FileOrganizer(self.config['paths'])
        self.logger = self._setup_logging()
        
        # Configure Gemini API
        self._configure_gemini_api()
        
        # Processing state
        self.current_input = ""
        self.processing_results = {}
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        short_uuid = str(uuid.uuid4())[:8]
        return f"{timestamp}_{short_uuid}"
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if config_path is None:
            config_path = os.path.join(script_dir, "Config", "default_config.yaml")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            # Expand relative paths
            base_dir = os.path.dirname(script_dir)  # Go up one level from Scripts
            for key, path in config['paths'].items():
                if not os.path.isabs(path):
                    config['paths'][key] = os.path.normpath(os.path.join(base_dir, path))
            
            return config
            
        except Exception as e:
            print(f"Error loading configuration from {config_path}: {e}")
            print("Using minimal default configuration.")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get minimal default configuration if config file fails to load."""
        base_dir = os.path.dirname(script_dir)
        return {
            'api': {
                'gemini_api_key': 'AIzaSyCsti0qnCEKOgzAnG_w41IfMNMxkyl3ysw',
                'huggingface_token': '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'
            },
            'processing': {
                'whisper_model': 'base',
                'batch_size': 4,
                'auto_gpu': True,
                'full_transcript_analysis': True
            },            'paths': {
                'audio_output': os.path.normpath(os.path.join(base_dir, 'Content', 'Audio', 'Rips')),
                'video_output': os.path.normpath(os.path.join(base_dir, 'Content', 'Video', 'Rips')),
                'transcript_output': os.path.normpath(os.path.join(base_dir, 'Content', 'Raw')),
                'analysis_rules': os.path.join(base_dir, 'Code', 'Content_Analysis', 'Rules', 'Joe_Rogan_selective_analysis_rules.txt')
            },
            'error_handling': {
                'max_retries': 3,
                'retry_delay': 5,
                'timeout': 3600
            },
            'logging': {
                'level': 'INFO',
                'file': 'master_processor.log',
                'console_output': True
            }
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration."""
        log_level = getattr(logging, self.config['logging']['level'].upper(), logging.INFO)
        
        # Create logger
        logger = logging.getLogger('master_processor')
        logger.setLevel(log_level)
        
        # Clear any existing handlers
        logger.handlers.clear()
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        simple_formatter = logging.Formatter('%(levelname)s: %(message)s')
        
        # File handler
        if self.config['logging']['file']:
            log_file = self.config['logging']['file']
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(log_level)
            file_handler.setFormatter(detailed_formatter)
            logger.addHandler(file_handler)
        
        # Console handler
        if self.config['logging']['console_output']:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.WARNING)  # Only warnings and errors to console
            console_handler.setFormatter(simple_formatter)
            logger.addHandler(console_handler)
        
        return logger
    
    def _configure_gemini_api(self):
        """Configure the Gemini API using the key from config or environment."""
        try:
            # Try to configure Gemini API
            if not configure_gemini():
                # If the imported configure_gemini fails, try using our config                import google.generativeai as genai
                api_key = self.config['api'].get('gemini_api_key')
                if api_key:
                    genai.configure(api_key=api_key)
                    self.logger.info("Gemini API configured successfully from config")
                else:
                    raise ValueError("No Gemini API key found in configuration")
            else:
                self.logger.info("Gemini API configured successfully")
        except Exception as e:
            self.logger.error(f"Failed to configure Gemini API: {e}")
            raise RuntimeError(f"Gemini API configuration failed: {e}")
    
    def _validate_youtube_url(self, url: str) -> bool:
        """Validate if the input is a valid YouTube URL."""
        try:
            return YouTubeUrlUtils.validate_youtube_url(url)
        except Exception:
            return False
    
    def _is_playlist_url(self, url: str) -> bool:
        """Check if the URL is a playlist URL."""
        try:
            return YouTubeUrlUtils.is_playlist_url(url)
        except Exception:
            return False
    
    def _validate_input(self, input_str: str) -> Dict[str, Any]:
        """Validate and categorize the input."""
        self.logger.info(f"Validating input: {input_str}")
        
        validation_result = {
            'valid': False,
            'type': 'unknown',
            'path': input_str,
            'warnings': [],
            'info': {}
        }
        
        # Check if it's a YouTube URL using YouTubeUrlUtils
        if self._validate_youtube_url(input_str):
            # Use YouTubeUrlUtils for comprehensive validation
            youtube_validation = YouTubeUrlUtils.validate_input(input_str)
            
            if youtube_validation['valid']:
                validation_result['valid'] = True
                validation_result['type'] = 'youtube_url'
                validation_result['info']['url'] = youtube_validation['sanitized_url']
                validation_result['info']['video_id'] = youtube_validation['video_id']
                validation_result['warnings'].extend(youtube_validation['warnings'])
                
                # Add timestamp info if available
                if youtube_validation.get('has_timestamp'):
                    validation_result['info']['timestamp'] = youtube_validation['timestamp']
            else:
                validation_result['warnings'].extend(youtube_validation['errors'])
                return validation_result
        
        # Check if it's a local audio file
        elif os.path.exists(input_str):
            audio_validation = self.file_organizer.validate_audio_file(input_str)
            validation_result['valid'] = audio_validation['valid']
            validation_result['type'] = 'local_audio'
            validation_result['info'] = audio_validation
            validation_result['warnings'].extend(audio_validation['warnings'])
        else:
            validation_result['warnings'].append(f"Input is neither a valid YouTube URL nor an existing audio file: {input_str}")
        
        return validation_result
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL."""
        try:
            return YouTubeUrlUtils.extract_video_id(url)
        except Exception:
            return None
    
    def _sanitize_youtube_url(self, url: str) -> str:
        """Sanitize YouTube URL by removing tracking parameters."""
        try:
            return YouTubeUrlUtils.sanitize_youtube_url(url)
        except Exception:
            return url
    
    def _is_safe_youtube_url(self, url: str) -> bool:
        """Check if URL is safe (no malicious patterns)."""
        try:
            return YouTubeUrlUtils.is_safe_youtube_url(url)
        except Exception:
            return False
    
    def _is_valid_youtube_domain(self, url: str) -> bool:
        """Validate YouTube domain."""
        try:
            return YouTubeUrlUtils.is_valid_youtube_domain(url)
        except Exception:
            return False
    
    def _is_valid_video_id(self, video_id: str) -> bool:
        """Validate video ID format."""
        try:
            return YouTubeUrlUtils.is_valid_video_id(video_id)
        except Exception:
            return False
    
    def _extract_timestamp(self, url: str) -> Optional[str]:
        """Extract timestamp parameter from YouTube URL."""
        try:
            return YouTubeUrlUtils.extract_timestamp(url)
        except Exception:
            return None
    
    def _extract_youtube_title(self, youtube_url: str) -> str:
        """Extract the title from a YouTube URL using yt-dlp."""
        try:
            get_title_command = [
                'yt-dlp',
                '--get-title',
                '--no-warnings',
                youtube_url
            ]
            process = subprocess.run(get_title_command, capture_output=True, text=True, check=True, encoding='utf-8')
            video_title = process.stdout.strip()
            self.logger.info(f"Extracted YouTube title: {video_title}")
            return video_title
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to extract YouTube title: {e}")
            raise ValueError(f"Could not extract title from YouTube URL: {youtube_url}")
        except Exception as e:
            self.logger.error(f"Unexpected error extracting YouTube title: {e}")
            raise ValueError(f"Unexpected error getting YouTube title: {str(e)}")
    
    def _create_episode_structure_early(self, youtube_url: str) -> Dict[str, str]:
        """Create the complete episode folder structure early using YouTube title."""
        try:
            # Extract title from YouTube
            video_title = self._extract_youtube_title(youtube_url)
            
            # Use the title to create episode structure
            dummy_audio_name = f"{video_title}.mp3"
            episode_paths = self.file_organizer.get_episode_paths(dummy_audio_name)
            
            self.logger.info(f"Created episode structure for: {video_title}")
            self.logger.info(f"Episode folder: {episode_paths['episode_folder']}")
              # Return the paths and title for later use
            return {
                'episode_title': video_title,
                'episode_paths': episode_paths
            }
        except Exception as e:
            self.logger.error(f"Failed to create early episode structure: {e}")
            raise
    
    def _stage_1_input_validation(self, youtube_url: str = None, audio_file: str = None) -> Dict[str, Any]:
        """Stage 1: Input Validation and Preparation."""
        self.progress_tracker.start_stage(ProcessingStage.INPUT_VALIDATION, estimated_duration=1)
        
        # Determine input string for processing
        input_str = youtube_url if youtube_url else audio_file if audio_file else None
        if not input_str:
            raise ValueError("Either youtube_url or audio_file must be provided")
            
        self.logger.info(f"Starting input validation for: {input_str}")
        
        try:            # Validate the input
            self.progress_tracker.update_stage_progress(30, "Validating input format")
            validation_result = self._validate_input(input_str)
            
            if not validation_result['valid']:
                # Don't raise exception for invalid inputs, return the validation result
                self.progress_tracker.update_stage_progress(100, "Input validation complete (invalid input)")
                self.progress_tracker.complete_stage(ProcessingStage.INPUT_VALIDATION)
                self.logger.warning(f"Input validation failed: {'; '.join(validation_result['warnings'])}")
                return validation_result
            
            # Add video_id to top level for YouTube URLs (for test compatibility)
            if validation_result['type'] == 'youtube_url' and 'video_id' in validation_result.get('info', {}):
                validation_result['video_id'] = validation_result['info']['video_id']
            
            # NEW: Create episode folder structure immediately for YouTube URLs
            if validation_result['type'] == 'youtube_url':
                self.progress_tracker.update_stage_progress(50, "Creating episode folder structure")
                try:
                    episode_structure = self._create_episode_structure_early(input_str)
                    validation_result['episode_structure'] = episode_structure
                    self.logger.info("Episode folder structure created before downloading")
                except Exception as e:
                    self.logger.warning(f"Could not create early episode structure: {e}")
                    # Don't fail validation, just log the warning
            
            # Check for existing outputs if skip-existing is enabled
            self.progress_tracker.update_stage_progress(70, "Checking existing outputs")
            
            # For local files, we can check immediately
            if validation_result['type'] == 'local_audio':
                existing_outputs = self.file_organizer.check_existing_outputs(input_str)
                validation_result['existing_outputs'] = existing_outputs
            
            self.progress_tracker.update_stage_progress(100, "Input validation complete")
            self.progress_tracker.complete_stage(ProcessingStage.INPUT_VALIDATION)
            
            self.logger.info(f"Input validation successful: {validation_result['type']}")
            return validation_result
            
        except Exception as e:
            self.progress_tracker.fail_stage(ProcessingStage.INPUT_VALIDATION, str(e))
            raise
    def _stage_2_audio_acquisition(self, input_info: Dict[str, Any]) -> Dict[str, str]:
        """Stage 2: Audio & Video Acquisition."""
        self.progress_tracker.start_stage(ProcessingStage.AUDIO_ACQUISITION, estimated_duration=120)
        self.logger.info("Starting audio and video acquisition")
        
        try:
            results = {}
            
            if input_info['type'] == 'youtube_url':
                # Download audio from YouTube
                self.progress_tracker.update_stage_progress(10, "Downloading audio from YouTube")
                  # Use retry mechanism for YouTube download
                audio_path = self.error_handler.retry_with_backoff(
                    download_audio,
                    input_info['info']['url'],
                    stage="audio_acquisition",
                    context="YouTube audio download"
                )
                
                if not audio_path or "Error" in audio_path or not os.path.exists(audio_path):
                    raise RuntimeError(f"YouTube audio download failed: {audio_path}")
                
                results['audio_path'] = audio_path
                
                # Download video if enabled in config (default: true)
                if self.config.get('video', {}).get('always_download_video', True):
                    self.progress_tracker.update_stage_progress(40, "Downloading video from YouTube")
                    try:
                        # Extract episode name from audio file for consistent naming
                        audio_basename = os.path.splitext(os.path.basename(audio_path))[0]
                        episode_folder = os.path.join(
                            self.config['paths']['video_output'],
                            audio_basename
                        )
                        
                        # Create episode folder if it doesn't exist
                        os.makedirs(episode_folder, exist_ok=True)
                        
                        # Download video with retry mechanism using the function
                        video_path = self.error_handler.retry_with_backoff(
                            download_youtube_video,
                            input_info['info']['url'],
                            stage="video_acquisition",
                            context="YouTube video download"
                        )
                        
                        if video_path and os.path.exists(video_path):
                            results['video_path'] = video_path
                            self.logger.info(f"Video downloaded successfully: {video_path}")
                        else:
                            self.logger.warning("Video download failed, continuing with audio-only processing")
                            
                    except Exception as e:
                        self.logger.warning(f"Video download failed: {e}, continuing with audio-only processing")
                    
                    self.progress_tracker.update_stage_progress(80, "Downloads complete")
                
                # Files are now downloaded directly to their episode structure, no organization needed
                self.progress_tracker.update_stage_progress(85, "Files ready in episode structure")
                self.logger.info("Audio and video files downloaded directly to episode Input folder")
                
            elif input_info['type'] == 'local_audio':
                # For local files, just validate and use the path
                audio_path = input_info['path']
                self.progress_tracker.update_stage_progress(50, "Validating local audio file")
                
                if not os.path.exists(audio_path):
                    raise FileNotFoundError(f"Local audio file not found: {audio_path}")
                
                results['audio_path'] = audio_path
                
                # Check for corresponding video file
                video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.webm']
                audio_base = os.path.splitext(audio_path)[0]
                
                for ext in video_extensions:
                    potential_video = audio_base + ext
                    if os.path.exists(potential_video):
                        results['video_path'] = potential_video
                        self.logger.info(f"Found corresponding video file: {potential_video}")
                        break
            
            else:
                raise ValueError(f"Unsupported input type: {input_info['type']}")
            
            # Final validation of audio file
            self.progress_tracker.update_stage_progress(90, "Final validation")
            audio_validation = self.file_organizer.validate_audio_file(results['audio_path'])
            
            if not audio_validation['valid']:
                raise ValueError(f"Invalid audio file: {'; '.join(audio_validation['warnings'])}")
            
            self.progress_tracker.update_stage_progress(100, "Audio and video acquisition complete")
            self.progress_tracker.complete_stage(ProcessingStage.AUDIO_ACQUISITION)
            
            # Log summary
            if 'video_path' in results:
                self.logger.info(f"Audio & Video acquisition successful:")
                self.logger.info(f"  Audio: {results['audio_path']}")
                self.logger.info(f"  Video: {results['video_path']}")
            else:
                self.logger.info(f"Audio acquisition successful: {results['audio_path']}")
            
            return results
            
        except Exception as e:
            self.progress_tracker.fail_stage(ProcessingStage.AUDIO_ACQUISITION, str(e))
            raise
    def _stage_3_transcript_generation(self, acquisition_results: Dict[str, str]) -> str:
        """Stage 3: Transcript Generation."""
        audio_path = acquisition_results['audio_path']
        self.progress_tracker.start_stage(ProcessingStage.TRANSCRIPT_GENERATION, estimated_duration=300)
        self.logger.info(f"Starting transcript generation for: {audio_path}")
        
        try:
            # Get organized output paths
            self.progress_tracker.update_stage_progress(5, "Organizing output paths")
            _, episode_folder, transcript_path = self.file_organizer.get_transcript_structure_paths(audio_path)
            
            # Check if transcript already exists
            if os.path.exists(transcript_path):
                self.logger.info(f"Transcript already exists: {transcript_path}")
                self.progress_tracker.update_stage_progress(100, "Using existing transcript")
                self.progress_tracker.complete_stage(ProcessingStage.TRANSCRIPT_GENERATION)
                return transcript_path
            
            # Prepare HuggingFace token
            self.progress_tracker.update_stage_progress(10, "Preparing diarization")
            hf_token = self.config['api'].get('huggingface_token')
            
            # Run transcript generation with retry
            self.progress_tracker.update_stage_progress(15, "Starting audio diarization")
            
            # Note: diarize_audio returns JSON string, not file path
            # We need to save it to the organized location
            transcript_json = self.error_handler.retry_with_backoff(
                diarize_audio,
                audio_path,
                hf_token,
                stage="transcript_generation",
                context="Audio diarization"            )
            
            self.progress_tracker.update_stage_progress(85, "Saving transcript")
            
            # Ensure the directory exists before saving
            transcript_dir = os.path.dirname(transcript_path)
            if not os.path.exists(transcript_dir):
                self.logger.info(f"Creating directory: {transcript_dir}")
                os.makedirs(transcript_dir, exist_ok=True)
            
            # Save the transcript to the organized location
            try:
                with open(transcript_path, 'w', encoding='utf-8') as f:
                    f.write(transcript_json)
                self.logger.info(f"Transcript saved to: {transcript_path}")
            except Exception as e:
                raise RuntimeError(f"Failed to save transcript: {e}")
            
            # Validate the transcript file
            self.progress_tracker.update_stage_progress(95, "Validating transcript")
            if not os.path.exists(transcript_path):
                raise RuntimeError(f"Transcript file was not created: {transcript_path}")
            
            # Quick validation of JSON content
            try:
                with open(transcript_path, 'r', encoding='utf-8') as f:
                    transcript_data = f.read()
                    if not transcript_data.strip():
                        raise ValueError("Transcript file is empty")
                    # Basic JSON validation will happen in the analysis stage
            except Exception as e:
                raise RuntimeError(f"Transcript validation failed: {e}")
            
            self.progress_tracker.update_stage_progress(100, "Transcript generation complete")
            self.progress_tracker.complete_stage(ProcessingStage.TRANSCRIPT_GENERATION)
            
            self.logger.info(f"Transcript generation successful: {transcript_path}")
            return transcript_path
            
        except Exception as e:
            self.progress_tracker.fail_stage(ProcessingStage.TRANSCRIPT_GENERATION, str(e))
            raise
    
    def _stage_4_content_analysis(self, transcript_path: str, analysis_rules_file: Optional[str] = None, audio_path: Optional[str] = None) -> str:
        """Stage 4: Content Analysis - NO CHUNKING."""
        self.progress_tracker.start_stage(ProcessingStage.CONTENT_ANALYSIS, estimated_duration=120)
        self.logger.info(f"Starting content analysis for: {transcript_path}")
        
        try:
            # Get analysis output path
            self.progress_tracker.update_stage_progress(5, "Preparing analysis")
            analysis_path = self.file_organizer.get_analysis_output_path(transcript_path)
            
            # Check if analysis already exists
            if os.path.exists(analysis_path):
                self.logger.info(f"Analysis already exists: {analysis_path}")
                self.progress_tracker.update_stage_progress(100, "Using existing analysis")
                self.progress_tracker.complete_stage(ProcessingStage.CONTENT_ANALYSIS)
                return analysis_path
            
            # Load transcript
            self.progress_tracker.update_stage_progress(10, "Loading transcript")
            transcript_text, metadata = load_transcript(transcript_path)
            
            if not transcript_text:
                raise ValueError(f"Failed to load transcript from: {transcript_path}")            # Auto-detect episode type and select appropriate rules
            self.progress_tracker.update_stage_progress(20, "Detecting episode type and loading analysis rules")
            
            # Use audio_path if available, otherwise extract from transcript path
            if audio_path:
                audio_filename = os.path.basename(audio_path)
            else:
                # Fallback: extract from transcript path
                transcript_dir = os.path.dirname(transcript_path)
                transcript_filename = os.path.basename(transcript_path)
                # Convert transcript filename back to likely audio filename
                audio_filename = transcript_filename.replace('.json', '').replace('_analysis', '')
            
            analysis_rules_file = self._detect_episode_type_and_rules(audio_filename, analysis_rules_file)
            analysis_rules = load_analysis_rules(analysis_rules_file)
            
            if not analysis_rules:
                raise ValueError("No analysis rules loaded")
            
            # CRITICAL: Perform analysis WITHOUT chunking - send full transcript
            self.progress_tracker.update_stage_progress(30, "Analyzing full transcript (no chunking)")
            self.logger.info(f"Sending full transcript to Gemini (length: {len(transcript_text)} characters)")
              # Use retry mechanism for API call
            analysis_result = self.error_handler.retry_with_backoff(
                analyze_with_gemini,
                transcript_text,  # Full transcript
                analysis_rules,
                stage="content_analysis",
                context="Gemini API call"
            )
            
            if not analysis_result:
                raise ValueError("Analysis returned empty result")
            
            # Save analysis results
            self.progress_tracker.update_stage_progress(90, "Saving analysis")
            
            # Create the full analysis output with header
            header = f"""TRANSCRIPT ANALYSIS REPORT
Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
Session ID: {self.session_id}
Source File: {os.path.basename(transcript_path)}
Analysis Rules Used:
{'-' * 40}
{analysis_rules}
{'-' * 40}

ANALYSIS RESULTS:
{'=' * 60}

"""
            
            full_output = header + analysis_result
            
            # Ensure the directory exists before saving
            analysis_dir = os.path.dirname(analysis_path)
            if not os.path.exists(analysis_dir):
                self.logger.info(f"Creating directory for analysis: {analysis_dir}")
                os.makedirs(analysis_dir, exist_ok=True)
            try:
                with open(analysis_path, 'w', encoding='utf-8') as f:
                    f.write(full_output)
                self.logger.info(f"Analysis saved to: {analysis_path}")
            except Exception as e:
                raise RuntimeError(f"Failed to save analysis: {e}")
            
            self.progress_tracker.update_stage_progress(100, "Content analysis complete")
            self.progress_tracker.complete_stage(ProcessingStage.CONTENT_ANALYSIS)
            
            self.logger.info(f"Content analysis successful: {analysis_path}")
            return analysis_path
            
        except Exception as e:
            self.progress_tracker.fail_stage(ProcessingStage.CONTENT_ANALYSIS, str(e))
            raise
    
    def _detect_episode_type_and_rules(self, audio_filename: str, custom_rules_file: Optional[str] = None) -> str:
        """
        Detect episode type and automatically select the appropriate analysis rules file.
        
        Args:
            audio_filename: Name of the audio file being processed
            custom_rules_file: User-specified custom rules file (takes precedence)
            
        Returns:
            Path to the appropriate analysis rules file
        """
        # If user specified custom rules, use those
        if custom_rules_file:
            if os.path.exists(custom_rules_file):
                self.logger.info(f"Using custom analysis rules: {custom_rules_file}")
                return custom_rules_file
            else:
                self.logger.warning(f"Custom rules file not found: {custom_rules_file}, falling back to auto-detection")
        
        # Extract base filename without extension
        base_name = os.path.splitext(os.path.basename(audio_filename))[0]        # Check for Joe Rogan episodes
        if "Joe Rogan Experience" in base_name:
            joe_rogan_rules = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 
                'Content_Analysis', 
                'Rules',
                'Joe_Rogan_selective_analysis_rules.txt'
            )
            if os.path.exists(joe_rogan_rules):
                self.logger.info(f"Detected Joe Rogan episode, using specialized rules: {joe_rogan_rules}")
                return joe_rogan_rules
            else:
                self.logger.warning(f"Joe Rogan rules file not found at {joe_rogan_rules}, using default rules")
          # For other episodes, use default rules
        default_rules = self.config['paths']['analysis_rules']
        self.logger.info(f"Using default analysis rules: {default_rules}")
        return default_rules
    
    def _stage_6_podcast_generation(self, analysis_path: str, episode_title: str, 
                                   template_name: str = "podcast_narrative_prompt.txt") -> Optional[str]:
        """Stage 6: Generate Podcast Script from Analysis."""
        self.progress_tracker.start_stage(ProcessingStage.PODCAST_GENERATION, estimated_duration=30)
        self.logger.info("Starting podcast script generation")
        
        try:
            # Initialize podcast generator
            self.progress_tracker.update_stage_progress(10, "Initializing podcast generator")
            generator = PodcastNarrativeGenerator()
            
            # Generate script
            self.progress_tracker.update_stage_progress(30, "Generating podcast script with Gemini")
            script_data = generator.generate_podcast_script(
                analysis_path, 
                episode_title, 
                template_name
            )            # Save script files
            self.progress_tracker.update_stage_progress(70, "Saving podcast script files")
            
            # Get the transcript path from analysis path to derive proper folder structure
            # analysis_path is in Processing folder, we need to get the corresponding transcript in Input folder
            analysis_dir = os.path.dirname(analysis_path)  # Processing folder
            episode_dir = os.path.dirname(analysis_dir)   # Episode folder
            input_dir = os.path.join(episode_dir, 'Input')
            
            # Extract base name and create transcript path
            analysis_basename = os.path.basename(analysis_path)
            base_name = analysis_basename.replace('_analysis.txt', '').replace('_analysis_analysis.txt', '')
            transcript_path = os.path.join(input_dir, f"{base_name}.json")
            
            # Use new folder structure - get Output/Scripts path
            script_output_path = self.file_organizer.get_podcast_script_output_path(
                transcript_path, 
                f"{base_name}_podcast_script"
            )
            
            json_path, txt_path = generator.save_podcast_script(script_data, script_output_path)
            
            # Log results
            self.progress_tracker.update_stage_progress(90, "Generating podcast summary")
            theme = script_data.get('narrative_theme', 'Unknown')
            selected_clips = len(script_data.get('selected_clips', []))
            
            self.logger.info(f"Podcast script generated successfully:")
            self.logger.info(f"  JSON Structure: {json_path}")
            self.logger.info(f"  Readable Script: {txt_path}")
            self.logger.info(f"  Narrative Theme: {theme}")
            self.logger.info(f"  Selected Clips: {selected_clips}")
            self.progress_tracker.update_stage_progress(100, "Podcast generation complete")
            self.progress_tracker.complete_stage(ProcessingStage.PODCAST_GENERATION)
            return str(json_path)
            
        except Exception as e:
            self.progress_tracker.fail_stage(ProcessingStage.PODCAST_GENERATION, str(e))
            self.logger.error(f"Podcast generation failed: {e}")
            return None
    def _stage_7_audio_generation(self, podcast_script_path: str, episode_title: str) -> Optional[str]:
        """Stage 7: Generate Audio from Podcast Script using TTS."""
        self.progress_tracker.start_stage(ProcessingStage.AUDIO_GENERATION, estimated_duration=60)
        self.logger.info("Starting audio generation from podcast script")
        
        try:
            # Initialize TTS processor
            self.progress_tracker.update_stage_progress(10, "Initializing TTS processor")
            
            # Use the new PodcastTTSProcessor if available, otherwise fallback to SimpleTTSGenerator
            if PodcastTTSProcessor:
                tts_processor = PodcastTTSProcessor()
                
                # Load podcast script
                self.progress_tracker.update_stage_progress(20, "Loading podcast script")
                  # Generate audio using the structured TTS processor
                self.progress_tracker.update_stage_progress(30, "Generating structured audio with TTS")
                
                audio_results = tts_processor.generate_podcast_audio(
                    tts_script_path=podcast_script_path
                )
                
                if audio_results and audio_results.get('successful_segments', 0) > 0:
                    output_dir = audio_results.get('output_directory')
                    generated_files = audio_results.get('generated_files', [])
                    successful_segments = audio_results.get('successful_segments', 0)
                    total_segments = audio_results.get('total_segments', 0)
                    
                    self.progress_tracker.update_stage_progress(90, "TTS generation complete")
                    self.logger.info(f"TTS audio generated successfully:")
                    self.logger.info(f"  Output Directory: {output_dir}")
                    self.logger.info(f"  Generated Files: {len(generated_files)}")
                    self.logger.info(f"  Success Rate: {successful_segments}/{total_segments}")
                    
                    self.progress_tracker.update_stage_progress(100, "Audio generation complete")
                    self.progress_tracker.complete_stage(ProcessingStage.AUDIO_GENERATION)
                    
                    return output_dir
                else:
                    raise Exception("TTS generation failed - no audio files created")
                    
            elif SimpleTTSGenerator:
                # Fallback to simple TTS generator
                self.progress_tracker.update_stage_progress(10, "Using fallback TTS generator")
                tts_generator = SimpleTTSGenerator()
                
                # Load podcast script
                self.progress_tracker.update_stage_progress(20, "Loading podcast script")
                with open(podcast_script_path, 'r', encoding='utf-8') as f:
                    script_data = json.load(f)
                
                # Extract readable script text
                if 'readable_script' in script_data:
                    script_text = script_data['readable_script']
                else:
                    # Fallback: construct from selected clips
                    clips = script_data.get('selected_clips', [])
                    script_text = f"# {script_data.get('narrative_theme', episode_title)}\n\n"
                    for clip in clips:
                        script_text += f"{clip.get('analysis', '')}\n\n"
                  # Generate audio
                self.progress_tracker.update_stage_progress(30, "Generating audio with fallback TTS")
                
                # Create output filename
                base_name = os.path.splitext(os.path.basename(podcast_script_path))[0]
                audio_filename = f"{base_name}_audio.wav"
                  # Generate audio using TTS
                audio_filename = f"{base_name}_audio.wav"
                success = tts_generator.generate_audio(
                    text=script_text,
                    output_filename=audio_filename,
                    voice_style="normal"
                )
                
                if success and os.path.exists(success):
                    # The generate_audio method returns the full path
                    audio_output_path = success
                    # Get file size for logging
                    file_size = os.path.getsize(audio_output_path) / (1024 * 1024)  # MB
                    
                    self.progress_tracker.update_stage_progress(90, "Audio generation complete")
                    self.logger.info(f"Audio generated successfully:")
                    self.logger.info(f"  Audio File: {audio_output_path}")
                    self.logger.info(f"  File Size: {file_size:.2f} MB")
                    
                    self.progress_tracker.update_stage_progress(100, "Audio generation complete")
                    self.progress_tracker.complete_stage(ProcessingStage.AUDIO_GENERATION)
                    
                    return audio_output_path
                else:
                    raise Exception("Audio generation failed - output file not created")
            else:
                raise Exception("No TTS generator available")
                
        except Exception as e:
            self.progress_tracker.fail_stage(ProcessingStage.AUDIO_GENERATION, str(e))
            self.logger.error(f"Audio generation failed: {e}")
            return None

    def _stage_8_video_clip_extraction(self, analysis_path: str, video_path: str, 
                                      podcast_script_path: Optional[str] = None) -> Optional[str]:
        """Stage 8: Extract Video Clips from Analysis Results."""
        self.progress_tracker.start_stage(ProcessingStage.VIDEO_CLIP_EXTRACTION, estimated_duration=120)
        self.logger.info("Starting video clip extraction")
        
        try:
            if not video_path or not os.path.exists(video_path):
                self.logger.warning("No video file available for clip extraction")
                self.progress_tracker.complete_stage(ProcessingStage.VIDEO_CLIP_EXTRACTION)
                return None
            
            # Extract clips using analysis_video_clipper
            self.progress_tracker.update_stage_progress(10, "Initializing video clipper")
            
            # Create output directory for clips
            video_episode_folder = os.path.dirname(video_path)
            clips_output_dir = os.path.join(video_episode_folder, "clips")
            os.makedirs(clips_output_dir, exist_ok=True)
            
            self.progress_tracker.update_stage_progress(30, "Extracting video clips")
            
            # Use the analysis_video_clipper module
            # Call the main extraction function with appropriate parameters
            extract_clips_result = self.error_handler.retry_with_backoff(
                AnalysisVideoClipper.extract_clips_from_analysis,
                analysis_path,
                video_path,
                clips_output_dir,
                start_buffer=self.config.get('video', {}).get('clip_extraction', {}).get('start_buffer_seconds', 3.0),
                end_buffer=self.config.get('video', {}).get('clip_extraction', {}).get('end_buffer_seconds', 0.0),
                stage="video_clip_extraction",
                context="Video clip extraction"
            )
            
            if extract_clips_result:
                clip_count = len([f for f in os.listdir(clips_output_dir) if f.endswith('.mp4')])
                
                self.progress_tracker.update_stage_progress(90, f"Extracted {clip_count} video clips")
                self.logger.info(f"Video clip extraction successful:")
                self.logger.info(f"  Clips Directory: {clips_output_dir}")
                self.logger.info(f"  Extracted Clips: {clip_count}")
                
                self.progress_tracker.update_stage_progress(100, "Video clip extraction complete")
                self.progress_tracker.complete_stage(ProcessingStage.VIDEO_CLIP_EXTRACTION)
                
                return clips_output_dir
            else:
                raise Exception("Video clip extraction failed")
                
        except Exception as e:
            self.progress_tracker.fail_stage(ProcessingStage.VIDEO_CLIP_EXTRACTION, str(e))
            self.logger.error(f"Video clip extraction failed: {e}")
            return None

    def _stage_9_video_timeline_building(self, podcast_script_path: str, audio_output_dir: str,
                                        clips_output_dir: str, episode_title: str) -> Optional[str]:
        """Stage 9: Build Video Timeline from Assets."""
        self.progress_tracker.start_stage(ProcessingStage.VIDEO_TIMELINE_BUILDING, estimated_duration=30)
        self.logger.info("Starting video timeline building")
        
        try:
            if not clips_output_dir or not os.path.exists(clips_output_dir):
                self.logger.warning("No video clips available for timeline building")
                self.progress_tracker.complete_stage(ProcessingStage.VIDEO_TIMELINE_BUILDING)
                return None
            
            # Initialize timeline builder
            self.progress_tracker.update_stage_progress(10, "Initializing timeline builder")
            timeline_builder = TimelineBuilder()
            
            # Build timeline from script and assets
            self.progress_tracker.update_stage_progress(30, "Building video timeline")
            
            timeline_result = timeline_builder.build_timeline_from_script(
                tts_script_path=podcast_script_path,
                episode_title=episode_title,
                audio_files_dir=audio_output_dir,
                video_clips_dir=clips_output_dir
            )
            
            if timeline_result and timeline_result.get('success', False):
                timeline_path = timeline_result.get('timeline_path')
                
                self.progress_tracker.update_stage_progress(90, "Timeline building complete")
                self.logger.info(f"Video timeline built successfully:")
                self.logger.info(f"  Timeline File: {timeline_path}")
                self.progress_tracker.update_stage_progress(100, "Video timeline building complete")
                self.progress_tracker.complete_stage(ProcessingStage.VIDEO_TIMELINE_BUILDING)
                
                return timeline_path
            else:
                raise Exception("Timeline building failed")
                
        except Exception as e:
            self.progress_tracker.fail_stage(ProcessingStage.VIDEO_TIMELINE_BUILDING, str(e))
            self.logger.error(f"Video timeline building failed: {e}")
            return None

    def _stage_9_final_video_assembly(self, timeline_path: str, episode_title: str) -> Optional[str]:
        """Stage 9: Assemble Final Video from Timeline."""
        self.progress_tracker.start_stage(ProcessingStage.FINAL_VIDEO_ASSEMBLY, estimated_duration=300)
        self.logger.info("Starting final video assembly")
        
        try:
            if not timeline_path or not os.path.exists(timeline_path):
                self.logger.warning("No timeline available for video assembly")
                self.progress_tracker.complete_stage(ProcessingStage.FINAL_VIDEO_ASSEMBLY)
                return None
            
            # Initialize video assembler
            self.progress_tracker.update_stage_progress(10, "Initializing video assembler")
            video_assembler = VideoAssembler()
            
            # Assemble final video
            self.progress_tracker.update_stage_progress(20, "Assembling final video")
            
            assembly_result = video_assembler.assemble_video_from_timeline(
                timeline_path=timeline_path,
                episode_title=episode_title,
                video_settings=self.config.get('video', {}).get('final_assembly', {})
            )
            
            if assembly_result and assembly_result.get('success', False):
                final_video_path = assembly_result.get('output_video_path')
                file_size = os.path.getsize(final_video_path) / (1024 * 1024 * 1024)  # GB
                
                self.progress_tracker.update_stage_progress(90, "Video assembly complete")
                self.logger.info(f"Final video assembled successfully:")
                self.logger.info(f"  Final Video: {final_video_path}")
                self.logger.info(f"  File Size: {file_size:.2f} GB")
                
                self.progress_tracker.update_stage_progress(100, "Final video assembly complete")
                self.progress_tracker.complete_stage(ProcessingStage.FINAL_VIDEO_ASSEMBLY)
                
                return final_video_path
            else:
                raise Exception("Video assembly failed")
        except Exception as e:
            self.progress_tracker.fail_stage(ProcessingStage.FINAL_VIDEO_ASSEMBLY, str(e))
            self.logger.error(f"Final video assembly failed: {e}")            
            return None
    
    def process_single_input(self, input_str: str, analysis_rules_file: Optional[str] = None, 
                           skip_existing: bool = False, generate_podcast: bool = False,
                           podcast_template: str = "podcast_narrative_prompt.txt",
                           generate_audio: bool = False, generate_video: bool = False,
                           full_pipeline: bool = False) -> Dict[str, str]:
        """Process a single input through the complete pipeline."""
        self.current_input = input_str
        self.logger.info(f"Starting processing for: {input_str}")
        
        try:
            # Stage 1: Input Validation
            # Determine if input is YouTube URL or audio file
            if self._validate_youtube_url(input_str):
                input_info = self._stage_1_input_validation(youtube_url=input_str, audio_file=None)
            else:
                input_info = self._stage_1_input_validation(youtube_url=None, audio_file=input_str)
            
            # Check skip_existing
            if skip_existing and input_info.get('existing_outputs', {}).get('analysis_exists', False):
                existing_analysis = input_info['existing_outputs']['analysis_path']
                self.logger.info(f"Skipping existing analysis: {existing_analysis}")
                return {
                    'transcript_path': input_info['existing_outputs']['transcript_path'],
                    'analysis_path': existing_analysis,
                    'skipped': True
                }
            
            # Stage 2: Audio & Video Acquisition
            acquisition_results = self._stage_2_audio_acquisition(input_info)
            audio_path = acquisition_results['audio_path']
            video_path = acquisition_results.get('video_path')
            
            # Stage 3: Transcript Generation
            transcript_path = self._stage_3_transcript_generation(acquisition_results)
              # Stage 4: Content Analysis (NO CHUNKING)
            # Pass audio_path for better episode type detection
            analysis_path = self._stage_4_content_analysis(transcript_path, analysis_rules_file, audio_path)
            
            # Build results dictionary
            final_results = {
                'audio_path': audio_path,
                'transcript_path': transcript_path,
                'analysis_path': analysis_path
            }
            
            # Add video path if available
            if video_path:
                final_results['video_path'] = video_path
            
            # Determine pipeline extent based on flags
            if full_pipeline:
                generate_podcast = True
                generate_audio = True
                generate_video = True
            elif generate_video:
                generate_podcast = True
                generate_audio = True
            
            # Stage 6: Podcast Generation (Optional)
            if generate_podcast:
                episode_title = os.path.splitext(os.path.basename(audio_path))[0]
                podcast_script_path = self._stage_6_podcast_generation(
                    final_results['analysis_path'], 
                    episode_title, 
                    podcast_template
                )
                if podcast_script_path:
                    final_results['podcast_script_path'] = podcast_script_path
                    
                    # Stage 7: Audio Generation (Optional, requires podcast script)
                    if generate_audio:
                        audio_output_dir = self._stage_7_audio_generation(
                            podcast_script_path,
                            episode_title
                        )
                        if audio_output_dir:
                            final_results['podcast_audio_path'] = audio_output_dir
                            
                            # Stage 8: Video Clip Extraction (Optional, requires video)
                            if generate_video and video_path:
                                clips_output_dir = self._stage_8_video_clip_extraction(
                                    final_results['analysis_path'],
                                    video_path,
                                    podcast_script_path
                                )
                                if clips_output_dir:
                                    final_results['video_clips_path'] = clips_output_dir
                                    
                                    # Stage 9: Video Timeline Building
                                    timeline_path = self._stage_9_video_timeline_building(
                                        podcast_script_path,
                                        audio_output_dir,
                                        clips_output_dir,
                                        episode_title
                                    )
                                    if timeline_path:
                                        final_results['timeline_path'] = timeline_path
                                          # Stage 9: Final Video Assembly
                                        final_video_path = self._stage_9_final_video_assembly(
                                            timeline_path,
                                            episode_title
                                        )
                                        if final_video_path:
                                            final_results['final_video_path'] = final_video_path
                            elif generate_video and not video_path:
                                self.logger.warning("Video generation requested but no video file available")
              # Create processing metadata summary after all stages complete
            try:
                summary_path = self.file_organizer.create_processing_summary(final_results, self.session_id)
                if summary_path:
                    final_results['processing_summary'] = summary_path
                    self.logger.info(f"Processing summary created: {summary_path}")
            except Exception as e:
                self.logger.warning(f"Failed to create processing summary: {e}")
            
            self.logger.info(f"Processing completed successfully for: {input_str}")
            return final_results
            
        except Exception as e:
            self.logger.error(f"Processing failed for {input_str}: {e}")
            raise
        finally:
            # Clean up any temporary files created during processing
            try:
                self.file_organizer.cleanup_temp_files()
                self.logger.debug("Temporary file cleanup completed")
            except Exception as e:
                self.logger.warning(f"Temporary file cleanup failed: {e}")
    
    def process_batch(self, input_file: str, analysis_rules_file: Optional[str] = None,
                     skip_existing: bool = False) -> List[Dict[str, Any]]:
        """Process multiple inputs from a file."""
        self.logger.info(f"Starting batch processing from: {input_file}")
        
        # Read input file
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                inputs = [line.strip() for line in f if line.strip()]
        except Exception as e:
            raise FileNotFoundError(f"Failed to read batch input file: {e}")
        
        if not inputs:
            raise ValueError(f"No valid inputs found in batch file: {input_file}")
        
        self.logger.info(f"Found {len(inputs)} inputs to process")
        
        results = []
        for i, input_str in enumerate(inputs, 1):
            print(f"\n{'='*60}")
            print(f"Processing {i}/{len(inputs)}: {input_str}")
            print(f"{'='*60}")
            
            try:
                result = self.process_single_input(input_str, analysis_rules_file, skip_existing)
                result['input'] = input_str
                result['success'] = True
                results.append(result)
                
            except Exception as e:
                self.logger.error(f"Failed to process {input_str}: {e}")
                results.append({
                    'input': input_str,
                    'success': False,
                    'error': str(e)
                })
        
        # Summary
        successful = sum(1 for r in results if r['success'])
        print(f"\n{'='*60}")
        print(f"BATCH PROCESSING COMPLETE")
        print(f"Successful: {successful}/{len(results)}")
        print(f"Failed: {len(results) - successful}/{len(results)}")
        print(f"{'='*60}")
        
        return results
    
    def print_progress(self):
        """Print current progress to console."""
        progress_display = self.progress_tracker.get_progress_display(self.current_input)
        print(f"\r{progress_display}", end="", flush=True)
  
    
    # ...existing code...
def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Master Processing Script for YouTube Content Processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python master_processor.py "https://youtube.com/watch?v=abc123"
  python master_processor.py "podcast_episode.mp3"
  python master_processor.py --batch urls.txt
  python master_processor.py "url" --analysis-rules custom_rules.txt
        """
    )
    
    # Positional argument
    parser.add_argument(
        'input',
        nargs='?',
        help='YouTube URL, audio file path, or batch file (with --batch)'
    )
    
    # Configuration options
    parser.add_argument(
        '--config',
        type=str,
        help='Configuration file path (default: config/default_config.yaml)'
    )
    
    parser.add_argument(
        '--analysis-rules',
        type=str,
        help='Custom analysis rules file path'
    )
    
    # Processing options
    parser.add_argument(
        '--whisper-model',
        choices=['base', 'small', 'medium', 'large'],
        help='Whisper model size override'
    )
    
    parser.add_argument(
        '--hf-token',
        type=str,
        help='HuggingFace token override'
    )
    
    parser.add_argument(
        '--gpu',
        action='store_true',
        help='Force GPU processing'
    )
    
    parser.add_argument(
        '--cpu',
        action='store_true',
        help='Force CPU processing'
    )
    
    # Workflow options
    parser.add_argument(
        '--batch',
        action='store_true',
        help='Process file containing multiple inputs'
    )
    
    parser.add_argument(
        '--skip-existing',
        action='store_true',
        help='Skip files that already have transcripts/analysis'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be processed without executing'
    )
    parser.add_argument(
        '--generate-podcast',
        action='store_true',
        help='Generate podcast script from analysis results'
    )
    
    parser.add_argument(
        '--podcast-template',
        type=str,
        default='podcast_narrative_prompt.txt',
        help='Prompt template to use for podcast generation'
    )
    
    parser.add_argument(
        '--generate-audio',
        action='store_true',
        help='Generate audio from podcast script using TTS (requires --generate-podcast)'
    )
    
    # Video processing options
    parser.add_argument(
        '--generate-video',
        action='store_true',
        help='Generate video from podcast script and analysis (enables full pipeline: Stages 1-10)'
    )
    
    parser.add_argument(
        '--full-pipeline',
        action='store_true',
        help='Run complete 10-stage pipeline including video generation'
    )
    
    return parser


def main():
    """Main entry point for the master processor."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Validate arguments
    if not args.input:
        parser.print_help()
        sys.exit(1)
    
    if args.gpu and args.cpu:
        print("Error: Cannot specify both --gpu and --cpu")
        sys.exit(1)
    if args.generate_audio and not args.generate_podcast:
        print("Error: --generate-audio requires --generate-podcast to be enabled")
        sys.exit(1)
    
    if args.generate_video and not args.generate_podcast:
        print("Error: --generate-video requires --generate-podcast to be enabled")
        sys.exit(1)
    
    if args.full_pipeline:
        # Full pipeline implies all generation options
        args.generate_podcast = True
        args.generate_audio = True
        args.generate_video = True
    
    try:
        # Initialize processor
        processor = MasterProcessor(config_path=args.config)
          # Apply command line overrides
        if args.whisper_model:
            processor.config['processing']['whisper_model'] = args.whisper_model
        
        if args.hf_token:
            processor.config['api']['huggingface_token'] = args.hf_token
        
        if args.verbose:
            processor.config['logging']['level'] = 'DEBUG'
            processor.logger.setLevel(logging.DEBUG)
        
        print(f">> Master Processor Starting")
        print(f"Session ID: {processor.session_id}")
        print(f"Configuration: {args.config or 'default'}")
        print("")
        
        # Process inputs
        if args.batch:
            if args.dry_run:
                print("DRY RUN: Would process batch file:", args.input)
                sys.exit(0)
            results = processor.process_batch(
                args.input,
                args.analysis_rules,
                args.skip_existing
            )
            
        else:
            if args.dry_run:
                print("DRY RUN: Would process input:", args.input)
                sys.exit(0)
            
            result = processor.process_single_input(
                args.input,
                args.analysis_rules,
                args.skip_existing,
                args.generate_podcast,
                args.podcast_template,
                args.generate_audio,
                args.generate_video,
                args.full_pipeline            )
            print("\n[SUCCESS] Processing Complete!")
            print(f"Transcript: {result['transcript_path']}")
            print(f"Analysis: {result['analysis_path']}")
            if 'podcast_script_path' in result:
                print(f"Podcast Script: {result['podcast_script_path']}")
            if 'podcast_audio_path' in result:
                print(f"Podcast Audio: {result['podcast_audio_path']}")
            if 'video_clips_path' in result:
                print(f"Video Clips: {result['video_clips_path']}")
            if 'timeline_path' in result:
                print(f"Timeline: {result['timeline_path']}")
            if 'final_video_path' in result:
                print(f"[VIDEO] Final Video: {result['final_video_path']}")
        
        # Show final progress
        print("\n" + processor.progress_tracker.get_progress_display())
        
        # Show error summary if any errors occurred
        error_summary = processor.error_handler.get_error_summary()
        if error_summary['total_errors'] > 0:
            print("\n[WARNING] Errors occurred during processing:")
            print(processor.error_handler.format_error_report())
        
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Processing interrupted by user")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n[ERROR] Fatal error: {e}")
        logging.getLogger().error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
