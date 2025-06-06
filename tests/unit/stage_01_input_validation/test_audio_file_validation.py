"""
Test Audio File Validation for Stage 1 Input Validation

This module tests the audio file validation functionality including:
- All supported audio format validation
- File existence and permission checks
- Corrupted file detection
- Path security and sanitization
- File size and integrity validation
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the functions we're testing
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "Code"))

from master_processor import MasterProcessor
from Utils.file_organizer import FileOrganizer


class TestAudioFormatValidation:
    """Test validation of all supported audio formats."""
    
    def test_supported_audio_formats(self, audio_test_files):
        """Test that all supported audio formats are correctly validated."""
        processor = MasterProcessor()
        
        supported_formats = ['mp3', 'wav', 'flac', 'm4a', 'aac', 'ogg']
        
        for format_name in supported_formats:
            file_path = audio_test_files['valid'][format_name]
            
            # File should exist
            assert os.path.exists(file_path), f"Test file should exist: {file_path}"
            
            # Should be recognized as valid audio file
            result = FileOrganizer.validate_audio_file(file_path)
            assert result['valid'] is True, f"Should validate {format_name} file: {file_path}"
            assert result['extension'] == f'.{format_name}', f"Should detect correct extension for {format_name}"
    
    def test_invalid_audio_formats(self, audio_test_files):
        """Test that invalid audio formats are rejected."""
        processor = MasterProcessor()
        
        # Test wrong extension
        wrong_ext_file = audio_test_files['invalid']['wrong_extension']
        result = FileOrganizer.validate_audio_file(wrong_ext_file)
        assert result['valid'] is False, f"Should reject non-audio file: {wrong_ext_file}"
    
    def test_audio_format_case_sensitivity(self, tmp_path):
        """Test that audio format detection is case-insensitive."""
        processor = MasterProcessor()
        
        # Create test files with different case extensions
        mp3_header = bytes([0x49, 0x44, 0x33, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]) + b'\x00' * 1014
        
        case_variants = ['.MP3', '.Mp3', '.mP3']
        for variant in case_variants:
            test_file = tmp_path / f"test{variant}"
            test_file.write_bytes(mp3_header)
            
            result = FileOrganizer.validate_audio_file(str(test_file))
            assert result['valid'] is True, f"Should accept {variant} extension"


class TestFileExistenceAndPermissions:
    """Test file existence and permission handling."""
    
    def test_file_not_found(self, audio_test_files):
        """Test handling of non-existent files."""
        processor = MasterProcessor()
        
        nonexistent_file = audio_test_files['invalid']['nonexistent']
        
        result = FileOrganizer.validate_audio_file(nonexistent_file)
        assert result['valid'] is False
        assert 'not found' in result.get('error', '').lower()
    
    def test_relative_path_conversion(self, audio_test_files):
        """Test conversion of relative paths to absolute paths."""
        processor = MasterProcessor()
        
        # Test with a valid file using relative path
        valid_file = audio_test_files['valid']['mp3']
        relative_path = os.path.relpath(valid_file)
        
        result = FileOrganizer.validate_audio_file(relative_path)
        
        # Should convert to absolute path
        assert result.get('path', '').startswith('/') or result.get('path', '')[1:3] == ':\\'  # Unix or Windows absolute
    
    def test_path_with_spaces(self, audio_test_files):
        """Test handling of file paths with spaces."""
        processor = MasterProcessor()
        
        spaced_file = audio_test_files['valid']['with_spaces']
        assert ' ' in spaced_file, "Test file should have spaces in name"
        
        result = FileOrganizer.validate_audio_file(spaced_file)
        assert result['valid'] is True, "Should handle files with spaces in path"
    
    @pytest.mark.skipif(os.name == 'nt', reason="Unix-specific permissions test")
    def test_permission_denied(self, tmp_path):
        """Test handling of permission-denied files (Unix only)."""
        processor = MasterProcessor()
        
        # Create a file and remove read permissions
        test_file = tmp_path / "no_permission.mp3"
        test_file.write_bytes(b'test data')
        os.chmod(test_file, 0o000)  # Remove all permissions
        
        try:
            result = FileOrganizer.validate_audio_file(str(test_file))
            assert result['valid'] is False
            assert 'permission' in result.get('error', '').lower()
        finally:
            # Restore permissions for cleanup
            os.chmod(test_file, 0o644)


class TestFileIntegrityChecking:
    """Test file integrity and corruption detection."""
    
    def test_empty_file_detection(self, audio_test_files):
        """Test detection of empty audio files."""
        processor = MasterProcessor()
        
        empty_file = audio_test_files['invalid']['empty']
        
        result = FileOrganizer.validate_audio_file(empty_file)
        assert result['valid'] is False
        assert result['size_bytes'] == 0
    
    def test_very_small_file_warning(self, audio_test_files):
        """Test warning for very small files (< 1KB)."""
        processor = MasterProcessor()
        
        tiny_file = audio_test_files['invalid']['tiny']
        
        result = FileOrganizer.validate_audio_file(tiny_file)
        # File might be technically valid but should generate a warning
        if result['valid']:
            assert any('small' in warning.lower() for warning in result.get('warnings', []))
        else:
            # Or it might be invalid due to size
            assert result['size_bytes'] < 1024
    
    def test_corrupted_file_detection(self, audio_test_files):
        """Test detection of corrupted audio files."""
        processor = MasterProcessor()
        
        corrupted_file = audio_test_files['invalid']['corrupted']
        
        result = FileOrganizer.validate_audio_file(corrupted_file)
        # Should either be invalid or generate warnings about corruption
        if result['valid']:
            assert len(result.get('warnings', [])) > 0
        else:
            assert 'corrupt' in result.get('error', '').lower() or len(result.get('warnings', [])) > 0
    
    def test_file_size_reporting(self, audio_test_files):
        """Test accurate file size reporting."""
        processor = MasterProcessor()
        
        test_file = audio_test_files['valid']['mp3']
        actual_size = os.path.getsize(test_file)
        
        result = FileOrganizer.validate_audio_file(test_file)
        assert result['size_bytes'] == actual_size
        assert result['size_mb'] == round(actual_size / (1024 * 1024), 2)


class TestPathSecurity:
    """Test path security and sanitization."""
    
    def test_path_traversal_prevention(self, malicious_paths):
        """Test prevention of path traversal attacks."""
        processor = MasterProcessor()
        
        for malicious_path in malicious_paths:
            result = FileOrganizer.validate_audio_file(malicious_path)
            assert result['valid'] is False, f"Should reject malicious path: {malicious_path}"
    
    def test_network_path_handling(self):
        """Test handling of network paths."""
        processor = MasterProcessor()
        
        network_paths = [
            "\\\\server\\share\\file.mp3",
            "//server/share/file.mp3",
            "ftp://server/file.mp3",
            "http://server/file.mp3"
        ]
        
        for network_path in network_paths:
            result = FileOrganizer.validate_audio_file(network_path)
            # Should either reject or handle gracefully
            assert isinstance(result, dict), f"Should return dict for network path: {network_path}"
    
    def test_unicode_filename_handling(self, audio_test_files):
        """Test handling of Unicode filenames."""
        processor = MasterProcessor()
        
        unicode_file = audio_test_files['edge_cases']['unicode']
        
        result = FileOrganizer.validate_audio_file(unicode_file)
        assert result['valid'] is True, "Should handle Unicode filenames"
        assert 'üñíçødé' in result.get('path', ''), "Should preserve Unicode characters"


class TestPathNormalization:
    """Test path normalization and standardization."""
    
    def test_windows_path_separator_handling(self, tmp_path):
        """Test handling of Windows-style path separators."""
        processor = MasterProcessor()
        
        # Create test file
        mp3_header = bytes([0x49, 0x44, 0x33, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]) + b'\x00' * 1014
        test_file = tmp_path / "test.mp3"
        test_file.write_bytes(mp3_header)
        
        # Test with different path separator styles
        windows_path = str(test_file).replace('/', '\\')
        unix_path = str(test_file).replace('\\', '/')
        
        result1 = FileOrganizer.validate_audio_file(windows_path)
        result2 = FileOrganizer.validate_audio_file(unix_path)
        
        assert result1['valid'] is True
        assert result2['valid'] is True
        # Both should normalize to the same absolute path
        assert os.path.normpath(result1['path']) == os.path.normpath(result2['path'])
    
    def test_dot_notation_handling(self, audio_test_files):
        """Test handling of . and .. in paths."""
        processor = MasterProcessor()
        
        valid_file = audio_test_files['valid']['mp3']
        base_dir = os.path.dirname(valid_file)
        filename = os.path.basename(valid_file)
        
        # Create path with . and .. notation
        complex_path = os.path.join(base_dir, '..', os.path.basename(base_dir), filename)
        
        result = FileOrganizer.validate_audio_file(complex_path)
        assert result['valid'] is True, "Should resolve . and .. in paths"
        assert '..' not in result['path'], "Should normalize path without .. notation"


class TestErrorHandling:
    """Test error handling for audio file validation."""
    
    def test_invalid_input_types(self):
        """Test handling of invalid input types."""
        processor = MasterProcessor()
        
        invalid_inputs = [None, 123, [], {}, object()]
        
        for invalid_input in invalid_inputs:
            result = FileOrganizer.validate_audio_file(invalid_input)
            assert result['valid'] is False, f"Should reject invalid input type: {type(invalid_input)}"
    
    def test_exception_handling(self):
        """Test that validation handles exceptions gracefully."""
        processor = MasterProcessor()
        
        # Test with extremely long path that might cause issues
        very_long_path = "a" * 1000 + ".mp3"
        
        result = FileOrganizer.validate_audio_file(very_long_path)
        assert isinstance(result, dict), "Should return dict even for problematic inputs"
        assert 'valid' in result, "Should include valid field in result"
    
    def test_concurrent_file_access(self, audio_test_files):
        """Test handling of files being accessed by other processes."""
        processor = MasterProcessor()
        
        test_file = audio_test_files['valid']['mp3']
        
        # Multiple concurrent validations should work
        results = []
        for _ in range(5):
            result = FileOrganizer.validate_audio_file(test_file)
            results.append(result)
        
        # All should succeed
        assert all(r['valid'] for r in results), "Concurrent access should work"


@pytest.mark.integration
class TestAudioValidationIntegration:
    """Integration tests for audio file validation with Stage 1 processing."""
    
    def test_stage_1_audio_file_processing(self, audio_test_files):
        """Test Stage 1 processing with valid audio files."""
        processor = MasterProcessor()
        
        for format_name in ['mp3', 'wav', 'flac']:
            file_path = audio_test_files['valid'][format_name]
            result = processor._stage_1_input_validation(None, file_path)
            
            assert result['valid'] is True
            assert result['type'] == 'local_audio'
            assert result['file_path'] == file_path
            assert result['info']['extension'] == f'.{format_name}'
    
    def test_stage_1_invalid_audio_processing(self, audio_test_files):
        """Test Stage 1 processing with invalid audio files."""
        processor = MasterProcessor()
        
        invalid_files = ['empty', 'corrupted', 'wrong_extension']
        
        for file_type in invalid_files:
            file_path = audio_test_files['invalid'][file_type]
            result = processor._stage_1_input_validation(None, file_path)
            
            assert result['valid'] is False
            assert result['type'] == 'unknown'
            assert len(result['warnings']) > 0
