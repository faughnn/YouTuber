# MVP Utility Tests

**Created:** June 5, 2025  
**Purpose:** Essential testing for core utility functions  
**Approach:** Critical functions only, basic error handling  
**Execution Time:** < 30 seconds

## 🎯 MVP Utility Testing Strategy

Focus on the most critical utility functions that support the main pipeline. These utilities are used across all pipeline stages and need basic reliability validation.

### Core Utilities to Test
- **ErrorHandler** - Critical error handling and retry logic
- **FileOrganizer** - Essential file operations and path management
- **ProgressTracker** - Basic stage tracking functionality

### Testing Principles
- **Critical Functions Only:** Focus on most-used methods
- **Happy Path + Basic Errors:** Core functionality plus critical error cases
- **Fast Execution:** Each test completes in seconds
- **Clear Validation:** Obvious success/failure criteria

---

## 🚨 ErrorHandler MVP Tests

### File: `test_error_handler_mvp.py`

#### Test 1: Basic Error Categorization
```python
def test_error_categorization():
    """
    MVP: Verify errors are categorized correctly
    """
    error_handler = ErrorHandler()
    
    # Test network error
    network_error = ConnectionError("Network timeout")
    category = error_handler.categorize_error(network_error)
    assert category == ErrorCategory.NETWORK
    
    # Test file error
    file_error = FileNotFoundError("File not found")
    category = error_handler.categorize_error(file_error)
    assert category == ErrorCategory.FILE_SYSTEM
    
    # Test API error
    api_error = ValueError("Invalid API response")
    category = error_handler.categorize_error(api_error)
    assert category == ErrorCategory.API
```

#### Test 2: Basic Retry Logic
```python
def test_basic_retry_logic():
    """
    MVP: Verify retry mechanism works for transient errors
    """
    error_handler = ErrorHandler()
    call_count = 0
    
    def failing_function():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("Temporary network issue")
        return "success"
    
    # Execute with retry
    result = error_handler.retry_on_failure(
        failing_function,
        max_retries=3,
        retry_delay=0.1
    )
    
    # Validate
    assert result == "success"
    assert call_count == 3  # Failed twice, succeeded on third attempt
```

#### Test 3: Error Logging
```python
def test_error_logging():
    """
    MVP: Verify errors are logged properly
    """
    error_handler = ErrorHandler()
    
    # Create test error
    test_error = ValueError("Test error message")
    
    # Log error
    error_handler.log_error(test_error, context="test_function")
    
    # Verify logging
    error_count = error_handler.get_error_count()
    assert error_count > 0
    
    recent_errors = error_handler.get_recent_errors(limit=1)
    assert len(recent_errors) == 1
    assert "Test error message" in str(recent_errors[0])
```

#### Test 4: Critical Error Handling
```python
def test_critical_error_handling():
    """
    MVP: Verify critical errors are handled properly
    """
    error_handler = ErrorHandler()
    
    # Test critical error (should not retry)
    def critical_function():
        raise PermissionError("Access denied")
    
    with pytest.raises(PermissionError):
        error_handler.retry_on_failure(
            critical_function,
            max_retries=3
        )
    
    # Should not have retried
    assert error_handler.get_retry_count() == 0
```

---

## 📁 FileOrganizer MVP Tests

### File: `test_file_organizer_mvp.py`

#### Test 1: Episode Structure Creation
```python
def test_episode_structure_creation():
    """
    MVP: Verify episode directory structure is created correctly
    """
    organizer = FileOrganizer()
    
    # Test data
    youtube_url = "https://www.youtube.com/watch?v=test123"
    base_path = "tests/temp"
    
    # Create structure
    episode_path = organizer.create_episode_structure(youtube_url, base_path)
    
    # Validate structure
    assert os.path.exists(episode_path)
    assert os.path.exists(os.path.join(episode_path, "audio"))
    assert os.path.exists(os.path.join(episode_path, "video"))
    assert os.path.exists(os.path.join(episode_path, "analysis"))
    assert os.path.exists(os.path.join(episode_path, "output"))
    
    # Cleanup
    shutil.rmtree(episode_path)
```

#### Test 2: File Path Generation
```python
def test_file_path_generation():
    """
    MVP: Verify file paths are generated correctly
    """
    organizer = FileOrganizer()
    
    episode_path = "/content/test_episode"
    
    # Test various file types
    audio_path = organizer.get_file_path(episode_path, "audio", "original.mp3")
    video_path = organizer.get_file_path(episode_path, "video", "original.mp4")
    analysis_path = organizer.get_file_path(episode_path, "analysis", "transcript.json")
    
    # Validate paths
    assert audio_path == "/content/test_episode/audio/original.mp3"
    assert video_path == "/content/test_episode/video/original.mp4"
    assert analysis_path == "/content/test_episode/analysis/transcript.json"
```

#### Test 3: File Validation
```python
def test_file_validation():
    """
    MVP: Verify file validation works for common formats
    """
    organizer = FileOrganizer()
    
    # Create test files
    test_dir = "tests/temp"
    os.makedirs(test_dir, exist_ok=True)
    
    # Valid audio file
    audio_file = os.path.join(test_dir, "test.mp3")
    with open(audio_file, 'wb') as f:
        f.write(b'fake mp3 content')
    
    # Valid video file
    video_file = os.path.join(test_dir, "test.mp4")
    with open(video_file, 'wb') as f:
        f.write(b'fake mp4 content')
    
    # Test validation
    assert organizer.is_valid_audio_file(audio_file) == True
    assert organizer.is_valid_video_file(video_file) == True
    assert organizer.is_valid_audio_file("nonexistent.mp3") == False
    
    # Cleanup
    shutil.rmtree(test_dir)
```

#### Test 4: Cleanup Functionality
```python
def test_cleanup_functionality():
    """
    MVP: Verify cleanup removes temporary files
    """
    organizer = FileOrganizer()
    
    # Create temporary files
    temp_dir = "tests/temp_cleanup"
    os.makedirs(temp_dir, exist_ok=True)
    
    temp_files = [
        os.path.join(temp_dir, "temp1.tmp"),
        os.path.join(temp_dir, "temp2.tmp")
    ]
    
    for file_path in temp_files:
        with open(file_path, 'w') as f:
            f.write("temporary content")
    
    # Verify files exist
    for file_path in temp_files:
        assert os.path.exists(file_path)
    
    # Cleanup
    organizer.cleanup_temporary_files(temp_dir)
    
    # Verify cleanup
    for file_path in temp_files:
        assert not os.path.exists(file_path)
    
    # Cleanup test directory
    shutil.rmtree(temp_dir)
```

---

## 📊 ProgressTracker MVP Tests

### File: `test_progress_tracker_mvp.py`

#### Test 1: Stage Tracking
```python
def test_stage_tracking():
    """
    MVP: Verify progress tracking for pipeline stages
    """
    tracker = ProgressTracker()
    
    # Start tracking
    tracker.start_stage(ProcessingStage.INPUT_VALIDATION)
    assert tracker.current_stage == ProcessingStage.INPUT_VALIDATION
    assert tracker.get_progress_percentage() > 0
    
    # Complete stage
    tracker.complete_stage(ProcessingStage.INPUT_VALIDATION)
    assert tracker.is_stage_complete(ProcessingStage.INPUT_VALIDATION)
    
    # Move to next stage
    tracker.start_stage(ProcessingStage.AUDIO_EXTRACTION)
    assert tracker.current_stage == ProcessingStage.AUDIO_EXTRACTION
```

#### Test 2: Progress Percentage Calculation
```python
def test_progress_percentage():
    """
    MVP: Verify progress percentage is calculated correctly
    """
    tracker = ProgressTracker()
    
    # No stages completed
    assert tracker.get_progress_percentage() == 0
    
    # Complete some stages
    tracker.complete_stage(ProcessingStage.INPUT_VALIDATION)
    tracker.complete_stage(ProcessingStage.AUDIO_EXTRACTION)
    
    progress = tracker.get_progress_percentage()
    assert 0 < progress < 100  # Should be partial progress
    
    # Complete all stages
    for stage in ProcessingStage:
        tracker.complete_stage(stage)
    
    assert tracker.get_progress_percentage() == 100
```

#### Test 3: Time Estimation
```python
def test_time_estimation():
    """
    MVP: Verify basic time estimation functionality
    """
    tracker = ProgressTracker()
    
    # Start tracking with timing
    start_time = time.time()
    tracker.start_stage(ProcessingStage.INPUT_VALIDATION)
    
    # Simulate some work
    time.sleep(0.1)
    
    # Complete stage
    tracker.complete_stage(ProcessingStage.INPUT_VALIDATION)
    
    # Check timing
    elapsed = tracker.get_elapsed_time()
    assert elapsed >= 0.1  # At least the sleep time
    
    estimated_total = tracker.estimate_total_time()
    assert estimated_total > elapsed  # Should estimate more time needed
```

#### Test 4: Error State Tracking
```python
def test_error_state_tracking():
    """
    MVP: Verify error state is tracked properly
    """
    tracker = ProgressTracker()
    
    # Start stage
    tracker.start_stage(ProcessingStage.AUDIO_EXTRACTION)
    
    # Mark stage as failed
    error = ValueError("Test error")
    tracker.mark_stage_failed(ProcessingStage.AUDIO_EXTRACTION, error)
    
    # Verify error state
    assert tracker.has_errors() == True
    assert tracker.is_stage_failed(ProcessingStage.AUDIO_EXTRACTION) == True
    
    failed_stages = tracker.get_failed_stages()
    assert ProcessingStage.AUDIO_EXTRACTION in failed_stages
```

---

## 🔗 Integration Tests

### File: `test_utilities_integration_mvp.py`

#### Test 1: Error Handler + File Organizer Integration
```python
def test_error_handler_file_organizer_integration():
    """
    MVP: Verify error handler and file organizer work together
    """
    error_handler = ErrorHandler()
    organizer = FileOrganizer()
    
    def create_structure_with_retry():
        try:
            return organizer.create_episode_structure(
                "https://youtube.com/test",
                "/invalid/path"  # Should fail
            )
        except Exception as e:
            error_handler.log_error(e, "file_creation")
            raise
    
    # Should fail and log error
    with pytest.raises(OSError):
        error_handler.retry_on_failure(create_structure_with_retry, max_retries=2)
    
    # Verify error was logged
    assert error_handler.get_error_count() > 0
```

#### Test 2: Progress Tracker + Error Handler Integration
```python
def test_progress_tracker_error_handler_integration():
    """
    MVP: Verify progress tracker and error handler integration
    """
    tracker = ProgressTracker()
    error_handler = ErrorHandler()
    
    # Start stage
    tracker.start_stage(ProcessingStage.CONTENT_ANALYSIS)
    
    # Simulate stage failure
    stage_error = RuntimeError("Analysis failed")
    error_handler.log_error(stage_error, "content_analysis")
    tracker.mark_stage_failed(ProcessingStage.CONTENT_ANALYSIS, stage_error)
    
    # Verify integration
    assert tracker.has_errors() == True
    assert error_handler.get_error_count() > 0
    
    # Both should report the same error context
    failed_stages = tracker.get_failed_stages()
    recent_errors = error_handler.get_recent_errors(limit=1)
    
    assert ProcessingStage.CONTENT_ANALYSIS in failed_stages
    assert "Analysis failed" in str(recent_errors[0])
```

---

## ⚡ Performance & Resource Tests

### File: `test_utility_performance_mvp.py`

#### Test 1: Memory Usage Validation
```python
def test_utility_memory_usage():
    """
    MVP: Verify utilities don't use excessive memory
    """
    import psutil
    
    process = psutil.Process()
    initial_memory = process.memory_info().rss
    
    # Create and use utilities
    error_handler = ErrorHandler()
    organizer = FileOrganizer()
    tracker = ProgressTracker()
    
    # Simulate typical usage
    for i in range(100):
        error_handler.log_error(ValueError(f"Test error {i}"), "test")
        tracker.start_stage(ProcessingStage.INPUT_VALIDATION)
        tracker.complete_stage(ProcessingStage.INPUT_VALIDATION)
    
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    
    # Should not increase memory by more than 50MB
    assert memory_increase < 50 * 1024 * 1024
```

#### Test 2: Performance Gates
```python
@pytest.mark.timeout(5)  # 5 second max
def test_utility_performance_gates():
    """
    MVP: Verify utilities perform within time limits
    """
    error_handler = ErrorHandler()
    organizer = FileOrganizer()
    tracker = ProgressTracker()
    
    start_time = time.time()
    
    # Perform typical operations
    for i in range(50):
        # Error handling
        error_handler.categorize_error(ValueError("test"))
        
        # File operations
        path = organizer.get_file_path("/test", "audio", f"file{i}.mp3")
        
        # Progress tracking
        tracker.start_stage(ProcessingStage.INPUT_VALIDATION)
        tracker.complete_stage(ProcessingStage.INPUT_VALIDATION)
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Should complete in under 2 seconds
    assert execution_time < 2.0
```

---

## ✅ Success Criteria

### Coverage Goals
- **ErrorHandler:** 70% coverage (critical error handling logic)
- **FileOrganizer:** 60% coverage (essential file operations)
- **ProgressTracker:** 60% coverage (basic tracking functionality)

### Quality Gates
- ✅ **All MVP utility tests pass consistently**
- ✅ **Basic error handling works reliably**
- ✅ **File operations complete successfully**
- ✅ **Progress tracking provides accurate information**

### Performance Targets
- ✅ **All tests complete in < 30 seconds total**
- ✅ **Memory usage stays reasonable**
- ✅ **No resource leaks detected**

---

*This MVP utility testing specification provides essential validation for the core utility functions while maintaining fast execution and focusing on the most critical functionality.*
