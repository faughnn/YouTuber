"""
Test YouTube URL Validation for Stage 1 Input Validation

This module tests the YouTube URL validation functionality including:
- All supported URL format patterns
- URL parameter handling and sanitization
- Playlist URL video extraction
- Invalid URL detection and error handling
- Video ID validation and extraction
"""

import pytest
import re
from unittest.mock import patch, MagicMock

# Import the functions we're testing
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "Code"))

from master_processor import MasterProcessor


class TestYouTubeUrlFormats:
    """Test all supported YouTube URL formats."""
    
    def test_standard_youtube_urls(self, youtube_test_urls):
        """Test standard YouTube URL formats are correctly validated."""
        processor = MasterProcessor()
        
        for url in youtube_test_urls['valid']:
            result = processor._validate_youtube_url(url)
            assert result is True, f"URL should be valid: {url}"
            
            # Test video ID extraction
            video_id = processor._extract_video_id(url)
            assert video_id is not None, f"Should extract video ID from: {url}"
            assert len(video_id) == 11, f"Video ID should be 11 characters: {video_id}"
    
    def test_youtube_url_with_parameters(self, youtube_test_urls):
        """Test YouTube URLs with additional parameters are handled correctly."""
        processor = MasterProcessor()
        
        for url in youtube_test_urls['valid_with_params']:
            result = processor._validate_youtube_url(url)
            assert result is True, f"URL with parameters should be valid: {url}"
            
            # Ensure video ID is still extractable
            video_id = processor._extract_video_id(url)
            assert video_id == "dQw4w9WgXcQ", f"Should extract correct video ID from: {url}"
    
    def test_playlist_url_video_extraction(self, youtube_test_urls):
        """Test extraction of video IDs from playlist URLs."""
        processor = MasterProcessor()
        
        playlist_url = youtube_test_urls['playlist_urls'][0]  # Has video in playlist
        
        # Should extract the individual video ID, not reject the URL
        video_id = processor._extract_video_id(playlist_url)
        assert video_id == "dQw4w9WgXcQ", f"Should extract video ID from playlist URL: {playlist_url}"
    
    def test_invalid_youtube_urls(self, youtube_test_urls):
        """Test that invalid URLs are properly rejected."""
        processor = MasterProcessor()
        
        for invalid_url in youtube_test_urls['invalid']:
            if invalid_url is not None:  # Skip null values
                result = processor._validate_youtube_url(invalid_url)
                assert result is False, f"URL should be invalid: {invalid_url}"
    
    def test_direct_video_id_validation(self):
        """Test direct video ID validation."""
        processor = MasterProcessor()
        
        # Valid 11-character video IDs
        valid_ids = ["dQw4w9WgXcQ", "aBcDeFgHiJk", "123456789AB"]
        for video_id in valid_ids:
            result = processor._validate_youtube_url(video_id)
            assert result is True, f"Valid video ID should be accepted: {video_id}"
        
        # Invalid video IDs
        invalid_ids = ["short", "toolongvideoid", "invalid-chars!", ""]
        for video_id in invalid_ids:
            result = processor._validate_youtube_url(video_id)
            assert result is False, f"Invalid video ID should be rejected: {video_id}"


class TestUrlSanitization:
    """Test URL sanitization and cleaning."""
    
    def test_tracking_parameter_removal(self):
        """Test removal of tracking parameters from URLs."""
        processor = MasterProcessor()
        
        dirty_url = "https://youtube.com/watch?v=dQw4w9WgXcQ&utm_source=facebook&fbclid=123&feature=share"
        clean_url = processor._sanitize_youtube_url(dirty_url)
        
        # Should contain video ID but not tracking parameters
        assert "dQw4w9WgXcQ" in clean_url
        assert "utm_source" not in clean_url
        assert "fbclid" not in clean_url
    
    def test_malicious_url_detection(self):
        """Test detection of potentially malicious URLs."""
        processor = MasterProcessor()
        
        malicious_urls = [
            "https://youtube.evil.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com.evil.com/watch?v=dQw4w9WgXcQ",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>"
        ]
        
        for url in malicious_urls:
            result = processor._validate_youtube_url(url)
            assert result is False, f"Malicious URL should be rejected: {url}"


class TestVideoIdExtraction:
    """Test video ID extraction from various URL formats."""
    
    def test_video_id_extraction_patterns(self, youtube_test_urls):
        """Test video ID extraction from all supported URL patterns."""
        processor = MasterProcessor()
        
        expected_video_id = "dQw4w9WgXcQ"
        
        for url in youtube_test_urls['valid']:
            if url != expected_video_id:  # Skip the direct ID case
                video_id = processor._extract_video_id(url)
                assert video_id == expected_video_id, f"Should extract '{expected_video_id}' from {url}, got '{video_id}'"
        
        # Test additional valid IDs if they exist
        if 'additional_valid_ids' in youtube_test_urls:
            for video_id in youtube_test_urls['additional_valid_ids']:
                extracted_id = processor._extract_video_id(video_id)
                assert extracted_id == video_id, f"Should extract '{video_id}' from direct ID, got '{extracted_id}'"
    
    def test_video_id_format_validation(self):
        """Test video ID format validation."""
        processor = MasterProcessor()
        
        # Test valid video ID characters
        valid_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        valid_id = valid_chars[:11]  # Take first 11 characters
        
        assert processor._is_valid_video_id(valid_id) is True
        
        # Test invalid characters
        invalid_id = "invalid@#$%"
        assert processor._is_valid_video_id(invalid_id) is False
        
        # Test wrong length
        assert processor._is_valid_video_id("short") is False
        assert processor._is_valid_video_id("toolongvideoidstring") is False


class TestUrlParameterHandling:
    """Test URL parameter parsing and handling."""
    
    def test_timestamp_parameter_preservation(self):
        """Test that timestamp parameters are preserved when needed."""
        processor = MasterProcessor()
        
        url_with_timestamp = "https://youtube.com/watch?v=dQw4w9WgXcQ&t=30s"
        
        # Should extract video ID correctly
        video_id = processor._extract_video_id(url_with_timestamp)
        assert video_id == "dQw4w9WgXcQ"
        
        # Should be able to extract timestamp if needed
        timestamp = processor._extract_timestamp(url_with_timestamp)
        assert timestamp == "30s" or timestamp == 30  # Depending on implementation
    
    def test_playlist_parameter_handling(self):
        """Test handling of playlist parameters."""
        processor = MasterProcessor()
        
        playlist_url = "https://youtube.com/watch?v=dQw4w9WgXcQ&list=PLtest&index=1"
        
        # Should extract video ID, ignoring playlist info
        video_id = processor._extract_video_id(playlist_url)
        assert video_id == "dQw4w9WgXcQ"
        
        # Should detect it's a playlist URL
        is_playlist = processor._is_playlist_url(playlist_url)
        assert is_playlist is True


class TestErrorHandling:
    """Test error handling for YouTube URL validation."""
    
    def test_empty_url_handling(self):
        """Test handling of empty or None URLs."""
        processor = MasterProcessor()
        
        assert processor._validate_youtube_url("") is False
        assert processor._validate_youtube_url(None) is False
        assert processor._validate_youtube_url("   ") is False  # Whitespace only
    
    def test_malformed_url_handling(self):
        """Test handling of malformed URLs."""
        processor = MasterProcessor()
        
        malformed_urls = [
            "https://",
            "youtube.com",
            "https://youtube.com/watch",
            "https://youtube.com/watch?v=",
            "https://youtube.com/watch?video=dQw4w9WgXcQ",  # Wrong parameter name
        ]
        
        for url in malformed_urls:
            result = processor._validate_youtube_url(url)
            assert result is False, f"Malformed URL should be invalid: {url}"
    
    def test_exception_handling(self):
        """Test that URL validation handles exceptions gracefully."""
        processor = MasterProcessor()
        
        # Test with objects that might cause exceptions
        invalid_inputs = [123, [], {}, object()]
        
        for invalid_input in invalid_inputs:
            result = processor._validate_youtube_url(invalid_input)
            assert result is False, f"Non-string input should be invalid: {type(invalid_input)}"


# Helper methods that should be implemented in master_processor.py
# These tests will help guide the implementation

@pytest.mark.integration
class TestUrlValidationIntegration:
    """Integration tests for URL validation with actual Stage 1 processing."""
    
    def test_stage_1_youtube_url_processing(self, youtube_test_urls):
        """Test Stage 1 processing with valid YouTube URLs."""
        processor = MasterProcessor()
        
        for url in youtube_test_urls['valid'][:3]:  # Test first 3 to avoid rate limiting
            result = processor._stage_1_input_validation(url, None)
            
            assert result['valid'] is True
            assert result['type'] == 'youtube_url'
            assert result['video_id'] is not None
            assert len(result['video_id']) == 11
    
    def test_stage_1_invalid_url_processing(self, youtube_test_urls):
        """Test Stage 1 processing with invalid YouTube URLs."""
        processor = MasterProcessor()
        
        for url in youtube_test_urls['invalid'][:3]:  # Test first 3 invalid URLs
            if url is not None:
                result = processor._stage_1_input_validation(url, None)
                
                assert result['valid'] is False
                assert result['type'] == 'unknown'
                assert len(result['warnings']) > 0
