# MVP Smoke Tests Specification

**Created:** June 5, 2025  
**Purpose:** Essential smoke tests for YouTube content processing pipeline  
**Approach:** Minimal viable testing - happy path validation only  
**Execution Time:** < 2 minutes

## 🎯 MVP Smoke Test Strategy

After completing comprehensive Stage 1 testing, we're implementing essential smoke tests that validate core pipeline functionality without deep edge case testing.

### Core Principles
- **Happy Path Only:** Single successful processing path
- **Fast Execution:** Complete in under 2 minutes
- **Clear Pass/Fail:** Obvious success/failure criteria
- **Essential Coverage:** Critical pipeline stages only

---

## 🔥 Test Suite: `test_pipeline_smoke.py`

### Test 1: End-to-End Pipeline Smoke Test
**Objective:** Validate complete pipeline can process a YouTube video without crashing

```python
def test_complete_pipeline_smoke():
    """
    Smoke test: Complete pipeline processing
    Time limit: 90 seconds
    """
    # Setup
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Short test video
    config = load_minimal_config()
    
    # Execute
    result = master_processor.process_video(test_url, config)
    
    # Validate
    assert result.success == True
    assert result.output_files['audio'] is not None
    assert result.output_files['transcript'] is not None
    assert result.processing_time < 120  # 2 minutes max
```

### Test 2: Video Processing Smoke Test
**Objective:** Validate video stages (7-9) can produce output

```python
def test_video_pipeline_smoke():
    """
    Smoke test: Video clip extraction, timeline, assembly
    Time limit: 30 seconds
    """
    # Setup - use pre-downloaded test files
    video_file = "tests/fixtures/sample_video.mp4"
    analysis_data = load_test_analysis()
    
    # Execute video stages
    clips = extract_video_clips(video_file, analysis_data)
    timeline = build_timeline(clips, analysis_data)
    final_video = assemble_video(timeline)
    
    # Validate
    assert len(clips) > 0
    assert timeline is not None
    assert os.path.exists(final_video)
    assert os.path.getsize(final_video) > 1000  # Non-empty file
```

### Test 3: Error Boundary Smoke Test
**Objective:** Validate critical errors are caught and logged

```python
def test_error_handling_smoke():
    """
    Smoke test: Basic error detection
    Time limit: 10 seconds
    """
    # Test invalid URL
    with pytest.raises(ValidationError):
        master_processor.process_video("invalid-url", config)
    
    # Test missing file
    with pytest.raises(FileNotFoundError):
        extract_video_clips("nonexistent.mp4", {})
    
    # Validate error logging
    assert error_handler.get_error_count() > 0
```

---

## 🔥 Test Suite: `test_video_smoke.py`

### Test 1: Video Clip Extraction Smoke
**Objective:** Basic video clip extraction functionality

```python
def test_clip_extraction_smoke():
    """
    Smoke test: Extract 1-2 clips from sample video
    """
    # Setup
    video_file = "tests/fixtures/sample_video.mp4"
    timestamps = [{"start": 10, "end": 20}, {"start": 30, "end": 40}]
    
    # Execute
    clips = analysis_video_clipper.extract_clips(video_file, timestamps)
    
    # Validate
    assert len(clips) == 2
    for clip in clips:
        assert os.path.exists(clip)
        assert os.path.getsize(clip) > 100  # Non-empty
```

### Test 2: Timeline Building Smoke
**Objective:** Basic timeline structure creation

```python
def test_timeline_smoke():
    """
    Smoke test: Create basic timeline structure
    """
    # Setup
    clips = ["clip1.mp4", "clip2.mp4"]
    audio_file = "background.mp3"
    
    # Execute
    timeline = timeline_builder.create_timeline(clips, audio_file)
    
    # Validate
    assert timeline is not None
    assert len(timeline.tracks) > 0
    assert timeline.duration > 0
```

### Test 3: Video Assembly Smoke
**Objective:** Basic video assembly produces output

```python
def test_assembly_smoke():
    """
    Smoke test: Assemble timeline into final video
    """
    # Setup
    timeline = load_test_timeline()
    output_path = "test_output.mp4"
    
    # Execute
    result = video_assembler.assemble(timeline, output_path)
    
    # Validate
    assert result.success == True
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 1000
```

---

## 🧪 Test Infrastructure Requirements

### Minimal Test Fixtures
```
tests/fixtures/
├── sample_url.json                # 1 valid YouTube URL (short video)
├── sample_video.mp4               # 30-second test video
├── sample_audio.mp3               # Background audio
├── test_analysis.json             # Sample analysis data
└── minimal_config.yaml            # Basic configuration
```

### Mock Services (Simple)
```python
# YouTube API Mock
@pytest.fixture
def mock_youtube_api():
    with patch('yt_dlp.YoutubeDL') as mock:
        mock.return_value.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 30,
            'url': 'test_url'
        }
        yield mock

# File System Mock
@pytest.fixture
def mock_filesystem(tmp_path):
    """Create temporary directory structure"""
    return tmp_path
```

### Performance Gates
```python
# Timing validation
@pytest.mark.timeout(120)  # 2 minute max
def test_with_timeout():
    pass

# Memory validation (basic)
def assert_memory_usage_reasonable():
    import psutil
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    assert memory_mb < 1000  # Less than 1GB
```

---

## ⚡ Execution Strategy

### Test Execution Order
1. **Infrastructure Tests** (5 seconds) - Basic setup validation
2. **Unit Smoke Tests** (20 seconds) - Core utilities
3. **Video Smoke Tests** (30 seconds) - Video processing
4. **Pipeline Smoke Test** (90 seconds) - End-to-end

### CI/CD Integration
```yaml
# .github/workflows/smoke-tests.yml
name: Smoke Tests
on: [push, pull_request]
jobs:
  smoke-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v2
      - name: Run Smoke Tests
        run: pytest tests/smoke/ -v --timeout=120
```

### Success Criteria
- ✅ **All smoke tests pass**
- ✅ **Total execution time < 2 minutes**
- ✅ **No memory leaks detected**
- ✅ **Clear pass/fail results**

---

## 🚀 Future Enhancements

### When to Expand Beyond Smoke Tests
1. **Video pipeline is stable** - Add edge case testing
2. **Performance requirements are clear** - Add detailed benchmarks
3. **Error handling is mature** - Add comprehensive error scenarios
4. **Production deployment needed** - Add security and load testing

### Expansion Path
1. **Stage 2-6 Basic Tests** - Happy path for remaining stages
2. **Error Scenario Tests** - Network failures, invalid inputs
3. **Performance Tests** - Timing and memory benchmarks
4. **Security Tests** - Input validation and API security

---

*This smoke test specification provides essential quality gates for the YouTube content processing pipeline while maintaining fast feedback loops and development velocity.*
