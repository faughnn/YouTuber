# Bug Report: Narrative Generator Not Working

**Date:** June 8, 2025  
**File:** `test_narrative_generator.py`  
**Status:** PARTIALLY RESOLVED - Multiple Issues Found  

## Problem Summary

The `NarrativeCreatorGenerator` fails to generate narrative scripts when tested with real analysis data from the Joe Rogan Experience #2330 - Bono episode.

## Investigation Timeline

### Initial Error: JSON Format Mismatch

**Error:** `'list' object has no attribute 'get'`  
**Location:** `podcast_narrative_generator.py:102`  

**Root Cause:** The code expected analysis data to be a dictionary with a `segments` key, but the actual analysis file (`original_audio_full_transcript_analysis_results.json`) contains a JSON array at the root level.

**Expected Format:**
```json
{
  "segments": [...]
}
```

**Actual Format:**
```json
[
  {
    "narrativeSegmentTitle": "...",
    "severityRating": "HIGH",
    ...
  }
]
```

**Fix Applied:** Updated validation logic in `_upload_analysis_file()` to handle both formats:
```python
# Check if it's a list (direct array) or dict with segments key
if isinstance(analysis_data, list):
    if not analysis_data:
        raise ValueError("Invalid analysis format: empty segments array")
elif isinstance(analysis_data, dict):
    if not analysis_data.get('segments'):
        raise ValueError("Invalid analysis format: no segments found")
```

### Second Error: Missing Template Parameter

**Error:** `KeyError: 'analysis_json'`  
**Location:** `podcast_narrative_generator.py:149` in `_build_unified_prompt()`  

**Root Cause:** The prompt template formatting was looking for an `{analysis_json}` placeholder that doesn't exist in the template file.

**Template Investigation:**
- Checked `tts_podcast_narrative_prompt.txt` 
- Only contains `{episode_title}` and `{custom_instructions}` placeholders
- All JSON braces properly escaped as `{{` and `}}`

**Current Status:** Error persists - source of `{analysis_json}` reference not yet identified

## File Analysis

### Analysis File Structure
**File:** `Content/Joe_Rogan_Experience/Joe Rogan Experience #2330 - Bono/Processing/original_audio_full_transcript_analysis_results.json`
- **Size:** 32,212 bytes
- **Format:** JSON array with 20 analysis segments
- **Structure:** Each segment contains:
  - `narrativeSegmentTitle`
  - `severityRating` 
  - `relevantChecklistTheme`
  - `suggestedClip` (with timestamps)
  - `fullerContextTimestamps` (start/end)
  - `harmPotential`

### Template File Structure
**File:** `Code/Content_Analysis/Prompts/tts_podcast_narrative_prompt.txt`
- **Size:** 4,090 characters
- **Valid Placeholders:** `{episode_title}`, `{custom_instructions}`
- **JSON Escaping:** Properly uses `{{` and `}}` for literal braces

## Test Results

### Test Script Output
```
=== Testing NarrativeCreatorGenerator ===
✓ Analysis file found (32212 bytes)
✓ Generator initialized successfully
✓ File uploaded successfully to Gemini
❌ Failed at prompt building stage
```

### Error Stack Trace
```
File "podcast_narrative_generator.py", line 149, in _build_unified_prompt
    formatted_prompt = self.prompt_template.format(
KeyError: 'analysis_json'
```

## Current Status

### ✅ Resolved Issues
1. **JSON Format Validation:** Fixed to handle both array and object formats
2. **File Upload:** Successfully uploads analysis file to Gemini API

### ❌ Outstanding Issues
1. **Template Formatting Error:** Unknown source of `{analysis_json}` reference
2. **Prompt Building:** Cannot complete unified prompt generation

## Next Steps

1. **Immediate Priority:** Locate source of `{analysis_json}` placeholder reference
   - Check for any string concatenation that might introduce this
   - Verify no hidden characters or encoding issues in template file
   - Review any recent manual edits to the codebase

2. **Testing:** Create isolated test for prompt formatting without file upload

3. **Validation:** Ensure template file integrity and correct placeholder usage

## Technical Notes

### File Upload Success Pattern
The Gemini file upload is working correctly following the pattern from `transcript_analyzer.py`:
- File validation ✅
- Upload with proper MIME type ✅  
- File reference generation ✅
- 48-hour auto-cleanup ✅

### Architecture Compatibility
The fix maintains compatibility with existing analysis data formats while adding support for the actual format used by the content analysis pipeline.

## Code Changes Made

### `podcast_narrative_generator.py`
**Method:** `_upload_analysis_file()`  
**Lines:** 99-113  
**Change:** Enhanced JSON validation to handle both array and dictionary formats

```python
# Before
if not analysis_data.get('segments'):
    raise ValueError("Invalid analysis format: no segments found")

# After  
if isinstance(analysis_data, list):
    if not analysis_data:
        raise ValueError("Invalid analysis format: empty segments array")
elif isinstance(analysis_data, dict):
    if not analysis_data.get('segments'):
        raise ValueError("Invalid analysis format: no segments found")
else:
    raise ValueError("Invalid analysis format: expected array or object with segments")
```

---

**Investigation Status:** ONGOING  
**Next Update:** After resolving template formatting issue