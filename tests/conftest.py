"""
pytest configuration and shared fixtures for YouTuber project tests.
"""

import pytest
import os
import sys
import json
import tempfile
from pathlib import Path

# Add the Code directory to Python path for imports
project_root = Path(__file__).parent.parent
code_dir = project_root / "Code"
sys.path.insert(0, str(code_dir))

@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent

@pytest.fixture
def test_data_dir():
    """Return the test fixtures directory."""
    return Path(__file__).parent / "fixtures"

@pytest.fixture
def sample_config():
    """Return a sample configuration for testing."""
    return {
        'paths': {
            'episode_base': str(Path(__file__).parent.parent / "Content"),
            'analysis_rules': str(Path(__file__).parent.parent / "Code" / "Content_Analysis" / "Rules"),
        },
        'openai': {
            'model': 'gpt-4',
            'max_tokens': 2000
        },
        'video': {
            'always_download_video': True
        }
    }

@pytest.fixture
def temp_episode_name():
    """Return a temporary episode name for testing."""
    return "Test Episode - Sample Content"

# Stage 1 Input Validation Test Fixtures

@pytest.fixture
def stage_01_test_data():
    """Load Stage 1 test data from JSON fixture."""
    test_data_path = Path(__file__).parent / "fixtures" / "stage_01" / "test_data.json"
    with open(test_data_path, 'r', encoding='utf-8') as f:
        return json.load(f)

@pytest.fixture  
def youtube_test_urls(stage_01_test_data):
    """All YouTube URL test cases organized by category."""
    return stage_01_test_data['youtube_urls']

@pytest.fixture
def mock_youtube_responses():
    """Load mock YouTube API responses for network testing."""
    mock_data_path = Path(__file__).parent / "fixtures" / "stage_01" / "mock_responses.json"
    with open(mock_data_path, 'r', encoding='utf-8') as f:
        return json.load(f)

@pytest.fixture
def audio_test_files():
    """Paths to test audio files for validation testing."""
    fixtures_path = Path(__file__).parent / "fixtures" / "stage_01" / "audio_files"
    
    return {
        'valid': {
            'mp3': str(fixtures_path / "valid" / "sample.mp3"),
            'wav': str(fixtures_path / "valid" / "sample.wav"),
            'flac': str(fixtures_path / "valid" / "sample.flac"),
            'm4a': str(fixtures_path / "valid" / "sample.m4a"),
            'aac': str(fixtures_path / "valid" / "sample.aac"),
            'ogg': str(fixtures_path / "valid" / "sample.ogg"),
            'with_spaces': str(fixtures_path / "valid" / "file with spaces.mp3"),
        },
        'invalid': {
            'empty': str(fixtures_path / "invalid" / "empty.mp3"),
            'corrupted': str(fixtures_path / "invalid" / "corrupted.mp3"),
            'wrong_extension': str(fixtures_path / "invalid" / "wrong_extension.txt"),
            'tiny': str(fixtures_path / "invalid" / "tiny.mp3"),
            'nonexistent': str(fixtures_path / "invalid" / "does_not_exist.mp3"),
        },
        'edge_cases': {
            'unicode': str(fixtures_path / "edge_cases" / "unicode_üñíçødé.mp3"),
        }
    }

@pytest.fixture
def temp_audio_file(tmp_path):
    """Create a temporary audio file for testing."""
    audio_file = tmp_path / "temp_test.mp3"
    # Create a minimal valid MP3 header
    mp3_header = bytes([0x49, 0x44, 0x33, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]) + b'\x00' * 1014
    audio_file.write_bytes(mp3_header)
    return str(audio_file)

@pytest.fixture
def malicious_paths():
    """Test paths for security validation."""
    return [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\config\\sam",
        "/etc/shadow",
        "C:\\Windows\\System32\\config\\SAM",
        "\\\\network\\share\\file.mp3",
        "file://etc/passwd",
        "http://malicious.com/file.mp3"
    ]
