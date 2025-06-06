"""
MVP Test Fixtures for Stage 2

This module provides lightweight fixtures specifically designed for MVP testing
of Stage 2 (Audio/Video Acquisition). These fixtures prioritize speed and
simplicity over comprehensive mocking.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch


@pytest.fixture
def mvp_temp_dir():
    """
    Create a temporary directory for MVP tests.
    Automatically cleaned up after test completion.
    """
    with tempfile.TemporaryDirectory(prefix="mvp_stage2_") as temp_dir:
        yield temp_dir


@pytest.fixture
def mvp_episode_structure(mvp_temp_dir):
    """
    Create a minimal episode directory structure for MVP tests.
    
    Returns:
        dict: Dictionary with folder paths
    """
    episode_name = "Test_Episode_MVP"
    episode_folder = Path(mvp_temp_dir) / episode_name
    input_folder = episode_folder / "Input"
    
    # Create structure
    input_folder.mkdir(parents=True, exist_ok=True)
    
    return {
        'episode_folder': str(episode_folder),
        'input_folder': str(input_folder),
        'episode_name': episode_name
    }


@pytest.fixture
def mvp_youtube_url():
    """Standard YouTube URL for MVP testing."""
    return "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll for testing


@pytest.fixture
def mvp_video_id():
    """Standard YouTube video ID for MVP testing."""
    return "dQw4w9WgXcQ"


@pytest.fixture
def mvp_mock_validation_success():
    """Mock successful YouTube URL validation."""
    return {
        'valid': True,
        'sanitized_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'video_id': 'dQw4w9WgXcQ',
        'warnings': [],
        'errors': []
    }


@pytest.fixture
def mvp_mock_validation_failure():
    """Mock failed YouTube URL validation."""
    return {
        'valid': False,
        'sanitized_url': None,
        'video_id': None,
        'warnings': [],
        'errors': ['Invalid URL format']
    }


@pytest.fixture
def mvp_expected_files(mvp_episode_structure):
    """
    Expected output files for MVP tests.
    
    Returns:
        dict: Dictionary with expected file paths
    """
    input_folder = mvp_episode_structure['input_folder']
    
    return {
        'audio': os.path.join(input_folder, "original_audio.mp3"),
        'video': os.path.join(input_folder, "original_video.mp4")
    }


@pytest.fixture
def mvp_mock_successful_subprocess():
    """
    Mock successful subprocess operations for yt-dlp.
    Returns a context manager that can be used with 'with' statement.
    """
    def _mock_subprocess():
        return patch('subprocess.run', side_effect=[
            Mock(stdout="Test Episode Title", stderr="", returncode=0),  # Get title
            Mock(stdout="Download completed", stderr="", returncode=0)   # Download
        ])
    
    return _mock_subprocess


@pytest.fixture
def mvp_performance_monitor():
    """
    Simple performance monitoring for MVP tests.
    
    Usage:
        def test_something(mvp_performance_monitor):
            with mvp_performance_monitor() as monitor:
                # ... test code ...
                pass
            
            assert monitor.execution_time < 5.0  # 5 second limit
    """
    import time
    import psutil
    import os
    
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.start_memory = None
            self.end_memory = None
            
        def __enter__(self):
            self.start_time = time.time()
            self.start_memory = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
            return self
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.end_time = time.time()
            self.end_memory = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
            
        @property
        def execution_time(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return 0
            
        @property
        def memory_used(self):
            if self.start_memory and self.end_memory:
                return self.end_memory - self.start_memory
            return 0
    
    return PerformanceMonitor


# Parametrized fixtures for testing multiple scenarios
@pytest.fixture(params=[
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://youtu.be/dQw4w9WgXcQ", 
    "dQw4w9WgXcQ"
])
def mvp_various_youtube_inputs(request):
    """Various YouTube input formats for MVP testing."""
    return request.param


@pytest.fixture(params=[
    "Network error",
    "Video unavailable", 
    "Private video",
    "No suitable format found"
])
def mvp_various_error_messages(request):
    """Various error messages for MVP error handling tests."""
    return request.param


# Marker definitions for MVP categorization
def pytest_configure(config):
    """Configure pytest markers for MVP tests."""
    config.addinivalue_line(
        "markers", "mvp: Mark test as MVP critical functionality"
    )
    config.addinivalue_line(
        "markers", "stage2: Mark test as Stage 2 specific"
    )
    config.addinivalue_line(
        "markers", "audio: Mark test as audio-related"
    )
    config.addinivalue_line(
        "markers", "video: Mark test as video-related"
    )
    config.addinivalue_line(
        "markers", "integration: Mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "performance: Mark test as performance validation"
    )
    config.addinivalue_line(
        "markers", "slow: Mark test as slow (>5 seconds)"
    )
    config.addinivalue_line(
        "markers", "network: Mark test as requiring network access"
    )
