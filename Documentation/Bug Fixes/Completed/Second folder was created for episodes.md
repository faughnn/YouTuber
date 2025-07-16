This was created C:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Content\Tucker_Carlson\RFK_Jr_Provides_an_Update_on_His_Mission_to_End_Skyrocketing_Autism_and_Declassifying_Kennedy_Files

as was this C:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Content\Tucker_Carlson\Tucker_Carlson_RFK_Jr

this is the one that was used C:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Content\Tucker_Carlson\Tucker_Carlson_RFK_Jr

where is the first one being created? its not being used

# Bug Report: Duplicate Episode Folders Being Created

## Problem Description

Two different episode folders are being created for the same video:

1. **Long folder name (created but unused):** `RFK_Jr_Provides_an_Update_on_His_Mission_to_End_Skyrocketing_Autism_and_Declassifying_Kennedy_Files`
2. **Short folder name (created and used):** `Tucker_Carlson_RFK_Jr`

The first folder is created but not used, leading to wasted disk space and confusion.

## Root Cause Analysis

After investigating the codebase, I've identified that there are **two separate directory creation systems** operating independently:

### 1. FileOrganizer System (Used by Master Processor)
- **Location:** `Code/Utils/file_organizer.py`
- **Method:** `get_episode_paths()`
- **Logic:** 
  - If guest exists: `{sanitized_host}_{sanitized_guest}` → `Tucker_Carlson_RFK_Jr`
  - If no guest: `{sanitized_original_title}` → Long title-based folder
- **Used by:** Master Processor V2 in Stage 1 (Media Extraction)

### 2. Audio Diarizer System (Legacy/Independent)
- **Location:** `Code/Extraction/audio_diarizer.py` 
- **Method:** `sanitize_audio_filename(audio_base_name)`
- **Logic:** Always uses the full audio filename/title → `RFK_Jr_Provides_an_Update_on_His_Mission_to_End_Skyrocketing_Autism_and_Declassifying_Kennedy_Files`
- **Used by:** Audio diarization process (when called independently)

## Technical Details

### Where the Long Folder is Created
In `audio_diarizer.py` lines 361-382:
```python
audio_base_name, _ = os.path.splitext(os.path.basename(audio_file_path))
episode_folder_name = sanitize_audio_filename(audio_base_name)
channel_folder = os.path.join(TRANSCRIPTS_FOLDER, channel_name)
audio_transcript_folder = os.path.join(channel_folder, episode_folder_name)

if not os.path.exists(audio_transcript_folder):
    os.makedirs(audio_transcript_folder)
```

### Where the Short Folder is Created  
In `file_organizer.py` lines 60-73:
```python
sanitized_host = self.sanitize_filename(host_name)
sanitized_guest = self.sanitize_filename(guest_name)

if sanitized_guest and sanitized_guest != "No_Guest":
    episode_folder_name = f"{sanitized_host}_{sanitized_guest}"
else:
    episode_folder_name = self.sanitize_filename(original_video_title)

episode_folder = os.path.join(content_base, sanitized_host, episode_folder_name)
```

## Why This Happens

1. The Master Processor creates the proper organized structure using FileOrganizer
2. The audio diarizer, when processing transcripts, creates its own directory structure based on the audio filename
3. Both systems run during the pipeline, creating two different folders
4. The Master Processor uses the FileOrganizer paths for all subsequent operations
5. The audio diarizer's folder gets created but abandoned

## Proposed Solution: Remove Legacy Directory Creation from Audio Diarizer

This approach eliminates the duplicate folder creation by removing the automatic directory creation logic from the audio diarizer and making it rely on explicitly provided output paths.

### Core Changes Required

1. **Remove automatic directory creation logic from audio_diarizer.py**
2. **Make the diarizer only create output files in explicitly provided paths**
3. **Update all callers to ensure proper output directories exist**

### Detailed Implementation Steps

#### Step 1: Modify Audio Diarizer Function Signature

**File:** `Code/Extraction/audio_diarizer.py`

**Current Function:**
```python
def diarize_audio(audio_file_path: str, hugging_face_token: str = None):
```

**New Function:**
```python
def diarize_audio(audio_file_path: str, hugging_face_token: str = None, output_file_path: str = None):
```

#### Step 2: Remove Directory Creation Logic

**Current Code to Remove (lines 358-388 in audio_diarizer.py):**
```python
# Extract base name for creating subfolder structure: Channel/Episode/
audio_base_name, _ = os.path.splitext(os.path.basename(audio_file_path))

# Extract channel name and create episode folder name
channel_name = extract_channel_name(audio_base_name)
episode_folder_name = sanitize_audio_filename(audio_base_name)

# Create the full path: Transcripts/Channel/Episode/
channel_folder = os.path.join(TRANSCRIPTS_FOLDER, channel_name)
audio_transcript_folder = os.path.join(channel_folder, episode_folder_name)

if not output_file_path_explicitly_provided:
    output_filename = audio_base_name + ".json"
    output_file_path = os.path.join(audio_transcript_folder, output_filename)
    # ... directory creation logic ...

# Ensure the audio-specific transcript folder exists
if not os.path.exists(audio_transcript_folder):
    os.makedirs(audio_transcript_folder)

# Also ensure the main Transcripts folder exists
if not os.path.exists(TRANSCRIPTS_FOLDER):
    os.makedirs(TRANSCRIPTS_FOLDER)
```

**New Simplified Logic:**
```python
def diarize_audio(audio_file_path: str, hugging_face_token: str = None, output_file_path: str = None):
    """
    Perform speaker diarization on audio file.
    
    Args:
        audio_file_path: Path to input audio file
        hugging_face_token: Optional HuggingFace token
        output_file_path: Explicit path where transcript should be saved
                         (caller is responsible for ensuring directory exists)
    
    Returns:
        JSON string with diarization results
    """
    
    if output_file_path is None:
        # For backward compatibility, generate default name but don't create directories
        audio_base_name, _ = os.path.splitext(os.path.basename(audio_file_path))
        output_file_path = f"{audio_base_name}_transcript.json"
        print(f"Warning: No output path specified. Using: {output_file_path}")
        print("Note: Caller must ensure output directory exists.")
    
    # Validate that output directory exists (but don't create it)
    output_dir = os.path.dirname(output_file_path)
    if output_dir and not os.path.exists(output_dir):
        raise ValueError(f"Output directory does not exist: {output_dir}. Please create it first.")
    
    # ... rest of diarization logic remains the same ...
```

#### Step 3: Update Master Processor to Provide Explicit Paths

**File:** `Code/master_processor_v2.py`

**Current Code (Stage 2):**
```python
def _stage_2_transcript_generation(self, audio_path: str) -> str:
    # ... existing validation code ...
    
    transcript_result = diarize_audio(audio_path, hf_token)
```

**New Code:**
```python
def _stage_2_transcript_generation(self, audio_path: str) -> str:
    # ... existing validation code ...
    
    # Ensure Processing directory exists before calling diarizer
    processing_dir = os.path.join(self.episode_dir, "Processing")
    if not os.path.exists(processing_dir):
        os.makedirs(processing_dir)
    
    # Provide explicit output path to diarizer
    transcript_path = os.path.join(processing_dir, "original_audio_transcript.json")
    transcript_result = diarize_audio(audio_path, hf_token, transcript_path)
    
    # Since diarizer now saves directly to the specified path, we don't need
    # to parse and re-save the JSON - just return the path
    return transcript_path
```

#### Step 4: Update Other Callers

**Files to Check and Update:**

Since direct script usage is not a concern, we only need to focus on updating code that imports and uses the `diarize_audio()` function:

1. **UI components that might call the diarizer**
   - **Location:** `Code/UI/` directory
   - **Impact:** If UI allows direct transcript generation
   - **Action needed:** Search for any direct calls to `diarize_audio()`

2. **Test files**
   - **Impact:** Unit tests that call `diarize_audio()` directly
   - **Action needed:** Update test cases to provide explicit output paths

3. **Other scripts that import the diarizer**
   - **Action needed:** Search codebase for `from audio_diarizer import` or similar imports

**Pattern for Updates:**
```python
# Old way (creates complex directory structure)
result = diarize_audio(audio_file, token)

# New way (explicit output path control)
output_dir = "desired/output/directory"
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "transcript.json")
result = diarize_audio(audio_file, token, output_path)
```

#### Step 5: Remove Helper Functions (Optional Cleanup)

**Functions that can be removed or simplified:**
- `extract_channel_name()` - No longer needed for directory structure
- `sanitize_audio_filename()` - Only needed if used elsewhere
- Directory creation constants like `TRANSCRIPTS_FOLDER`

### Implementation Plan

#### Phase 1: Core Changes (Day 1)
1. Modify `diarize_audio()` function signature and logic
2. Update Master Processor Stage 2
3. Test basic pipeline functionality

#### Phase 2: Update All Callers (Day 2)
1. Search for all calls to `diarize_audio()` in codebase
2. Update each caller to provide explicit output paths
3. Ensure all callers create necessary directories

#### Phase 3: Testing and Validation (Day 3)
1. Test Master Processor pipeline end-to-end
2. Test standalone diarizer usage
3. Verify no duplicate folders are created
4. Clean up any orphaned folders from previous runs

#### Phase 4: Cleanup (Day 4)
1. Remove unused helper functions
2. Update documentation
3. Add unit tests to prevent regression

## Files to Modify

1. **`Code/Extraction/audio_diarizer.py`** - Remove automatic directory creation, add explicit output path parameter
2. **`Code/master_processor_v2.py`** - Update Stage 2 to provide explicit output path
3. **Any standalone scripts** - Update calls to provide output paths
4. **UI components** - Update any direct calls to diarizer
5. **Test files** - Update test cases

## Risk Assessment

- **Medium Risk:** Requires updating all callers to provide explicit paths
- **High Impact:** Will completely eliminate duplicate folder creation
- **Breaking Changes:** May break standalone usage if not handled properly
- **Testing Required:** Comprehensive testing of all diarizer usage patterns

## Benefits of This Approach

1. **Complete Elimination:** No chance of duplicate folders being created
2. **Clear Responsibility:** Callers explicitly control where files are saved
3. **Simplified Logic:** Removes complex directory creation logic from diarizer
4. **Better Separation of Concerns:** Directory management handled by appropriate components
5. **Easier Testing:** Explicit paths make testing more predictable

## Testing Strategy

1. **Unit Tests:**
   - Test diarizer with explicit output paths
   - Test error handling when output directory doesn't exist
   - Test backward compatibility warnings

2. **Integration Tests:**
   - Test full Master Processor pipeline creates only one folder
   - Test standalone diarizer usage with manual directory creation
   - Test various episode types (with/without guests)

3. **Regression Tests:**
   - Verify existing episodes still process correctly
   - Ensure no functionality is lost

## Rollback Plan

If issues arise during implementation:
1. Keep original `diarize_audio()` as `diarize_audio_legacy()`
2. Temporarily switch callers back to legacy version
3. Fix issues and re-deploy new version

## Success Criteria

- [ ] Master Processor pipeline creates only one episode folder
- [ ] Standalone diarizer usage still works with manual directory creation
- [ ] No duplicate folders created for any episode type
- [ ] All existing functionality preserved
- [ ] No orphaned folders left behind