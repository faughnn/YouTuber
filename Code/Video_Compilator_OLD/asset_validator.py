"""
Asset Validator for Video Compilator

Pre-flight validation of all required assets before compilation.
"""
import logging
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional

from .config import get_background_image_path, FILE_EXTENSIONS

logger = logging.getLogger(__name__)


class ValidationResult(NamedTuple):
    """Result of asset validation"""
    success: bool
    missing_audio: List[str]
    missing_video: List[str]
    missing_background: bool
    error_message: str
    
    @property
    def is_valid(self) -> bool:
        """Alias for success to maintain compatibility"""
        return self.success
    
    @property
    def missing_assets(self) -> Dict[str, List[str]]:
        """Combined missing assets dictionary"""
        return {
            'audio': self.missing_audio,
            'video': self.missing_video,
            'background': ["Background image not found"] if self.missing_background else []
        }


class AssetValidator:
    """Validates all required assets exist and are accessible"""
    
    def __init__(self):
        self.validation_errors: List[str] = []
        
    def validate_all_assets(self, script_data: Dict, paths: Dict) -> ValidationResult:
        """
        Comprehensive validation of all required assets
        
        Args:
            script_data: Parsed script data
            paths: Dictionary containing paths (audio_dir, video_dir, script_path)
            
        Returns:
            ValidationResult with validation status and details
        """
        self.validation_errors.clear()
        
        audio_dir = paths['audio_dir']
        video_dir = paths['video_dir']
        
        missing_audio = self.check_audio_files(script_data, audio_dir)
        missing_video = self.check_video_files(script_data, video_dir)
        missing_background = not self.check_background_image()
        
        success = (len(missing_audio) == 0 and 
                  len(missing_video) == 0 and 
                  not missing_background)
        
        error_message = ""
        if not success:
            error_message = self.generate_error_report({
                'audio': missing_audio,
                'video': missing_video, 
                'background': missing_background
            })
            
        result = ValidationResult(
            success=success,
            missing_audio=missing_audio,
            missing_video=missing_video,
            missing_background=missing_background,
            error_message=error_message
        )
        
        if success:
            logger.info("✓ All assets validated successfully")
        else:
            logger.error(f"✗ Asset validation failed: {len(missing_audio + missing_video)} missing files")
            
        return result
        
    def check_audio_files(self, script_data: Dict, audio_dir: Path) -> List[str]:
        """
        Check that all required audio files exist
        
        Args:
            script_data: Parsed script data
            audio_dir: Directory containing audio files
            
        Returns:
            List of missing audio file names
        """
        missing_files = []
        
        if not audio_dir.exists():
            logger.error(f"Audio directory does not exist: {audio_dir}")
            return ["Audio directory not found"]
            
        sections = script_data.get('podcast_sections', [])
        
        for section in sections:
            section_type = section.get('section_type')
            section_id = section.get('section_id')
            
            # Audio files needed for narration sections
            if section_type in ['intro', 'pre_clip', 'post_clip', 'outro']:
                audio_file = audio_dir / f"{section_id}{FILE_EXTENSIONS['audio']}"
                
                if not audio_file.exists():
                    missing_files.append(f"{section_id}{FILE_EXTENSIONS['audio']}")
                    logger.warning(f"Missing audio file: {audio_file}")
                else:
                    logger.debug(f"Found audio file: {audio_file}")
                    
        return missing_files
        
    def check_video_files(self, script_data: Dict, video_dir: Path) -> List[str]:
        """
        Check that all required video files exist
        
        Args:
            script_data: Parsed script data
            video_dir: Directory containing video files
            
        Returns:
            List of missing video file names
        """
        missing_files = []
        
        if not video_dir.exists():
            logger.error(f"Video directory does not exist: {video_dir}")
            return ["Video directory not found"]
            
        sections = script_data.get('podcast_sections', [])
        
        for section in sections:
            section_type = section.get('section_type')
            section_id = section.get('section_id')
            
            # Video files needed for video clip sections
            if section_type == 'video_clip':
                video_file = video_dir / f"{section_id}{FILE_EXTENSIONS['video']}"
                
                if not video_file.exists():
                    missing_files.append(f"{section_id}{FILE_EXTENSIONS['video']}")
                    logger.warning(f"Missing video file: {video_file}")
                else:
                    logger.debug(f"Found video file: {video_file}")
                    
        return missing_files
        
    def check_background_image(self) -> bool:
        """
        Check that the background image exists and is readable
        
        Returns:
            True if background image is available, False otherwise
        """
        background_path = get_background_image_path()
        
        if not background_path.exists():
            logger.error(f"Background image not found: {background_path}")
            return False
            
        if not background_path.is_file():
            logger.error(f"Background image path is not a file: {background_path}")
            return False
            
        try:
            # Test if file is readable
            with open(background_path, 'rb') as f:
                f.read(1024)  # Read first 1KB to test accessibility
            logger.debug(f"Background image verified: {background_path}")
            return True
        except Exception as e:
            logger.error(f"Cannot read background image: {e}")
            return False
            
    def generate_error_report(self, missing_assets: Dict) -> str:
        """
        Generate a formatted error report for missing assets
        
        Args:
            missing_assets: Dictionary with missing asset lists
            
        Returns:
            Formatted error message string
        """
        report_lines = ["ERROR: Video Compilator Pre-Flight Check Failed", ""]
        
        # Missing audio assets
        if missing_assets['audio']:
            report_lines.append("Missing Audio Assets:")
            for audio_file in missing_assets['audio']:
                section_id = audio_file.replace(FILE_EXTENSIONS['audio'], '')
                report_lines.append(f"- {audio_file} (required for section: {section_id})")
            report_lines.append("")
            
        # Missing video assets
        if missing_assets['video']:
            report_lines.append("Missing Video Assets:")
            for video_file in missing_assets['video']:
                section_id = video_file.replace(FILE_EXTENSIONS['video'], '')
                report_lines.append(f"- {video_file} (required for section: {section_id})")
            report_lines.append("")
            
        # Missing background image
        if missing_assets['background']:
            report_lines.append("Background Image Issues:")
            report_lines.append(f"- File not found: {get_background_image_path()}")
            report_lines.append("")
            
        report_lines.append("Please resolve these issues before running compilation.")
        
        return "\n".join(report_lines)
        
    def validate_file_formats(self, audio_dir: Path, video_dir: Path) -> bool:
        """
        Validate that files have the expected formats
        
        Args:
            audio_dir: Directory containing audio files
            video_dir: Directory containing video files
            
        Returns:
            True if all files have valid formats, False otherwise
        """
        valid = True
        
        # Check audio file formats
        for audio_file in audio_dir.glob(f"*{FILE_EXTENSIONS['audio']}"):
            if not self._is_valid_audio_file(audio_file):
                logger.warning(f"Invalid audio format: {audio_file}")
                valid = False
                
        # Check video file formats  
        for video_file in video_dir.glob(f"*{FILE_EXTENSIONS['video']}"):
            if not self._is_valid_video_file(video_file):
                logger.warning(f"Invalid video format: {video_file}")
                valid = False
                
        return valid
        
    def _is_valid_audio_file(self, audio_file: Path) -> bool:
        """Check if audio file format is valid"""
        # Basic check - file exists and has content
        try:
            return audio_file.stat().st_size > 0
        except:
            return False
            
    def _is_valid_video_file(self, video_file: Path) -> bool:
        """Check if video file format is valid"""
        # Basic check - file exists and has content
        try:
            return video_file.stat().st_size > 0
        except:
            return False