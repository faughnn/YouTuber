"""
Test Network Verification for Stage 1 Input Validation

This module tests the network verification functionality including:
- YouTube video accessibility checks
- Private/region-blocked video detection
- Network error handling and retry logic
- Audio track availability verification
- Mock response testing
"""

import pytest
import requests
from unittest.mock import patch, MagicMock, Mock
import json

# Import the functions we're testing
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "Code"))

from master_processor import MasterProcessor


class TestVideoAccessibility:
    """Test YouTube video accessibility verification."""
    
    @patch('requests.get')
    def test_valid_video_accessibility(self, mock_get, mock_youtube_responses):
        """Test verification of accessible public videos."""
        processor = MasterProcessor()
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_youtube_responses['mock_responses']['valid_video']
        mock_get.return_value = mock_response
        
        video_id = "dQw4w9WgXcQ"
        result = processor._verify_youtube_video(video_id)
        
        assert result['accessible'] is True
        assert result['has_audio'] is True
        assert result['title'] is not None
        assert result['duration'] > 0
    
    @patch('requests.get')
    def test_private_video_detection(self, mock_get, mock_youtube_responses):
        """Test detection of private videos."""
        processor = MasterProcessor()
        
        # Mock private video response
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.json.return_value = mock_youtube_responses['mock_responses']['private_video']
        mock_get.return_value = mock_response
        
        video_id = "private123"
        result = processor._verify_youtube_video(video_id)
        
        assert result['accessible'] is False
        assert result['error_type'] == 'VIDEO_UNAVAILABLE'
        assert 'private' in result['error_message'].lower()
    
    @patch('requests.get')
    def test_region_blocked_video(self, mock_get, mock_youtube_responses):
        """Test detection of region-blocked videos."""
        processor = MasterProcessor()
        
        # Mock region-blocked response
        mock_response = Mock()
        mock_response.status_code = 451  # Unavailable for legal reasons
        mock_response.json.return_value = mock_youtube_responses['mock_responses']['region_blocked']
        mock_get.return_value = mock_response
        
        video_id = "blocked123"
        result = processor._verify_youtube_video(video_id)
        
        assert result['accessible'] is False
        assert result['error_type'] == 'VIDEO_UNAVAILABLE'
        assert 'country' in result['error_message'].lower() or 'region' in result['error_message'].lower()
    
    @patch('requests.get')
    def test_deleted_video_detection(self, mock_get, mock_youtube_responses):
        """Test detection of deleted/non-existent videos."""
        processor = MasterProcessor()
        
        # Mock deleted video response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = mock_youtube_responses['mock_responses']['deleted_video']
        mock_get.return_value = mock_response
        
        video_id = "deleted123"
        result = processor._verify_youtube_video(video_id)
        
        assert result['accessible'] is False
        assert result['error_type'] == 'VIDEO_NOT_FOUND'
        assert 'removed' in result['error_message'].lower() or 'not found' in result['error_message'].lower()


class TestNetworkErrorHandling:
    """Test network error handling and retry logic."""
    
    @patch('requests.get')
    def test_connection_timeout_handling(self, mock_get, mock_youtube_responses):
        """Test handling of connection timeouts."""
        processor = MasterProcessor()
        
        # Mock timeout exception
        mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")
        
        video_id = "dQw4w9WgXcQ"
        result = processor._verify_youtube_video(video_id)
        
        assert result['accessible'] is False
        assert result['error_type'] == 'NETWORK_ERROR'
        assert 'timeout' in result['error_message'].lower()
    
    @patch('requests.get')
    def test_connection_error_handling(self, mock_get, mock_youtube_responses):
        """Test handling of connection errors."""
        processor = MasterProcessor()
        
        # Mock connection error
        mock_get.side_effect = requests.exceptions.ConnectionError("Failed to establish connection")
        
        video_id = "dQw4w9WgXcQ"
        result = processor._verify_youtube_video(video_id)
        
        assert result['accessible'] is False
        assert result['error_type'] == 'NETWORK_ERROR'
        assert 'connection' in result['error_message'].lower()
    
    @patch('requests.get')
    def test_dns_resolution_error(self, mock_get, mock_youtube_responses):
        """Test handling of DNS resolution failures."""
        processor = MasterProcessor()
        
        # Mock DNS error
        mock_get.side_effect = requests.exceptions.DNSError("Name or service not known")
        
        video_id = "dQw4w9WgXcQ"
        result = processor._verify_youtube_video(video_id)
        
        assert result['accessible'] is False
        assert result['error_type'] == 'NETWORK_ERROR'
    
    @patch('requests.get')
    def test_api_rate_limiting(self, mock_get, mock_youtube_responses):
        """Test handling of YouTube API rate limiting."""
        processor = MasterProcessor()
        
        # Mock rate limit response
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"error": "Too Many Requests"}
        mock_get.return_value = mock_response
        
        video_id = "dQw4w9WgXcQ"
        result = processor._verify_youtube_video(video_id)
        
        assert result['accessible'] is False
        assert result['error_type'] == 'API_ERROR'
        assert 'rate' in result['error_message'].lower() or 'limit' in result['error_message'].lower()
    
    @patch('requests.get')
    def test_retry_logic(self, mock_get):
        """Test retry logic for transient network errors."""
        processor = MasterProcessor()
        
        # Mock first call fails, second succeeds
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'success',
            'data': {'id': 'dQw4w9WgXcQ', 'available': True, 'has_audio': True}
        }
        
        mock_get.side_effect = [
            requests.exceptions.ConnectionError("Temporary failure"),
            mock_response
        ]
        
        video_id = "dQw4w9WgXcQ"
        result = processor._verify_youtube_video(video_id, max_retries=2)
        
        assert result['accessible'] is True
        assert mock_get.call_count == 2  # Should have retried once


class TestAudioTrackVerification:
    """Test audio track availability verification."""
    
    @patch('requests.get')
    def test_video_with_audio_track(self, mock_get, mock_youtube_responses):
        """Test verification of videos with audio tracks."""
        processor = MasterProcessor()
        
        # Mock video with audio
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_youtube_responses['mock_responses']['valid_video']
        mock_get.return_value = mock_response
        
        video_id = "dQw4w9WgXcQ"
        result = processor._verify_youtube_video(video_id)
        
        assert result['has_audio'] is True
        assert result['accessible'] is True
    
    @patch('requests.get')
    def test_video_without_audio_track(self, mock_get, mock_youtube_responses):
        """Test detection of videos without audio tracks."""
        processor = MasterProcessor()
        
        # Mock video without audio
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_youtube_responses['mock_responses']['no_audio']
        mock_get.return_value = mock_response
        
        video_id = "silent123"
        result = processor._verify_youtube_video(video_id)
        
        assert result['has_audio'] is False
        assert result['accessible'] is True  # Video exists but no audio
        assert 'audio' in result.get('warnings', [None])[0].lower() if result.get('warnings') else True


class TestResponseParsing:
    """Test parsing of YouTube API responses."""
    
    def test_successful_response_parsing(self, mock_youtube_responses):
        """Test parsing of successful API responses."""
        processor = MasterProcessor()
        
        api_response = mock_youtube_responses['mock_responses']['valid_video']['data']
        result = processor._parse_youtube_response(api_response)
        
        assert result['title'] == "Rick Astley - Never Gonna Give You Up (Official Music Video)"
        assert result['duration'] == 212
        assert result['video_id'] == "dQw4w9WgXcQ"
        assert result['uploader'] == "RickAstleyVEVO"
    
    def test_error_response_parsing(self, mock_youtube_responses):
        """Test parsing of error API responses."""
        processor = MasterProcessor()
        
        error_response = mock_youtube_responses['mock_responses']['private_video']
        result = processor._parse_youtube_error(error_response)
        
        assert result['error_code'] == 'VIDEO_UNAVAILABLE'
        assert result['error_message'] == 'This video is private'
    
    def test_malformed_response_handling(self):
        """Test handling of malformed API responses."""
        processor = MasterProcessor()
        
        malformed_responses = [
            {},  # Empty response
            {'invalid': 'structure'},  # Missing required fields
            None,  # None response
            "not json",  # String instead of dict
        ]
        
        for response in malformed_responses:
            result = processor._parse_youtube_response(response)
            assert result.get('error') is not None, f"Should handle malformed response: {response}"


class TestCaching:
    """Test caching of network verification results."""
    
    @patch('requests.get')
    def test_response_caching(self, mock_get):
        """Test that responses are cached to avoid repeated API calls."""
        processor = MasterProcessor()
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'success',
            'data': {'id': 'dQw4w9WgXcQ', 'available': True, 'has_audio': True}
        }
        mock_get.return_value = mock_response
        
        video_id = "dQw4w9WgXcQ"
        
        # Call twice
        result1 = processor._verify_youtube_video(video_id)
        result2 = processor._verify_youtube_video(video_id)
        
        assert result1['accessible'] is True
        assert result2['accessible'] is True
        
        # Should only make one API call due to caching
        assert mock_get.call_count == 1
    
    def test_cache_expiration(self, mock_get):
        """Test that cache expires after appropriate time."""
        processor = MasterProcessor()
        
        # This test would need implementation details about cache expiration
        # Placeholder for when cache expiration is implemented
        pass


@pytest.mark.integration
class TestNetworkVerificationIntegration:
    """Integration tests for network verification with actual YouTube."""
    
    @pytest.mark.slow
    def test_real_youtube_video_verification(self):
        """Test verification with a real YouTube video (Rick Roll - always available)."""
        processor = MasterProcessor()
        
        # Test with Rick Astley's "Never Gonna Give You Up" - should always be available
        video_id = "dQw4w9WgXcQ"
        result = processor._verify_youtube_video(video_id)
        
        # This video should be accessible
        assert result['accessible'] is True
        assert result['has_audio'] is True
        assert result['title'] is not None
        assert result['duration'] > 0
    
    @pytest.mark.slow
    def test_network_connectivity_check(self):
        """Test basic network connectivity to YouTube."""
        processor = MasterProcessor()
        
        connectivity = processor._check_youtube_connectivity()
        assert connectivity is True, "Should be able to connect to YouTube"


class TestMockResponseValidation:
    """Test that mock responses match expected formats."""
    
    def test_mock_response_structure(self, mock_youtube_responses):
        """Test that mock responses have correct structure."""
        responses = mock_youtube_responses['mock_responses']
        
        # Test valid video response structure
        valid_response = responses['valid_video']
        assert 'status' in valid_response
        assert 'data' in valid_response
        assert valid_response['status'] == 'success'
        
        # Test error response structure
        error_response = responses['private_video']
        assert 'status' in error_response
        assert 'error_code' in error_response
        assert 'message' in error_response
        assert error_response['status'] == 'error'
    
    def test_mock_data_completeness(self, mock_youtube_responses):
        """Test that mock data includes all required fields."""
        valid_data = mock_youtube_responses['mock_responses']['valid_video']['data']
        
        required_fields = ['id', 'title', 'duration', 'available', 'has_audio', 'uploader']
        for field in required_fields:
            assert field in valid_data, f"Mock data missing required field: {field}"
        
        # Test data types
        assert isinstance(valid_data['duration'], int)
        assert isinstance(valid_data['available'], bool)
        assert isinstance(valid_data['has_audio'], bool)
