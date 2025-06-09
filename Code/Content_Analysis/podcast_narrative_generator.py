"""
Single-Call Podcast Narrative Generator

Creates unified script-timeline JSON structure from analysis data using a single Gemini API call.
Replaces the complex two-call system with a simplified approach that uploads analysis JSON
to Gemini and produces complete script ready for both TTS processing and video editing.

Usage:
    from podcast_narrative_generator import NarrativeCreatorGenerator
    
    generator = NarrativeCreatorGenerator()
    script_data = generator.generate_unified_narrative(analysis_json_path, episode_title)
    output_path = generator.save_unified_script(script_data, episode_output_path)
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any
import traceback

import google.generativeai as genai

# Add path for utilities
current_dir = os.path.dirname(os.path.abspath(__file__))
utils_dir = os.path.join(current_dir, '..', 'Utils')
config_dir = os.path.join(current_dir, '..', 'Config')
sys.path.extend([utils_dir, config_dir])

try:
    from file_organizer import FileOrganizer
except ImportError as e:
    print(f"Warning: Could not import FileOrganizer: {e}")
    FileOrganizer = None

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


class NarrativeCreatorGenerator:
    """Single-call narrative generator that creates unified script-timeline structure."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the narrative generator with API configuration."""
        self.api_key = "AIzaSyCsti0qnCEKOgzAnG_w41IfMNMxkyl3ysw"  # From transcript_analyzer.py
        self.model_name = "gemini-2.5-flash-preview-05-20"
        self.prompt_file = os.path.join(
            current_dir, 'Prompts', 'tts_podcast_narrative_prompt.txt'
        )
        
        # Initialize Gemini API
        self._configure_gemini()
        
        # Load prompt template
        self.prompt_template = self._load_prompt_template()
        
        logger.info("NarrativeCreatorGenerator initialized successfully")
    
    def _configure_gemini(self) -> bool:
        """Configure Gemini API connection."""
        logger.info("Configuring Gemini API")
        try:
            if self.api_key:
                genai.configure(api_key=self.api_key)
                logger.info("Gemini API configured successfully")
                return True
            else:
                logger.error("No API key found")
                return False
        except Exception as e:
            logger.error(f"Error configuring Gemini API: {e}")
            return False
    
    def _load_prompt_template(self) -> str:
        """Load the prompt template from file."""
        try:
            with open(self.prompt_file, 'r', encoding='utf-8') as f:
                template = f.read()
            logger.info(f"Loaded prompt template: {len(template)} characters")
            return template
        except Exception as e:
            logger.error(f"Error loading prompt template: {e}")
            raise
    
    def _upload_analysis_file(self, analysis_json_path: str, episode_title: str):
        """Upload analysis JSON file to Gemini following transcript_analyzer.py pattern."""
        logger.info(f"Uploading analysis file to Gemini: {analysis_json_path}")
        try:
            # Validate JSON structure before upload
            with open(analysis_json_path, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)
                # Check if it's a list (direct array) or dict with segments key
                if isinstance(analysis_data, list):
                    if not analysis_data:
                        raise ValueError("Invalid analysis format: empty segments array")
                elif isinstance(analysis_data, dict):
                    if not analysis_data.get('segments'):
                        raise ValueError("Invalid analysis format: no segments found")
                else:
                    raise ValueError("Invalid analysis format: expected array or object with segments")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
        
        try:
            # Upload file using the pattern from transcript_analyzer.py
            display_name = f"Analysis Results - {episode_title}"
            logger.info(f"Uploading to Gemini with display name: {display_name}")
            
            uploaded_file = genai.upload_file(
                path=analysis_json_path,
                mime_type="text/plain",
                display_name=display_name
            )
            
            logger.info(f"File uploaded successfully: {uploaded_file.name}")
            logger.info(f"File URI: {uploaded_file.uri}")
            
            # Wait for processing to complete
            while uploaded_file.state.name == "PROCESSING":
                logger.info("Waiting for file processing...")
                time.sleep(2)
                uploaded_file = genai.get_file(uploaded_file.name)
            
            if uploaded_file.state.name == "FAILED":
                raise Exception("File processing failed")
            
            logger.info("File processing completed successfully")
            return uploaded_file
        except Exception as e:
            logger.error(f"CRITICAL: File upload to Gemini failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    def _build_unified_prompt(self, episode_title: str, custom_instructions: str = "") -> str:
        """Build the unified prompt that references the uploaded analysis file."""
        logger.info("Building unified narrative prompt")
        
        # Format the prompt template with episode title and custom instructions
        # The template file contains the complete prompt including JSON format specification
        formatted_prompt = self.prompt_template.format(
            episode_title=episode_title,
            custom_instructions=custom_instructions or ""
        )
        
        logger.info(f"Unified prompt created: {len(formatted_prompt)} characters")
        
        return formatted_prompt
    
    def _create_model(self):
        """Create Gemini model with optimized configuration."""
        return genai.GenerativeModel(
            self.model_name,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                top_p=0.9,
                candidate_count=1,
                response_mime_type="application/json"
            )
        )
    
    def _parse_unified_response(self, response_text: str, episode_title: str) -> Dict:
        """Parse and validate the unified response from Gemini."""
        logger.info("Parsing unified response from Gemini")
        
        try:
            # Clean response text (remove any markdown or extra text)
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            cleaned_text = cleaned_text.strip()
            
            # Parse JSON
            script_data = json.loads(cleaned_text)
            
            # Validate structure
            if self._validate_output_structure(script_data):
                logger.info("Response validation successful")
                return script_data
            else:
                raise ValueError("Response structure validation failed")
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.error(f"Response text: {response_text[:500]}...")
            raise ValueError(f"Invalid JSON response: {e}")
        except Exception as e:
            logger.error(f"Response parsing error: {e}")
            raise
    
    def _validate_output_structure(self, script_data: Dict) -> bool:
        """Validate the output structure matches expected format."""
        logger.info("Validating output structure")
        
        try:
            # Check required top-level keys
            required_keys = ['narrative_theme', 'podcast_sections', 'script_metadata']
            for key in required_keys:
                if key not in script_data:
                    logger.error(f"Missing required key: {key}")
                    return False
            
            # Check podcast_sections structure
            sections = script_data.get('podcast_sections', [])
            if not isinstance(sections, list) or len(sections) == 0:
                logger.error("podcast_sections must be a non-empty list")
                return False
              # Validate each section has required fields based on section type
            for i, section in enumerate(sections):
                section_type = section.get('section_type')
                
                # Check section_type is valid
                valid_types = ['intro', 'pre_clip', 'video_clip', 'post_clip', 'outro']
                if section_type not in valid_types:
                    logger.error(f"Invalid section_type: {section_type}")
                    return False
                
                # Common required fields for all sections
                common_keys = ['section_type', 'section_id', 'estimated_duration']
                for key in common_keys:
                    if key not in section:
                        logger.error(f"Section {i} missing required key: {key}")
                        return False
                
                # Section-specific required fields
                if section_type == 'video_clip':
                    video_clip_keys = ['clip_id', 'start_time', 'end_time', 'title', 'selection_reason', 'severity_level', 'key_claims']
                    for key in video_clip_keys:
                        if key not in section:
                            logger.error(f"Video clip section {i} missing required key: {key}")
                            return False
                else:
                    # All other section types require audio_tone and script_content
                    other_section_keys = ['script_content', 'audio_tone']
                    for key in other_section_keys:
                        if key not in section:
                            logger.error(f"Section {i} missing required key: {key}")
                            return False
                    
                    # Pre-clip and post-clip sections also need clip_reference
                    if section_type in ['pre_clip', 'post_clip']:
                        if 'clip_reference' not in section:
                            logger.error(f"{section_type} section {i} missing required key: clip_reference")
                            return False
            
            # Check metadata structure
            metadata = script_data.get('script_metadata', {})
            required_metadata_keys = ['timeline_ready', 'tts_segments_count']
            for key in required_metadata_keys:
                if key not in metadata:
                    logger.error(f"Missing metadata key: {key}")
                    return False
            
            if not metadata.get('timeline_ready'):
                logger.error("timeline_ready must be true")
                return False
            
            logger.info("Output structure validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False
    
    def generate_unified_narrative(self, analysis_json_path: str, episode_title: str, 
                                 custom_instructions: str = "") -> Dict:
        """
        Generate unified narrative script-timeline structure from analysis data.
        
        Args:
            analysis_json_path: Path to the analysis JSON file
            episode_title: Title of the episode for context
            custom_instructions: Optional custom instructions to add to prompt
            
        Returns:
            Dict containing the unified script-timeline structure
        """
        logger.info(f"Starting unified narrative generation for: {episode_title}")
        logger.info(f"Analysis file: {analysis_json_path}")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempt {attempt + 1}/{max_retries}")
                
                # Step 1: Upload analysis file to Gemini
                uploaded_file = self._upload_analysis_file(analysis_json_path, episode_title)
                if not uploaded_file:
                    raise Exception("File upload failed")
                
                # Step 2: Build unified prompt
                prompt_text = self._build_unified_prompt(episode_title, custom_instructions)
                
                # Step 3: Create model and generate response
                model = self._create_model()
                logger.info("Sending request to Gemini with uploaded file")
                
                response = model.generate_content([prompt_text, uploaded_file])
                
                # Step 4: Check response validity
                if not response:
                    raise Exception("No response from Gemini")
                
                # Check for safety blocks
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'finish_reason'):
                        finish_reason = candidate.finish_reason
                        logger.info(f"Gemini finish reason: {finish_reason}")
                        
                        if finish_reason == 2:  # SAFETY
                            logger.warning("Gemini blocked response due to safety concerns")
                            raise Exception("SAFETY_BLOCKED: Content was blocked by Gemini's safety filters")
                        elif finish_reason == 3:  # RECITATION
                            logger.warning("Gemini blocked response due to recitation concerns")
                            raise Exception("RECITATION_BLOCKED: Content was blocked due to potential recitation")
                        elif finish_reason != 1:  # 1 = STOP (successful completion)
                            logger.warning(f"Unexpected finish reason: {finish_reason}")
                            raise Exception(f"BLOCKED: Finish reason {finish_reason}")                # Step 5: Parse and validate response
                response_text = response.text
                logger.info(f"Received response: {len(response_text)} characters")
                
                # Save debug files using the new method
                self._save_debug_files(prompt_text, response_text, analysis_json_path)
                
                script_data = self._parse_unified_response(response_text, episode_title)
                
                logger.info("Unified narrative generation completed successfully")
                return script_data
                
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    logger.error("All retry attempts failed")
                    raise Exception(f"Failed to generate narrative after {max_retries} attempts: {e}")
                else:
                    logger.info(f"Retrying in 5 seconds...")
                    time.sleep(5)
    
    def save_unified_script(self, script_data: Dict, episode_output_path: str) -> Path:
        """
        Save the unified script-timeline JSON to the episode's Scripts folder.
        
        Args:
            script_data: The unified script-timeline data
            episode_output_path: Path to the episode's output directory
            
        Returns:
            Path to the saved JSON file
        """
        logger.info(f"Saving unified script to: {episode_output_path}")
        
        try:
            # Create Scripts directory if it doesn't exist
            scripts_dir = Path(episode_output_path) / "Scripts"
            scripts_dir.mkdir(parents=True, exist_ok=True)
            
            # Define output file path
            output_file = scripts_dir / "unified_podcast_script.json"
            
            # Save the script data
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(script_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Unified script saved successfully: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Error saving unified script: {e}")
            raise
    
    def _save_debug_files(self, prompt_text: str, response_text: str, analysis_json_path: str) -> None:
        """Save debug copies of the unified prompt and Gemini response to Processing folder."""
        try:
            # Find the Processing folder by navigating from the analysis file path
            analysis_path = Path(analysis_json_path)
            processing_folder = analysis_path.parent  # Should be the Processing folder
            
            if not processing_folder.exists():
                logger.warning(f"Processing folder not found: {processing_folder}")
                return
            
            # Generate timestamp for unique filenames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save unified prompt
            prompt_file = processing_folder / f"debug_unified_prompt_{timestamp}.txt"
            with open(prompt_file, 'w', encoding='utf-8') as f:
                f.write("=== UNIFIED NARRATIVE PROMPT ===\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n")
                f.write(f"Character count: {len(prompt_text)}\n")
                f.write("=" * 50 + "\n\n")
                f.write(prompt_text)
            
            # Save Gemini response
            response_file = processing_folder / f"debug_gemini_response_{timestamp}.txt"
            with open(response_file, 'w', encoding='utf-8') as f:
                f.write("=== GEMINI RESPONSE ===\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n")
                f.write(f"Character count: {len(response_text)}\n")
                f.write("=" * 50 + "\n\n")
                f.write(response_text)
            
            logger.info(f"Debug files saved:")
            logger.info(f"  Prompt: {prompt_file}")
            logger.info(f"  Response: {response_file}")
            
        except Exception as e:
            logger.error(f"Failed to save debug files: {e}")


def main():
    """Command line interface for testing."""
    if len(sys.argv) < 3:
        print("Usage: python podcast_narrative_generator.py <analysis_json_path> <episode_title> [output_path]")
        sys.exit(1)
    
    analysis_json_path = sys.argv[1]
    episode_title = sys.argv[2]
    output_path = sys.argv[3] if len(sys.argv) > 3 else "."
    
    try:
        generator = NarrativeCreatorGenerator()
        script_data = generator.generate_unified_narrative(analysis_json_path, episode_title)
        saved_path = generator.save_unified_script(script_data, output_path)
        print(f"Success! Script saved to: {saved_path}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()