"""
Test Return Structure Validation for Stage 1 Input Validation

This module tests the return structure validation functionality including:
- Success response structure validation
- Error response structure validation  
- Data type validation for all fields
- Required field validation
- Response format consistency
"""

import pytest
from unittest.mock import patch

# Import the functions we're testing
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "Code"))

from master_processor import MasterProcessor


class TestSuccessResponseStructures:
    """Test validation of success response structures."""
    
    def test_youtube_url_success_structure(self, youtube_test_urls):
        """Test that YouTube URL success responses have correct structure."""
        processor = MasterProcessor()
        
        # Mock successful YouTube verification
        with patch.object(processor, '_verify_youtube_video') as mock_verify:
            mock_verify.return_value = {
                'accessible': True,
                'has_audio': True,
                'title': 'Test Video',
                'duration': 180
            }
            
            valid_url = youtube_test_urls['valid'][0]
            result = processor._stage_1_input_validation(valid_url, None)
            
            if result['valid']:
                # Test required fields for YouTube URL success
                required_fields = ['valid', 'type', 'input_type', 'path', 'validated_input', 'video_id', 'info', 'warnings', 'file_path']
                for field in required_fields:
                    assert field in result, f"Missing required field: {field}"
                
                # Test field values
                assert result['valid'] is True
                assert result['type'] == 'youtube_url'
                assert result['input_type'] == 'youtube_url'
                assert result['video_id'] is not None
                assert len(result['video_id']) == 11
                assert result['file_path'] is None
                
                # Test info structure
                info = result['info']
                assert isinstance(info, dict)
                info_required_fields = ['url', 'title', 'duration']
                for field in info_required_fields:
                    assert field in info, f"Missing info field: {field}"
    
    def test_audio_file_success_structure(self, audio_test_files):
        """Test that audio file success responses have correct structure."""
        processor = MasterProcessor()
        
        valid_audio_file = audio_test_files['valid']['mp3']
        result = processor._stage_1_input_validation(None, valid_audio_file)
        
        if result['valid']:
            # Test required fields for audio file success
            required_fields = ['valid', 'type', 'input_type', 'path', 'validated_input', 'video_id', 'info', 'warnings', 'file_path']
            for field in required_fields:
                assert field in result, f"Missing required field: {field}"
            
            # Test field values
            assert result['valid'] is True
            assert result['type'] == 'local_audio'
            assert result['input_type'] == 'audio_file'
            assert result['video_id'] is None
            assert result['file_path'] == valid_audio_file
            
            # Test info structure
            info = result['info']
            assert isinstance(info, dict)
            info_required_fields = ['size_bytes', 'size_mb', 'extension', 'path']
            for field in info_required_fields:
                assert field in info, f"Missing info field: {field}"
    
    def test_required_fields_presence(self, youtube_test_urls, audio_test_files):
        """Test that all required fields are present in success responses."""
        processor = MasterProcessor()
        
        # Test with YouTube URL
        with patch.object(processor, '_verify_youtube_video') as mock_verify:
            mock_verify.return_value = {'accessible': True, 'has_audio': True, 'title': 'Test', 'duration': 100}
            
            youtube_result = processor._stage_1_input_validation(youtube_test_urls['valid'][0], None)
            
            if youtube_result['valid']:
                self._validate_base_structure(youtube_result)
        
        # Test with audio file
        audio_result = processor._stage_1_input_validation(None, audio_test_files['valid']['mp3'])
        
        if audio_result['valid']:
            self._validate_base_structure(audio_result)
    
    def _validate_base_structure(self, result):
        """Helper method to validate base response structure."""
        base_required_fields = ['valid', 'type', 'path', 'warnings', 'info']
        for field in base_required_fields:
            assert field in result, f"Missing base required field: {field}"
        
        # Test basic field types
        assert isinstance(result['valid'], bool)
        assert isinstance(result['type'], str)
        assert isinstance(result['path'], str)
        assert isinstance(result['warnings'], list)
        assert isinstance(result['info'], dict)


class TestErrorResponseStructures:
    """Test validation of error response structures."""
    
    def test_failure_response_structure(self, youtube_test_urls):
        """Test that failure responses have correct structure."""
        processor = MasterProcessor()
        
        # Test with invalid URL
        invalid_url = youtube_test_urls['invalid'][0] if youtube_test_urls['invalid'] else "invalid_url"
        result = processor._stage_1_input_validation(invalid_url, None)
        
        if not result['valid']:
            # Test required fields for failure response
            required_fields = ['valid', 'type', 'path', 'warnings', 'info']
            for field in required_fields:
                assert field in result, f"Missing required field in failure response: {field}"
            
            # Test field values
            assert result['valid'] is False
            assert result['type'] == 'unknown'
            assert isinstance(result['warnings'], list)
            assert len(result['warnings']) > 0  # Should have error messages
            assert isinstance(result['info'], dict)
    
    def test_error_message_consistency(self):
        """Test that error messages are consistently formatted."""
        processor = MasterProcessor()
        
        error_test_cases = [
            ("invalid_url", None),
            (None, "/nonexistent/file.mp3"),
            ("", None),
        ]
        
        for url, file_path in error_test_cases:
            result = processor._stage_1_input_validation(url, file_path)
            
            if not result['valid']:
                # Test warning structure
                warnings = result['warnings']
                assert isinstance(warnings, list)
                
                for warning in warnings:
                    assert isinstance(warning, str)
                    assert len(warning) > 0
                    # Should be properly formatted
                    assert not warning.startswith(' ')
                    assert not warning.endswith(' ')


class TestDataTypeValidation:
    """Test that all fields have correct data types."""
    
    def test_boolean_field_types(self, youtube_test_urls):
        """Test that boolean fields are properly typed."""
        processor = MasterProcessor()
        
        with patch.object(processor, '_verify_youtube_video') as mock_verify:
            mock_verify.return_value = {'accessible': True, 'has_audio': True, 'title': 'Test', 'duration': 100}
            
            result = processor._stage_1_input_validation(youtube_test_urls['valid'][0], None)
            
            # Test boolean fields
            assert isinstance(result['valid'], bool)
            
            # If info has boolean fields, test them
            info = result.get('info', {})
            for key, value in info.items():
                if key in ['available', 'has_audio', 'accessible']:
                    assert isinstance(value, bool), f"Field {key} should be boolean, got {type(value)}"
    
    def test_string_field_types(self, youtube_test_urls):
        """Test that string fields are properly typed."""
        processor = MasterProcessor()
        
        with patch.object(processor, '_verify_youtube_video') as mock_verify:
            mock_verify.return_value = {'accessible': True, 'has_audio': True, 'title': 'Test Video', 'duration': 100}
            
            result = processor._stage_1_input_validation(youtube_test_urls['valid'][0], None)
            
            # Test string fields
            string_fields = ['type', 'input_type', 'path', 'validated_input']
            for field in string_fields:
                if field in result and result[field] is not None:
                    assert isinstance(result[field], str), f"Field {field} should be string, got {type(result[field])}"
            
            # Test video_id if present
            if result.get('video_id') is not None:
                assert isinstance(result['video_id'], str)
                assert len(result['video_id']) == 11
    
    def test_numeric_field_types(self, audio_test_files):
        """Test that numeric fields are properly typed."""
        processor = MasterProcessor()
        
        result = processor._stage_1_input_validation(None, audio_test_files['valid']['mp3'])
        
        if result['valid']:
            info = result.get('info', {})
            
            # Test numeric fields in info
            if 'size_bytes' in info:
                assert isinstance(info['size_bytes'], int), f"size_bytes should be int, got {type(info['size_bytes'])}"
            
            if 'size_mb' in info:
                assert isinstance(info['size_mb'], (int, float)), f"size_mb should be numeric, got {type(info['size_mb'])}"
            
            if 'duration' in info:
                assert isinstance(info['duration'], (int, float)), f"duration should be numeric, got {type(info['duration'])}"
    
    def test_list_field_types(self, youtube_test_urls):
        """Test that list fields are properly typed."""
        processor = MasterProcessor()
        
        result = processor._stage_1_input_validation(youtube_test_urls['invalid'][0] if youtube_test_urls['invalid'] else "invalid", None)
        
        # Test warnings field
        assert isinstance(result['warnings'], list)
        
        # Test that all warning items are strings
        for warning in result['warnings']:
            assert isinstance(warning, str), f"Warning should be string, got {type(warning)}"
    
    def test_dict_field_types(self, youtube_test_urls):
        """Test that dictionary fields are properly typed."""
        processor = MasterProcessor()
        
        with patch.object(processor, '_verify_youtube_video') as mock_verify:
            mock_verify.return_value = {'accessible': True, 'has_audio': True, 'title': 'Test', 'duration': 100}
            
            result = processor._stage_1_input_validation(youtube_test_urls['valid'][0], None)
            
            # Test info field
            assert isinstance(result['info'], dict)
            
            # Test that dict values have expected types
            info = result['info']
            if 'url' in info:
                assert isinstance(info['url'], str)
            if 'title' in info:
                assert isinstance(info['title'], str)


class TestResponseFormatConsistency:
    """Test consistency of response formats across different scenarios."""
    
    def test_success_response_consistency(self, youtube_test_urls, audio_test_files):
        """Test that success responses have consistent format."""
        processor = MasterProcessor()
        
        responses = []
        
        # Get YouTube success response
        with patch.object(processor, '_verify_youtube_video') as mock_verify:
            mock_verify.return_value = {'accessible': True, 'has_audio': True, 'title': 'Test', 'duration': 100}
            
            youtube_response = processor._stage_1_input_validation(youtube_test_urls['valid'][0], None)
            if youtube_response['valid']:
                responses.append(youtube_response)
        
        # Get audio file success response
        audio_response = processor._stage_1_input_validation(None, audio_test_files['valid']['mp3'])
        if audio_response['valid']:
            responses.append(audio_response)
        
        # Compare structure consistency
        if len(responses) >= 2:
            base_keys = set(responses[0].keys())
            for response in responses[1:]:
                assert set(response.keys()) == base_keys, "All success responses should have same top-level keys"
    
    def test_error_response_consistency(self, youtube_test_urls, audio_test_files):
        """Test that error responses have consistent format."""
        processor = MasterProcessor()
        
        error_responses = []
        
        # Get various error responses
        test_cases = [
            (youtube_test_urls['invalid'][0] if youtube_test_urls['invalid'] else "invalid", None),
            (None, "/nonexistent/file.mp3"),
            ("", None),
        ]
        
        for url, file_path in test_cases:
            response = processor._stage_1_input_validation(url, file_path)
            if not response['valid']:
                error_responses.append(response)
        
        # Compare structure consistency
        if len(error_responses) >= 2:
            base_keys = set(error_responses[0].keys())
            for response in error_responses[1:]:
                assert set(response.keys()) == base_keys, "All error responses should have same top-level keys"
    
    def test_field_value_constraints(self, youtube_test_urls, audio_test_files):
        """Test that field values meet expected constraints."""
        processor = MasterProcessor()
        
        # Test various responses
        test_cases = [
            (youtube_test_urls['valid'][0], None),
            (None, audio_test_files['valid']['mp3']),
            (youtube_test_urls['invalid'][0] if youtube_test_urls['invalid'] else "invalid", None),
        ]
        
        for url, file_path in test_cases:
            with patch.object(processor, '_verify_youtube_video') as mock_verify:
                mock_verify.return_value = {'accessible': True, 'has_audio': True, 'title': 'Test', 'duration': 100}
                
                result = processor._stage_1_input_validation(url, file_path)
                
                # Test constraints
                assert result['type'] in ['youtube_url', 'local_audio', 'unknown'], f"Invalid type: {result['type']}"
                
                if 'input_type' in result:
                    assert result['input_type'] in ['youtube_url', 'audio_file', 'unknown'], f"Invalid input_type: {result['input_type']}"
                
                # Video ID should be None or 11 characters
                if result.get('video_id') is not None:
                    assert len(result['video_id']) == 11, f"Video ID should be 11 characters: {result['video_id']}"
                
                # Warnings should be list of strings
                assert isinstance(result['warnings'], list)
                for warning in result['warnings']:
                    assert isinstance(warning, str)
                    assert len(warning) > 0


class TestOptionalFieldHandling:
    """Test handling of optional fields in responses."""
    
    def test_optional_field_presence(self, youtube_test_urls):
        """Test that optional fields are handled correctly."""
        processor = MasterProcessor()
        
        with patch.object(processor, '_verify_youtube_video') as mock_verify:
            # Test with minimal response
            mock_verify.return_value = {'accessible': True, 'has_audio': True}
            
            result = processor._stage_1_input_validation(youtube_test_urls['valid'][0], None)
            
            # Optional fields should either be present or handled gracefully
            optional_fields = ['title', 'duration', 'uploader']
            info = result.get('info', {})
            
            for field in optional_fields:
                if field in info:
                    # If present, should not be None or empty string
                    assert info[field] is not None
                    if isinstance(info[field], str):
                        assert len(info[field]) > 0
    
    def test_null_value_handling(self, youtube_test_urls):
        """Test that null values are handled correctly."""
        processor = MasterProcessor()
        
        result = processor._stage_1_input_validation(youtube_test_urls['valid'][0], None)
        
        # file_path should be None for YouTube URLs
        assert result.get('file_path') is None
        
        # Test audio file case
        result2 = processor._stage_1_input_validation(None, "test.mp3")
        
        # video_id should be None for audio files
        assert result2.get('video_id') is None


@pytest.mark.integration
class TestReturnStructureIntegration:
    """Integration tests for return structure validation."""
    
    def test_end_to_end_structure_validation(self, youtube_test_urls, audio_test_files):
        """Test return structure through complete Stage 1 processing."""
        processor = MasterProcessor()
        
        # Test multiple scenarios
        test_scenarios = [
            (youtube_test_urls['valid'][0], None, True),
            (None, audio_test_files['valid']['mp3'], True),
            (youtube_test_urls['invalid'][0] if youtube_test_urls['invalid'] else "invalid", None, False),
            (None, "/nonexistent.mp3", False),
        ]
        
        for url, file_path, should_be_valid in test_scenarios:
            with patch.object(processor, '_verify_youtube_video') as mock_verify:
                mock_verify.return_value = {'accessible': True, 'has_audio': True, 'title': 'Test', 'duration': 100}
                
                result = processor._stage_1_input_validation(url, file_path)
                
                # Validate complete structure
                self._validate_complete_structure(result, should_be_valid)
    
    def _validate_complete_structure(self, result, expected_valid):
        """Helper to validate complete response structure."""
        # Basic structure
        assert isinstance(result, dict)
        assert 'valid' in result
        assert isinstance(result['valid'], bool)
        
        if expected_valid is not None:
            assert result['valid'] == expected_valid
        
        # Required fields
        required_base_fields = ['type', 'path', 'warnings', 'info']
        for field in required_base_fields:
            assert field in result, f"Missing required field: {field}"
        
        # Type validation
        assert isinstance(result['type'], str)
        assert isinstance(result['path'], str)
        assert isinstance(result['warnings'], list)
        assert isinstance(result['info'], dict)
        
        # Content validation
        for warning in result['warnings']:
            assert isinstance(warning, str)
            assert len(warning.strip()) > 0
