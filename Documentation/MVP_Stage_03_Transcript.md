# MVP Stage 3: Transcript Generation Tests

## 🎯 MVP Stage 3 Testing Strategy

Stage 3 (Transcript Generation) bridges Stage 2 (Audio/Video Acquisition) to Stage 4 (Content Analysis) by converting audio files into structured, speaker-diarized transcripts. This stage is critical as it enables all downstream text-based analysis.

### Stage 3 Modules
- **`audio_diarizer.py`** - Core transcript generation using WhisperX and speaker diarization
- **`youtube_transcript_extractor.py`** - Alternative YouTube transcript extraction via API
- **Stage 3 Integration** - `_stage_3_transcript_generation()` in master processor

### Testing Principles
- **Core Functionality:** Audio transcription and speaker diarization work as expected
- **Output Validation:** Generated transcripts have proper JSON structure and content
- **Error Boundaries:** Missing dependencies, invalid audio, and API failures are handled
- **Integration Validation:** Stage 2 → Stage 3 handoff and Stage 3 → Stage 4 preparation

---

## 🧪 MVP Test Categories

### Category 1: Audio Diarization Tests (3 tests)
**Focus:** Core `audio_diarizer.py` functionality with WhisperX

#### Test 1: Basic Audio Transcription
- **Scenario:** Valid audio file with clear speech
- **Input:** Mock audio file with known content
- **Expected:** JSON transcript with segments, timestamps, and metadata
- **Validation:** 
  - JSON structure matches expected format
  - Contains transcript segments with text content
  - Has proper metadata (language, model info, segment count)

#### Test 2: Speaker Diarization Functionality  
- **Scenario:** Audio with multiple speakers
- **Input:** Mock multi-speaker audio file
- **Expected:** Transcript with speaker labels (SPEAKER_00, SPEAKER_01, etc.)
- **Validation:**
  - Multiple speakers identified
  - Speaker labels assigned to segments
  - Timestamp alignment preserved

#### Test 3: Error Handling for Audio Issues
- **Scenario:** Invalid/corrupted audio files
- **Input:** Non-existent file, invalid format, corrupted audio
- **Expected:** Graceful error handling with descriptive messages
- **Validation:**
  - No crashes or exceptions
  - Clear error messages for debugging
  - Proper error propagation to master processor

### Category 2: YouTube Transcript Extraction Tests (3 tests)
**Focus:** Alternative transcript extraction via `youtube_transcript_extractor.py`

#### Test 4: YouTube API Transcript Retrieval
- **Scenario:** YouTube video with available transcript
- **Input:** Valid video ID with known transcript
- **Expected:** Raw transcript text extracted successfully
- **Validation:**
  - Transcript content retrieved
  - Handles both manual and auto-generated transcripts
  - Language preference handling

#### Test 5: Transcript Availability Handling
- **Scenario:** YouTube videos without transcripts
- **Input:** Video ID without available transcripts
- **Expected:** Clear "no transcript available" message
- **Validation:**
  - No crashes when transcripts unavailable
  - Informative error messages
  - Proper fallback behavior

#### Test 6: YouTube API Error Handling
- **Scenario:** Network issues, invalid video IDs, disabled transcripts
- **Input:** Invalid video ID, network simulation, disabled transcripts
- **Expected:** Robust error handling for API failures
- **Validation:**
  - Network error handling
  - Invalid video ID detection
  - Graceful API failure recovery

### Category 3: Stage Integration Tests (3 tests)
**Focus:** Integration with master processor pipeline

#### Test 7: Stage 2 to Stage 3 Handoff
- **Scenario:** Successful audio acquisition leading to transcript generation
- **Input:** Stage 2 results with valid audio path
- **Expected:** Transcript generation using acquired audio
- **Validation:**
  - Stage 2 audio path correctly processed
  - Transcript saved to proper organized location
  - Progress tracking and logging functional

#### Test 8: File Organization Integration
- **Scenario:** Transcript files saved to correct episode structure
- **Input:** Audio file with episode organization context
- **Expected:** Transcript saved with proper naming and location
- **Validation:**
  - Correct episode folder structure maintained
  - Standardized transcript naming (`{episode}.json`)
  - Directory creation and file permissions

#### Test 9: Stage 3 to Stage 4 Preparation
- **Scenario:** Generated transcript ready for content analysis
- **Input:** Completed transcript generation
- **Expected:** Valid JSON output ready for Stage 4 consumption
- **Validation:**
  - JSON format validation
  - Required transcript structure present
  - Metadata completeness for analysis stage

---

## 📋 MVP Test Implementation Plan

### Test Infrastructure Requirements

#### Mock Services
- **Audio File Mocks:** Pre-recorded test audio with known content
- **WhisperX Mocks:** Simulated transcription and diarization results
- **YouTube API Mocks:** Controlled transcript availability scenarios
- **File System Mocks:** Temporary directories for output validation

#### Test Fixtures
```
tests/fixtures/stage_3/
├── audio/
│   ├── single_speaker.mp3          # Clear single speaker
│   ├── multi_speaker.mp3           # Multiple speakers
│   └── short_sample.mp3            # Quick test audio
├── transcripts/
│   ├── expected_single.json        # Expected output format
│   ├── expected_multi.json         # Multi-speaker format
│   └── expected_metadata.json      # Metadata structure
└── youtube/
    ├── valid_video_ids.txt         # Test video IDs
    └── transcript_samples.txt      # Sample transcript content
```

#### Mocking Strategy
- **WhisperX Operations:** Mock model loading, transcription, and diarization
- **File Operations:** Use temporary directories for output testing
- **YouTube API:** Mock transcript availability and content
- **HuggingFace Token:** Mock authentication for diarization pipeline

### Test Support Functions

#### Audio Processing Validation
```python
def validate_transcript_json_structure(transcript_json: str) -> bool:
    """Validate that transcript JSON has required structure."""
    # Check for required fields: metadata, segments
    # Validate segment structure: start, end, text, speaker
    # Verify timestamp consistency and ordering

def validate_speaker_diarization(transcript_json: str) -> bool:
    """Validate speaker diarization quality."""
    # Check for multiple speakers when expected
    # Verify speaker label consistency
    # Validate speaker assignment across segments

def validate_transcript_metadata(transcript_json: str) -> bool:
    """Validate transcript metadata completeness."""
    # Check for language, model_used, total_segments
    # Verify device and processing information
    # Validate timing and duration information
```

#### File Organization Testing
```python
def validate_episode_transcript_structure(transcript_path: str) -> bool:
    """Validate transcript is saved in correct episode structure."""
    # Check episode folder organization
    # Verify file naming conventions
    # Validate directory permissions and access

def simulate_stage_2_audio_acquisition() -> Dict[str, str]:
    """Simulate Stage 2 results for integration testing."""
    # Return mock acquisition results structure
    # Include audio_path and optional video_path
    # Maintain consistency with Stage 2 output format
```

---

## 🎯 MVP Performance Targets

### Execution Time
- **Target:** < 2 minutes total test execution
- **Rationale:** Stage 3 involves AI models and processing, needs slightly more time than Stages 1-2
- **Strategy:** Mock expensive operations (WhisperX model loading, actual transcription)

### Memory Usage
- **Target:** < 100MB peak memory usage
- **Rationale:** Audio processing typically memory-intensive, but mocked for MVP
- **Strategy:** Use small test audio files and mock heavy AI model operations

### Success Criteria
- **Core Functionality:** 100% pass rate on basic transcription and diarization mocks
- **Integration:** Successful Stage 2 → Stage 3 → Stage 4 handoff validation
- **Error Handling:** Robust failure scenarios covered without crashes

---

## 🔧 Technical Implementation Notes

### WhisperX Integration Challenges
- **Model Loading:** Mock expensive model initialization for test speed
- **GPU/CPU Detection:** Mock device selection to avoid hardware dependencies  
- **HuggingFace Authentication:** Mock token validation for diarization pipeline
- **Audio Format Support:** Test common formats without actual audio processing

### YouTube API Integration
- **Rate Limiting:** Mock API calls to avoid quota usage during testing
- **Language Handling:** Test multi-language transcript preference logic
- **Availability Detection:** Mock transcript availability scenarios consistently

### File Organization Consistency
- **Episode Structure:** Ensure transcript location matches Stage 2 audio organization
- **Naming Conventions:** Validate standardized transcript naming across pipeline
- **Permission Handling:** Test directory creation and file access permissions

### Progress Tracking Integration
- **Stage Progress:** Validate progress tracking percentages align with actual processing
- **Error States:** Ensure failed transcription properly updates progress tracker
- **Logging Integration:** Verify transcript generation events properly logged

---

## 🚀 MVP Success Definition

Stage 3 MVP testing is successful when:

1. **Core Transcription:** Mock audio files produce expected JSON transcript structure
2. **Speaker Diarization:** Multi-speaker audio correctly assigns speaker labels
3. **Error Resilience:** Invalid inputs and API failures handled gracefully
4. **Pipeline Integration:** Stage 2 → Stage 3 → Stage 4 handoff works seamlessly
5. **File Organization:** Transcripts saved in correct episode structure with proper naming
6. **Performance:** All tests complete within 2-minute target with <100MB memory usage

This MVP ensures Stage 3 provides reliable transcript generation that enables downstream content analysis while maintaining development velocity through focused testing of critical functionality.

---

## 📚 Dependencies for Implementation

### Required Packages
- `pytest` - Test framework
- `unittest.mock` - Mocking framework for external dependencies
- `tempfile` - Temporary file and directory management
- `json` - JSON validation and parsing
- `pathlib` - Path manipulation and validation

### Mock Targets
- `whisperx.load_model()` - Model loading simulation
- `whisperx.load_audio()` - Audio loading simulation  
- `whisperx.DiarizationPipeline()` - Diarization pipeline mock
- `youtube_transcript_api` - YouTube transcript API mock
- `subprocess.run()` - For any subprocess calls in transcript generation

### Test Data Requirements
- **Audio Samples:** Small test audio files (2-3 seconds each)
- **Expected Outputs:** JSON transcript structures for validation
- **YouTube Test Data:** Video IDs with known transcript availability
- **Error Scenarios:** Invalid file paths, corrupted audio references

This comprehensive MVP testing approach ensures Stage 3 transcript generation is robust and reliable while maintaining the fast development cycle essential for the MVP approach.
