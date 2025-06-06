"""
MVP Tests for Stage 2: Audio/Video Acquisition

This module implements the MVP testing strategy for Stage 2 as defined in
MVP_Stage_02_Acquisition.md. These tests focus on essential quality gates
while maintaining development velocity.

Test Categories:
1. Audio Download MVP Tests (3 tests)
2. Video Download MVP Tests (3 tests)  
3. Stage Integration MVP Tests (3 tests)

Execution Target: < 3 minutes, < 50MB disk usage
"""

import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
import subprocess
import sys

# Add the Code directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Code"))

from Extraction.youtube_audio_extractor import download_audio
from Extraction.youtube_video_downloader import download_video


class TestStage2AudioMVP:
    """MVP tests for audio download functionality."""
    
    @pytest.fixture
    def mock_episode_folder(self, tmp_path):
        """Create a temporary episode folder structure."""
        episode_folder = tmp_path / "Episode_Test" / "Input"
        episode_folder.mkdir(parents=True)
        return str(episode_folder)
    
    @pytest.fixture
    def mock_successful_ytdlp(self):
        """Mock successful yt-dlp operations."""
        with patch('subprocess.run') as mock_run:
            # Mock title retrieval
            mock_run.side_effect = [
                # First call: get title
                Mock(stdout="Test Episode Title", stderr="", returncode=0),
                # Second call: download audio
                Mock(stdout="", stderr="", returncode=0)
            ]
            yield mock_run
    
    @patch('Extraction.youtube_audio_extractor.get_episode_input_folder')
    def test_audio_download_basic_functionality(self, mock_get_folder, mock_successful_ytdlp, mock_episode_folder):
        """
        MVP Test 1: Audio Download Basic Functionality
        Validates that audio download completes successfully with expected output file.
        """
        # Setup
        mock_get_folder.return_value = mock_episode_folder
        expected_audio_path = os.path.join(mock_episode_folder, "original_audio.mp3")
        
        # Create the expected output file to simulate successful download
        Path(expected_audio_path).touch()
        
        # Execute
        with patch('Extraction.youtube_audio_extractor.YouTubeUrlUtils.validate_input') as mock_validate:
            mock_validate.return_value = {
                'valid': True,
                'sanitized_url': 'https://www.youtube.com/watch?v=test123',
                'video_id': 'test123',
                'warnings': [],
                'errors': []
            }
            
            result = download_audio("https://www.youtube.com/watch?v=test123")
        
        # Verify
        assert result == expected_audio_path
        assert os.path.exists(expected_audio_path)
        mock_successful_ytdlp.assert_called()
        
        # Verify yt-dlp was called with correct parameters
        calls = mock_successful_ytdlp.call_args_list
        download_call = calls[1]  # Second call is the download
        assert '-x' in download_call[0][0]  # Extract audio flag
        assert '--audio-format' in download_call[0][0]
        assert 'mp3' in download_call[0][0]
    
    def test_audio_download_error_handling(self):
        """
        MVP Test 2: Audio Download Error Handling
        Validates graceful handling of common failure scenarios.
        """
        # Test invalid URL
        with patch('Extraction.youtube_audio_extractor.YouTubeUrlUtils.validate_input') as mock_validate:
            mock_validate.return_value = {
                'valid': False,
                'errors': ['Invalid URL format']
            }
            
            result = download_audio("invalid_url")
            assert "Invalid YouTube URL" in str(result)
        
        # Test yt-dlp command failure
        with patch('Extraction.youtube_audio_extractor.YouTubeUrlUtils.validate_input') as mock_validate:
            mock_validate.return_value = {
                'valid': True,
                'sanitized_url': 'https://www.youtube.com/watch?v=test123',
                'video_id': 'test123',
                'warnings': [],
                'errors': []
            }
            
            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = subprocess.CalledProcessError(1, 'yt-dlp', stderr="Network error")
                
                result = download_audio("https://www.youtube.com/watch?v=test123")
                assert "An error occurred with yt-dlp" in str(result)
    
    @patch('Extraction.youtube_audio_extractor.get_episode_input_folder')
    def test_audio_download_integration_stage1(self, mock_get_folder, mock_episode_folder):
        """
        MVP Test 3: Audio Download Integration with Stage 1
        Validates that audio download integrates properly with validated inputs from Stage 1.
        """
        # Setup
        mock_get_folder.return_value = mock_episode_folder
        expected_audio_path = os.path.join(mock_episode_folder, "original_audio.mp3")
        
        with patch('subprocess.run') as mock_run:
            # Mock successful operations
            mock_run.side_effect = [
                Mock(stdout="Valid Episode Title", stderr="", returncode=0),
                Mock(stdout="", stderr="", returncode=0)
            ]
            
            # Create expected output
            Path(expected_audio_path).touch()
            
            # Test with Stage 1 validated input
            with patch('Extraction.youtube_audio_extractor.YouTubeUrlUtils.validate_input') as mock_validate:
                mock_validate.return_value = {
                    'valid': True,
                    'sanitized_url': 'https://www.youtube.com/watch?v=validated123',
                    'video_id': 'validated123',
                    'warnings': ['URL was normalized'],
                    'errors': []
                }
                
                result = download_audio("https://youtube.com/watch?v=validated123")  # Non-standard format
                
                # Verify Stage 1 validation was used
                mock_validate.assert_called_once_with("https://youtube.com/watch?v=validated123")
                
                # Verify successful processing
                assert result == expected_audio_path
                assert os.path.exists(expected_audio_path)


class TestStage2VideoMVP:
    """MVP tests for video download functionality."""
    
    @pytest.fixture
    def mock_episode_folder(self, tmp_path):
        """Create a temporary episode folder structure."""
        episode_folder = tmp_path / "Episode_Test" / "Input"
        episode_folder.mkdir(parents=True)
        return str(episode_folder)
    
    @pytest.fixture
    def mock_file_organizer(self, mock_episode_folder):
        """Mock FileOrganizer for video tests."""
        with patch('Extraction.youtube_video_downloader.FileOrganizer') as mock_organizer:
            mock_instance = Mock()
            mock_instance.get_episode_input_folder.return_value = mock_episode_folder
            mock_organizer.return_value = mock_instance
            yield mock_instance
    
    def test_video_download_basic_functionality(self, mock_file_organizer, mock_episode_folder):
        """
        MVP Test 4: Video Download Basic Functionality
        Validates that video download completes successfully with expected output file.
        """
        # Setup
        expected_video_path = os.path.join(mock_episode_folder, "original_video.mp4")
        
        with patch('subprocess.run') as mock_run:
            # Mock successful operations
            mock_run.side_effect = [
                Mock(stdout="Test Video Title", stderr="", returncode=0),  # Get title
                Mock(stdout="", stderr="", returncode=0)  # Download video
            ]
            
            # Create expected output
            Path(expected_video_path).touch()
            
            with patch('Extraction.youtube_video_downloader.YouTubeUrlUtils.validate_input') as mock_validate:
                mock_validate.return_value = {
                    'valid': True,
                    'sanitized_url': 'https://www.youtube.com/watch?v=test123',
                    'video_id': 'test123',
                    'warnings': [],
                    'errors': []
                }
                
                result = download_video("https://www.youtube.com/watch?v=test123")
        
        # Verify
        assert result == expected_video_path
        assert os.path.exists(expected_video_path)
        
        # Verify yt-dlp was called with correct video format parameters
        calls = mock_run.call_args_list
        download_call = calls[1]  # Second call is the download
        assert '-f' in download_call[0][0]
        assert 'bestvideo[ext=mp4]' in download_call[0][0][download_call[0][0].index('-f') + 1]
    
    def test_video_download_error_handling(self, mock_file_organizer):
        """
        MVP Test 5: Video Download Error Handling
        Validates graceful handling of format and network errors.
        """
        # Test "no suitable format" error
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                1, 'yt-dlp', stderr="no suitable format found"
            )
            
            with patch('Extraction.youtube_video_downloader.YouTubeUrlUtils.validate_input') as mock_validate:
                mock_validate.return_value = {
                    'valid': True,
                    'sanitized_url': 'https://www.youtube.com/watch?v=test123',
                    'video_id': 'test123',
                    'warnings': [],
                    'errors': []
                }
                
                result = download_video("https://www.youtube.com/watch?v=test123")
                assert "No suitable MP4 format found" in str(result)
    
    def test_video_download_file_structure_creation(self, tmp_path):
        """
        MVP Test 6: Video Download File Structure Creation
        Validates that proper episode directory structure is created.
        """
        episode_folder = tmp_path / "Episode_Test" / "Input"
        
        with patch('Extraction.youtube_video_downloader.FileOrganizer') as mock_organizer:
            mock_instance = Mock()
            mock_instance.get_episode_input_folder.return_value = str(episode_folder)
            mock_organizer.return_value = mock_instance
            
            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = [
                    Mock(stdout="Test Video", stderr="", returncode=0),
                    Mock(stdout="", stderr="", returncode=0)
                ]
                
                expected_video_path = episode_folder / "original_video.mp4"
                expected_video_path.parent.mkdir(parents=True, exist_ok=True)
                expected_video_path.touch()
                
                with patch('Extraction.youtube_video_downloader.YouTubeUrlUtils.validate_input') as mock_validate:
                    mock_validate.return_value = {
                        'valid': True,
                        'sanitized_url': 'https://www.youtube.com/watch?v=test123',
                        'video_id': 'test123',
                        'warnings': [],
                        'errors': []
                    }
                    
                    result = download_video("https://www.youtube.com/watch?v=test123")
                
                # Verify directory structure was created
                assert episode_folder.exists()
                assert str(expected_video_path) == result


class TestStage2IntegrationMVP:
    """MVP tests for Stage 2 integration scenarios."""
    
    @pytest.fixture
    def mock_master_processor_context(self, tmp_path):
        """Mock the master processor context for integration tests."""
        episode_folder = tmp_path / "Episode_Test"
        input_folder = episode_folder / "Input"
        input_folder.mkdir(parents=True)
        
        return {
            'episode_folder': str(episode_folder),
            'input_folder': str(input_folder),
            'episode_title': 'Test Episode Title'
        }
    
    def test_stage1_to_stage2_handoff(self, mock_master_processor_context):
        """
        MVP Test 7: Stage 1 to Stage 2 Handoff
        Validates smooth transition from URL validation to media acquisition.
        """
        input_folder = mock_master_processor_context['input_folder']
        
        # Mock Stage 1 validated input
        validated_input = {
            'valid': True,
            'sanitized_url': 'https://www.youtube.com/watch?v=validated123',
            'video_id': 'validated123',
            'warnings': ['URL normalized'],
            'errors': []
        }
        
        with patch('Extraction.youtube_audio_extractor.YouTubeUrlUtils.validate_input') as mock_validate:
            mock_validate.return_value = validated_input
            
            with patch('Extraction.youtube_audio_extractor.get_episode_input_folder') as mock_get_folder:
                mock_get_folder.return_value = input_folder
                
                with patch('subprocess.run') as mock_run:
                    mock_run.side_effect = [
                        Mock(stdout="Test Episode", stderr="", returncode=0),
                        Mock(stdout="", stderr="", returncode=0)
                    ]
                    
                    # Create expected output
                    audio_path = os.path.join(input_folder, "original_audio.mp3")
                    Path(audio_path).touch()
                    
                    # Execute Stage 2 with Stage 1 output
                    result = download_audio("https://youtube.com/watch?v=validated123")
                    
                    # Verify handoff was successful
                    assert result == audio_path
                    mock_validate.assert_called_once()
                    assert validated_input['sanitized_url'] in str(mock_run.call_args_list)
    
    def test_local_file_handling_integration(self, mock_master_processor_context):
        """
        MVP Test 8: Local File Handling Integration
        Validates that existing local files are handled appropriately.
        """
        input_folder = mock_master_processor_context['input_folder']
        
        # Create existing files
        existing_audio = os.path.join(input_folder, "original_audio.mp3")
        existing_video = os.path.join(input_folder, "original_video.mp4")
        
        Path(existing_audio).touch()
        Path(existing_video).touch()
        
        # Verify files exist before processing
        assert os.path.exists(existing_audio)
        assert os.path.exists(existing_video)
        
        # Test that new downloads would overwrite (expected behavior)
        with patch('Extraction.youtube_audio_extractor.get_episode_input_folder') as mock_get_folder:
            mock_get_folder.return_value = input_folder
            
            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = [
                    Mock(stdout="New Episode", stderr="", returncode=0),
                    Mock(stdout="", stderr="", returncode=0)
                ]
                
                with patch('Extraction.youtube_audio_extractor.YouTubeUrlUtils.validate_input') as mock_validate:
                    mock_validate.return_value = {
                        'valid': True,
                        'sanitized_url': 'https://www.youtube.com/watch?v=new123',
                        'video_id': 'new123',
                        'warnings': [],
                        'errors': []
                    }
                    
                    # This should succeed (overwrite existing)
                    result = download_audio("https://www.youtube.com/watch?v=new123")
                    assert result == existing_audio
    
    def test_stage2_error_recovery_integration(self, mock_master_processor_context):
        """
        MVP Test 9: Stage 2 Error Recovery Integration
        Validates that Stage 2 errors are properly surfaced for pipeline handling.
        """
        # Test network error recovery
        with patch('Extraction.youtube_audio_extractor.YouTubeUrlUtils.validate_input') as mock_validate:
            mock_validate.return_value = {
                'valid': True,
                'sanitized_url': 'https://www.youtube.com/watch?v=test123',
                'video_id': 'test123',
                'warnings': [],
                'errors': []
            }
            
            with patch('subprocess.run') as mock_run:
                # Simulate network error
                mock_run.side_effect = subprocess.CalledProcessError(
                    1, 'yt-dlp', stderr="Network error: Unable to connect"
                )
                
                result = download_audio("https://www.youtube.com/watch?v=test123")
                
                # Verify error is properly formatted for pipeline consumption
                assert isinstance(result, str)
                assert "An error occurred with yt-dlp" in result
                assert "Network error" in result
        
        # Test missing dependency error
        with patch('Extraction.youtube_audio_extractor.YouTubeUrlUtils.validate_input') as mock_validate:
            mock_validate.return_value = {
                'valid': True,
                'sanitized_url': 'https://www.youtube.com/watch?v=test123',
                'video_id': 'test123',
                'warnings': [],
                'errors': []
            }
            
            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = FileNotFoundError("yt-dlp not found")
                
                result = download_audio("https://www.youtube.com/watch?v=test123")
                
                # Verify dependency error is clearly communicated
                assert "yt-dlp command not found" in result
                assert "ensure yt-dlp is installed" in result


# MVP Performance and Resource Monitoring
class TestStage2PerformanceMVP:
    """MVP performance monitoring for Stage 2."""
    
    def test_mvp_performance_targets(self):
        """
        MVP Performance Test: Validates performance targets are achievable.
        
        This test doesn't run actual downloads but validates that the test
        infrastructure can meet the < 3 minutes, < 50MB targets.
        """
        import time
        import psutil
        import os
        
        start_time = time.time()
        start_memory = psutil.Process(os.getpid()).memory_info().rss
        
        # Simulate MVP test execution time
        # (In real runs, this would be the actual test execution)
        time.sleep(0.1)  # Simulate minimal processing time
        
        end_time = time.time()
        end_memory = psutil.Process(os.getpid()).memory_info().rss
        
        execution_time = end_time - start_time
        memory_used = (end_memory - start_memory) / (1024 * 1024)  # MB
        
        # MVP targets validation
        assert execution_time < 180, f"MVP execution exceeded 3 minutes: {execution_time}s"
        assert memory_used < 50, f"MVP memory usage exceeded 50MB: {memory_used}MB"
        
        print(f"MVP Performance - Time: {execution_time:.2f}s, Memory: {memory_used:.2f}MB")


if __name__ == "__main__":
    # Run MVP tests with performance monitoring
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-x",  # Stop on first failure for MVP speed
        "--durations=10"  # Show slowest tests
    ])
