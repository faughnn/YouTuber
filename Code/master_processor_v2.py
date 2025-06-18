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

Created: June 10, 2025
Agent: Pipeline-Driven Implementation Agent
Task Reference: Phase 2, Task 2.1 - Pipeline-Driven Orchestrator Foundation

USAGE EXAMPLES
==============

1. Command Line Usage:
   
   # Full pipeline (all 7 stages) - YouTube URL to final video
   python master_processor_v2.py --full-pipeline "https://www.youtube.com/watch?v=example"
   
   # Audio-only pipeline (stages 1-5) - Creates podcast-style audio
   python master_processor_v2.py --audio-only "https://www.youtube.com/watch?v=example"
   
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
   final_video_path = processor.process_full_pipeline(youtube_url)
   print(f"Final video created: {final_video_path}")
   
   # Execute audio-only pipeline
   results = processor.process_audio_only(youtube_url)
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
   generated_audio = processor._stage_5_audio_generation(script_path)
   
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

# ============================================================================
# DIRECT WORKING MODULE IMPORTS - No abstraction layers
# ============================================================================

# Stage 1: Media Extraction - Direct imports
from Extraction.youtube_audio_extractor import download_audio
from Extraction.youtube_video_downloader import download_video

# Stage 2: Transcript Generation - Direct import
from Extraction.audio_diarizer import diarize_audio

# Stage 3: Content Analysis - Direct import
from Content_Analysis.transcript_analyzer import analyze_with_gemini_file_upload

# Stage 4: Narrative Generation - Direct import
from Content_Analysis.podcast_narrative_generator import NarrativeCreatorGenerator

# Stage 5: Audio Generation - Direct import  
from Chatterbox.simple_tts_engine import SimpleTTSEngine

# Stage 6: Video Clipping - Direct import
from Video_Clipper.integration import extract_clips_from_script

# Stage 7: Video Compilation - Direct import
from Video_Compilator import SimpleCompiler

# Utility imports - Direct usage
from Utils.file_organizer import FileOrganizer


class MasterProcessorV2:
    """
    Pipeline-driven orchestrator serving working modules directly.
    
    Core Principle: Orchestrator adapts to working module interfaces,
    not the reverse. All 7 stages implemented as direct calls to 
    working modules without abstraction layers.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize orchestrator with direct configuration loading.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        # Load configuration directly - no complex config abstraction
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()
        
        # Setup simple logging - no complex logging abstraction
        self.logger = self._setup_simple_logging()
        
        # Initialize FileOrganizer directly - no path logic in orchestrator
        self.file_organizer = FileOrganizer(self.config['paths'])
        
        # Session management for tracking
        self.session_id = self._generate_session_id()
        self.episode_dir = None
        
        self.logger.info(f"MasterProcessorV2 initialized - Session: {self.session_id}")
    
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
        Stage 1: Direct calls to download_audio() and download_video().
        Implemented for Task 2.2 - Media Extraction Stage Implementation.
        
        Args:
            url: YouTube URL
            
        Returns:
            Dict: Audio and video file paths
        """
        self.logger.info(f"Stage 1: Media Extraction for {url}")
        
        try:
            # Direct calls to working modules - let them handle episode directory creation
            self.logger.info("Downloading audio...")
            audio_path = download_audio(url)
            
            self.logger.info("Downloading video...")
            video_path = download_video(url, self.file_organizer)
            
            # Set episode directory based on where the files were actually saved
            # Extract episode directory from the audio path (remove Input/filename)
            audio_dir = os.path.dirname(audio_path)  # This is the Input folder
            self.episode_dir = os.path.dirname(audio_dir)  # This is the episode folder
            
            self.logger.info(f"Episode directory determined from downloads: {self.episode_dir}")
            
            # Simple error checking - working modules return error strings on failure
            if isinstance(audio_path, str) and "Error" in audio_path:
                raise Exception(f"Audio download failed: {audio_path}")
            
            if isinstance(video_path, str) and "Error" in video_path:
                raise Exception(f"Video download failed: {video_path}")
            
            # Validate files exist            if not os.path.exists(audio_path):
                raise Exception(f"Downloaded audio file not found: {audio_path}")
            
            if not os.path.exists(video_path):
                raise Exception(f"Downloaded video file not found: {video_path}")
            
            self.logger.info(f"Media extraction completed successfully")
            self.logger.info(f"Audio: {audio_path}")
            self.logger.info(f"Video: {video_path}")
            
            return {
                'audio_path': audio_path,
                'video_path': video_path
            }
            
        except Exception as e:
            self.logger.error(f"Stage 1 failed: {e}")
            raise Exception(f"Media extraction failed: {e}")
    def _stage_2_transcript_generation(self, audio_path: str) -> str:
        """
        Stage 2: Direct call to diarize_audio() with caching.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            str: Transcript file path
        """
        self.logger.info(f"Stage 2: Transcript Generation for {audio_path}")
        
        try:
            # Validate audio file exists
            if not os.path.exists(audio_path):
                raise Exception(f"Audio file not found: {audio_path}")
            
            # Check if transcript already exists
            processing_dir = os.path.join(self.episode_dir, "Processing")
            transcript_filename = "original_audio_transcript.json"
            transcript_path = os.path.join(processing_dir, transcript_filename)
            
            if os.path.exists(transcript_path):
                self.logger.info(f"Transcript already exists, skipping diarization: {transcript_path}")
                return transcript_path
            
            # Direct call to working module
            self.logger.info("Starting audio diarization...")
            hf_token = self.config.get('api', {}).get('huggingface_token', None)
            
            transcript_result = diarize_audio(audio_path, hf_token)            
            # Simple error checking - working module returns error strings on failure
            if isinstance(transcript_result, str) and "Error" in transcript_result:
                raise Exception(f"Transcript generation failed: {transcript_result}")
            
            # Save transcript to Processing folder and return file path
            if not os.path.exists(processing_dir):
                os.makedirs(processing_dir)
            
            # Parse the JSON string returned by diarize_audio into a dictionary
            # then save it properly as JSON
            transcript_data = json.loads(transcript_result)
            
            with open(transcript_path, 'w', encoding='utf-8') as f:
                json.dump(transcript_data, f, indent=2, ensure_ascii=False)
            
            # Validate transcript file exists
            if not os.path.exists(transcript_path):
                raise Exception(f"Generated transcript file not found: {transcript_path}")            
            self.logger.info(f"Transcript generation completed: {transcript_path}")
            return transcript_path
            
        except Exception as e:
            self.logger.error(f"Stage 2 failed: {e}")
            raise Exception(f"Transcript generation failed: {e}")
    
    def _stage_3_content_analysis(self, transcript_path: str) -> str:
        """
        Stage 3: Direct call to analyze_with_gemini_file_upload() with caching.
        
        Args:
            transcript_path: Path to transcript file
            
        Returns:
            str: Analysis result file path
        """
        self.logger.info(f"Stage 3: Content Analysis for {transcript_path}")
        
        try:
            # Validate transcript file exists
            if not os.path.exists(transcript_path):
                raise Exception(f"Transcript file not found: {transcript_path}")
            
            # Check if analysis already exists
            processing_dir = os.path.join(self.episode_dir, "Processing")
            analysis_filename = "original_audio_analysis_results.json"
            analysis_file_path = os.path.join(processing_dir, analysis_filename)
            
            if os.path.exists(analysis_file_path):
                self.logger.info(f"Analysis results already exist, skipping analysis: {analysis_file_path}")
                return analysis_file_path
            
            # Ensure Processing directory exists
            if not os.path.exists(processing_dir):
                os.makedirs(processing_dir)
              # Configure Gemini API with the key from config BEFORE upload
            self.logger.info("Starting content analysis...")
            api_key = self.config['api']['gemini_api_key']
            
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            
            # Load transcript and upload to Gemini
            from Content_Analysis.transcript_analyzer import upload_transcript_to_gemini
            display_name = f"transcript_{os.path.basename(transcript_path)}"
            file_object = upload_transcript_to_gemini(transcript_path, display_name)
            
            if not file_object:
                raise Exception("Failed to upload transcript to Gemini")
            
            # Load analysis rules from file
            rules_path = os.path.join(
                os.path.dirname(__file__), 
                'Content_Analysis', 
                'Rules', 
                'Joe_Rogan_selective_analysis_rules.txt'
            )
            
            analysis_rules = ""
            if os.path.exists(rules_path):
                with open(rules_path, 'r', encoding='utf-8') as f:
                    analysis_rules = f.read()
                self.logger.info(f"Loaded analysis rules from: {rules_path}")
            else:
                self.logger.warning(f"Analysis rules file not found: {rules_path}")
            
            analysis_content = analyze_with_gemini_file_upload(
                file_object, 
                analysis_rules,  # Use loaded rules instead of empty string
                processing_dir
            )            
            if not analysis_content:
                raise Exception("Analysis failed - no content returned")
            
            # Handle file saving in orchestrator (Option 2 from task instructions)
            with open(analysis_file_path, 'w', encoding='utf-8') as f:
                f.write(analysis_content)            # Validate analysis file exists
            if not os.path.exists(analysis_file_path):
                raise Exception(f"Generated analysis file not found: {analysis_file_path}")
            
            self.logger.info(f"Content analysis completed: {analysis_file_path}")
            return analysis_file_path
            
        except Exception as e:
            self.logger.error(f"Stage 3 failed: {e}")
            raise Exception(f"Content analysis failed: {e}")
    
    def _stage_4_narrative_generation(self, analysis_path: str) -> str:
        """
        Stage 4: Direct call to NarrativeCreatorGenerator.generate_unified_narrative().
        
        Args:
            analysis_path: Path to analysis file
            
        Returns:
            str: Unified podcast script file path
        """
        self.logger.info(f"Stage 4: Narrative Generation for {analysis_path}")
        
        try:
            # Check if unified script already exists
            expected_script_path = os.path.join(self.episode_dir, "Output", "Scripts", "unified_podcast_script.json")
            if os.path.exists(expected_script_path):
                self.logger.info(f"Unified script already exists, skipping narrative generation: {expected_script_path}")
                return expected_script_path
            
            # Validate analysis file exists
            if not os.path.exists(analysis_path):
                raise Exception(f"Analysis file not found: {analysis_path}")
            
            # Direct class instantiation - no wrapper methods
            generator = NarrativeCreatorGenerator()
            
            # Generate episode title from directory name
            episode_title = os.path.basename(self.episode_dir)
              # Direct method call to working module
            script_data = generator.generate_unified_narrative(analysis_path, episode_title)
            
            # Save script to Output/Scripts directory
            output_dir = os.path.join(self.episode_dir, "Output")
            script_path = generator.save_unified_script(script_data, output_dir)
            
            # Convert Path object to string and validate script file exists
            script_path_str = str(script_path)
            if not os.path.exists(script_path_str):
                raise Exception(f"Generated script file not found: {script_path_str}")
            
            self.logger.info(f"Narrative generation completed: {script_path_str}")
            return script_path_str
            
        except Exception as e:
            self.logger.error(f"Stage 4 failed: {e}")
            raise Exception(f"Narrative generation failed: {e}")

    def _stage_5_audio_generation(self, script_path: str) -> Dict:
        """
        Stage 5: Direct call to SimpleTTSEngine.process_episode_script().
        
        Args:
            script_path: Path to unified podcast script
            
        Returns:
            Dict: SimpleTTSEngine audio generation results
        """
        self.logger.info(f"Stage 5: SimpleTTSEngine Audio Generation for {script_path}")
        
        try:
            # Validate script file exists
            if not os.path.exists(script_path):
                raise Exception(f"Script file not found: {script_path}")
            
            # Direct class instantiation - no wrapper methods
            engine = SimpleTTSEngine(self.config_path)
            
            # Direct method call to working module
            audio_results = engine.process_episode_script(script_path)
            
            # Validate audio generation results
            if not audio_results or not hasattr(audio_results, 'successful_sections'):
                raise Exception("Audio generation failed - no results returned")
            
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
            
            self.logger.info(f"SimpleTTSEngine audio generation completed: {results_dict}")
            return results_dict
            
        except Exception as e:
            self.logger.error(f"Stage 5 SimpleTTSEngine failed: {e}")
            raise Exception(f"SimpleTTSEngine audio generation failed: {e}")
    
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
        Stage 7: Direct call to Video_Compilator module for final video assembly.
        
        Args:
            audio_paths: Audio file paths from stage 5
            clips_manifest: Video clips manifest from stage 6
            
        Returns:
            str: Final compiled video path
        """
        self.logger.info(f"Stage 7: Video Compilation")
        
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
            
            self.logger.info(f"Compiling episode with {total_clips} video clips and audio from {audio_dir}")
            
            # Direct import and instantiation
            compiler = SimpleCompiler(keep_temp_files=True, validate_segments=True)
            
            # Compile final video using episode directory (SimpleCompiler expects episode path)
            episode_path = Path(self.episode_dir)
            output_filename = f"{os.path.basename(self.episode_dir)}_final.mp4"
            
            self.logger.info(f"Starting video compilation for episode: {episode_path.name}")
            compilation_result = compiler.compile_episode(episode_path, output_filename)
            
            # Validate compilation was successful
            if not compilation_result.success:
                raise Exception(f"Video compilation failed: {compilation_result.error}")
            
            # Validate final video was created
            final_video_path = str(compilation_result.output_path)
            if not os.path.exists(final_video_path):
                raise Exception(f"Final video not created: {final_video_path}")
            
            # Get file size for verification
            file_size_mb = os.path.getsize(final_video_path) / (1024 * 1024)
            
            self.logger.info(f"Video compilation completed: {final_video_path}")
            self.logger.info(f"Final video size: {file_size_mb:.1f} MB")
            self.logger.info(f"Segments processed: {compilation_result.segments_processed}")
            self.logger.info(f"Audio segments converted: {compilation_result.audio_segments_converted}")
            
            return final_video_path
            
        except Exception as e:
            self.logger.error(f"Stage 7 failed: {e}")
            raise Exception(f"Video compilation failed: {e}")

    # ========================================================================
    # PIPELINE COORDINATION FRAMEWORK - Simple orchestration
    # ========================================================================
    
    def process_full_pipeline(self, url: str) -> str:
        """
        Execute all 7 stages with direct handoffs.
        
        Args:
            url: YouTube URL to process
            
        Returns:
            str: Final video file path
        """
        self.logger.info(f"Starting full pipeline for: {url}")
        
        try:
            # Sequential execution with direct handoffs
            stage1_result = self._stage_1_media_extraction(url)
            
            stage2_result = self._stage_2_transcript_generation(stage1_result['audio_path'])
            
            stage3_result = self._stage_3_content_analysis(stage2_result)
            
            stage4_result = self._stage_4_narrative_generation(stage3_result)
            
            stage5_result = self._stage_5_audio_generation(stage4_result)
            
            stage6_result = self._stage_6_video_clipping(stage4_result)
            
            stage7_result = self._stage_7_video_compilation(stage5_result, stage6_result)
            
            self.logger.info(f"Full pipeline completed: {stage7_result}")
            return stage7_result
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}")
            raise Exception(f"Full pipeline execution failed: {e}")
    
    def process_audio_only(self, url: str) -> Dict:
        """
        Execute stages 1-5 for audio-only output.
        
        Args:
            url: YouTube URL to process
            
        Returns:
            Dict: Audio generation results
        """
        self.logger.info(f"Starting audio-only pipeline for: {url}")
        
        try:
            # Sequential execution through stage 5
            stage1_result = self._stage_1_media_extraction(url)
            stage2_result = self._stage_2_transcript_generation(stage1_result['audio_path'])
            stage3_result = self._stage_3_content_analysis(stage2_result)
            stage4_result = self._stage_4_narrative_generation(stage3_result)
            stage5_result = self._stage_5_audio_generation(stage4_result)
            
            self.logger.info(f"Audio-only pipeline completed")
            return stage5_result
            
        except Exception as e:
            self.logger.error(f"Audio pipeline failed: {e}")
            raise Exception(f"Audio-only pipeline execution failed: {e}")
    
    def process_until_script(self, url: str) -> str:
        """
        Execute stages 1-4 for script generation only.
        
        Args:
            url: YouTube URL to process
            
        Returns:
            str: Script file path
        """
        self.logger.info(f"Starting script-only pipeline for: {url}")
        
        try:
            # Sequential execution through stage 4
            stage1_result = self._stage_1_media_extraction(url)
            stage2_result = self._stage_2_transcript_generation(stage1_result['audio_path'])
            stage3_result = self._stage_3_content_analysis(stage2_result)
            stage4_result = self._stage_4_narrative_generation(stage3_result)
            
            self.logger.info(f"Script-only pipeline completed: {stage4_result}")
            return stage4_result
            
        except Exception as e:
            self.logger.error(f"Script pipeline failed: {e}")
            raise Exception(f"Script-only pipeline execution failed: {e}")


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
  %(prog)s https://www.youtube.com/watch?v=dQw4w9WgXcQ --audio-only
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
    
    return parser


def main():
    """
    Main entry point for Master Processor V2 command line interface.
    
    Handles:
        - Command line argument parsing
        - Orchestrator initialization with optional custom configuration
        - Pipeline execution based on selected mode (full/audio-only/script-only)
        - Error handling and user feedback
        - Session ID reporting for tracking
        
    Exit Codes:
        0: Success
        1: Error or user cancellation
        
    Notes:
        - Supports keyboard interrupt (Ctrl+C) for graceful cancellation
        - Provides clear error messages for debugging
        - Session ID printed for tracking and log correlation
    """
    try:
        # Parse arguments
        parser = create_argument_parser()
        args = parser.parse_args()
        
        # Initialize orchestrator
        processor = MasterProcessorV2(config_path=args.config)
        
        # Execute requested pipeline
        if args.full_pipeline:
            result = processor.process_full_pipeline(args.input)
            print(f"Full pipeline completed. Final video: {result}")
            
        elif args.audio_only:
            result = processor.process_audio_only(args.input)
            print(f"Audio-only pipeline completed. Results: {result}")
            
        elif args.script_only:
            result = processor.process_until_script(args.input)
            print(f"Script-only pipeline completed. Script: {result}")
        
        print(f"Session ID: {processor.session_id}")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
