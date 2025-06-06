# MVP Stage 2: Audio/Video Acquisition Tests

**Created:** June 5, 2025  
**Purpose:** Minimal viable testing for Stage 2 (Audio/Video Acquisition)  
**Approach:** Essential download functionality with basic error boundaries  
**Execution Time:** < 3 minutes

## 🎯 MVP Stage 2 Testing Strategy

Focus on essential YouTube download functionality that bridges Stage 1 (validated URLs) to Stage 3 (transcript generation). Tests the critical acquisition functionality without comprehensive edge case testing.

### Stage 2 Modules
- **`youtube_audio_extractor.py`** - Downloads audio from YouTube videos using yt-dlp
- **`youtube_video_downloader.py`** - Downloads video from YouTube videos using yt-dlp
- **Stage 2 Integration** - `_stage_2_audio_acquisition()` in master processor

### Testing Principles
- **Basic Download Functionality:** Audio and video downloads work as expected
- **File Validation:** Downloaded files exist and are non-empty
- **Error Boundaries:** Critical failures are detected and handled
- **Integration Validation:** Stage 1 → Stage 2 handoff works correctly

---

## 🎵 Audio Download Tests

### File: `test_audio_extractor_mvp.py`

#### Test 1: Basic Audio Download
```python
def test_basic_audio_download():
    """
    MVP: Download audio from short YouTube video
    """
    # Setup - use short test video (< 30 seconds)
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll (3:32)
    
    # Execute
    result = download_audio(test_url)
    
    # Validate
    assert isinstance(result, str)
    assert result.endswith('.mp3')
    assert os.path.exists(result)
    assert os.path.getsize(result) > 10000  # At least 10KB (non-empty)
    
    # Cleanup
    if os.path.exists(result):
        os.remove(result)
```

#### Test 2: Audio Download Error Handling
```python
def test_audio_download_error_handling():
    """
    MVP: Basic error handling for audio download
    """
    # Test invalid URL
    invalid_url = "https://www.youtube.com/watch?v=INVALID_ID"
    result = download_audio(invalid_url)
    
    # Should return error message string
    assert isinstance(result, str)
    assert "error" in result.lower() or "failed" in result.lower()
    
    # Test private video
    private_url = "https://www.youtube.com/watch?v=PRIVATE_VIDEO_ID"
    result = download_audio(private_url)
    assert isinstance(result, str)
    # Should handle gracefully without crashing
```

#### Test 3: Audio Download Integration
```python
def test_audio_download_integration():
    """
    MVP: Audio download integrates with file organization
    """
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    # Execute download
    result = download_audio(test_url)
    
    # Validate file structure
    assert os.path.exists(result)
    
    # Check if file is in proper episode structure
    parent_dir = os.path.dirname(result)
    assert "Input" in parent_dir or "Content" in parent_dir
    
    # Validate filename format
    filename = os.path.basename(result)
    assert filename == "original_audio.mp3"  # Standardized filename
    
    # Cleanup
    if os.path.exists(result):
        os.remove(result)
```

---

## 🎬 Video Download Tests

### File: `test_video_downloader_mvp.py`

#### Test 1: Basic Video Download
```python
def test_basic_video_download():
    """
    MVP: Download video from short YouTube video
    """
    # Setup - use short test video
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    # Execute
    result = download_video(test_url)
    
    # Validate
    assert isinstance(result, str)
    assert result.endswith('.mp4')
    assert os.path.exists(result)
    assert os.path.getsize(result) > 100000  # At least 100KB (video should be larger)
    
    # Cleanup
    if os.path.exists(result):
        os.remove(result)
```

#### Test 2: Video Download Error Handling
```python
def test_video_download_error_handling():
    """
    MVP: Basic error handling for video download
    """
    # Test invalid URL
    invalid_url = "https://www.youtube.com/watch?v=INVALID_VIDEO_ID"
    result = download_video(invalid_url)
    
    # Should return error message string
    assert isinstance(result, str)
    assert "error" in result.lower() or "failed" in result.lower()
    
    # Verify no files were created
    assert not result.endswith('.mp4') or not os.path.exists(result)
```

#### Test 3: Video Download File Structure
```python
def test_video_download_file_structure():
    """
    MVP: Video download creates proper file structure
    """
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    # Execute download
    result = download_video(test_url)
    
    # Validate file structure
    assert os.path.exists(result)
    
    # Check if file is in proper episode structure
    parent_dir = os.path.dirname(result)
    assert "Input" in parent_dir
    
    # Validate filename format
    filename = os.path.basename(result)
    assert filename == "original_video.mp4"  # Standardized filename
    
    # Cleanup
    if os.path.exists(result):
        os.remove(result)
```

---

## 🔗 Stage 2 Integration Tests

### File: `test_stage_2_integration_mvp.py`

#### Test 1: Stage 1 → Stage 2 Handoff
```python
def test_stage_1_to_stage_2_integration():
    """
    MVP: Verify Stage 1 validation results work with Stage 2 acquisition
    """
    # Setup
    processor = MasterProcessor()
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    # Execute Stage 1
    stage_1_result = processor._stage_1_input_validation(youtube_url=test_url)
    
    # Validate Stage 1 output
    assert stage_1_result['valid'] == True
    assert stage_1_result['type'] == 'youtube_url'
    
    # Execute Stage 2 with Stage 1 output
    stage_2_result = processor._stage_2_audio_acquisition(stage_1_result)
    
    # Validate Stage 2 output
    assert 'audio_path' in stage_2_result
    assert os.path.exists(stage_2_result['audio_path'])
    
    # Check video path if available
    if 'video_path' in stage_2_result:
        assert os.path.exists(stage_2_result['video_path'])
    
    # Cleanup
    for path in stage_2_result.values():
        if os.path.exists(path):
            os.remove(path)
```

#### Test 2: Local Audio File Handling
```python
def test_local_audio_acquisition():
    """
    MVP: Verify Stage 2 handles local audio files correctly
    """
    # Setup - create test audio file
    test_audio_path = "tests/fixtures/sample_audio.mp3"
    
    # Ensure test file exists (or skip test)
    if not os.path.exists(test_audio_path):
        pytest.skip("Test audio file not available")
    
    processor = MasterProcessor()
    
    # Execute Stage 1
    stage_1_result = processor._stage_1_input_validation(audio_file=test_audio_path)
    
    # Validate Stage 1
    assert stage_1_result['valid'] == True
    assert stage_1_result['type'] == 'local_audio'
    
    # Execute Stage 2
    stage_2_result = processor._stage_2_audio_acquisition(stage_1_result)
    
    # Validate Stage 2 - should use existing file
    assert 'audio_path' in stage_2_result
    assert stage_2_result['audio_path'] == test_audio_path
```

#### Test 3: Download Error Recovery
```python
def test_acquisition_error_recovery():
    """
    MVP: Stage 2 handles download failures gracefully
    """
    processor = MasterProcessor()
    
    # Test with invalid YouTube URL
    invalid_input = {
        'valid': True,  # Passed Stage 1 validation
        'type': 'youtube_url',
        'info': {
            'url': 'https://www.youtube.com/watch?v=DEFINITELY_INVALID',
            'video_id': 'DEFINITELY_INVALID'
        }
    }
    
    # Should raise exception or return error
    with pytest.raises(Exception):
        processor._stage_2_audio_acquisition(invalid_input)
```

---

## 🧪 Test Support Functions

### Helper Functions
```python
def create_test_url():
    """Create a known-good short YouTube URL for testing"""
    return "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll - reliable test video

def cleanup_downloaded_files(base_dir="Content"):
    """Clean up any downloaded test files"""
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.startswith("Never Gonna Give You Up"):  # Rick Roll title
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                except Exception:
                    pass  # Ignore cleanup failures

def assert_valid_audio_file(file_path):
    """Assert file is a valid audio file"""
    assert os.path.exists(file_path)
    assert os.path.getsize(file_path) > 1000  # Non-empty
    assert file_path.endswith('.mp3')

def assert_valid_video_file(file_path):
    """Assert file is a valid video file"""
    assert os.path.exists(file_path)
    assert os.path.getsize(file_path) > 10000  # Videos are larger
    assert file_path.endswith('.mp4')
```

### Mock Services (for CI/CD)
```python
@pytest.fixture
def mock_youtube_download():
    """Mock YouTube downloads for fast CI testing"""
    with patch('Extraction.youtube_audio_extractor.download_audio') as mock_audio, \
         patch('Extraction.youtube_video_downloader.download_video') as mock_video:
        
        # Mock successful downloads
        mock_audio.return_value = "tests/fixtures/mock_audio.mp3"
        mock_video.return_value = "tests/fixtures/mock_video.mp4"
        
        yield mock_audio, mock_video

@pytest.fixture
def mock_yt_dlp():
    """Mock yt-dlp subprocess calls"""
    with patch('subprocess.run') as mock_run:
        # Mock successful yt-dlp execution
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Never Gonna Give You Up",
            stderr=""
        )
        yield mock_run
```

---

## ⚡ Performance Targets

### Execution Time Goals
- **Individual Tests:** < 30 seconds each (with real downloads)
- **Full Stage 2 Test Suite:** < 3 minutes
- **Mock Tests (CI):** < 10 seconds total

### Resource Limits
- **Test Downloads:** Use short videos (< 1 minute) only
- **Disk Space:** < 50MB total for test downloads
- **Network Usage:** Minimize with mocking in CI

---

## ✅ Success Criteria

### Coverage Goals
- **Audio Download:** 70% coverage (core download logic)
- **Video Download:** 70% coverage (core download logic)
- **Stage 2 Integration:** 80% coverage (critical path)

### Quality Gates
- ✅ **All MVP tests pass consistently**
- ✅ **Downloaded files are valid and non-empty**
- ✅ **Basic error handling works**
- ✅ **Stage 1 → Stage 2 integration works**

### Risk Mitigation
- ✅ **Critical download failures detected**
- ✅ **Network error handling validated**
- ✅ **File system integration verified**

---

## 🧪 Test Infrastructure Requirements

### Minimal Test Fixtures
```
tests/fixtures/stage_02/
├── sample_audio.mp3               # Small test audio file (for local testing)
├── expected_downloads.json        # Expected download results
└── mock_responses/                # Mock yt-dlp responses
    ├── success.json
    ├── error.json
    └── private_video.json
```

### Required Dependencies
```bash
# Test framework
pytest>=7.0.0
pytest-mock>=3.10.0

# For mocking external processes
pytest-subprocess>=1.4.0

# For network testing (optional)
responses>=0.18.0
```

### Environment Setup
```python
# Required environment variables (for real testing)
YOUTUBE_TEST_URL=https://www.youtube.com/watch?v=dQw4w9WgXcQ
SKIP_NETWORK_TESTS=false  # Set to true for offline testing

# Mock mode (for CI/CD)
USE_MOCK_DOWNLOADS=true
```

---

*This MVP Stage 2 testing specification provides essential validation for the YouTube acquisition functionality that bridges input validation to content processing. The approach balances thorough testing with fast execution and development velocity.*
