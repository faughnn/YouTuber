"""
Master Processor V2: Pipeline-Driven Orchestrator
=================================================

A clean, streamlined orchestrator that focuses purely on coordination and delegation,
serving the 7-stage YouTube video processing pipeline through direct module calls.

Architecture Philosophy:
- Orchestrator adapts to working modules, not the reverse
- Direct function calls without abstraction layers
- Pure delegation pattern with minimal orchestration logic
- Working modules define interaction patterns
- Enhanced Rich logging for beautiful, organized output

Created: June 10, 2025
Agent: Pipeline-Driven Implementation Agent
Task Reference: Phase 2, Task 2.1 - Pipeline-Driven Orchestrator Foundation
Enhanced: Rich logging system integration

USAGE EXAMPLES
==============

1. Command Line Usage:
   
   # Full pipeline (all 7 stages) - YouTube URL to final video
   python master_processor_v2.py --full-pipeline "https://www.youtube.com/watch?v=example"
   
   # Audio-only pipeline (stages 1-5) - Creates podcast-style audio with ElevenLabs TTS
   python master_processor_v2.py --audio-only "https://www.youtube.com/watch?v=example" --tts-provider elevenlabs
   
   # Script-only pipeline (stages 1-4) - Generates narrative script only
   python master_processor_v2.py --script-only "https://www.youtube.com/watch?v=example"
   
   # Using custom configuration file
   python master_processor_v2.py --full-pipeline "https://www.youtube.com/watch?v=example" --config "path/to/config.yaml"

2. Programmatic Usage:

   from master_processor_v2 import MasterProcessorV2
   
   # Initialize with default configuration
   processor = MasterProcessorV2()
   
   # Or initialize with custom configuration
   processor = MasterProcessorV2(config_path="path/to/custom_config.yaml")
   
   # Execute full pipeline
   youtube_url = "https://www.youtube.com/watch?v=example"
   final_video_path = processor.process_full_pipeline(youtube_url, "chatterbox")  # or "elevenlabs"
   print(f"Final video created: {final_video_path}")
   
   # Execute audio-only pipeline with ElevenLabs TTS
   results = processor.process_audio_only(youtube_url, "elevenlabs")
   print(f"Generated audio: {results['audio_path']}")
   print(f"Generated script: {results['script_path']}")
   
   # Execute script-only pipeline
   script_path = processor.process_until_script(youtube_url)
   print(f"Generated script: {script_path}")

3. Individual Stage Execution:

   # For custom workflows, you can execute individual stages
   processor = MasterProcessorV2()
   
   # Stage 1: Media Extraction
   media_files = processor._stage_1_media_extraction(youtube_url)
   audio_path = media_files['audio_path']
   video_path = media_files['video_path']
   
   # Stage 2: Transcript Generation
   transcript_path = processor._stage_2_transcript_generation(audio_path)
   
   # Stage 3: Content Analysis
   analysis_path = processor._stage_3_content_analysis(transcript_path)
   
   # Stage 4: Narrative Generation
   script_path = processor._stage_4_narrative_generation(analysis_path)
   
   # Stage 5: Audio Generation
   generated_audio = processor._stage_5_audio_generation(script_path, "chatterbox")  # or "elevenlabs"
   
   # Stage 6: Video Clipping
   clips_info = processor._stage_6_video_clipping(script_path, video_path)
   
   # Stage 7: Video Compilation
   final_video = processor._stage_7_video_compilation(generated_audio, clips_info)

4. Error Handling and Logging:

   import logging
   
   # Set up logging to see detailed pipeline execution
   logging.basicConfig(level=logging.INFO)
   
   try:
       processor = MasterProcessorV2()
       result = processor.process_full_pipeline(youtube_url)
       print(f"Success! Session ID: {processor.session_id}")
       
   except Exception as e:
       print(f"Pipeline failed: {e}")
       # Check log file at: Code/Config/master_processor_v2.log

5. Configuration Management:

   # Default configuration is loaded from: Code/Config/default_config.yaml
   # You can override paths, API keys, and processing parameters
   
   # Example custom configuration:
   custom_config = {
       'paths': {
           'base_output_dir': 'C:/MyVideos/YouTuber_Output',
           'content_dir': 'C:/MyVideos/Content'
       },
       'gemini_api_key': 'your-api-key-here',
       'tts_settings': {
           'voice': 'en-US-Studio-O',
           'speed': 1.0
       }
   }

6. Output Structure:

   Each processing session creates an organized directory structure:
   
   Content/
   └── Episode_Title_YYYYMMDD_HHMMSS/
       ├── Input/              # Downloaded audio and video files
       ├── Processing/         # Intermediate processing files
       │   ├── original_audio_transcript.json
       │   ├── content_analysis.json
       │   └── narrative_script.json
       ├── Generated/          # Generated audio files
       │   └── generated_audio.wav
       ├── Clips/              # Video clips extracted from original
       └── Output/             # Final compiled video
           └── final_video.mp4

PIPELINE STAGES OVERVIEW
========================

Stage 1: Media Extraction
- Downloads audio (MP3) and video (MP4) from YouTube URL
- Creates organized episode directory structure
- Validates download integrity

Stage 2: Transcript Generation  
- Performs speaker diarization on audio
- Generates timestamped transcript with speaker labels
- Outputs structured JSON transcript

Stage 3: Content Analysis
- Analyzes transcript using Google Gemini AI
- Extracts key themes, topics, and insights
- Identifies compelling moments for video clips

Stage 4: Narrative Generation
- Creates engaging podcast-style narrative script
- Structures content for audio presentation
- Includes timing and emphasis instructions

Stage 5: Audio Generation
- Converts script to speech using Google TTS
- Handles text chunking and audio concatenation
- Manages silence detection and cleanup

Stage 6: Video Clipping
- Extracts video segments based on content analysis
- Synchronizes clips with narrative timing
- Prepares clips for final compilation

Stage 7: Video Compilation
- Combines generated audio with video clips
- Creates final polished video output
- Handles timing synchronization and transitions
"""

import os
import sys
import time
import yaml
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Union, Optional

# Enhanced logging system
from Utils.enhanced_pipeline_logger import get_enhanced_logger, LogLevel
from Utils.tts_operation_logger import create_tts_logger
from Utils.video_operation_logger import create_video_logger

# ============================================================================
# DIRECT WORKING MODULE IMPORTS - No abstraction layers
# ============================================================================

# Stage 1: Media Extraction - Direct imports
from Extraction.youtube_audio_extractor import download_audio
from Extraction.youtube_video_downloader import download_video, get_video_metadata

# Stage 2: Transcript Generation - Direct import
from Extraction.audio_diarizer import diarize_audio

# Stage 3: Content Analysis - Direct import
from Content_Analysis.transcript_analyzer import analyze_with_gemini_file_upload

# Stage 4: Narrative Generation - Direct import
from Content_Analysis.podcast_narrative_generator import NarrativeCreatorGenerator

# Stage 5: Audio Generation - Direct import  
from Chatterbox.simple_tts_engine import SimpleTTSEngine
from ElevenLabs.elevenlabs_tts_engine import ElevenLabsTTSEngine

# Stage 6: Video Clipping - Direct import
from Video_Clipper.integration import extract_clips_from_script

# Stage 7: Video Compilation - Direct import
from Video_Compilator import SimpleCompiler

# Utility imports - Direct usage
from Utils.file_organizer import FileOrganizer
from Utils.logger_factory import get_pipeline_logger
from Utils.name_extractor import NameExtractor
from Utils.config_manager import get_config
from Utils.user_verification import UserVerification


class MasterProcessorV2:
    """
    Pipeline-driven orchestrator serving working modules directly.
    
    Core Principle: Orchestrator adapts to working module interfaces,
    not the reverse. All 7 stages implemented as direct calls to 
    working modules without abstraction layers.
    """
    
    def __init__(self, config_path: Optional[str] = None, verbosity: LogLevel = LogLevel.NORMAL):
        """
        Initialize orchestrator with enhanced logging system.
        
        Args:
            config_path: Path to configuration file (optional)
            verbosity: Logging verbosity level
        """
        # Load configuration directly - no complex config abstraction
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()
        
        # Setup enhanced logging system
        self.enhanced_logger = get_enhanced_logger(verbosity)
        self.tts_logger = create_tts_logger(self.enhanced_logger)
        self.video_logger = create_video_logger(self.enhanced_logger)
        
        # Keep legacy logger for compatibility
        self.logger = self._setup_simple_logging()
        
        # Initialize FileOrganizer directly - no path logic in orchestrator
        self.file_organizer = FileOrganizer(self.config['paths'])
        
        # Session management for tracking
        self.session_id = self._generate_session_id()
        self.episode_dir = None
        
        self.enhanced_logger.info(f"MasterProcessorV2 initialized - Session: {self.session_id}")
        self.enhanced_logger.info(f"Configuration loaded from: {self.config_path}")
        # Use episode_base instead of base_output_dir which doesn't exist in current config
        base_dir = self.config['paths'].get('base_output_dir', self.config['paths']['episode_base'])
        self.enhanced_logger.info(f"Content directory: {base_dir}")
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, "Config", "default_config.yaml")
    
    def _load_config(self) -> Dict:
        """
        Simple YAML configuration loading - no complex config abstraction.
        
        Returns:
            Dict: Configuration dictionary
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Expand relative paths to absolute paths
            script_dir = os.path.dirname(os.path.abspath(__file__))
            base_dir = os.path.dirname(script_dir)  # YouTuber directory
            
            # Resolve relative paths in config
            if 'paths' in config:
                for key, path in config['paths'].items():
                    if not os.path.isabs(path):
                        config['paths'][key] = os.path.normpath(os.path.join(base_dir, path))
            
            return config
            
        except Exception as e:
            print(f"Error loading configuration: {e}")
            raise Exception(f"Configuration loading failed: {e}")
    
    def _setup_simple_logging(self) -> logging.Logger:
        """
        Basic logging setup - no complex logging abstraction.
        
        Returns:
            logging.Logger: Configured logger
        """
        logger = logging.getLogger('master_processor_v2')
        logger.setLevel(logging.INFO)
        
        # Avoid duplicate handlers
        if logger.handlers:
            return logger
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'        )
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)
          # File handler
        log_file = os.path.join(os.path.dirname(self.config_path), "master_processor_v2.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(console_format)
        logger.addHandler(file_handler)
        
        return logger
    def _generate_session_id(self) -> str:
        """
        Generate unique session identifier for tracking pipeline execution.
        
        Returns:
            str: Unique session ID in format 'session_YYYYMMDD_HHMMSS'
            
        Notes:
            - Used for logging and episode directory organization
            - Provides timestamp-based tracking for debugging
            - Each processor instance gets unique session ID at initialization
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"session_{timestamp}"

    # ========================================================================
    # STAGE METHOD TEMPLATES - Direct delegation patterns
    # ========================================================================
    
    def _stage_1_media_extraction(self, url: str) -> Dict[str, str]:
        """
        Stage 1: Enhanced media extraction with intelligent name extraction and path management.
        
        New workflow:
        1. Fetch metadata without downloading
        2. Extract host/guest names using NameExtractor
        3. User verification (if configured or no guest found)
        4. Create proper directory structure
        5. Download directly to correct paths
        
        Args:
            url: YouTube URL
            
        Returns:
            Dict: Audio and video file paths with episode info
        """
        self.enhanced_logger.info(f"YouTube URL: {url}")
        
        try:
            # Step 1: Metadata-First Fetch
            self.enhanced_logger.info("📋 Fetching video metadata...")
            with self.enhanced_logger.spinner_context("Getting video information..."):
                metadata = get_video_metadata(url)
            
            if not metadata:
                raise Exception("Failed to fetch video metadata")
            
            title = metadata.get('title', 'Unknown Title')
            uploader = metadata.get('uploader', 'Unknown Channel')
            
            self.enhanced_logger.info(f"📺 Title: {title}")
            self.enhanced_logger.info(f"📢 Channel: {uploader}")
            
            # Step 2: Name Extraction
            self.enhanced_logger.info("🔍 Extracting host and guest names...")
            name_extractor = NameExtractor(title, uploader)
            extracted_names = name_extractor.extract()
            
            # Log extraction results
            rule_used = extracted_names.get('rule_used', 'unknown')
            self.enhanced_logger.info(f"Name extraction: Host='{extracted_names['host']}' Guest='{extracted_names['guest']}' (Rule: {rule_used})")
            
            # Step 3: Conditional User Verification
            config = get_config()
            should_verify = (
                config.get('settings', {}).get('prompt_for_verification', False) or
                not extracted_names['guest'] or 
                extracted_names['guest'] == 'No Guest'
            )
            
            if should_verify:
                self.enhanced_logger.info("🔍 User verification required...")
                if not extracted_names['guest'] or extracted_names['guest'] == 'No Guest':
                    self.enhanced_logger.warning("Name extraction failed, triggered verification")
                
                verified_names = UserVerification.prompt_for_verification(extracted_names, metadata)
                
                # Log any corrections made
                if verified_names['host'] != extracted_names['host'] or verified_names['guest'] != extracted_names['guest']:
                    self.enhanced_logger.info(f"User correction: Host='{extracted_names['host']}' -> '{verified_names['host']}', Guest='{extracted_names['guest']}' -> '{verified_names['guest']}'")
                
                final_names = verified_names
            else:
                final_names = extracted_names
            
            # Step 4: Directory Setup
            self.enhanced_logger.info("📁 Creating directory structure...")
            episode_paths = self.file_organizer.get_episode_paths(
                title, 
                final_names['host'], 
                final_names['guest']
            )
            
            # Set episode directory for use by other stages
            self.episode_dir = episode_paths['episode_folder']
            
            self.enhanced_logger.info(f"📁 Episode directory: {Path(self.episode_dir).name}")
            
            # Step 5: Direct Download to Target Paths
            # Download audio with progress feedback
            self.enhanced_logger.info("🎵 Downloading audio...")
            with self.enhanced_logger.spinner_context("Extracting audio from YouTube..."):
                audio_path = download_audio(url, episode_paths['original_audio'])
            
            # Download video with progress feedback  
            self.enhanced_logger.info("🎬 Downloading video...")
            with self.enhanced_logger.spinner_context("Extracting video from YouTube..."):
                video_path = download_video(url, episode_paths['original_video'])
            
            # Error checking - working modules return error strings on failure
            if isinstance(audio_path, str) and "Error" in audio_path:
                raise Exception(f"Audio download failed: {audio_path}")
            
            if isinstance(video_path, str) and "Error" in video_path:
                raise Exception(f"Video download failed: {video_path}")
            
            # Validate files exist
            if not os.path.exists(audio_path):
                raise Exception(f"Downloaded audio file not found: {audio_path}")
            
            if not os.path.exists(video_path):
                raise Exception(f"Downloaded video file not found: {video_path}")
            
            # Get file sizes for summary
            audio_size = os.path.getsize(audio_path) / (1024 * 1024)  # MB
            video_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
            
            self.enhanced_logger.success(f"Media extraction completed successfully")
            self.enhanced_logger.info(f"🎵 Audio: {Path(audio_path).name} ({audio_size:.1f}MB)")
            self.enhanced_logger.info(f"🎬 Video: {Path(video_path).name} ({video_size:.1f}MB)")
            
            return {
                'audio_path': audio_path,
                'video_path': video_path,
                'episode_info': {
                    'host': final_names['host'],
                    'guest': final_names['guest'],
                    'title': title,
                    'paths': episode_paths
                }
            }
            
        except Exception as e:
            self.enhanced_logger.error(f"Media extraction failed: {e}")
            raise Exception(f"Media extraction failed: {e}")
    def _stage_2_transcript_generation(self, audio_path: str) -> str:
        """
        Stage 2: Direct call to diarize_audio() with caching.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            str: Transcript file path
        """
        
        try:
            # Validate audio file exists
            if not os.path.exists(audio_path):
                self.enhanced_logger.error(f"Audio file not found: [red]{audio_path}[/red]")
                raise Exception(f"Audio file not found: {audio_path}")
            
            audio_size = os.path.getsize(audio_path) / (1024 * 1024)  # MB
            self.enhanced_logger.info(f"Processing audio file: [cyan]{os.path.basename(audio_path)}[/cyan] ({audio_size:.1f} MB)")
            
            # Check if transcript already exists
            processing_dir = os.path.join(self.episode_dir, "Processing")
            transcript_filename = "original_audio_transcript.json"
            transcript_path = os.path.join(processing_dir, transcript_filename)
            
            if os.path.exists(transcript_path):
                self.enhanced_logger.warning("Transcript already exists, using cached version")
                self.enhanced_logger.success(f"Using existing transcript: [green]{transcript_filename}[/green]")
                return transcript_path
            
            # Ensure processing directory exists before calling diarizer
            if not os.path.exists(processing_dir):
                os.makedirs(processing_dir)
            
            # Direct call to working module with progress spinner
            with self.enhanced_logger.spinner("Initializing audio diarization"):
                time.sleep(0.5)  # Brief pause for UI
                hf_token = self.config.get('api', {}).get('huggingface_token', None)
                if not hf_token:
                    self.enhanced_logger.warning("No HuggingFace token found in config")
            
            self.enhanced_logger.info("Starting audio diarization and transcription...")
            with self.enhanced_logger.spinner("Processing audio with AI models"):
                # Pass explicit output path to diarizer - it will save the file directly
                transcript_result = diarize_audio(audio_path, hf_token, transcript_path)
            
            # Simple error checking - working module returns error strings on failure
            if isinstance(transcript_result, str) and "Error" in transcript_result:
                self.enhanced_logger.error(f"Transcript generation failed: {transcript_result}")
                raise Exception(f"Transcript generation failed: {transcript_result}")
            
            # Diarizer now saves the file directly, so we just need to validate it exists
            if not os.path.exists(transcript_path):
                self.enhanced_logger.error(f"Generated transcript file not found: {transcript_path}")
                raise Exception(f"Generated transcript file not found: {transcript_path}")
            
            # Parse the JSON for validation and stats
            with self.enhanced_logger.spinner("Validating transcript data"):
                transcript_data = json.loads(transcript_result)
            
            # Show completion summary
            transcript_size = os.path.getsize(transcript_path) / 1024  # KB
            num_speakers = len(set(segment.get('speaker', 'Unknown') for segment in transcript_data.get('segments', [])))
            
            self.enhanced_logger.success("Transcript generation completed successfully!")
            self.enhanced_logger.info(f"• Output file: [green]{transcript_filename}[/green]")
            self.enhanced_logger.info(f"• File size: [cyan]{transcript_size:.1f} KB[/cyan]")
            self.enhanced_logger.info(f"• Detected speakers: [yellow]{num_speakers}[/yellow]")
            
            return transcript_path
            
        except Exception as e:
            self.enhanced_logger.error(f"Stage 2 failed: [red]{str(e)}[/red]")
            raise Exception(f"Transcript generation failed: {e}")
    
    def _stage_3_content_analysis(self, transcript_path: str) -> str:
        """
        Stage 3: Direct call to analyze_with_gemini_file_upload() with caching.
        
        Args:
            transcript_path: Path to transcript file
            
        Returns:
            str: Analysis result file path
        """
        
        try:
            # Validate transcript file exists
            if not os.path.exists(transcript_path):
                self.enhanced_logger.error(f"Transcript file not found: [red]{transcript_path}[/red]")
                raise Exception(f"Transcript file not found: {transcript_path}")
            
            transcript_size = os.path.getsize(transcript_path) / 1024  # KB
            self.enhanced_logger.info(f"Processing transcript: [cyan]{os.path.basename(transcript_path)}[/cyan] ({transcript_size:.1f} KB)")
            
            # Check if analysis already exists
            processing_dir = os.path.join(self.episode_dir, "Processing")
            analysis_filename = "original_audio_analysis_results.json"
            analysis_file_path = os.path.join(processing_dir, analysis_filename)
            
            if os.path.exists(analysis_file_path):
                self.enhanced_logger.warning("Analysis results already exist, using cached version")
                self.enhanced_logger.success(f"Using existing analysis: [green]{analysis_filename}[/green]")
                return analysis_file_path
            
            # Ensure Processing directory exists
            if not os.path.exists(processing_dir):
                os.makedirs(processing_dir)
            
            # Configure Gemini API with the key from config
            with self.enhanced_logger.spinner("Initializing Gemini AI"):
                time.sleep(0.5)  # Brief pause for UI
                api_key = self.config['api']['gemini_api_key']
                import google.generativeai as genai
                genai.configure(api_key=api_key)
            
            # Load and upload transcript to Gemini
            self.enhanced_logger.info("Uploading transcript to Gemini AI...")
            with self.enhanced_logger.spinner("Uploading transcript data"):
                from Content_Analysis.transcript_analyzer import upload_transcript_to_gemini
                display_name = f"transcript_{os.path.basename(transcript_path)}"
                file_object = upload_transcript_to_gemini(transcript_path, display_name)
                
                if not file_object:
                    self.enhanced_logger.error("Failed to upload transcript to Gemini")
                    raise Exception("Failed to upload transcript to Gemini")
            
            # Load analysis rules from file
            rules_path = os.path.join(
                os.path.dirname(__file__), 
                'Content_Analysis', 
                'Analysis_Guidelines', 
                'Joe_Rogan_selective_analysis_rules.txt'
            )
            
            analysis_rules = ""
            if os.path.exists(rules_path):
                with open(rules_path, 'r', encoding='utf-8') as f:
                    analysis_rules = f.read()
                rules_size = len(analysis_rules) / 1024  # KB
                self.enhanced_logger.info(f"Loaded analysis rules: [cyan]{rules_size:.1f} KB[/cyan]")
            else:
                self.enhanced_logger.warning(f"Analysis rules file not found: [yellow]{rules_path}[/yellow]")
            
            # Perform content analysis with progress indication
            self.enhanced_logger.info("Starting AI content analysis...")
            with self.enhanced_logger.spinner("Analyzing content with Gemini AI (this may take a few minutes)"):
                analysis_content = analyze_with_gemini_file_upload(
                    file_object, 
                    analysis_rules,  # Use loaded rules instead of empty string
                    processing_dir,
                    transcript_path  # Pass the transcript file path for name extraction
                )
            
            if not analysis_content:
                self.enhanced_logger.error("Analysis failed - no content returned")
                raise Exception("Analysis failed - no content returned")
            
            # Save analysis results
            with self.enhanced_logger.spinner("Saving analysis results"):
                with open(analysis_file_path, 'w', encoding='utf-8') as f:
                    f.write(analysis_content)
            
            # Validate analysis file exists
            if not os.path.exists(analysis_file_path):
                self.enhanced_logger.error(f"Generated analysis file not found: {analysis_file_path}")
                raise Exception(f"Generated analysis file not found: {analysis_file_path}")
            
            # Show completion summary
            analysis_size = os.path.getsize(analysis_file_path) / 1024  # KB
            
            self.enhanced_logger.success("Content analysis completed successfully!")
            self.enhanced_logger.info(f"• Output file: [green]{analysis_filename}[/green]")
            self.enhanced_logger.info(f"• Analysis size: [cyan]{analysis_size:.1f} KB[/cyan]")
            
            return analysis_file_path
            
        except Exception as e:
            self.enhanced_logger.error(f"Stage 3 failed: [red]{str(e)}[/red]")
            raise Exception(f"Content analysis failed: {e}")
    
    def _stage_4_narrative_generation(self, analysis_path: str, narrative_format: str = "with_hook") -> str:
        """
        Stage 4: Direct call to NarrativeCreatorGenerator.generate_unified_narrative().
        
        Args:
            analysis_path: Path to analysis file
            narrative_format: Format for narrative generation ("with_hook" or "without_hook")
            
        Returns:
            str: Unified podcast script file path
        """
        
        try:
            # Check if unified script already exists
            expected_script_path = os.path.join(self.episode_dir, "Output", "Scripts", "unified_podcast_script.json")
            if os.path.exists(expected_script_path):
                self.enhanced_logger.warning("Unified script already exists, using cached version")
                self.enhanced_logger.success(f"Using existing script: [green]{os.path.basename(expected_script_path)}[/green]")
                return expected_script_path
            
            # Validate analysis file exists
            if not os.path.exists(analysis_path):
                self.enhanced_logger.error(f"Analysis file not found: [red]{analysis_path}[/red]")
                raise Exception(f"Analysis file not found: {analysis_path}")
            
            analysis_size = os.path.getsize(analysis_path) / 1024  # KB
            self.enhanced_logger.info(f"Processing analysis: [cyan]{os.path.basename(analysis_path)}[/cyan] ({analysis_size:.1f} KB)")
            
            # Generate episode title from directory name
            episode_title = os.path.basename(self.episode_dir)
            self.enhanced_logger.info(f"Episode title: [yellow]{episode_title}[/yellow]")
            
            # Initialize narrative generator
            with self.enhanced_logger.spinner("Initializing narrative generator"):
                time.sleep(0.5)  # Brief pause for UI
                generator = NarrativeCreatorGenerator()
            
            # Generate unified narrative with progress indication
            self.enhanced_logger.info("Starting narrative generation...")
            with self.enhanced_logger.spinner("Generating unified podcast narrative (this may take a few minutes)"):
                script_data = generator.generate_unified_narrative(analysis_path, episode_title, narrative_format)
            
            # Save script to Output/Scripts directory
            with self.enhanced_logger.spinner("Saving generated script"):
                output_dir = os.path.join(self.episode_dir, "Output")
                script_path = generator.save_unified_script(script_data, output_dir)
            
            # Convert Path object to string and validate script file exists
            script_path_str = str(script_path)
            if not os.path.exists(script_path_str):
                self.enhanced_logger.error(f"Generated script file not found: {script_path_str}")
                raise Exception(f"Generated script file not found: {script_path_str}")
            
            # Show completion summary
            script_size = os.path.getsize(script_path_str) / 1024  # KB
            
            # Try to extract some basic stats from the script
            try:
                with open(script_path_str, 'r', encoding='utf-8') as f:
                    script_content = json.load(f)
                    num_segments = len(script_content.get('segments', []))
                    total_duration = sum(seg.get('duration', 0) for seg in script_content.get('segments', []))
            except:
                num_segments = "Unknown"
                total_duration = 0
            
            self.enhanced_logger.success("Narrative generation completed successfully!")
            self.enhanced_logger.info(f"• Output file: [green]{os.path.basename(script_path_str)}[/green]")
            self.enhanced_logger.info(f"• Script size: [cyan]{script_size:.1f} KB[/cyan]")
            if num_segments != "Unknown":
                self.enhanced_logger.info(f"• Script segments: [yellow]{num_segments}[/yellow]")
                if total_duration > 0:
                    self.enhanced_logger.info(f"• Estimated duration: [blue]{total_duration/60:.1f} minutes[/blue]")
            
            return script_path_str
            
        except Exception as e:
            self.enhanced_logger.error(f"Stage 4 failed: [red]{str(e)}[/red]")
            raise Exception(f"Narrative generation failed: {e}")

    def _stage_5_audio_generation(self, script_path: str, tts_provider: str = "chatterbox") -> Dict:
        """
        Stage 5: Enhanced TTS audio generation with specialized logging.
        
        Args:
            script_path: Path to unified podcast script
            tts_provider: TTS provider to use ("chatterbox" or "elevenlabs")
            
        Returns:
            Dict: TTS engine audio generation results
        """
        self.enhanced_logger.info(f"Initializing TTS audio generation with {tts_provider.upper()}")
        self.enhanced_logger.info(f"Script: {Path(script_path).name}")
        
        try:
            # Validate script file exists
            if not os.path.exists(script_path):
                raise Exception(f"Script file not found: {script_path}")
            
            # Pre-parse script to get section counts for progress tracking
            from Chatterbox.json_parser import ChatterboxResponseParser
            parser = ChatterboxResponseParser()
            
            with self.enhanced_logger.spinner("Analyzing script structure..."):
                json_data = parser.parse_response_file(script_path)
                all_sections = json_data.get('podcast_sections', [])
                audio_sections = parser.extract_audio_sections(all_sections)
            
            total_sections = len(audio_sections)
            if total_sections == 0:
                self.enhanced_logger.warning("No audio sections found in script")
                return {
                    'status': 'success',
                    'total_sections': 0,
                    'successful_sections': 0,
                    'failed_sections': 0,
                    'generated_files': [],
                    'output_directory': "",
                    'processing_time': 0
                }
            
            # Initialize TTS engine based on provider
            engine = self._get_tts_engine(tts_provider)
            
            # Check for existing files to show accurate progress
            from Chatterbox.simple_audio_file_manager import SimpleAudioFileManager
            file_manager = SimpleAudioFileManager()
            episode_dir = file_manager.discover_episode_from_script(script_path)
            output_dir = file_manager.create_episode_structure(episode_dir)
            
            existing_sections, missing_sections, existing_files = engine.check_existing_audio_files(audio_sections, output_dir)
            sections_to_generate = len(missing_sections)
            existing_count = len(existing_sections)
            
            # Log configuration and progress information
            tts_config = {
                "TTS Provider": tts_provider.upper(),
                "Engine Type": type(engine).__name__,
                "Script File": Path(script_path).name
            }
            self.tts_logger.log_configuration_info(tts_config)
            
            # Display initial summary
            self.enhanced_logger.info(f"📊 Processing {total_sections} audio sections")
            if existing_count > 0:
                self.enhanced_logger.info(f"   • {existing_count} existing files (will skip)")
            if sections_to_generate > 0:
                self.enhanced_logger.info(f"   • {sections_to_generate} files to generate")
            
            # Process with enhanced progress tracking
            self.enhanced_logger.info("Starting TTS audio generation...")
            
            # Direct method call to working module with progress callback
            if sections_to_generate > 0:
                with self.enhanced_logger.progress_context(sections_to_generate, "Generating audio sections") as progress:
                    def progress_callback(section_id: str, is_success: bool, is_existing: bool = False):
                        """Callback to update progress as sections complete"""
                        if not is_existing:  # Only count newly generated sections
                            status = "✅" if is_success else "❌"
                            self.enhanced_logger.info(f"{status} {section_id}")
                            progress.advance(1)
                    
                    audio_results = engine.process_episode_script(script_path, progress_callback=progress_callback)
            else:
                # All files exist, just call without progress tracking
                audio_results = engine.process_episode_script(script_path)
            
            # Validate audio generation results
            if not audio_results or not hasattr(audio_results, 'successful_sections'):
                raise Exception("Audio generation failed - no results returned")
            
            # Display processing summary
            stats = {
                'total_sections': audio_results.total_sections,
                'successful_sections': audio_results.successful_sections,
                'failed_sections': audio_results.failed_sections,
                'skipped_sections': getattr(audio_results, 'skipped_sections', 0),
                'processing_time': audio_results.processing_time
            }
            self.tts_logger.display_processing_summary(stats)
            
            # Convert SimpleProcessingReport to dictionary for pipeline handoff
            results_dict = {
                'status': 'success' if audio_results.failed_sections == 0 else 'partial_success',
                'total_sections': audio_results.total_sections,
                'successful_sections': audio_results.successful_sections,
                'failed_sections': audio_results.failed_sections,
                'generated_files': audio_results.generated_files,
                'output_directory': audio_results.output_directory,
                'metadata_file': audio_results.metadata_file or "",
                'processing_time': audio_results.processing_time
            }
            
            self.enhanced_logger.success(f"TTS generation completed: {audio_results.successful_sections}/{audio_results.total_sections} sections")
            return results_dict
            
        except Exception as e:
            self.enhanced_logger.error(f"TTS audio generation failed: {e}")
            raise Exception(f"{tts_provider.upper()} TTS engine audio generation failed: {e}")
    
    def _stage_6_video_clipping(self, script_path: str) -> Dict:
        """
        Stage 6: Direct call to Video_Clipper module for clip extraction.
        
        Args:
            script_path: Path to unified podcast script
            
        Returns:
            Dict: Video clips manifest with clip information and file paths
        """
        self.logger.info(f"Stage 6: Video Clipping for {script_path}")
        
        try:
            # Validate script file exists
            if not os.path.exists(script_path):
                raise Exception(f"Script file not found: {script_path}")
            
            self.logger.info(f"Processing script file: {script_path}")
            
            # Direct call to Video_Clipper integration function
            clip_results = extract_clips_from_script(
                episode_dir=self.episode_dir,
                script_filename=os.path.basename(script_path)
            )
            
            # Validate the results
            if not clip_results.get('success', False):
                error_msg = clip_results.get('error', 'Unknown error in video clipping')
                raise Exception(f"Video clipping failed: {error_msg}")
            
            # Create video clips manifest for Stage 7 handoff
            clips_manifest = {
                'status': 'completed',
                'total_clips': clip_results.get('clips_created', 0),
                'clips_failed': clip_results.get('clips_failed', 0),
                'output_directory': clip_results.get('output_directory', ''),
                'extraction_time': clip_results.get('extraction_time', 0),
                'success_rate': clip_results.get('success_rate', '0%'),
                'script_reference': script_path,
                'stage_6_results': clip_results  # Include full results for debugging
            }
            
            self.logger.info(f"Video clipping completed: {clips_manifest['total_clips']} clips extracted")
            self.logger.info(f"Output directory: {clips_manifest['output_directory']}")
            self.logger.info(f"Success rate: {clips_manifest['success_rate']}")
            
            return clips_manifest
            
        except Exception as e:
            self.logger.error(f"Stage 6 failed: {e}")
            raise Exception(f"Video clipping failed: {e}")
    
    def _stage_7_video_compilation(self, audio_paths: Dict, clips_manifest: Dict) -> str:
        """
        Stage 7: Enhanced video compilation with specialized logging.
        
        Args:
            audio_paths: Audio file paths from stage 5
            clips_manifest: Video clips manifest from stage 6
            
        Returns:
            str: Final compiled video path
        """
        self.enhanced_logger.info(f"Initializing video compilation")
        
        try:
            # Validate audio files exist
            audio_dir = audio_paths.get('output_directory', '')
            if not audio_dir or not os.path.exists(audio_dir):
                raise Exception(f"Audio directory not found: {audio_dir}")
            
            # Validate video clips exist
            clips_dir = clips_manifest.get('output_directory', '')
            if not clips_dir or not os.path.exists(clips_dir):
                raise Exception(f"Video clips directory not found: {clips_dir}")
            
            # Validate clip count
            total_clips = clips_manifest.get('total_clips', 0)
            if total_clips == 0:
                raise Exception("No video clips available for compilation")
            
            # Display compilation info
            compilation_info = {
                "Video Clips": f"{total_clips} clips",
                "Audio Directory": Path(audio_dir).name,
                "Video Directory": Path(clips_dir).name,
                "Episode": Path(self.episode_dir).name
            }
            self.video_logger.log_technical_specs(compilation_info)
            
            self.video_logger.start_compilation(
                input_files=[f"{total_clips} segments"],
                output_file=f"{os.path.basename(self.episode_dir)}_final.mp4"
            )
            
            # Direct import and instantiation
            compiler = SimpleCompiler(keep_temp_files=True, validate_segments=True)
            
            # Compile final video using episode directory
            episode_path = Path(self.episode_dir)
            output_filename = f"{os.path.basename(self.episode_dir)}_final.mp4"
            
            self.enhanced_logger.info(f"Compiling episode: {episode_path.name}")
            
            # Use long operation context for compilation
            with self.video_logger.long_operation_context("Compiling final video..."):
                compilation_result = compiler.compile_episode(episode_path, output_filename)
            
            # Validate compilation was successful
            if not compilation_result.success:
                raise Exception(f"Video compilation failed: {compilation_result.error}")
            
            # Validate final video was created
            final_video_path = str(compilation_result.output_path)
            if not os.path.exists(final_video_path):
                raise Exception(f"Final video not created: {final_video_path}")
            
            # Get file information
            file_size = os.path.getsize(final_video_path)
            
            # Log successful compilation with correct duration mapping
            self.video_logger.log_compilation_success(
                output_file=final_video_path,
                duration=getattr(compilation_result, 'duration', 0) or 0,  # Processing time
                total_duration=getattr(compilation_result, 'duration', 0) or 0,  # Video duration
                file_size=file_size
            )
            
            # Display compilation summary with correct attribute mapping
            compilation_stats = {
                'total_files': getattr(compilation_result, 'segments_processed', 0),
                'successful_conversions': getattr(compilation_result, 'audio_segments_converted', 0),
                'failed_conversions': 0,  # CompilationResult doesn't track failed separately
                'skipped_conversions': getattr(compilation_result, 'segments_skipped', 0),
                'output_file_size': file_size,
                'processing_time': getattr(compilation_result, 'duration', 0) or 0,
                'total_video_duration': getattr(compilation_result, 'duration', 0) or 0
            }
            self.video_logger.display_conversion_summary(compilation_stats)
            
            return final_video_path
            
        except Exception as e:
            self.enhanced_logger.error(f"Video compilation failed: {e}")
            raise Exception(f"Video compilation failed: {e}")

    # ========================================================================
    # PIPELINE COORDINATION FRAMEWORK - Simple orchestration
    # ========================================================================
    
    def process_full_pipeline(self, url: str, tts_provider: str = "chatterbox", narrative_format: str = None) -> str:
        """
        Execute all 7 stages with enhanced logging and progress tracking.
        
        Args:
            url: YouTube URL to process
            tts_provider: TTS provider to use ("chatterbox" or "elevenlabs")
            narrative_format: Narrative format to use ("with_hook" or "without_hook")
            
        Returns:
            str: Final video file path
        """
        start_time = time.time()
        
        # Display pipeline header
        self.enhanced_logger.info(f"🚀 Starting Full Pipeline Processing")
        self.enhanced_logger.info(f"📺 URL: {url}")
        self.enhanced_logger.info(f"🆔 Session: {self.session_id}")
        
        try:
            # Stage 1: Media Extraction
            with self.enhanced_logger.stage_context("extraction", 1):
                stage1_result = self._stage_1_media_extraction(url)
            
            # Stage 2: Transcript Generation  
            with self.enhanced_logger.stage_context("transcript", 2):
                stage2_result = self._stage_2_transcript_generation(stage1_result['audio_path'])
            
            # Stage 3: Content Analysis
            with self.enhanced_logger.stage_context("analysis", 3):
                stage3_result = self._stage_3_content_analysis(stage2_result)
            
            # Stage 4: Narrative Generation
            with self.enhanced_logger.stage_context("generation", 4):
                stage4_result = self._stage_4_narrative_generation(stage3_result, narrative_format)
            
            # Stage 5: Audio Generation (TTS)
            with self.enhanced_logger.stage_context("tts", 5):
                stage5_result = self._stage_5_audio_generation(stage4_result, tts_provider)
            
            # Stage 6: Video Clipping
            with self.enhanced_logger.stage_context("video", 6):
                stage6_result = self._stage_6_video_clipping(stage4_result)
            
            # Stage 7: Video Compilation
            with self.enhanced_logger.stage_context("compilation", 7):
                stage7_result = self._stage_7_video_compilation(stage5_result, stage6_result)
            
            # Pipeline completion summary
            total_time = time.time() - start_time
            self.enhanced_logger.success(f"🎉 Full Pipeline Complete!")
            self.enhanced_logger.display_summary_table("Pipeline Summary", {
                "Final Video": stage7_result,
                "Episode Directory": self.episode_dir,
                "Total Processing Time": f"{total_time:.1f}s",
                "Session ID": self.session_id
            })
            
            return stage7_result
            
        except Exception as e:
            total_time = time.time() - start_time
            self.enhanced_logger.error(f"Pipeline failed after {total_time:.1f}s: {e}")
            raise Exception(f"Full pipeline execution failed: {e}")
    
    def process_audio_only(self, url: str, tts_provider: str = "chatterbox") -> Dict:
        """
        Execute stages 1-5 for audio-only output.
        
        Args:
            url: YouTube URL to process
            
        Returns:
            Dict: Audio generation results
        """
        self.pipeline_logger.pipeline_start(url, "AUDIO-ONLY")
        
        try:
            # Sequential execution through stage 5
            self.pipeline_logger.stage_start(1, "Media Extraction")
            stage1_result = self._stage_1_media_extraction(url)
            self.pipeline_logger.stage_success(1, "Media Extraction", stage1_result.get('audio_path'))
            
            self.pipeline_logger.stage_start(2, "Transcript Generation")
            stage2_result = self._stage_2_transcript_generation(stage1_result['audio_path'])
            self.pipeline_logger.stage_success(2, "Transcript Generation", stage2_result)
            
            self.pipeline_logger.stage_start(3, "Content Analysis")
            stage3_result = self._stage_3_content_analysis(stage2_result)
            self.pipeline_logger.stage_success(3, "Content Analysis", stage3_result)
            
            self.pipeline_logger.stage_start(4, "Narrative Generation")
            stage4_result = self._stage_4_narrative_generation(stage3_result)
            self.pipeline_logger.stage_success(4, "Narrative Generation", stage4_result)
            
            self.pipeline_logger.stage_start(5, "Audio Generation")
            stage5_result = self._stage_5_audio_generation(stage4_result, tts_provider)
            self.pipeline_logger.stage_success(5, "Audio Generation", stage5_result)
            
            self.pipeline_logger.pipeline_complete(stage5_result)
            return stage5_result
            
        except Exception as e:
            self.pipeline_logger.pipeline_failed(e)
            raise Exception(f"Audio-only pipeline execution failed: {e}")
    
    def process_until_script(self, url: str) -> str:
        """
        Execute stages 1-4 for script generation only.
        
        Args:
            url: YouTube URL to process
            
        Returns:
            str: Script file path
        """
        self.pipeline_logger.pipeline_start(url, "SCRIPT-ONLY")
        
        try:
            # Sequential execution through stage 4
            self.pipeline_logger.stage_start(1, "Media Extraction")
            stage1_result = self._stage_1_media_extraction(url)
            self.pipeline_logger.stage_success(1, "Media Extraction", stage1_result.get('audio_path'))
            
            self.pipeline_logger.stage_start(2, "Transcript Generation")
            stage2_result = self._stage_2_transcript_generation(stage1_result['audio_path'])
            self.pipeline_logger.stage_success(2, "Transcript Generation", stage2_result)
            
            self.pipeline_logger.stage_start(3, "Content Analysis")
            stage3_result = self._stage_3_content_analysis(stage2_result)
            self.pipeline_logger.stage_success(3, "Content Analysis", stage3_result)
            
            self.pipeline_logger.stage_start(4, "Narrative Generation")
            stage4_result = self._stage_4_narrative_generation(stage3_result)
            self.pipeline_logger.stage_success(4, "Narrative Generation", stage4_result)
            
            self.pipeline_logger.pipeline_complete(stage4_result)
            return stage4_result
            
        except Exception as e:
            self.pipeline_logger.pipeline_failed(e)
            raise Exception(f"Script-only pipeline execution failed: {e}")

    def _get_tts_engine(self, provider: str):
        """
        Factory method to get the appropriate TTS engine based on provider.
        
        Args:
            provider: TTS provider ("chatterbox" or "elevenlabs")
            
        Returns:
            TTS engine instance
        """
        if provider.lower() == "elevenlabs":
            return ElevenLabsTTSEngine(self.config_path)
        else:
            return SimpleTTSEngine(self.config_path)


# ============================================================================
# CLI FOUNDATION - Basic argument parser and main function
# ============================================================================

def create_argument_parser() -> argparse.ArgumentParser:
    """
    Create command line argument parser for Master Processor V2.
    
    Returns:
        argparse.ArgumentParser: Configured argument parser with pipeline options
        
    Notes:
        - URL is positional argument (different from original implementation)
        - Pipeline options are mutually exclusive (--full-pipeline, --audio-only, --script-only)
        - Optional configuration file path can be specified
        - Includes built-in help with usage examples
    """
    parser = argparse.ArgumentParser(
        description='Master Processor V2: Pipeline-driven YouTube video processing orchestrator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s https://www.youtube.com/watch?v=dQw4w9WgXcQ --full-pipeline
  %(prog)s https://www.youtube.com/watch?v=dQw4w9WgXcQ --audio-only --tts-provider elevenlabs
  %(prog)s https://www.youtube.com/watch?v=dQw4w9WgXcQ --script-only
        """
    )
    
    # Main input argument
    parser.add_argument(
        'input',
        help='YouTube URL to process'
    )
    
    # Pipeline execution options (mutually exclusive)
    pipeline_group = parser.add_mutually_exclusive_group(required=True)
    pipeline_group.add_argument(
        '--full-pipeline',
        action='store_true',
        help='Execute all 7 stages (default: stages 1-7)'
    )
    pipeline_group.add_argument(
        '--audio-only',
        action='store_true',
        help='Execute stages 1-5 for audio podcast generation'
    )
    pipeline_group.add_argument(
        '--script-only',
        action='store_true',
        help='Execute stages 1-4 for script generation only'
    )
    
    # Configuration options
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file (optional)'
    )
    
    # TTS provider option
    parser.add_argument(
        '--tts-provider',
        choices=['chatterbox', 'elevenlabs'],
        default='chatterbox',
        help='TTS provider for audio generation (default: chatterbox)'
    )
    
    # Logging verbosity options
    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Minimal output (errors only)'
    )
    verbosity_group.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Detailed technical output'
    )
    verbosity_group.add_argument(
        '--debug',
        action='store_true',
        help='Full debug output with all details'
    )
    
    return parser


def main():
    """
    Main entry point for Master Processor V2 command line interface.
    
    Handles:
        - Command line argument parsing
        - Verbosity level configuration
        - Orchestrator initialization with enhanced logging
        - Pipeline execution based on selected mode
        - Error handling and user feedback
        - Session ID reporting for tracking
        
    Exit Codes:
        0: Success
        1: Error or user cancellation
    """
    try:
        # Parse arguments
        parser = create_argument_parser()
        args = parser.parse_args()
        
        # Determine verbosity level
        if args.quiet:
            verbosity = LogLevel.QUIET
        elif args.debug:
            verbosity = LogLevel.DEBUG
        elif args.verbose:
            verbosity = LogLevel.VERBOSE
        else:
            verbosity = LogLevel.NORMAL
        
        # Initialize orchestrator with enhanced logging
        processor = MasterProcessorV2(config_path=args.config, verbosity=verbosity)
        
        # Execute requested pipeline
        if args.full_pipeline:
            result = processor.process_full_pipeline(args.input, args.tts_provider)
            if verbosity != LogLevel.QUIET:
                print(f"\n🎉 Full pipeline completed!")
                print(f"📁 Final video: {result}")
            
        elif args.audio_only:
            result = processor.process_audio_only(args.input, args.tts_provider)
            if verbosity != LogLevel.QUIET:
                print(f"\n🎵 Audio-only pipeline completed!")
                print(f"📁 Results: {result}")
            
        elif args.script_only:
            result = processor.process_until_script(args.input)
            if verbosity != LogLevel.QUIET:
                print(f"\n📝 Script-only pipeline completed!")
                print(f"📁 Script: {result}")
        
        if verbosity in [LogLevel.VERBOSE, LogLevel.DEBUG]:
            print(f"\n🆔 Session ID: {processor.session_id}")
        
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user.")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if verbosity == LogLevel.DEBUG:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
