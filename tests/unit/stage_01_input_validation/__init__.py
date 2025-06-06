"""
Stage 1 Input Validation Tests

This package contains comprehensive unit tests for Stage 1 of the master_processor.py
pipeline, which handles input validation for YouTube URLs and audio files.

Test Categories:
- YouTube URL validation and parsing
- Audio file validation and format checking
- Network verification and connectivity
- Input sanitization and security
- Error handling and messaging
- Return structure validation

Test Files:
- test_youtube_url_validation.py: YouTube URL pattern testing
- test_audio_file_validation.py: Audio file format and integrity testing  
- test_network_verification.py: YouTube video accessibility testing
- test_input_sanitization.py: Security and sanitization testing
- test_error_handling.py: Error message and exception testing
- test_return_structures.py: Response format validation

Usage:
    # Run all Stage 1 tests
    pytest tests/unit/stage_01_input_validation/ -v
    
    # Run with coverage
    pytest tests/unit/stage_01_input_validation/ --cov=Code.master_processor --cov-report=html
    
    # Run specific test file
    pytest tests/unit/stage_01_input_validation/test_youtube_url_validation.py -v
"""

__version__ = "1.0.0"
__author__ = "YouTuber Project"
__description__ = "Stage 1 Input Validation Test Suite"
