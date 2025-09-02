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
        self.api_key = os.getenv('GEMINI_API_KEY')  # From environment variable
        self.model_name = "gemini-2.5-pro-preview-06-05"  # Fixed model name
        # Initialize Gemini API
        self._configure_gemini()
        
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
    
    def _load_prompt_template(self, prompt_file_path: str) -> str:
        """Load the prompt template from file."""
        try:
            with open(prompt_file_path, 'r', encoding='utf-8') as f:
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
    def _extract_guest_name_from_title(self, episode_title: str) -> str:
        """
        Extract guest name from folder structure.
        
        Args:
            episode_title: Episode title (usually folder name) from master processor
            
        Returns:
            str: Extracted guest name or "Unknown Guest"
        """
        try:
            # Use the folder structure to extract names
            host_name, guest_name = self._extract_host_and_guest_names_from_path(episode_title)
            logger.info(f"Extracted guest name from folder structure: {guest_name}")
            return guest_name
        except Exception as e:
            logger.error(f"Error extracting guest name: {e}")
            return "Unknown Guest"
        for pattern in folder_patterns:
            match = re.search(pattern, episode_title)
            if match:
                if pattern.startswith("Tucker_Carlson"):
                    # For Tucker Carlson format, extract the guest name after "Tucker_Carlson_"
                    guest_string = match.group(1).strip()
                    logger.info(f"Extracted guest string using Tucker Carlson pattern: {guest_string}")
                    return self._parse_multiple_guests(guest_string)
                elif len(match.groups()) == 3:
                    # For three-part format, assume middle part is host, last part is guest
                    guest_string = match.group(3).strip()
                    logger.info(f"Extracted guest string using three-part pattern: {guest_string}")
                    return self._parse_multiple_guests(guest_string)
                elif len(match.groups()) == 2:
                    # For two-part format, assume second part is guest
                    guest_string = match.group(2).strip()
                    logger.info(f"Extracted guest string using two-part pattern: {guest_string}")
                    return self._parse_multiple_guests(guest_string)
        
        # Fallback to YouTube title patterns
        youtube_patterns = [
            r"Joe Rogan Experience #\d+ - (.+)",  # JRE format: "Joe Rogan Experience #2325 - Aaron Rodgers"
            r"(.+) #\d+ - (.+)",                  # General format with episode number
            r"(.+) - (.+)",                       # Simple dash format
            r"(.+) with (.+)",                    # "with" format
            r"(.+): (.+)"                         # Colon format
        ]
        
        for pattern in youtube_patterns:
            match = re.search(pattern, episode_title)
            if match:
                # For JRE format, return the guest name after the dash
                if "Joe Rogan Experience" in pattern:
                    guest_string = match.group(1).strip()
                    logger.info(f"Extracted guest string using JRE pattern: {guest_string}")
                    return self._parse_multiple_guests(guest_string)
                # For other formats, return the second group (assuming it's the guest)
                else:
                    guest_string = match.group(2).strip()
                    logger.info(f"Extracted guest string using YouTube pattern: {guest_string}")
                    return self._parse_multiple_guests(guest_string)
        
        logger.warning(f"Could not extract guest name from title: {episode_title}")
        return "Unknown Guest"
    
    def _parse_multiple_guests(self, guest_string: str) -> str:
        """
        Parse a guest string that may contain multiple guests and format appropriately.
        
        Args:
            guest_string: Raw guest string extracted from title
            
        Returns:
            str: Properly formatted guest name(s)
        """
        import re
        
        # Common separators for multiple guests
        separators = [
            r'\s+&\s+',           # " & "
            r'\s+and\s+',         # " and "
            r',\s+and\s+',        # ", and "
            r',\s+',              # ", "
            r'\s+with\s+',        # " with "
        ]
        
        # Try to split on common separators
        guests = [guest_string]  # Start with the whole string
        
        for separator in separators:
            if re.search(separator, guest_string):
                guests = re.split(separator, guest_string)
                break
        
        # Clean up each guest name
        cleaned_guests = []
        for guest in guests:
            cleaned = guest.strip()
            # Remove common prefixes/suffixes that might indicate roles
            cleaned = re.sub(r'^(Dr\.?|Professor|Prof\.?|Mr\.?|Ms\.?|Mrs\.?)\s+', '', cleaned)
            if cleaned:
                cleaned_guests.append(cleaned)
        
        if len(cleaned_guests) == 1:
            logger.info(f"Single guest identified: {cleaned_guests[0]}")
            return cleaned_guests[0]
        elif len(cleaned_guests) == 2:
            result = f"{cleaned_guests[0]} and {cleaned_guests[1]}"
            logger.info(f"Two guests identified: {result}")
            return result
        elif len(cleaned_guests) > 2:
            # For 3+ guests: "Name1, Name2, and Name3"
            result = ", ".join(cleaned_guests[:-1]) + f", and {cleaned_guests[-1]}"
            logger.info(f"Multiple guests identified: {result}")
            return result
        else:
            logger.warning(f"Could not parse guests from: {guest_string}")
            return guest_string

    def _build_unified_prompt(self, episode_title: str, custom_instructions: str = "") -> str:
        """Build the unified prompt that references the uploaded analysis file."""
        logger.info("Building unified narrative prompt")
        
        # Extract both host and guest names from episode title (folder structure)
        host_name = self._extract_host_name_from_title(episode_title)
        guest_name = self._extract_guest_name_from_title(episode_title)
        logger.info(f"Extracted host name: {host_name} and guest name: {guest_name} from episode title: {episode_title}")
        
        # Inject episode context at the beginning of the prompt
        episode_context = f"""
## EPISODE CONTEXT

**Episode Title:** {episode_title}
**Host Name:** {host_name}
**Guest Name:** {guest_name}

**CRITICAL INSTRUCTION:** Use "{host_name}" as the host's name and "{guest_name}" as the guest's name throughout your script. Do NOT try to research or infer different participant names from the analysis data. These are the authoritative names extracted from the folder structure.

---

"""
        
        # Combine episode context with the original prompt template
        formatted_prompt = episode_context + self.prompt_template
        
        # Add custom instructions if provided
        if custom_instructions.strip():
            formatted_prompt += f"\n\n## ADDITIONAL INSTRUCTIONS\n{custom_instructions}\n"
        
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
                section_type = section.get('section_type')                # Check section_type is valid (supporting both old and new structures)
                old_types = ['intro', 'pre_clip', 'video_clip', 'post_clip', 'outro']
                new_types = ['hook_clip', 'intro_plus_hook_analysis', 'pre_clip', 'video_clip', 'post_clip', 'outro']
                valid_types = old_types + new_types
                # Remove duplicates while preserving order
                valid_types = list(dict.fromkeys(valid_types))
                
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
                if section_type in ['video_clip', 'hook_clip']:
                    video_clip_keys = ['clip_id', 'start_time', 'end_time', 'title', 'selection_reason', 
                                     'severity_level', 'key_claims', 'suggestedClip']
                    for key in video_clip_keys:
                        if key not in section:
                            logger.error(f"Video clip section {i} missing required key: {key}")
                            return False
                    
                    # Validate suggestedClip structure
                    suggested_clip = section.get('suggestedClip', [])
                    if not isinstance(suggested_clip, list):
                        logger.error(f"Video clip section {i}: suggestedClip must be a list")
                        return False
                    
                    # Validate each clip entry in suggestedClip
                    for j, clip_entry in enumerate(suggested_clip):
                        if not isinstance(clip_entry, dict):
                            logger.error(f"Video clip section {i}, suggestedClip entry {j}: must be a dict")
                            return False
                        
                        clip_required_keys = ['timestamp', 'speaker', 'quote']
                        for key in clip_required_keys:
                            if key not in clip_entry:
                                logger.error(f"Video clip section {i}, suggestedClip entry {j} missing key: {key}")
                                return False                
                elif section_type in ['intro', 'outro']:
                    # Intro and outro sections require script_content
                    if 'script_content' not in section:
                        logger.error(f"{section_type} section {i} missing required key: script_content")
                        return False
                
                elif section_type == 'intro_plus_hook_analysis':
                    # intro_plus_hook_analysis requires script_content and hook_clip_reference
                    required_keys = ['script_content', 'hook_clip_reference']
                    for key in required_keys:
                        if key not in section:
                            logger.error(f"{section_type} section {i} missing required key: {key}")
                            return False
                
                elif section_type in ['pre_clip', 'post_clip']:
                    # Pre-clip and post-clip sections require script_content and clip_reference
                    required_keys = ['script_content', 'clip_reference']
                    for key in required_keys:
                        if key not in section:
                            logger.error(f"{section_type} section {i} missing required key: {key}")
                            return False
              # Check metadata structure
            metadata = script_data.get('script_metadata', {})
            required_metadata_keys = ['total_estimated_duration', 'target_audience', 'key_themes', 
                                    'total_clips_analyzed', 'tts_segments_count', 'timeline_ready']
            
            # Check if this is the new structure with hook_clip
            has_hook_clip = any(section.get('section_type') == 'hook_clip' for section in sections)
            if has_hook_clip:
                required_metadata_keys.append('hook_clip_id')
            
            for key in required_metadata_keys:
                if key not in metadata:
                    logger.error(f"Missing metadata key: {key}")
                    return False
            
            # Validate key_themes is a list
            if not isinstance(metadata.get('key_themes'), list):
                logger.error("script_metadata.key_themes must be a list")
                return False
            
            # Validate timeline_ready is boolean and true
            if not isinstance(metadata.get('timeline_ready'), bool):
                logger.error("script_metadata.timeline_ready must be a boolean")
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
                                 narrative_format: str, custom_instructions: str = "") -> Dict:
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
        
        max_retries = 1
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempt {attempt + 1}/{max_retries}")
                
                # Step 1: Upload analysis file to Gemini
                logger.info("📤 Uploading analysis results to Gemini for narrative generation...")
                uploaded_file = self._upload_analysis_file(analysis_json_path, episode_title)
                if not uploaded_file:
                    raise Exception("File upload failed")
                logger.info("✅ File upload completed")
                
                # Determine which prompt file to use based on narrative_format
                if narrative_format == "with_hook":
                    prompt_file_name = 'tts_podcast_narrative_prompt.txt'
                elif narrative_format == "without_hook":
                    prompt_file_name = 'tts_podcast_narrative_prompt_WITHOUT_HOOK.txt'
                else:
                    raise ValueError(f"Invalid narrative format: {narrative_format}")

                prompt_file_path = os.path.join(
                    current_dir, 'Generation_Templates', prompt_file_name
                )
                self.prompt_template = self._load_prompt_template(prompt_file_path)

                # Step 2: Build unified prompt
                prompt_text = self._build_unified_prompt(episode_title, custom_instructions)
                
                # Step 3: Create model and generate response
                model = self._create_model()
                logger.info("🤖 Sending narrative generation request to Gemini AI...")
                logger.info("⏳ This may take 1-3 minutes depending on content complexity...")
                
                response = model.generate_content([prompt_text, uploaded_file])
                
                logger.info("✅ Received response from Gemini AI")
                
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
    def _extract_host_name_from_title(self, episode_title: str) -> str:
        """
        Extract host name from folder structure.
        
        Args:
            episode_title: Episode title (usually folder name) from master processor
            
        Returns:
            str: Extracted host name or "Unknown Host"
        """
        try:
            # Use the folder structure to extract names
            host_name, guest_name = self._extract_host_and_guest_names_from_path(episode_title)
            logger.info(f"Extracted host name from folder structure: {host_name}")
            return host_name
        except Exception as e:
            logger.error(f"Error extracting host name: {e}")
            return "Unknown Host"
    
    def _extract_host_and_guest_names_from_path(self, episode_title: str):
        """
        Extract host and guest names from folder structure or file path.
        
        The folder format is ALWAYS: Content/{HOST}/{HOST}_{GUEST}/...
        Example: Tucker_Carlson_RFK_Jr -> ("Tucker Carlson", "RFK Jr")
        
        Args:
            episode_title: Episode title (usually folder name) or file path
            
        Returns:
            tuple: (host_name, guest_name) with underscores replaced by spaces
                   Returns ("Unknown Host", "Unknown Guest") if parsing fails
        """
        try:
            # If it's a full path, extract just the episode folder part
            if 'Content' in episode_title:
                # Convert to forward slashes for consistent parsing
                normalized_path = episode_title.replace('\\', '/')
                
                # Find the Content folder and extract the structure after it
                content_index = normalized_path.find('/Content/')
                if content_index != -1:
                    # Extract the part after Content/
                    path_after_content = normalized_path[content_index + 9:]  # 9 = len('/Content/')
                    path_parts = path_after_content.split('/')
                    
                    if len(path_parts) >= 2:
                        # First part is host folder name
                        host_folder = path_parts[0]
                        # Second part is the host_guest combination
                        host_guest_folder = path_parts[1]
                        
                        # Extract guest name by removing the host prefix and underscore
                        if host_guest_folder.startswith(host_folder + '_'):
                            guest_part = host_guest_folder[len(host_folder) + 1:]  # +1 for the underscore
                            
                            # Format names by replacing underscores with spaces
                            host_name = host_folder.replace('_', ' ')
                            guest_name = guest_part.replace('_', ' ')
                            
                            logger.info(f"Extracted from path - host: '{host_name}', guest: '{guest_name}'")
                            return (host_name, guest_name)
            
            # If it's just the episode folder name (like "Tucker_Carlson_RFK_Jr")
            # Try to parse it directly
            if '_' in episode_title:
                # Look for the pattern where the host name is repeated
                parts = episode_title.split('_')
                if len(parts) >= 2:
                    # Check if it follows the HOST_HOST_GUEST pattern by looking for repeats
                    # Find the longest matching prefix
                    for i in range(1, len(parts)):
                        host_candidate = '_'.join(parts[:i])
                        remaining = '_'.join(parts[i:])
                        
                        # Check if the remaining part starts with the host candidate
                        if remaining.startswith(host_candidate + '_'):
                            guest_part = remaining[len(host_candidate) + 1:]
                            if guest_part:  # Make sure there's something left for the guest
                                host_name = host_candidate.replace('_', ' ')
                                guest_name = guest_part.replace('_', ' ')
                                logger.info(f"Extracted from title pattern - host: '{host_name}', guest: '{guest_name}'")
                                return (host_name, guest_name)
                    
                    # If no pattern matches, fall back to simple split
                    if len(parts) >= 2:
                        # Try to guess: if we have an even number of parts, split in half
                        # Otherwise, take the first part as host, rest as guest
                        if len(parts) % 2 == 0:
                            mid = len(parts) // 2
                            host_name = '_'.join(parts[:mid]).replace('_', ' ')
                            guest_name = '_'.join(parts[mid:]).replace('_', ' ')
                        else:
                            host_name = parts[0].replace('_', ' ')
                            guest_name = '_'.join(parts[1:]).replace('_', ' ')
                        
                        logger.info(f"Extracted from title (fallback) - host: '{host_name}', guest: '{guest_name}'")
                        return (host_name, guest_name)
                        
        except Exception as e:
            logger.error(f"Error extracting names from path/title: {e}")
        
        logger.warning(f"Could not extract names from: {episode_title}")
        return ("Unknown Host", "Unknown Guest")


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