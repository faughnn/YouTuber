# Bug Fix Implementation Summary

## Issue Fixed
Fixed the bug where guest and host names were not correctly included in the prompts sent to the Gemini API for podcast script generation. Scripts were using "Unknown Guest" instead of the real guest name.

## Root Cause
1. **First prompt (analysis)**: Did not include participant names at all
2. **Second prompt (narrative generation)**: Used regex parsing on episode titles which failed for underscore-separated folder names like "Tucker_Carlson_RFK_Jr"

## Solution Implemented

### 1. Enhanced Transcript Analyzer (`transcript_analyzer.py`)
- **Added function**: `extract_host_and_guest_names(file_path)`
  - Parses the folder structure: `Content/{HOST}/{HOST}_{GUEST}/...`
  - Extracts names and formats them (replaces underscores with spaces)
  - Returns tuple: `(host_name, guest_name)`

- **Updated function**: `create_file_based_prompt(analysis_rules, file_path=None)`
  - Now accepts optional `file_path` parameter
  - When file_path is provided, extracts participant names and adds them to the prompt
  - Prepends participant information to the analysis prompt

- **Updated function**: `analyze_with_gemini_file_upload(file_object, analysis_rules, output_dir=None, file_path=None)`
  - Added optional `file_path` parameter
  - Passes file_path to `create_file_based_prompt`

### 2. Enhanced Podcast Narrative Generator (`podcast_narrative_generator.py`)
- **Added function**: `_extract_host_and_guest_names_from_path(episode_title)`
  - Handles both full paths and episode folder names
  - Parses folder structure patterns intelligently
  - Handles HOST_HOST_GUEST patterns (e.g., "Tucker_Carlson_RFK_Jr")

- **Updated function**: `_extract_guest_name_from_title(episode_title)`
  - Now uses the new folder structure parsing function
  - Simplified to call `_extract_host_and_guest_names_from_path`

- **Updated function**: `_extract_host_name_from_title(episode_title)`
  - Now uses the new folder structure parsing function
  - Simplified to call `_extract_host_and_guest_names_from_path`

### 3. Enhanced Master Processor (`master_processor_v2.py`)
- **Updated function**: `_stage_3_content_analysis(transcript_path)`
  - Now passes `transcript_path` to `analyze_with_gemini_file_upload`
  - Enables name extraction from the file path

## Testing
Created and ran comprehensive tests to verify:
- ✅ Name extraction from full paths works correctly
- ✅ Name extraction from episode folder names works correctly  
- ✅ Proper handling of underscores (replaced with spaces)
- ✅ Fallback to "Unknown Host"/"Unknown Guest" for invalid paths
- ✅ Both transcript analyzer and narrative generator functions work

## Expected Results
1. **First prompt (analysis)** will now include:
   ```
   ## PARTICIPANT INFORMATION
   
   **Host Name:** Tucker Carlson
   **Guest Name:** RFK Jr
   
   **CRITICAL INSTRUCTION:** Use "Tucker Carlson" as the host's name and "RFK Jr" as the guest's name throughout your analysis.
   ```

2. **Second prompt (narrative generation)** will continue to include participant names but now extracted correctly from folder structure instead of failing regex parsing.

3. **Generated scripts** will use the correct participant names instead of "Unknown Guest".

## Files Modified
- `Code/Content_Analysis/transcript_analyzer.py`
- `Code/Content_Analysis/podcast_narrative_generator.py`
- `Code/master_processor_v2.py`

## Backward Compatibility
All changes are backward compatible:
- New optional parameters have default values
- Functions continue to work with existing call patterns
- Fallback logic handles edge cases gracefully

The fix ensures that both the analysis and narrative generation prompts will use the correct host and guest names extracted from the folder structure, eliminating the "Unknown Guest" issue in generated podcast scripts.
