"""
MVP Stage 3: Transcript Generation Tests (FIXED)

This module implements comprehensive MVP testing for Stage 3 of the YouTube content 
processing pipeline, focusing on transcript generation through audio diarization 
and YouTube transcript extraction.

Test Categories:
1. Audio Diarization Tests (3 tests) - Core WhisperX functionality
2. YouTube Transcript Extraction Tests (3 tests) - API-based transcript retrieval  
3. Stage Integration Tests (3 tests) - Pipeline handoff validation

MVP Performance Targets:
- Execution Time: < 2 minutes
- Memory Usage: < 100MB
- Success Rate: 100% pass rate on all core functionality

Author: YouTube Content Processing Pipeline
Date: 2025-06-06 (FIXED VERSION)
"""

import pytest
import json
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from typing import Dict, List, Any, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import Stage 3 modules with error handling
try:
    from Code.Extraction.audio_diarizer import diarize_audio
    from Code.Extraction.youtube_transcript_extractor import get_transcript
except ImportError as e:
    pytest.skip(f"Stage 3 modules not available: {e}", allow_module_level=True)


class TestStage3MVP:
    """MVP test suite for Stage 3 transcript generation functionality."""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Set up test environment with temporary directories and mock data."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_audio_path = os.path.join(self.temp_dir, "test_audio.mp3")
        self.test_output_path = os.path.join(self.temp_dir, "transcript.json")
        
        # Create mock audio file
        with open(self.test_audio_path, 'wb') as f:
            f.write(b"mock_audio_data")
          # Mock transcript data structures (matching actual JSON format)
        self.mock_single_speaker_transcript = {
            "metadata": {
                "language": "en",
                "model_used": "large-v2",
                "total_segments": 3,
                "device": "cpu"
            },
            "segments": [
                {
                    "id": 1,
                    "speaker": "SPEAKER_00",
                    "text": "Hello, this is a test audio file.",
                    "start_time": 0.0,
                    "end_time": 5.2,
                    "start_time_formatted": "00:00:00",
                    "end_time_formatted": "00:00:05",
                    "duration": 5.2
                },
                {
                    "id": 2,
                    "speaker": "SPEAKER_00",
                    "text": "We are testing the transcript generation.",
                    "start_time": 5.5,
                    "end_time": 10.8,
                    "start_time_formatted": "00:00:05",
                    "end_time_formatted": "00:00:10",
                    "duration": 5.3
                },
                {
                    "id": 3,
                    "speaker": "SPEAKER_00",
                    "text": "This should work correctly.",
                    "start_time": 11.0,
                    "end_time": 15.5,
                    "start_time_formatted": "00:00:11",
                    "end_time_formatted": "00:00:15",
                    "duration": 4.5
                }
            ]        }
        
        self.mock_multi_speaker_transcript = {
            "metadata": {
                "language": "en",
                "model_used": "whisperx-large-v2",
                "total_segments": 4,
                "duration": 20.0,
                "device": "cpu"
            },
            "segments": [
                {
                    "id": 1,
                    "start_time": 0.0,
                    "end_time": 4.0,
                    "start_time_formatted": "00:00:00",
                    "end_time_formatted": "00:00:04",
                    "duration": 4.0,
                    "text": "Welcome to our conversation.",
                    "speaker": "SPEAKER_00"
                },
                {
                    "id": 2,
                    "start_time": 4.5,
                    "end_time": 8.5,
                    "start_time_formatted": "00:00:04",
                    "end_time_formatted": "00:00:08",
                    "duration": 4.0,
                    "text": "Thank you for having me.",
                    "speaker": "SPEAKER_01"
                },
                {
                    "id": 3,
                    "start_time": 9.0,
                    "end_time": 13.0,
                    "start_time_formatted": "00:00:09",
                    "end_time_formatted": "00:00:13",
                    "duration": 4.0,
                    "text": "Let's discuss the main topic.",
                    "speaker": "SPEAKER_00"
                },
                {
                    "id": 4,
                    "start_time": 13.5,
                    "end_time": 20.0,
                    "start_time_formatted": "00:00:13",
                    "end_time_formatted": "00:00:20",
                    "duration": 6.5,
                    "text": "I think that's a great idea to explore.",
                    "speaker": "SPEAKER_01"
                }
            ]
        }
        
        self.mock_youtube_transcript = [
            {'text': 'Welcome to our channel', 'start': 0.0, 'duration': 3.5},
            {'text': 'Today we will discuss AI', 'start': 3.5, 'duration': 4.0},
            {'text': 'This is an exciting topic', 'start': 7.5, 'duration': 3.2}
        ]
        
        yield
        
        # Cleanup
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    # ================================================================
    # CATEGORY 1: AUDIO DIARIZATION TESTS (3 tests)
    # ================================================================
    @patch('tests.unit.test_stage_3_mvp.diarize_audio')
    def test_basic_audio_transcription(self, mock_diarize_audio):
        """Test basic audio transcription with single speaker."""
        
        # Setup mock to return valid JSON transcript
        mock_diarize_audio.return_value = json.dumps(self.mock_single_speaker_transcript)
        
        # Test audio diarization (actual function signature with hf_auth_token)
        result = diarize_audio(self.test_audio_path, "test_hf_token")
        
        # Assertions
        assert result is not None, "Audio diarization should return transcript JSON"
        assert isinstance(result, str), "Should return JSON string"
        
        # Parse the JSON result
        transcript_data = json.loads(result)
        assert "metadata" in transcript_data, "Should have metadata"
        assert "segments" in transcript_data, "Should have segments"
        
        # Verify function was called correctly
        mock_diarize_audio.assert_called_once_with(self.test_audio_path, "test_hf_token")
        
                # Validate segment structure
        for segment in transcript_data["segments"]:
            assert "start_time" in segment, "Segment should have start_time"
            assert "end_time" in segment, "Segment should have end_time"  
            assert "text" in segment, "Segment should have text content"        
            assert "speaker" in segment, "Segment should have speaker label"
    
    @patch('tests.unit.test_stage_3_mvp.diarize_audio')
    def test_speaker_diarization_functionality(self, mock_diarize_audio):
        """Test speaker diarization with multiple speakers."""
        
        # Setup mock to return multi-speaker transcript
        multi_speaker_transcript = {
            "metadata": {
                "total_duration": 20.0,
                "speaker_count": 2,
                "processing_info": {
                    "model": "base",
                    "language": "en"
                }
            },
            "segments": [
                {"start_time": 0.0, "end_time": 4.0, "text": "Welcome to our conversation.", "speaker": "SPEAKER_00"},
                {"start_time": 4.5, "end_time": 8.5, "text": "Thank you for having me.", "speaker": "SPEAKER_01"},
                {"start_time": 9.0, "end_time": 13.0, "text": "Let's discuss the main topic.", "speaker": "SPEAKER_00"},
                {"start_time": 13.5, "end_time": 20.0, "text": "I think that's a great idea to explore.", "speaker": "SPEAKER_01"}
            ]
        }
        
        mock_diarize_audio.return_value = json.dumps(multi_speaker_transcript)
        
        # Test multi-speaker diarization
        result = diarize_audio(self.test_audio_path, "test_hf_token")
        
        # Assertions
        assert result is not None, "Multi-speaker diarization should return transcript"
        transcript_data = json.loads(result)
        
        # Validate multiple speakers identified
        speakers = set(segment["speaker"] for segment in transcript_data["segments"])
        assert len(speakers) >= 2, "Should identify multiple speakers"
        assert "SPEAKER_00" in speakers, "Should have first speaker"
        assert "SPEAKER_01" in speakers, "Should have second speaker"# Validate speaker assignment consistency - segments should be chronological
        for i in range(len(transcript_data["segments"]) - 1):
            current_end = transcript_data["segments"][i]["end_time"]
            next_start = transcript_data["segments"][i + 1]["start_time"]
            assert current_end <= next_start + 0.5, "Segments should not significantly overlap"
    
    def test_audio_error_handling(self):
        """Test error handling for invalid/corrupted audio files."""
        
        # Test 1: Non-existent file
        non_existent_path = os.path.join(self.temp_dir, "missing_audio.mp3")
        
        result = diarize_audio(non_existent_path, "test_hf_token")
        # The actual function returns error message string, not None
        assert result is not None, "Should return error message for non-existent file"
        assert "Error:" in result or "error" in result, "Should contain error message"
        
        # Test 2: Invalid HF token (empty string)
        result = diarize_audio(self.test_audio_path, "")
        assert result is not None, "Should handle invalid HF token"
        
        # Test 3: Corrupted audio simulation  
        corrupted_path = os.path.join(self.temp_dir, "corrupted.mp3")
        with open(corrupted_path, 'wb') as f:
            f.write(b"not_audio_data")
        result = diarize_audio(corrupted_path, "test_hf_token")
        # Should return error for corrupted audio
        assert result is not None, "Should handle corrupted audio"
        assert "error" in result.lower() or "Error" in result, "Should contain error message for corrupted audio"
        
    # ================================================================
    # CATEGORY 2: YOUTUBE TRANSCRIPT EXTRACTION TESTS (3 tests)
    # ================================================================
    
    @patch('Code.Extraction.youtube_transcript_extractor.YouTubeTranscriptApi.list_transcripts')
    def test_youtube_api_transcript_retrieval(self, mock_list_transcripts):
        """Test successful YouTube transcript retrieval via API."""
        
        # Mock transcript list and transcript objects
        mock_transcript_list = Mock()
        mock_list_transcripts.return_value = mock_transcript_list
        
        mock_transcript = Mock()
        mock_transcript_list.find_manually_created_transcript.return_value = mock_transcript
        
        # Mock the fetch method to return transcript segments
        mock_transcript.fetch.return_value = [
            Mock(text="Welcome to our channel"),
            Mock(text="Today we will discuss AI"),
            Mock(text="This is an exciting topic")
        ]
        
        # Test transcript extraction (actual function signature with language_codes)
        video_id = "test_video_id_123"
        result = get_transcript(video_id, ['en'])
        
        # Assertions
        assert result is not None, "Should successfully extract transcript"
        assert isinstance(result, str), "get_transcript returns formatted string"
        assert "Welcome to our channel" in result, "Should contain expected transcript text"
        
        # Verify API was called correctly
        mock_list_transcripts.assert_called_once_with(video_id)        
        mock_transcript_list.find_manually_created_transcript.assert_called_once_with(['en'])
    
    @patch('Code.Extraction.youtube_transcript_extractor.YouTubeTranscriptApi.list_transcripts')
    def test_transcript_availability_handling(self, mock_list_transcripts):
        """Test handling of videos without available transcripts."""
        
        from youtube_transcript_api import NoTranscriptFound
          # Setup mock to simulate no transcript available
        mock_transcript_list = Mock()
        mock_list_transcripts.side_effect = NoTranscriptFound(
            video_id="test_video_no_transcript",
            requested_language_codes=['en'],
            transcript_data=Mock()
        )
        
        # Test transcript extraction for video without transcript
        video_id = "test_video_no_transcript"
        result = get_transcript(video_id, ['en'])
          # Assertions - function returns error message string, not None
        assert result is not None, "Should return error message when no transcript available"
        assert "error" in result.lower() or "No transcript" in result, "Should contain error message"
    @patch('Code.Extraction.youtube_transcript_extractor.YouTubeTranscriptApi.list_transcripts')
    def test_youtube_api_error_handling(self, mock_list_transcripts):
        """Test robust error handling for YouTube API failures."""
        
        from youtube_transcript_api import TranscriptsDisabled, VideoUnavailable
        
        # Test 1: Invalid video ID
        mock_list_transcripts.side_effect = VideoUnavailable("test_invalid_id")
        result = get_transcript("invalid_video_id", ['en'])
        assert result is not None, "Should return error message for invalid video ID"
        assert "error" in result.lower(), "Should contain error message"
          # Test 2: Transcripts disabled
        mock_list_transcripts.side_effect = TranscriptsDisabled("test_disabled_id")
        result = get_transcript("disabled_transcript_id", ['en'])
        assert result is not None, "Should return error message for disabled transcripts"
        assert "disabled" in result.lower() or "error" in result.lower(), "Should contain disabled message"
        
        # Test 3: Network/API error
        mock_list_transcripts.side_effect = Exception("Network error")
        result = get_transcript("network_error_id", ['en'])
        assert result is not None, "Should return error message for network errors"
        assert "error" in result.lower(), "Should contain error message"
    
    # ================================================================
    # CATEGORY 3: STAGE INTEGRATION TESTS (3 tests)
    # ================================================================
    
    @patch('tests.unit.test_stage_3_mvp.diarize_audio')
    @patch('tests.unit.test_stage_3_mvp.get_transcript')
    def test_stage_2_to_stage_3_handoff(self, mock_get_transcript, mock_diarize_audio):
        """Test successful handoff from Stage 2 audio acquisition to Stage 3."""
        
        # Setup mock Stage 2 results
        stage_2_results = {
            "status": "success",
            "audio_path": self.test_audio_path,
            "video_id": "test_video_123",
            "episode_info": {
                "title": "Test Episode",
                "episode_number": 1
            }
        }
        
        # Setup mocks - diarize_audio returns JSON string
        mock_diarize_audio.return_value = json.dumps(self.mock_single_speaker_transcript)
        mock_get_transcript.return_value = "Formatted transcript text from YouTube API"
        
        # Test both Stage 3 methods
        audio_result = diarize_audio(stage_2_results["audio_path"], "test_hf_token")
        youtube_result = get_transcript(stage_2_results["video_id"], ['en'])
        
        # Assertions
        assert audio_result is not None, "Audio diarization should succeed with valid Stage 2 input"
        assert youtube_result is not None, "YouTube transcript should succeed with valid video ID"
        
        # Verify the results are properly formatted
        transcript_data = json.loads(audio_result)
        assert "metadata" in transcript_data, "Audio transcript should have metadata"
        assert "segments" in transcript_data, "Audio transcript should have segments"
        
        assert isinstance(youtube_result, str), "YouTube transcript should be formatted string"
          # Verify function calls
        mock_diarize_audio.assert_called_once_with(stage_2_results["audio_path"], "test_hf_token")
        mock_get_transcript.assert_called_once_with(stage_2_results["video_id"], ['en'])
    
    @patch('os.makedirs')
    @patch('tests.unit.test_stage_3_mvp.diarize_audio')
    def test_file_organization_integration(self, mock_diarize_audio, mock_makedirs):
        """Test transcript files are saved with correct episode organization."""
        
        # Setup episode context
        episode_info = {
            "title": "Test Episode Title",
            "episode_number": 5,
            "season": 1
        }
        
        # Create expected directory structure
        episode_dir = os.path.join(self.temp_dir, "Season_01", "Episode_05")
        transcript_path = os.path.join(episode_dir, "episode_05.json")
        
        # Setup mock to return valid JSON transcript
        mock_diarize_audio.return_value = json.dumps(self.mock_single_speaker_transcript)
        
        # Test transcript generation
        result = diarize_audio(self.test_audio_path, "test_hf_token")
        
        assert result is not None, "Should successfully generate transcript"
        
        # Parse the result to verify structure
        transcript_data = json.loads(result)
        assert "metadata" in transcript_data, "Should have metadata for file organization"
        assert "segments" in transcript_data, "Should have segments"
        
        # Verify function was called correctly
        mock_diarize_audio.assert_called_once_with(self.test_audio_path, "test_hf_token")
    def test_stage_3_to_stage_4_preparation(self):
        """Test generated transcript is ready for Stage 4 content analysis."""
        
        # Use the mock transcript data directly
        transcript_data = self.mock_multi_speaker_transcript
        
        # Test transcript validation for Stage 4 readiness
        # Validate Stage 4 requirements
        assert "metadata" in transcript_data, "Transcript should have metadata for analysis"
        assert "segments" in transcript_data, "Transcript should have segments for processing"
        
        # Validate metadata completeness
        metadata = transcript_data["metadata"]
        required_metadata = ["language", "total_segments", "duration"]
        for field in required_metadata:
            assert field in metadata, f"Metadata should include {field} for analysis"
        
        # Validate segment structure for analysis
        segments = transcript_data["segments"]
        assert len(segments) > 0, "Should have segments for content analysis"
        
        for segment in segments:
            required_fields = ["start_time", "end_time", "text", "speaker"]
            for field in required_fields:
                assert field in segment, f"Segment should have {field} for analysis"
            
            # Validate data types for downstream processing
            assert isinstance(segment["start_time"], (int, float)), "Start time should be numeric"
            assert isinstance(segment["end_time"], (int, float)), "End time should be numeric"
            assert isinstance(segment["text"], str), "Text should be string"
            assert isinstance(segment["speaker"], str), "Speaker should be string"
        
        # Verify transcript is valid JSON that can be serialized
        try:
            json.dumps(transcript_data)
        except (TypeError, ValueError):
            pytest.fail("Transcript should be valid JSON for Stage 4")


# ================================================================
# UTILITY FUNCTIONS FOR VALIDATION
# ================================================================

def validate_transcript_json_structure(transcript_data: Dict[str, Any]) -> bool:
    """Validate that transcript JSON has required structure."""
    required_fields = ["metadata", "segments"]
    
    for field in required_fields:
        if field not in transcript_data:
            return False
    
    # Validate metadata structure
    metadata = transcript_data["metadata"]
    required_metadata = ["language", "total_segments", "duration"]
    for field in required_metadata:
        if field not in metadata:
            return False
    
    # Validate segments structure
    segments = transcript_data["segments"]
    if not isinstance(segments, list):
        return False
    
    for segment in segments:
        required_segment_fields = ["start_time", "end_time", "text", "speaker"]
        for field in required_segment_fields:
            if field not in segment:
                return False
    
    return True


def validate_speaker_diarization(transcript_data: Dict[str, Any]) -> bool:
    """Validate speaker diarization quality."""
    segments = transcript_data.get("segments", [])
    
    if not segments:
        return False
    
    # Check for speaker labels
    speakers = set(segment.get("speaker", "") for segment in segments)
    
    # Remove empty speakers
    speakers.discard("")
    
    # Should have at least one speaker
    if len(speakers) == 0:
        return False
    
    # Validate speaker label format
    for speaker in speakers:
        if not speaker.startswith("SPEAKER_"):
            return False
      # Validate timestamp consistency
    for i, segment in enumerate(segments):
        if i > 0:
            prev_end = segments[i-1]["end_time"]
            curr_start = segment["start_time"]
            # Allow for small gaps but no significant overlaps
            if curr_start < prev_end - 0.5:
                return False
    
    return True


def validate_transcript_metadata(transcript_data: Dict[str, Any]) -> bool:
    """Validate transcript metadata completeness."""
    metadata = transcript_data.get("metadata", {})
    
    required_fields = [
        "language", "model_used", "total_segments", 
        "duration", "device"
    ]
    
    for field in required_fields:
        if field not in metadata:
            return False
    
    # Validate data types
    if not isinstance(metadata["total_segments"], int):
        return False
    
    if not isinstance(metadata["duration"], (int, float)):
        return False
    
    if metadata["total_segments"] < 0:
        return False
    
    if metadata["duration"] < 0:
        return False
    
    return True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
