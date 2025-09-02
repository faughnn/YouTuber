"""
JSON Parser and Validator for Chatterbox TTS Processing

This module handles parsing and validation of podcast script files that contain
the podcast_sections[] format. It extracts audio sections for TTS processing
and validates the structure according to the expected schema.

Adapted from Audio_Generation/json_parser.py with simplifications for Chatterbox TTS:
- Removed audio_tone processing (Chatterbox uses fixed parameters)
- Simplified validation rules
- Maintained interface compatibility with existing pipeline
"""

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class AudioSection:
    """Simplified audio section for Chatterbox TTS processing."""
    section_id: str
    section_type: str  # intro, pre_clip, post_clip, outro
    script_content: str
    estimated_duration: str
    clip_reference: Optional[str] = None  # For pre_clip and post_clip sections
    # Note: audio_tone removed - not needed for fixed-parameter Chatterbox


@dataclass
class EpisodeInfo:
    """Episode metadata extracted from the response."""
    narrative_theme: str
    total_estimated_duration: str
    target_audience: str
    key_themes: List[str]
    total_clips_analyzed: int
    source_file: str


@dataclass
class ValidationResult:
    """Result of JSON validation with details about the structure."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    audio_section_count: int
    video_section_count: int
    episode_info: Optional[EpisodeInfo] = None


class ChatterboxResponseParser:
    """
    Parser for podcast script files with podcast_sections[] format.
    
    Simplified version of the original GeminiResponseParser, adapted for Chatterbox TTS.
    Handles both clean JSON files and debug response files that may contain
    additional text around the JSON structure.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
          # Valid section types
        self.audio_section_types = {'intro', 'intro_plus_hook_analysis', 'pre_clip', 'post_clip', 'outro'}
        self.video_section_types = {'video_clip', 'hook_clip'}
        self.all_section_types = self.audio_section_types | self.video_section_types
        
        # Required fields for different section types (simplified for Chatterbox)
        self.common_required_fields = {'section_type', 'section_id', 'estimated_duration'}
        self.audio_required_fields = self.common_required_fields | {'script_content'}
        # Note: audio_tone removed from required fields
        self.video_required_fields = self.common_required_fields | {
            'clip_id', 'start_time', 'end_time', 'title', 'selection_reason', 
            'severity_level', 'key_claims'
        }
        self.clip_reference_sections = {'pre_clip', 'post_clip'}

    def parse_response_file(self, file_path: Union[str, Path]) -> Dict:
        """
        Parse a podcast script file and extract the JSON structure.
        
        Args:
            file_path: Path to the verified_unified_script.json file (two-pass quality control required)
            
        Returns:
            Parsed JSON data as dictionary
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If JSON cannot be parsed
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Response file not found: {file_path}")
        
        self.logger.info(f"Parsing response file: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try to extract JSON from the content
            json_data = self._extract_json_from_content(content)
            
            self.logger.info(f"Successfully parsed JSON with {len(json_data.get('podcast_sections', []))} sections")
            return json_data
            
        except Exception as e:
            self.logger.error(f"Failed to parse response file: {e}")
            raise ValueError(f"Unable to parse JSON from file {file_path}: {e}")

    def _extract_json_from_content(self, content: str) -> Dict:
        """
        Extract JSON from content that might contain debug text or formatting.
        
        Args:
            content: Raw file content
            
        Returns:
            Parsed JSON data
        """
        # Try direct JSON parsing first
        try:
            return json.loads(content.strip())
        except json.JSONDecodeError:
            pass
        
        # Look for JSON structure within the content
        json_patterns = [
            r'\{.*"podcast_sections".*\}',  # JSON with podcast_sections
            r'\{.*\}',  # Any JSON-like structure
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            for match in matches:
                try:
                    # Clean up the match
                    cleaned = match.strip()
                    
                    # Try to balance braces if needed
                    if cleaned.count('{') > cleaned.count('}'):
                        cleaned += '}' * (cleaned.count('{') - cleaned.count('}'))
                    
                    data = json.loads(cleaned)
                    if 'podcast_sections' in data:
                        return data
                except json.JSONDecodeError:
                    continue
        
        # If no valid JSON found, try line-by-line approach
        lines = content.split('\n')
        json_lines = []
        in_json = False
        brace_count = 0
        
        for line in lines:
            if '{' in line and not in_json:
                in_json = True
                brace_count = line.count('{') - line.count('}')
                json_lines.append(line)
            elif in_json:
                json_lines.append(line)
                brace_count += line.count('{') - line.count('}')
                if brace_count <= 0:
                    break
        
        if json_lines:
            try:
                return json.loads('\n'.join(json_lines))
            except json.JSONDecodeError:
                pass
        
        raise ValueError("No valid JSON structure found in content")

    def validate_podcast_sections(self, data: Dict) -> ValidationResult:
        """
        Validate the podcast_sections structure and content.
        
        Args:
            data: Parsed JSON data
            
        Returns:
            ValidationResult with validation details
        """
        errors = []
        warnings = []
        
        self.logger.info("Validating podcast sections structure")
        
        # Check top-level structure
        required_top_keys = {'narrative_theme', 'podcast_sections', 'script_metadata'}
        missing_keys = required_top_keys - set(data.keys())
        if missing_keys:
            errors.append(f"Missing required top-level keys: {missing_keys}")
        
        # Validate podcast_sections array
        sections = data.get('podcast_sections', [])
        if not isinstance(sections, list):
            errors.append("podcast_sections must be a list")
            return ValidationResult(False, errors, warnings, 0, 0)
        
        if len(sections) == 0:
            errors.append("podcast_sections cannot be empty")
            return ValidationResult(False, errors, warnings, 0, 0)
        
        # Validate individual sections
        audio_count = 0
        video_count = 0
        section_ids = set()
        
        for i, section in enumerate(sections):
            section_errors = self._validate_section(section, i)
            errors.extend(section_errors)
            
            # Count sections by type and check for duplicates
            section_type = section.get('section_type')
            section_id = section.get('section_id')
            
            if section_id:
                if section_id in section_ids:
                    errors.append(f"Duplicate section_id: {section_id}")
                section_ids.add(section_id)
            
            if section_type in self.audio_section_types:
                audio_count += 1
            elif section_type in self.video_section_types:
                video_count += 1
        
        # Validate episode metadata
        episode_info = None
        try:
            episode_info = self._extract_episode_metadata(data)
        except Exception as e:
            warnings.append(f"Could not extract episode metadata: {e}")
        
        # Check for logical structure
        if audio_count == 0:
            warnings.append("No audio sections found - nothing to generate")
        
        is_valid = len(errors) == 0
        
        self.logger.info(f"Validation complete: {audio_count} audio sections, {video_count} video sections, {len(errors)} errors")
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            audio_section_count=audio_count,
            video_section_count=video_count,
            episode_info=episode_info
        )

    def _validate_section(self, section: Dict, index: int) -> List[str]:
        """Validate an individual section structure."""
        errors = []
        
        if not isinstance(section, dict):
            errors.append(f"Section {index} must be a dictionary")
            return errors
        
        section_type = section.get('section_type')
        
        # Validate section_type
        if not section_type:
            errors.append(f"Section {index}: missing section_type")
            return errors
        
        if section_type not in self.all_section_types:
            errors.append(f"Section {index}: invalid section_type '{section_type}'")
        
        # Validate required fields based on section type
        if section_type in self.audio_section_types:
            missing_fields = self.audio_required_fields - set(section.keys())
            if missing_fields:
                errors.append(f"Section {index} ({section_type}): missing required fields {missing_fields}")
            
            # Check for clip_reference requirement
            if section_type in self.clip_reference_sections and 'clip_reference' not in section:
                errors.append(f"Section {index} ({section_type}): missing required clip_reference")
                
        elif section_type in self.video_section_types:
            missing_fields = self.video_required_fields - set(section.keys())
            if missing_fields:
                errors.append(f"Section {index} ({section_type}): missing required fields {missing_fields}")
        
        # Validate field content
        section_id = section.get('section_id', '')
        if section_id and not self._is_valid_section_id(section_id, section_type):
            errors.append(f"Section {index}: invalid section_id format '{section_id}'")
        
        script_content = section.get('script_content', '')
        if section_type in self.audio_section_types and not script_content.strip():
            errors.append(f"Section {index}: script_content cannot be empty for audio sections")
        
        return errors

    def _is_valid_section_id(self, section_id: str, section_type: str) -> bool:
        """Validate section_id format matches expected pattern."""
        # Expected pattern: {section_type}_{number}
        pattern = rf'^{section_type}_\d{{3}}$'
        return bool(re.match(pattern, section_id))

    def extract_audio_sections(self, sections: List[Dict]) -> List[AudioSection]:
        """
        Extract and convert audio sections to AudioSection objects.
        
        Args:
            sections: List of all sections from podcast_sections
            
        Returns:
            List of AudioSection objects for TTS processing
        """
        audio_sections = []
        
        for section in sections:
            section_type = section.get('section_type')
            
            if section_type in self.audio_section_types:
                audio_section = AudioSection(
                    section_id=section['section_id'],
                    section_type=section_type,
                    script_content=section['script_content'],
                    estimated_duration=section['estimated_duration'],
                    clip_reference=section.get('clip_reference')
                    # Note: audio_tone field removed - not needed for Chatterbox
                )
                audio_sections.append(audio_section)
        
        self.logger.info(f"Extracted {len(audio_sections)} audio sections for TTS processing")
        return audio_sections

    def _extract_episode_metadata(self, data: Dict) -> EpisodeInfo:
        """Extract episode metadata from the response data."""
        metadata = data.get('script_metadata', {})
        
        return EpisodeInfo(
            narrative_theme=data.get('narrative_theme', 'Unknown Theme'),
            total_estimated_duration=metadata.get('total_estimated_duration', 'Unknown'),
            target_audience=metadata.get('target_audience', 'General'),
            key_themes=metadata.get('key_themes', []),
            total_clips_analyzed=int(metadata.get('total_clips_analyzed', 0)),
            source_file=''  # Will be set by caller
        )

    def extract_episode_metadata(self, data: Dict) -> EpisodeInfo:
        """
        Public method to extract episode metadata.
        
        Args:
            data: Parsed JSON data
            
        Returns:
            EpisodeInfo object with metadata
        """
        return self._extract_episode_metadata(data)

    def parse_episode_script(self, episode_dir: Union[str, Path]) -> Dict:
        """
        Parse episode script - requires verified script from two-pass quality control.
        
        Args:
            episode_dir: Path to episode directory
            
        Returns:
            Parsed JSON data as dictionary
            
        Raises:
            FileNotFoundError: If verified script doesn't exist
            ValueError: If JSON cannot be parsed
        """
        episode_dir = Path(episode_dir)
        scripts_dir = episode_dir / "Output" / "Scripts"
        
        # Only use verified scripts - two-pass quality control is mandatory
        verified_script = scripts_dir / "verified_unified_script.json"
        
        if not verified_script.exists():
            raise FileNotFoundError(
                f"Verified script file not found: {verified_script}. "
                f"Run the complete two-pass pipeline to generate verified scripts."
            )
        
        self.logger.info("Using verified unified script (two-pass quality control)")
        return self.parse_response_file(verified_script)
