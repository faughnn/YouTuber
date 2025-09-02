"""
Project Path Discovery and Management

This module provides centralized path discovery for the YouTube video processing pipeline.
It automatically discovers the project root and provides standardized paths for all
directories and files used throughout the system.

This eliminates hardcoded paths and makes the codebase portable across different
environments and platforms.
"""

import os
from pathlib import Path
from typing import Optional


def get_project_root() -> Path:
    """
    Automatically discover the project root directory.
    
    Looks for key indicators that uniquely identify the YouTuber project root:
    - requirements.txt file
    - Code/ directory
    - run_pipeline.py file
    
    Returns:
        Path: The project root directory
        
    Raises:
        RuntimeError: If the project root cannot be found
    """
    # Start from this file's directory and walk up
    current_path = Path(__file__).parent.absolute()
    
    while current_path != current_path.parent:
        # Check for YouTuber project indicators
        if (
            (current_path / "requirements.txt").exists() and
            (current_path / "Code").is_dir() and
            (current_path / "run_pipeline.py").exists()
        ):
            return current_path
        current_path = current_path.parent
    
    raise RuntimeError(
        "Could not find YouTuber project root. "
        "Expected to find requirements.txt, Code/ directory, and run_pipeline.py"
    )


def get_content_dir() -> Path:
    """
    Get the Content directory path, creating it if it doesn't exist.
    
    Returns:
        Path: Path to the Content directory
    """
    content_dir = get_project_root() / "Content"
    content_dir.mkdir(exist_ok=True)
    return content_dir


def get_config_dir() -> Path:
    """
    Get the Code/Config directory path.
    
    Returns:
        Path: Path to the Code/Config directory
        
    Raises:
        FileNotFoundError: If the Config directory doesn't exist
    """
    config_dir = get_project_root() / "Code" / "Config"
    if not config_dir.exists():
        raise FileNotFoundError(
            f"Config directory not found at {config_dir}. "
            f"Expected Code/Config directory in project root."
        )
    return config_dir


def get_transcripts_dir() -> Path:
    """
    Get the Transcripts directory path, creating it if it doesn't exist.
    
    Returns:
        Path: Path to the Transcripts directory
    """
    transcripts_dir = get_project_root() / "Transcripts"
    transcripts_dir.mkdir(exist_ok=True)
    return transcripts_dir


def get_config_file(filename: str) -> Path:
    """
    Get path to a specific config file.
    
    Args:
        filename: Name of the config file (e.g., 'default_config.yaml')
        
    Returns:
        Path: Full path to the config file
        
    Raises:
        FileNotFoundError: If the config file doesn't exist
    """
    config_file = get_config_dir() / filename
    if not config_file.exists():
        raise FileNotFoundError(
            f"Config file '{filename}' not found at {config_file}. "
            f"Expected file in {get_config_dir()}"
        )
    return config_file


def ensure_episode_base_dir() -> Path:
    """
    Ensure the episode base directory exists (same as Content dir).
    This is a convenience function for FileOrganizer compatibility.
    
    Returns:
        Path: Path to the episode base directory
    """
    return get_content_dir()


def get_file_organizer_config() -> dict:
    """
    Get properly configured base paths for FileOrganizer.
    
    This replaces hardcoded {'episode_base': 'Content'} throughout the codebase.
    
    Returns:
        dict: Configuration dictionary for FileOrganizer
    """
    return {
        'episode_base': str(ensure_episode_base_dir())
    }


def validate_project_structure() -> bool:
    """
    Validate that the project has the expected directory structure.
    
    Returns:
        bool: True if structure is valid, False otherwise
    """
    try:
        root = get_project_root()
        
        required_dirs = [
            root / "Code",
            root / "Code" / "Utils",
            root / "Code" / "Config",
            root / "Code" / "Extraction",
            root / "Code" / "Content_Analysis"
        ]
        
        required_files = [
            root / "requirements.txt",
            root / "run_pipeline.py",
            root / "Code" / "master_processor_v2.py"
        ]
        
        for directory in required_dirs:
            if not directory.is_dir():
                return False
                
        for file_path in required_files:
            if not file_path.exists():
                return False
                
        return True
        
    except Exception:
        return False


# Environment variable override support
def get_project_root_with_override() -> Path:
    """
    Get project root with optional environment variable override.
    
    Checks YOUTUBER_PROJECT_ROOT environment variable first,
    falls back to automatic discovery.
    
    Returns:
        Path: The project root directory
    """
    if override_root := os.getenv('YOUTUBER_PROJECT_ROOT'):
        override_path = Path(override_root)
        if override_path.exists():
            return override_path
            
    return get_project_root()


if __name__ == '__main__':
    """Test the path discovery functionality."""
    print("Testing YouTuber project path discovery...")
    
    try:
        # Test basic path discovery
        root = get_project_root()
        print(f"[OK] Project root: {root}")
        
        # Test directory discovery
        content_dir = get_content_dir()
        print(f"[OK] Content directory: {content_dir}")
        
        config_dir = get_config_dir()
        print(f"[OK] Config directory: {config_dir}")
        
        transcripts_dir = get_transcripts_dir()
        print(f"[OK] Transcripts directory: {transcripts_dir}")
        
        # Test FileOrganizer config
        organizer_config = get_file_organizer_config()
        print(f"[OK] FileOrganizer config: {organizer_config}")
        
        # Test project structure validation
        is_valid = validate_project_structure()
        print(f"[OK] Project structure valid: {is_valid}")
        
        print("\n[SUCCESS] All path discovery tests passed!")
        
    except Exception as e:
        print(f"[FAIL] Path discovery test failed: {e}")