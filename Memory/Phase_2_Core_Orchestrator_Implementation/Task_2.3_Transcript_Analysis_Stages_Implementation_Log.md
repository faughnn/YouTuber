# Task 2.3: Transcript & Analysis Stages Implementation

**Project Goal**: Create a clean, streamlined master_processor_v2.py orchestrator that focuses purely on coordination and delegation, replacing the current bloated 1507-line implementation with proper separation of concerns.

**Phase**: Phase 2: Core Orchestrator Implementation  
**Task Reference**: Phase 2, Task 2.3 - Transcript & Analysis Stages Implementation  
**Prerequisites**: Task 2.2 (Media Extraction) must be completed  
**Agent Type**: Stage Implementation Agent  

---

## Task Objective

Implement `_stage_2_transcript_generation()` and `_stage_3_content_analysis()` with direct delegation to `audio_diarizer.py` and `transcript_analyzer.py`, following the pipeline-driven architecture pattern established in Task 2.2.

**CRITICAL DESIGN ISSUE DISCOVERED**: The current `analyze_with_gemini_file_upload()` function returns analysis content directly but doesn't save it to a file or return a file path. This breaks the pipeline's file-based handoff pattern where Stage 3 should return an analysis file path for Stage 4 to consume.

## Success Criteria

### Stage 2 Implementation
- [ ] Replace template `_stage_2_transcript_generation()` with working implementation
- [ ] Direct call to `diarize_audio(audio_path, hf_token)` without wrapper methods
- [ ] Audio file validation before transcription
- [ ] Transcript JSON saved to episode Processing folder
- [ ] Return transcript file path for Stage 3 handoff

### Stage 3 Implementation
- [ ] Replace template `_stage_3_content_analysis()` with working implementation  
- [ ] **FIX DESIGN FLAW**: Modify to save analysis output to file and return file path
- [ ] Direct integration with `analyze_with_gemini_file_upload()` 
- [ ] Analysis results saved to episode Processing folder
- [ ] Return analysis file path for Stage 4 handoff

### Pipeline Integration
- [ ] Stage 1 → Stage 2 handoff working (audio_path from Stage 1)
- [ ] Stage 2 → Stage 3 handoff working (transcript_path from Stage 2)  
- [ ] Stage 3 → Stage 4 handoff ready (analysis_file_path for Stage 4)

## Implementation Specifications

### Stage 2: Transcript Generation

**Working Module Interface**:
```python
from Extraction.audio_diarizer import diarize_audio

# Function signature (verified in Phase 1 analysis):
diarize_audio(audio_path: str, hf_auth_token_to_use: str) -> dict
```

**Expected Implementation Pattern**:
```python
def _stage_2_transcript_generation(self, audio_path: str) -> str:
    """Stage 2: Direct call to diarize_audio()."""
    self.logger.info(f"Stage 2: Transcript Generation for {audio_path}")
    
    try:
        # Validate audio file exists
        if not os.path.exists(audio_path):
            raise Exception(f"Audio file not found: {audio_path}")
        
        # Direct call to working module
        transcript_data = diarize_audio(
            audio_path, 
            self.config['api']['huggingface_token']
        )
        
        # Save transcript to Processing folder and return file path
        processing_dir = os.path.join(self.episode_dir, "Processing")
        if not os.path.exists(processing_dir):
            os.makedirs(processing_dir)
        
        transcript_filename = "original_audio_transcript.json"
        transcript_path = os.path.join(processing_dir, transcript_filename)
        
        with open(transcript_path, 'w', encoding='utf-8') as f:
            json.dump(transcript_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Transcript saved: {transcript_path}")
        return transcript_path
        
    except Exception as e:
        self.logger.error(f"Stage 2 failed: {e}")
        raise Exception(f"Transcript generation failed: {e}")
```

### Stage 3: Content Analysis (REQUIRES DESIGN FIX)

**Current Problem**: The `analyze_with_gemini_file_upload()` function returns analysis content directly:
```python
# CURRENT BROKEN PATTERN:
analysis_content = analyze_with_gemini_file_upload(file_object, rules, output_dir)
return analysis_content  # This returns content, not file path!
```

**Required Fix**: Modify the function to save output and return file path:
```python
def _stage_3_content_analysis(self, transcript_path: str) -> str:
    """Stage 3: Direct call to analyze_with_gemini_file_upload() with file output fix."""
    self.logger.info(f"Stage 3: Content Analysis for {transcript_path}")
    
    try:
        # Ensure Processing directory exists
        processing_dir = os.path.join(self.episode_dir, "Processing")
        if not os.path.exists(processing_dir):
            os.makedirs(processing_dir)
        
        # Load transcript and upload to Gemini
        from Content_Analysis.transcript_analyzer import upload_transcript_to_gemini
        display_name = f"transcript_{os.path.basename(transcript_path)}"
        file_object = upload_transcript_to_gemini(transcript_path, display_name)
        
        if not file_object:
            raise Exception("Failed to upload transcript to Gemini")
        
        # Call analysis function
        analysis_content = analyze_with_gemini_file_upload(
            file_object, 
            "",  # Empty rules for default analysis
            processing_dir
        )
        
        if not analysis_content:
            raise Exception("Analysis failed - no content returned")
        
        # CRITICAL FIX: Save analysis content to file and return file path
        analysis_filename = "original_audio_analysis_results.json"
        analysis_file_path = os.path.join(processing_dir, analysis_filename)
        
        with open(analysis_file_path, 'w', encoding='utf-8') as f:
            f.write(analysis_content)
        
        self.logger.info(f"Analysis saved: {analysis_file_path}")
        return analysis_file_path
        
    except Exception as e:
        self.logger.error(f"Stage 3 failed: {e}")
        raise Exception(f"Content analysis failed: {e}")
```

## Design Flaw Resolution Strategy

### Option 1: Modify transcript_analyzer.py (RECOMMENDED)
**Modify `analyze_with_gemini_file_upload()` to save output automatically:**
- Add file saving logic inside the function
- Return file path instead of content when `output_dir` is provided
- Maintain backward compatibility for standalone usage

### Option 2: Wrapper in Master Processor (SIMPLER)
**Handle file saving in the orchestrator:**
- Keep `analyze_with_gemini_file_upload()` unchanged
- Add file saving logic in `_stage_3_content_analysis()`
- Cleaner separation but adds orchestrator complexity

**Recommendation**: Use Option 2 for this task to minimize module changes and maintain clear separation of concerns.

## Anti-Pattern Prevention

### What NOT to implement:
- ❌ No wrapper methods around `diarize_audio()` or analysis functions
- ❌ No embedded transcription/analysis logic in orchestrator  
- ❌ No complex API configuration abstractions
- ❌ No duplicate file management (beyond necessary pipeline handoffs)

### Direct Delegation Pattern:
- ✅ Trust working modules to handle their complexity
- ✅ Simple input validation and error checking only
- ✅ File-based handoffs between stages (CRITICAL FOR PIPELINE)
- ✅ Clean exception handling without service layers

## Testing Requirements

### Stage 2 Testing
1. **Input Validation**: Test with valid audio path from Stage 1
2. **Transcription Process**: Verify WhisperX integration works
3. **Output Format**: Confirm transcript JSON is properly formatted
4. **File Handoff**: Verify transcript file path returned for Stage 3

### Stage 3 Testing  
1. **Input Processing**: Test with transcript file from Stage 2
2. **Gemini Integration**: Verify file upload and analysis works
3. **File Output**: Confirm analysis results saved to file
4. **Pipeline Handoff**: Verify analysis file path returned for Stage 4

### Integration Testing
1. **Stages 1-3 Pipeline**: Run complete sequence from URL to analysis file
2. **File Validation**: Confirm all expected files are created in correct locations
3. **Error Handling**: Test failure scenarios at each stage

## Expected Output Structure

After successful implementation, episode folder should contain:

```
Episode_Folder/
├── Input/
│   ├── original_audio.mp3                      # From Stage 1
│   └── original_video.mp4                      # From Stage 1  
└── Processing/
    ├── original_audio_transcript.json          # From Stage 2 (NEW)
    ├── original_audio_analysis_results.json    # From Stage 3 (NEW - FIXED)
    └── gemini_prompt_file_upload_analysis.txt  # From Stage 3 (debug)
```

## Dependencies & Prerequisites

### Required Modules (Verified Working):
- `Extraction.audio_diarizer` - WhisperX-based transcription
- `Content_Analysis.transcript_analyzer` - Gemini analysis (NEEDS FILE OUTPUT FIX)
- `Utils.file_organizer` - Episode structure management

### Configuration Requirements:
- HuggingFace token: `self.config['api']['huggingface_token']`
- Gemini API key: `self.config['api']['gemini_api_key']`

### Files to Modify:
- `c:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Code\master_processor_v2.py` (Stages 2 & 3)

### Import Requirements for Stage 3:
```python
# Add to master_processor_v2.py imports:
from Content_Analysis.transcript_analyzer import analyze_with_gemini_file_upload, upload_transcript_to_gemini
import json  # For JSON file operations
```

## Critical Success Factors

1. **File-Based Pipeline**: Both stages MUST return file paths, not content
2. **Direct Delegation**: Minimal orchestrator logic, maximum module trust
3. **Error Handling**: Clear failure reporting without abstraction layers
4. **Processing Folder**: Consistent file organization for downstream stages

**Priority**: Implement both stages to complete the content analysis pipeline foundation for subsequent narrative generation tasks.
