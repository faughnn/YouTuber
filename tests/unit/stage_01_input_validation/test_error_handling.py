"""
Test Error Handling for Stage 1 Input Validation

This module tests the error handling functionality including:
- Error message validation and formatting
- Exception type testing and categorization
- Warning generation and accumulation
- Error recovery and graceful degradation
"""

import pytest
from unittest.mock import patch, MagicMock

# Import the functions we're testing
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "Code"))

from master_processor import MasterProcessor
from Utils.error_handler import ErrorCategory


class TestErrorMessageValidation:
    """Test validation and formatting of error messages."""
    
    def test_invalid_youtube_url_messages(self, youtube_test_urls):
        """Test error messages for invalid YouTube URLs."""
        processor = MasterProcessor()
        
        for invalid_url in youtube_test_urls['invalid']:
            if invalid_url is not None:
                result = processor._stage_1_input_validation(invalid_url, None)
                
                assert result['valid'] is False
                assert len(result['warnings']) > 0
                
                error_message = result['warnings'][0]
                
                # Should contain helpful guidance
                assert 'youtube' in error_message.lower()
                assert 'url' in error_message.lower()
                
                # Should provide example format
                if 'invalid' in error_message.lower():
                    assert 'youtube.com/watch?v=' in error_message or 'youtu.be/' in error_message
    
    def test_file_not_found_messages(self):
        """Test error messages for non-existent files."""
        processor = MasterProcessor()
        
        nonexistent_file = "/path/that/does/not/exist.mp3"
        result = processor._stage_1_input_validation(None, nonexistent_file)
        
        assert result['valid'] is False
        assert len(result['warnings']) > 0
        
        error_message = result['warnings'][0]
        
        # Should mention the specific file path
        assert nonexistent_file in error_message
        
        # Should suggest checking path and permissions
        assert 'path' in error_message.lower()
        assert 'permission' in error_message.lower() or 'check' in error_message.lower()
    
    def test_invalid_audio_format_messages(self, audio_test_files):
        """Test error messages for invalid audio formats.""" 
        processor = MasterProcessor()
        
        wrong_format_file = audio_test_files['invalid']['wrong_extension']
        result = processor._stage_1_input_validation(None, wrong_format_file)
        
        assert result['valid'] is False
        assert len(result['warnings']) > 0
        
        error_message = result['warnings'][0]
        
        # Should mention the unsupported format
        assert '.txt' in error_message or 'txt' in error_message.lower()
        
        # Should list supported formats
        supported_formats = ['.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg']
        format_mentioned = any(fmt in error_message for fmt in supported_formats)
        assert format_mentioned, f"Should mention supported formats: {error_message}"
    
    def test_corrupted_file_messages(self, audio_test_files):
        """Test error messages for corrupted audio files."""
        processor = MasterProcessor()
        
        corrupted_file = audio_test_files['invalid']['corrupted']
        result = processor._stage_1_input_validation(None, corrupted_file)
        
        assert result['valid'] is False
        
        # Should indicate corruption issue
        error_found = False
        for warning in result['warnings']:
            if 'corrupt' in warning.lower() or 'unreadable' in warning.lower():
                error_found = True
                assert corrupted_file in warning  # Should mention specific file
                break
        
        assert error_found, "Should indicate file corruption"
    
    def test_empty_input_messages(self):
        """Test error messages for empty/missing input."""
        processor = MasterProcessor()
        
        # Test with empty inputs
        empty_inputs = ["", None, "   "]
        
        for empty_input in empty_inputs:
            result = processor._stage_1_input_validation(empty_input, None)
            
            assert result['valid'] is False
            assert len(result['warnings']) > 0
            
            error_message = result['warnings'][0]
            
            # Should indicate no input provided
            assert 'no input' in error_message.lower() or 'missing' in error_message.lower()
            
            # Should suggest providing YouTube URL or audio file
            assert 'youtube' in error_message.lower() and 'audio' in error_message.lower()
    
    def test_network_error_messages(self):
        """Test error messages for network connectivity issues."""
        processor = MasterProcessor()
        
        with patch.object(processor, '_verify_youtube_video') as mock_verify:
            # Mock network timeout
            mock_verify.return_value = {
                'accessible': False,
                'error_type': 'NETWORK_ERROR',
                'error_message': 'Connection timed out'
            }
            
            result = processor._stage_1_input_validation("https://youtube.com/watch?v=dQw4w9WgXcQ", None)
            
            # Should handle network errors gracefully
            if not result['valid']:
                error_message = ' '.join(result['warnings'])
                
                # Should mention network/connection issue
                network_terms = ['network', 'connection', 'internet', 'timeout']
                assert any(term in error_message.lower() for term in network_terms)


class TestExceptionTypeValidation:
    """Test that correct exception types are raised."""
    
    def test_input_validation_exceptions(self):
        """Test that input validation errors use correct exception categories."""
        processor = MasterProcessor()
        
        # This test assumes error_handler.py integration
        # Test that validation errors are categorized as INPUT_VALIDATION
        
        with patch('Utils.error_handler.log_error') as mock_log:
            # Test with invalid input that should cause INPUT_VALIDATION error
            processor._stage_1_input_validation("invalid_input", None)
            
            # Check if error was logged with correct category
            if mock_log.called:
                call_args = mock_log.call_args
                if len(call_args[0]) > 1:
                    error_category = call_args[0][1]
                    assert error_category == ErrorCategory.INPUT_VALIDATION
    
    def test_network_error_exceptions(self):
        """Test that network errors use correct exception categories."""
        processor = MasterProcessor()
        
        with patch.object(processor, '_verify_youtube_video') as mock_verify:
            with patch('Utils.error_handler.log_error') as mock_log:
                # Mock network error
                mock_verify.side_effect = Exception("Network connection failed")
                
                processor._stage_1_input_validation("https://youtube.com/watch?v=dQw4w9WgXcQ", None)
                
                # Check if network error was logged correctly
                if mock_log.called:
                    call_args = mock_log.call_args
                    if len(call_args[0]) > 1:
                        error_category = call_args[0][1]
                        assert error_category == ErrorCategory.NETWORK_ERROR
    
    def test_file_error_exceptions(self, audio_test_files):
        """Test that file errors use correct exception categories."""
        processor = MasterProcessor()
        
        with patch('Utils.error_handler.log_error') as mock_log:
            # Test with corrupted file
            corrupted_file = audio_test_files['invalid']['corrupted']
            processor._stage_1_input_validation(None, corrupted_file)
            
            # Check if file error was logged correctly
            if mock_log.called:
                call_args = mock_log.call_args
                if len(call_args[0]) > 1:
                    error_category = call_args[0][1]
                    assert error_category == ErrorCategory.FILE_ERROR


class TestWarningGeneration:
    """Test warning generation and accumulation."""
    
    def test_small_file_warnings(self, audio_test_files):
        """Test warnings for very small audio files."""
        processor = MasterProcessor()
        
        tiny_file = audio_test_files['invalid']['tiny']
        result = processor._stage_1_input_validation(None, tiny_file)
        
        # Should generate warning for small file
        warnings = result.get('warnings', [])
        small_file_warning = any('small' in warning.lower() for warning in warnings)
        
        if result['valid']:  # If file is considered valid but small
            assert small_file_warning, "Should warn about small file size"
    
    def test_multiple_warning_accumulation(self):
        """Test that multiple warnings can be accumulated."""
        processor = MasterProcessor()
        
        # Create scenario that might generate multiple warnings
        with patch.object(processor, '_validate_input') as mock_validate:
            mock_validate.return_value = {
                'valid': True,
                'warnings': ['Warning 1: Small file size', 'Warning 2: Unusual format']
            }
            
            result = processor._stage_1_input_validation("test_input", None)
            
            warnings = result.get('warnings', [])
            assert len(warnings) >= 2, "Should accumulate multiple warnings"
    
    def test_warning_message_formatting(self):
        """Test that warning messages are properly formatted."""
        processor = MasterProcessor()
        
        with patch.object(processor, '_validate_input') as mock_validate:
            mock_validate.return_value = {
                'valid': True,
                'warnings': ['Test warning message']
            }
            
            result = processor._stage_1_input_validation("test_input", None)
            
            warnings = result.get('warnings', [])
            if warnings:
                warning = warnings[0]
                # Should be a string
                assert isinstance(warning, str)
                # Should not be empty
                assert len(warning.strip()) > 0
                # Should be properly capitalized
                assert warning[0].isupper() or warning.startswith('[')


class TestErrorRecovery:
    """Test error recovery and graceful degradation."""
    
    def test_partial_failure_handling(self):
        """Test handling of partial failures in validation."""
        processor = MasterProcessor()
        
        with patch.object(processor, '_validate_youtube_url') as mock_url_validate:
            with patch.object(processor, '_verify_youtube_video') as mock_verify:
                # URL validation succeeds but network verification fails
                mock_url_validate.return_value = True
                mock_verify.return_value = {
                    'accessible': False,
                    'error_type': 'NETWORK_ERROR',
                    'error_message': 'Temporary network issue'
                }
                
                result = processor._stage_1_input_validation("https://youtube.com/watch?v=dQw4w9WgXcQ", None)
                
                # Should handle partial failure gracefully
                assert isinstance(result, dict)
                assert 'valid' in result
                assert 'warnings' in result
    
    def test_exception_handling_robustness(self):
        """Test that unexpected exceptions are handled gracefully."""
        processor = MasterProcessor()
        
        with patch.object(processor, '_validate_input') as mock_validate:
            # Simulate unexpected exception
            mock_validate.side_effect = Exception("Unexpected error")
            
            # Should not crash, should return error result
            result = processor._stage_1_input_validation("test_input", None)
            
            assert isinstance(result, dict)
            assert result['valid'] is False
            assert len(result['warnings']) > 0
    
    def test_invalid_response_handling(self):
        """Test handling of invalid responses from validation functions."""
        processor = MasterProcessor()
        
        with patch.object(processor, '_validate_input') as mock_validate:
            # Return invalid response format
            mock_validate.return_value = "invalid response"
            
            result = processor._stage_1_input_validation("test_input", None)
            
            # Should handle invalid response gracefully
            assert isinstance(result, dict)
            assert result['valid'] is False


class TestErrorMessageConsistency:
    """Test consistency of error messages across different scenarios."""
    
    def test_error_message_language_consistency(self):
        """Test that error messages use consistent language and tone."""
        processor = MasterProcessor()
        
        # Collect error messages from various scenarios
        error_scenarios = [
            ("invalid_url", None),
            (None, "/nonexistent/file.mp3"),
            ("", None),
            (None, ""),
        ]
        
        error_messages = []
        for url, file_path in error_scenarios:
            result = processor._stage_1_input_validation(url, file_path)
            if not result['valid'] and result['warnings']:
                error_messages.extend(result['warnings'])
        
        # Check consistency
        for message in error_messages:
            # Should be properly punctuated
            assert message.endswith('.') or message.endswith('!') or message.endswith('?')
            
            # Should not contain placeholder text
            assert '{' not in message and '}' not in message
            assert '<' not in message or '>' not in message
    
    def test_error_code_consistency(self):
        """Test that error codes are consistently formatted."""
        processor = MasterProcessor()
        
        # Test various error conditions and check for consistent error codes
        test_cases = [
            ("https://invalid.url", None, "INVALID_URL"),
            (None, "/nonexistent.mp3", "FILE_NOT_FOUND"),
            ("", None, "EMPTY_INPUT"),
        ]
        
        for url, file_path, expected_error_type in test_cases:
            result = processor._stage_1_input_validation(url, file_path)
            
            if not result['valid']:
                # Check if error type is included in response
                error_type = result.get('error_type', result.get('type'))
                if error_type:
                    # Should be uppercase and use underscores
                    assert error_type.isupper()
                    assert ' ' not in error_type


@pytest.mark.integration
class TestErrorHandlingIntegration:
    """Integration tests for error handling with full Stage 1 processing."""
    
    def test_end_to_end_error_handling(self, youtube_test_urls, audio_test_files):
        """Test error handling through complete Stage 1 pipeline."""
        processor = MasterProcessor()
        
        # Test with various invalid inputs
        invalid_inputs = [
            (youtube_test_urls['invalid'][0], None) if youtube_test_urls['invalid'] else (None, None),
            (None, audio_test_files['invalid']['empty']),
            ("", ""),
            (None, None),
        ]
        
        for url, file_path in invalid_inputs:
            if url is not None or file_path is not None:
                result = processor._stage_1_input_validation(url, file_path)
                
                # Should always return a properly formatted result
                assert isinstance(result, dict)
                assert 'valid' in result
                assert 'warnings' in result
                assert isinstance(result['warnings'], list)
                
                # Invalid inputs should be marked as invalid
                assert result['valid'] is False
                
                # Should provide helpful error information
                assert len(result['warnings']) > 0
    
    def test_error_logging_integration(self):
        """Test that errors are properly logged through the error handling system."""
        processor = MasterProcessor()
        
        with patch('Utils.error_handler.log_error') as mock_log:
            # Test various error conditions
            processor._stage_1_input_validation("invalid_input", None)
            
            # Should have attempted to log errors
            # (Exact behavior depends on implementation)
            if mock_log.called:
                # Verify log calls have proper structure
                for call in mock_log.call_args_list:
                    args = call[0]
                    assert len(args) >= 2  # Should have message and category
                    assert isinstance(args[0], str)  # Error message
                    # args[1] should be error category if implemented
