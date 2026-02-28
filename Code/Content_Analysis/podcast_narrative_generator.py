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

from google import genai
from google.genai import types

# Global client for Gemini API
_gemini_client = None

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
        self.model_name = "gemini-2.5-pro"  # Fixed model name
        # Initialize Gemini API
        self._configure_gemini()
        
        logger.info("NarrativeCreatorGenerator initialized successfully")
    
    def _configure_gemini(self) -> bool:
        """Configure Gemini API connection using new google.genai Client pattern."""
        global _gemini_client
        logger.info("Configuring Gemini API")
        try:
            if self.api_key:
                _gemini_client = genai.Client(api_key=self.api_key)
                logger.info("Gemini API client configured successfully")
                return True
            else:
                logger.error("No API key found")
                return False
        except Exception as e:
            logger.error(f"Error configuring Gemini API: {e}")
            return False

    def _get_client(self):
        """Get the Gemini client, initializing if needed."""
        global _gemini_client
        if _gemini_client is None:
            if not self._configure_gemini():
                raise Exception("Failed to configure Gemini API client")
        return _gemini_client
    
    def _resolve_conditionals(self, template: str, has_hook: bool) -> str:
        """Resolve {%if has_hook%}...{%else%}...{%endif%} conditionals in template."""
        import re
        pattern = r'\{%if has_hook%\}(.*?)\{%else%\}(.*?)\{%endif%\}'

        def replacer(match):
            if has_hook:
                return match.group(1)
            else:
                return match.group(2)

        return re.sub(pattern, replacer, template, flags=re.DOTALL)

    def _load_persona(self) -> str:
        """Load the canonical persona definition from file."""
        persona_path = os.path.join(current_dir, 'Generation_Templates', 'persona_definition.txt')
        try:
            with open(persona_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            logger.error(f"Error loading persona definition: {e}")
            raise

    def _load_prompt_template(self, prompt_file_path: str) -> str:
        """Load the prompt template from file and inject persona."""
        try:
            with open(prompt_file_path, 'r', encoding='utf-8') as f:
                template = f.read()
            # Inject persona definition
            persona = self._load_persona()
            template = template.replace('{persona_definition}', persona)
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
            # Upload file using the new google.genai Client pattern
            client = self._get_client()
            display_name = f"Analysis Results - {episode_title}"
            logger.info(f"Uploading to Gemini with display name: {display_name}")

            uploaded_file = client.files.upload(
                file=analysis_json_path,
                config=types.UploadFileConfig(
                    mime_type="text/plain",
                    display_name=display_name
                )
            )

            logger.info(f"File uploaded successfully: {uploaded_file.name}")
            logger.info(f"File URI: {uploaded_file.uri}")

            # Wait for processing to complete
            while uploaded_file.state.name == "PROCESSING":
                logger.info("Waiting for file processing...")
                time.sleep(2)
                uploaded_file = client.files.get(name=uploaded_file.name)

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
    
    def _get_generation_config(self):
        """Get the generation configuration for Gemini API calls.

        Includes Google Search grounding to verify facts during rebuttal generation,
        such as checking current/historical positions of people mentioned.
        """
        return types.GenerateContentConfig(
            temperature=0.6,
            top_p=0.9,
            candidate_count=1,
            response_mime_type="application/json",
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
                
                # Common required fields for all sections - add defaults if missing
                if 'section_id' not in section:
                    section['section_id'] = f"section_{i:03d}"
                    logger.warning(f"Section {i} missing section_id, using default: {section['section_id']}")
                if 'estimated_duration' not in section:
                    section['estimated_duration'] = "30 seconds"
                    logger.warning(f"Section {i} missing estimated_duration, using default: {section['estimated_duration']}")
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
            
            # Add default values for missing metadata keys
            metadata_defaults = {
                'total_estimated_duration': '10 minutes',
                'target_audience': 'General audience interested in political discourse',
                'key_themes': ['political commentary', 'media analysis'],
                'total_clips_analyzed': len([s for s in sections if s.get('section_type') in ['video_clip', 'hook_clip']]),
                'tts_segments_count': len([s for s in sections if s.get('section_type') not in ['video_clip', 'hook_clip']]),
                'timeline_ready': True
            }
            for key in required_metadata_keys:
                if key not in metadata:
                    if key in metadata_defaults:
                        metadata[key] = metadata_defaults[key]
                        logger.warning(f"Missing metadata key: {key}, using default: {metadata[key]}")
                    else:
                        logger.warning(f"Missing metadata key: {key}, no default available")
            
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
    
    def _check_response_safety(self, response) -> None:
        """Check Gemini response for safety blocks and raise on critical issues."""
        if not response:
            raise Exception("No response from Gemini")

        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'finish_reason'):
                finish_reason = candidate.finish_reason
                finish_str = str(finish_reason).upper()
                logger.info(f"Gemini finish reason: {finish_reason}")

                if 'SAFETY' in finish_str:
                    raise Exception("SAFETY_BLOCKED: Content was blocked by Gemini's safety filters")
                elif 'RECITATION' in finish_str:
                    raise Exception("RECITATION_BLOCKED: Content was blocked due to potential recitation")
                elif 'MAX_TOKENS' in finish_str:
                    logger.warning("Response may be truncated due to MAX_TOKENS")
                elif 'STOP' not in finish_str and finish_reason not in [1, 'STOP']:
                    logger.warning(f"Unexpected finish reason: {finish_reason}")

    def _generate_structure_plan(self, uploaded_file, episode_title: str, narrative_format: str) -> Dict:
        """
        Call 1: Generate structure plan (temp 0.3).

        Returns:
            Dict containing the structure plan
        """
        logger.info("📋 Call 1/2: Generating structure plan...")

        # Load structure prompt
        structure_prompt_path = os.path.join(
            current_dir, 'Generation_Templates', 'narrative_structure_prompt.txt'
        )
        with open(structure_prompt_path, 'r', encoding='utf-8') as f:
            structure_prompt = f.read()

        # Add episode context
        host_name = self._extract_host_name_from_title(episode_title)
        guest_name = self._extract_guest_name_from_title(episode_title)

        episode_context = f"""
## EPISODE CONTEXT
**Episode Title:** {episode_title}
**Host Name:** {host_name}
**Guest Name:** {guest_name}
**Narrative Format:** {narrative_format}

---

"""
        full_prompt = episode_context + structure_prompt

        client = self._get_client()
        response = client.models.generate_content(
            model=self.model_name,
            contents=[full_prompt, uploaded_file],
            config=types.GenerateContentConfig(
                temperature=0.3,
                top_p=0.9,
                candidate_count=1,
                response_mime_type="application/json",
            )
        )

        self._check_response_safety(response)

        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        structure_plan = json.loads(response_text.strip())
        logger.info("✅ Structure plan generated")
        return structure_plan

    def _generate_creative_script(self, uploaded_file, structure_plan: Dict,
                                   episode_title: str, narrative_format: str) -> Dict:
        """
        Call 2: Generate creative script from structure plan (temp 0.6).

        Returns:
            Dict containing the final podcast script
        """
        logger.info("🎨 Call 2/2: Generating creative script...")

        # Load creative prompt
        creative_prompt_path = os.path.join(
            current_dir, 'Generation_Templates', 'narrative_creative_prompt.txt'
        )
        with open(creative_prompt_path, 'r', encoding='utf-8') as f:
            creative_prompt = f.read()

        # Inject persona
        persona = self._load_persona()
        creative_prompt = creative_prompt.replace('{persona_definition}', persona)

        # Inject structure plan
        creative_prompt = creative_prompt.replace(
            '{structure_plan}', json.dumps(structure_plan, indent=2)
        )

        # Build output format section based on narrative format
        # Load the main template to get the output format
        main_prompt_path = os.path.join(
            current_dir, 'Generation_Templates', 'tts_podcast_narrative_prompt.txt'
        )
        main_template = self._load_prompt_template(main_prompt_path)
        has_hook = narrative_format == "with_hook"
        main_template = self._resolve_conditionals(main_template, has_hook)

        # Extract just the output format section
        import re
        output_match = re.search(
            r'## 6\. MANDATORY OUTPUT FORMAT\s*\n(.*?)(?=\n## 7\.|\Z)',
            main_template, re.DOTALL
        )
        output_format = output_match.group(1).strip() if output_match else ""
        creative_prompt = creative_prompt.replace('{output_format}', output_format)

        # Add episode context
        host_name = self._extract_host_name_from_title(episode_title)
        guest_name = self._extract_guest_name_from_title(episode_title)

        episode_context = f"""
## EPISODE CONTEXT
**Episode Title:** {episode_title}
**Host Name:** {host_name}
**Guest Name:** {guest_name}

**CRITICAL INSTRUCTION:** Use "{host_name}" as the host's name and "{guest_name}" as the guest's name throughout your script.

---

"""
        full_prompt = episode_context + creative_prompt

        client = self._get_client()
        response = client.models.generate_content(
            model=self.model_name,
            contents=[full_prompt, uploaded_file],
            config=types.GenerateContentConfig(
                temperature=0.6,
                top_p=0.9,
                candidate_count=1,
                response_mime_type="application/json",
            )
        )

        self._check_response_safety(response)

        response_text = response.text
        logger.info(f"Received creative script: {len(response_text)} characters")
        return response_text

    def generate_unified_narrative(self, analysis_json_path: str, episode_title: str,
                                 narrative_format: str, custom_instructions: str = "") -> Dict:
        """
        Generate unified narrative via 2-call approach: structure plan + creative script.

        Args:
            analysis_json_path: Path to the analysis JSON file
            episode_title: Title of the episode for context
            narrative_format: "with_hook" or "without_hook"
            custom_instructions: Optional custom instructions to add to prompt

        Returns:
            Dict containing the unified script-timeline structure
        """
        logger.info(f"Starting 2-call narrative generation for: {episode_title}")
        logger.info(f"Analysis file: {analysis_json_path}")

        try:
            # Step 1: Upload analysis file to Gemini
            logger.info("📤 Uploading analysis results to Gemini...")
            uploaded_file = self._upload_analysis_file(analysis_json_path, episode_title)
            if not uploaded_file:
                raise Exception("File upload failed")
            logger.info("✅ File upload completed")

            # Step 2: Generate structure plan (Call 1, temp 0.3)
            structure_plan = self._generate_structure_plan(
                uploaded_file, episode_title, narrative_format
            )

            # Save structure plan for debugging
            analysis_path = Path(analysis_json_path)
            processing_folder = analysis_path.parent
            if processing_folder.exists():
                plan_path = processing_folder / "structure_plan.json"
                with open(plan_path, 'w', encoding='utf-8') as f:
                    json.dump(structure_plan, f, indent=2, ensure_ascii=False)
                logger.info(f"Structure plan saved to: {plan_path}")

            # Step 3: Generate creative script (Call 2, temp 0.6)
            response_text = self._generate_creative_script(
                uploaded_file, structure_plan, episode_title, narrative_format
            )

            # Save debug files
            self._save_debug_files("[2-call approach]", response_text, analysis_json_path)

            # Step 4: Parse and validate response
            script_data = self._parse_unified_response(response_text, episode_title)

            logger.info("2-call narrative generation completed successfully")
            return script_data

        except Exception as e:
            logger.error(f"Narrative generation failed: {e}")
            raise Exception(f"Failed to generate narrative: {e}")
    
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