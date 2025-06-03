#!/usr/bin/env python3
"""
Master Processing Script for YouTube Content Processing

This script orchestrates the complete workflow from YouTube URL or audio file
to final transcript analysis, integrating all existing processing components.

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
except ImportError as e:
    print(f"Error importing processing modules: {e}")
    print("Make sure you're running this script from the Scripts directory.")
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
                'audio_output': os.path.normpath(os.path.join(base_dir, 'Audio Rips')),
                'transcript_output': os.path.normpath(os.path.join(base_dir, 'Transcripts')),
                'analysis_rules': os.path.join(base_dir, 'Scripts', 'Content Analysis', 'AnalysisRules.txt')
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
                # If the imported configure_gemini fails, try using our config
                import google.generativeai as genai
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
        youtube_patterns = [
            r'https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
            r'https?://youtu\.be/[\w-]+',
            r'https?://(?:www\.)?youtube\.com/embed/[\w-]+',
            r'^[\w-]{11}$'  # Direct video ID
        ]
        
        return any(re.match(pattern, url) for pattern in youtube_patterns)
    
    def _is_playlist_url(self, url: str) -> bool:
        """Check if the URL is a playlist URL."""
        return 'playlist' in url.lower() or 'list=' in url
    
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
        
        # Check if it's a YouTube URL
        if self._validate_youtube_url(input_str):
            if self._is_playlist_url(input_str):
                validation_result['warnings'].append("Playlist URLs are not yet supported. Please provide individual video URLs.")
                return validation_result
            
            validation_result['valid'] = True
            validation_result['type'] = 'youtube_url'
            validation_result['info']['url'] = input_str
        
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
    
    def _stage_1_input_validation(self, input_str: str) -> Dict[str, Any]:
        """Stage 1: Input Validation and Preparation."""
        self.progress_tracker.start_stage(ProcessingStage.INPUT_VALIDATION, estimated_duration=1)
        self.logger.info(f"Starting input validation for: {input_str}")
        
        try:
            # Validate the input
            self.progress_tracker.update_stage_progress(30, "Validating input format")
            validation_result = self._validate_input(input_str)
            
            if not validation_result['valid']:
                raise ValueError(f"Invalid input: {'; '.join(validation_result['warnings'])}")
            
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
    
    def _stage_2_audio_acquisition(self, input_info: Dict[str, Any]) -> str:
        """Stage 2: Audio Acquisition."""
        self.progress_tracker.start_stage(ProcessingStage.AUDIO_ACQUISITION, estimated_duration=60)
        self.logger.info("Starting audio acquisition")
        
        try:
            if input_info['type'] == 'youtube_url':
                # Download audio from YouTube
                self.progress_tracker.update_stage_progress(10, "Downloading audio from YouTube")
                
                # Use retry mechanism for YouTube download
                audio_path = self.error_handler.retry_with_backoff(
                    download_audio,
                    input_info['info']['url'],
                    stage="audio_acquisition",
                    context="YouTube download"
                )
                
                self.progress_tracker.update_stage_progress(90, "Download complete")
                
                if not audio_path or "Error" in audio_path or not os.path.exists(audio_path):
                    raise RuntimeError(f"YouTube download failed: {audio_path}")
                
            elif input_info['type'] == 'local_audio':
                # For local files, just validate and use the path
                audio_path = input_info['path']
                self.progress_tracker.update_stage_progress(50, "Validating local audio file")
                
                if not os.path.exists(audio_path):
                    raise FileNotFoundError(f"Local audio file not found: {audio_path}")
            
            else:
                raise ValueError(f"Unsupported input type: {input_info['type']}")
            
            # Final validation of audio file
            self.progress_tracker.update_stage_progress(95, "Final validation")
            audio_validation = self.file_organizer.validate_audio_file(audio_path)
            
            if not audio_validation['valid']:
                raise ValueError(f"Invalid audio file: {'; '.join(audio_validation['warnings'])}")
            
            self.progress_tracker.update_stage_progress(100, "Audio acquisition complete")
            self.progress_tracker.complete_stage(ProcessingStage.AUDIO_ACQUISITION)
            
            self.logger.info(f"Audio acquisition successful: {audio_path}")
            return audio_path
            
        except Exception as e:
            self.progress_tracker.fail_stage(ProcessingStage.AUDIO_ACQUISITION, str(e))
            raise
    
    def _stage_3_transcript_generation(self, audio_path: str) -> str:
        """Stage 3: Transcript Generation."""
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
                chunk_number=None,  # No chunking
                total_chunks=None,  # No chunking
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
    
    def _stage_5_file_organization(self, results: Dict[str, str]) -> Dict[str, str]:
        """Stage 5: File Organization and Cleanup."""
        self.progress_tracker.start_stage(ProcessingStage.FILE_ORGANIZATION, estimated_duration=5)
        self.logger.info("Starting file organization and cleanup")
        
        try:
            # Validate all output files exist
            self.progress_tracker.update_stage_progress(20, "Validating outputs")
            
            required_files = ['transcript_path', 'analysis_path']
            for file_key in required_files:
                if file_key not in results:
                    raise ValueError(f"Missing required output: {file_key}")
                
                file_path = results[file_key]
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"Expected output file not found: {file_path}")
            
            # Create processing metadata
            self.progress_tracker.update_stage_progress(50, "Creating metadata")
            
            # Get episode folder for metadata
            episode_folder = os.path.dirname(results['transcript_path'])
            
            processing_metadata = {
                'session_id': self.session_id,
                'timestamp': time.time(),
                'input': self.current_input,
                'outputs': results,
                'config_used': {
                    'whisper_model': self.config['processing']['whisper_model'],
                    'full_transcript_analysis': self.config['processing']['full_transcript_analysis']
                }            }
            
            metadata_path = os.path.join(episode_folder, f"processing_metadata_{self.session_id}.json")
            
            # Ensure the episode folder exists before saving metadata
            if not os.path.exists(episode_folder):
                self.logger.info(f"Creating episode folder for metadata: {episode_folder}")
                os.makedirs(episode_folder, exist_ok=True)
            
            try:
                import json
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(processing_metadata, f, indent=2)
                results['metadata_path'] = metadata_path
            except Exception as e:
                self.logger.warning(f"Failed to create metadata file: {e}")
            
            # Cleanup temporary files
            self.progress_tracker.update_stage_progress(80, "Cleaning up temporary files")
            self.file_organizer.cleanup_temp_files()
            
            # Final validation
            self.progress_tracker.update_stage_progress(95, "Final validation")
            
            # Generate summary
            transcript_size = os.path.getsize(results['transcript_path']) / 1024  # KB
            analysis_size = os.path.getsize(results['analysis_path']) / 1024    # KB
            
            self.logger.info(f"Processing complete:")
            self.logger.info(f"  Transcript: {results['transcript_path']} ({transcript_size:.1f} KB)")
            self.logger.info(f"  Analysis: {results['analysis_path']} ({analysis_size:.1f} KB)")
            
            self.progress_tracker.update_stage_progress(100, "File organization complete")
            self.progress_tracker.complete_stage(ProcessingStage.FILE_ORGANIZATION)
            
            return results
            
        except Exception as e:
            self.progress_tracker.fail_stage(ProcessingStage.FILE_ORGANIZATION, str(e))
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
        base_name = os.path.splitext(os.path.basename(audio_filename))[0]
        # Check for Joe Rogan episodes
        if "Joe Rogan Experience" in base_name:
            joe_rogan_rules = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 
                'Content_Analysis', 
                'JoeRoganAnalysisRules.txt'
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
            )
            
            # Save script files
            self.progress_tracker.update_stage_progress(70, "Saving podcast script files")
            episode_folder = os.path.dirname(analysis_path)
            base_name = os.path.splitext(os.path.basename(analysis_path))[0].replace('_analysis_analysis', '')
            script_base_path = os.path.join(episode_folder, f"{base_name}_podcast_script")
            
            json_path, txt_path = generator.save_podcast_script(script_data, script_base_path)
            
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
    
    def process_single_input(self, input_str: str, analysis_rules_file: Optional[str] = None, 
                           skip_existing: bool = False, generate_podcast: bool = False,
                           podcast_template: str = "podcast_narrative_prompt.txt") -> Dict[str, str]:
        """Process a single input through the complete pipeline."""
        self.current_input = input_str
        self.logger.info(f"Starting processing for: {input_str}")
        
        try:
            # Stage 1: Input Validation
            input_info = self._stage_1_input_validation(input_str)
            
            # Check skip_existing
            if skip_existing and input_info.get('existing_outputs', {}).get('analysis_exists', False):
                existing_analysis = input_info['existing_outputs']['analysis_path']
                self.logger.info(f"Skipping existing analysis: {existing_analysis}")
                return {
                    'transcript_path': input_info['existing_outputs']['transcript_path'],
                    'analysis_path': existing_analysis,
                    'skipped': True
                }
            
            # Stage 2: Audio Acquisition
            audio_path = self._stage_2_audio_acquisition(input_info)
            
            # Stage 3: Transcript Generation
            transcript_path = self._stage_3_transcript_generation(audio_path)
              # Stage 4: Content Analysis (NO CHUNKING)
            # Pass audio_path for better episode type detection
            analysis_path = self._stage_4_content_analysis(transcript_path, analysis_rules_file, audio_path)
            
            # Stage 5: File Organization
            results = {
                'audio_path': audio_path,
                'transcript_path': transcript_path,
                'analysis_path': analysis_path
            }
            
            final_results = self._stage_5_file_organization(results)
            
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
            
            self.logger.info(f"Processing completed successfully for: {input_str}")
            return final_results
            
        except Exception as e:
            self.logger.error(f"Processing failed for {input_str}: {e}")
            raise
    
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
            )
            
            # Save script files
            self.progress_tracker.update_stage_progress(70, "Saving podcast script files")
            episode_folder = os.path.dirname(analysis_path)
            base_name = os.path.splitext(os.path.basename(analysis_path))[0].replace('_analysis_analysis', '')
            script_base_path = os.path.join(episode_folder, f"{base_name}_podcast_script")
            
            json_path, txt_path = generator.save_podcast_script(script_data, script_base_path)
            
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
        
        print(f"🚀 Master Processor Starting")
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
                args.podcast_template
            )
            
            print("\n🎉 Processing Complete!")
            print(f"Transcript: {result['transcript_path']}")
            print(f"Analysis: {result['analysis_path']}")
            if 'podcast_script_path' in result:
                print(f"Podcast Script: {result['podcast_script_path']}")
        
        # Show final progress
        print("\n" + processor.progress_tracker.get_progress_display())
        
        # Show error summary if any errors occurred
        error_summary = processor.error_handler.get_error_summary()
        if error_summary['total_errors'] > 0:
            print("\n⚠️ Errors occurred during processing:")
            print(processor.error_handler.format_error_report())
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Processing interrupted by user")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        logging.getLogger().error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
