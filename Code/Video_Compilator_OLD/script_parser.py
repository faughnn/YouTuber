"""
Script Parser for Video Compilator

Parses and validates the unified podcast script JSON file.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

from .config import SECTION_TYPES, FILE_EXTENSIONS

logger = logging.getLogger(__name__)


class ScriptParser:
    """Parses and validates unified podcast script"""
    
    def __init__(self):
        self.script_data: Optional[Dict] = None
        self.script_path: Optional[Path] = None
        
    def parse_script(self, script_path: Path) -> Dict:
        """
        Load and parse the unified podcast script JSON file
        
        Args:
            script_path: Path to unified_podcast_script.json
            
        Returns:
            Dict containing parsed script data
            
        Raises:
            FileNotFoundError: If script file doesn't exist
            json.JSONDecodeError: If script file is invalid JSON
            ValueError: If script structure is invalid
        """
        if not script_path.exists():
            raise FileNotFoundError(f"Script file not found: {script_path}")
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                self.script_data = json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON in script file: {e}")
            
        self.script_path = script_path
        
        if not self.validate_script_structure():
            raise ValueError("Invalid script structure")
            
        logger.info(f"Successfully parsed script: {script_path}")
        return self.script_data
        
    def get_section_sequence(self) -> List[Dict]:
        """
        Extract the sequence of sections from the script
        
        Returns:
            List of section dictionaries in order
        """
        if not self.script_data:
            raise ValueError("No script data loaded. Call parse_script() first.")
            
        sections = self.script_data.get('podcast_sections', [])
        
        # The JSON should already be in the correct alternating order
        # (intro -> pre_clip_001 -> video_clip_001 -> post_clip_001 -> pre_clip_002 -> video_clip_002 -> post_clip_002 -> etc. -> outro)
        # We'll preserve the original order from the unified script JSON as it contains the proper sequence
        
        logger.info(f"Using original section order from JSON: {len(sections)} sections")
        return sections
        
    def map_assets(self, audio_dir: Path, video_dir: Path) -> Dict:
        """
        Map section IDs to corresponding audio/video files
        
        Args:
            audio_dir: Directory containing TTS audio files
            video_dir: Directory containing video clips
            
        Returns:
            Dict mapping section_ids to asset paths
        """
        if not self.script_data:
            raise ValueError("No script data loaded. Call parse_script() first.")
            
        asset_map = {
            'audio': {},
            'video': {}
        }
        
        sections = self.get_section_sequence()
        
        for section in sections:
            section_id = section.get('section_id')
            section_type = section.get('section_type')
            
            if not section_id:
                continue
                
            # Map audio files for narration sections
            if section_type in ['intro', 'pre_clip', 'post_clip', 'outro']:
                audio_file = audio_dir / f"{section_id}{FILE_EXTENSIONS['audio']}"
                asset_map['audio'][section_id] = audio_file
                
            # Map video files for video clip sections
            elif section_type == 'video_clip':
                video_file = video_dir / f"{section_id}{FILE_EXTENSIONS['video']}"
                asset_map['video'][section_id] = video_file
                
        logger.info(f"Mapped {len(asset_map['audio'])} audio assets and {len(asset_map['video'])} video assets")
        return asset_map
        
    def validate_script_structure(self) -> bool:
        """
        Validate the JSON structure and required fields
        
        Returns:
            True if valid, False otherwise
        """
        if not self.script_data:
            return False
            
        # Check required top-level fields
        required_fields = ['narrative_theme', 'podcast_sections']
        for field in required_fields:
            if field not in self.script_data:
                logger.error(f"Missing required field: {field}")
                return False
                
        # Check podcast_sections structure
        sections = self.script_data.get('podcast_sections', [])
        if not isinstance(sections, list) or len(sections) == 0:
            logger.error("podcast_sections must be a non-empty list")
            return False
              # Validate each section
        for i, section in enumerate(sections):
            if not self._validate_section(section, i):
                return False
                
        logger.info("Script structure validation passed")
        return True
        
    def _validate_section(self, section: Dict, index: int) -> bool:
        """
        Validate individual section structure
        
        Args:
            section: Section dictionary to validate
            index: Section index for error reporting
            
        Returns:
            True if valid, False otherwise
        """
        # Common required fields for all sections
        common_required_fields = ['section_type', 'section_id']
        
        for field in common_required_fields:
            if field not in section:
                logger.error(f"Section {index}: Missing required field '{field}'")
                return False
                
        # Validate section_type
        section_type = section.get('section_type')
        if section_type not in SECTION_TYPES.values():
            logger.error(f"Section {index}: Invalid section_type '{section_type}'")
            return False
            
        # Validate section_id format
        section_id = section.get('section_id')
        if not isinstance(section_id, str) or not section_id:
            logger.error(f"Section {index}: Invalid section_id '{section_id}'")
            return False
            
        # Section type specific validation
        if section_type == 'video_clip':
            # Video clip sections have different required fields
            video_required = ['clip_id', 'start_time', 'end_time']
            for field in video_required:
                if field not in section:
                    logger.error(f"Video section {index}: Missing required field '{field}'")
                    return False
        else:
            # Narration sections (intro, pre_clip, post_clip, outro) require script_content
            if 'script_content' not in section:
                logger.error(f"Section {index}: Missing required field 'script_content'")
                return False
                    
        return True
        
    def get_script_summary(self) -> Dict:
        """
        Get a summary of the script contents
        
        Returns:
            Dictionary with script statistics
        """
        if not self.script_data:
            return {}
            
        sections = self.get_section_sequence()
        
        summary = {
            'total_sections': len(sections),
            'narrative_theme': self.script_data.get('narrative_theme', ''),
            'section_counts': {},
            'estimated_total_duration': '0s'
        }
        
        # Count sections by type
        for section in sections:
            section_type = section.get('section_type', 'unknown')
            summary['section_counts'][section_type] = summary['section_counts'].get(section_type, 0) + 1
            
        return summary
