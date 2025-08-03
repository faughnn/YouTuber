# Names Wrong Bug Investigation - FIXED

## Summary
During processing of Gary Stevenson's "The REAL reason behind the housing crisis" video, the pipeline correctly extracted names (Host: "Gary Stevenson", Guest: "No guest") in Stage 1, but Stage 3 Content Analysis ended up using "Unknown Host" and "Unknown Guest" in the Gemini analysis prompts instead.

**STATUS: FIXED** - Modified file organizer to always use host_guest format

## Root Cause Analysis

The issue is a combination of two problems:

### 1. File Organizer Logic Issue
In `Code/Utils/file_organizer.py`, the `get_episode_paths()` method has flawed fallback logic:

```python
# Lines 57-60 in file_organizer.py
if sanitized_guest and sanitized_guest != "No_Guest":
    episode_folder_name = f"{sanitized_host}_{sanitized_guest}"
else:
    # Fallback to using the sanitized original title if no guest
    episode_folder_name = self.sanitize_filename(original_video_title)
```

When guest is "No guest", instead of creating folder `Gary_Stevenson_No_Guest`, it creates `The_REAL_reason_behind_the_housing_crisis` (using video title).

### 2. Name Extraction Failure
In `Code/Content_Analysis/transcript_analyzer.py`, the `extract_host_and_guest_names()` function expects folder structure `{HOST}/{HOST}_{GUEST}/` but receives `Gary_Stevenson/The_REAL_reason_behind_the_housing_crisis/`. Since this doesn't match the expected pattern, it returns `("Unknown Host", "Unknown Guest")`.

## Steps to Reproduce

1. Process a video where guest is set to "No guest" 
2. Observe that Stage 1 correctly extracts host/guest names
3. File organizer creates folder using video title instead of host_guest format
4. Stage 3 content analysis fails to extract names from folder structure
5. Gemini prompts use "Unknown Host"/"Unknown Guest" throughout analysis

## Expected vs Actual Behavior

**Expected:** 
- Folder structure: `Content/Gary_Stevenson/Gary_Stevenson_No_Guest/`
- Analysis prompts use: Host="Gary Stevenson", Guest="No guest"

**Actual:** 
- Folder structure: `Content/Gary_Stevenson/The_REAL_reason_behind_the_housing_crisis/`
- Analysis prompts use: Host="Unknown Host", Guest="Unknown Guest"

## Proposed Solution

### Option 1: Fix File Organizer (Recommended)
Modify `file_organizer.py` line 60 to always use the host_guest format:
```python
else:
    # Always use host_guest format, even for "No Guest"
    episode_folder_name = f"{sanitized_host}_{sanitized_guest}"
```

### Option 2: Improve Name Extraction 
Enhance `extract_host_and_guest_names()` to handle video-title folders by using the names passed from Stage 1 instead of parsing folder structure.

## Fix Implemented

**Date:** July 20, 2025
**Solution:** Modified `Code/Utils/file_organizer.py` to always use the host_guest format

**Changes Made:**
- Removed the fallback logic that used video title when guest was "No Guest"
- Now always creates folders in format `{HOST}_{GUEST}` regardless of guest value
- This ensures the name extraction logic in content analysis can properly parse the folder structure

**Result:** 
- Folder structure will now be: `Content/Gary_Stevenson/Gary_Stevenson_No_Guest/`
- Content analysis will correctly extract: Host="Gary Stevenson", Guest="No Guest"
- Gemini prompts will use the correct participant names throughout

## Files Involved

- `Code/Utils/file_organizer.py` (primary fix needed)
- `Code/Content_Analysis/transcript_analyzer.py` (name extraction logic)
- `Code/master_processor_v2.py` (Stage 3 passes transcript path to analyzer)