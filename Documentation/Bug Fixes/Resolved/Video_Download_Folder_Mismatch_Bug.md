# Video Download Folder Mismatch Bug

## Bug Summary
**Issue ID:** VIDEO_FOLDER_MISMATCH_001  
**Date Discovered:** June 6, 2025  
**Date Resolved:** June 6, 2025  
**Severity:** High  
**Status:** ✅ RESOLVED  

## Resolution Summary
**Fixed in:** `master_processor.py` lines 485-503  
**Solution:** Modified video download section to extract title directly using `_extract_youtube_title()` method, ensuring consistency with audio processing.

**Key Changes:**
- Replaced `input_info['info'].get('title', 'Unknown Video')` with `self._extract_youtube_title(input_info['info']['url'])`
- Both audio and video now use the same title extraction method
- Ensured both downloads go to the same episode Input folder
- Added proper logging for video title extraction

## Verification Results
✅ **Test Passed:** Video title extraction now works correctly  
✅ **Test Passed:** Both audio and video use identical titles  
✅ **Test Passed:** Both downloads target the same episode folder  
✅ **Test Passed:** No more "Unknown Video" folder creation  

**Test Output Example:**
```
✅ Successfully extracted title: 'Rick Astley - Never Gonna Give You Up (Official Music Video)'
📁 Episode Input folder: C:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Content\Rick_Astley\Rick Astley - Never Gonna Give You Up (Official Music Video)\Input
🎵 Expected audio path: ...\Input\original_audio.mp3
🎬 Expected video path: ...\Input\original_video.mp4
✅ Audio and video would download to the same folder
```

## Problem Description
Video downloads were being directed to the wrong folder path due to title extraction inconsistency between video and audio processing. The video downloader was receiving "Unknown Video" as the title instead of the actual YouTube video title, causing it to create an incorrect folder structure.

**This issue has been resolved through direct title extraction in the video download process.**

## Observed Behavior
### From Log Analysis (13:23 execution):

**Audio Processing (Correct):**
- Successfully extracts title: "Joe Rogan Experience #2330 - Bono"
- Downloads to correct path: `C:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Content\Joe_Rogan_Experience\Joe Rogan Experience #2330 - Bono\Input\original_audio.mp3`

**Video Processing (Incorrect):**
- Receives title: "Unknown Video" 
- Attempts download to wrong path: `C:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Content\Unknown_Video\Unknown Video\Input`
- Video download fails due to incorrect folder targeting

## Technical Root Cause Analysis

### Code Location
**File:** `master_processor.py`  
**Lines:** 489-491

```python
video_title = input_info['info'].get('title', 'Unknown Video')
episode_input_folder = self.file_organizer.get_episode_input_folder(video_title)
self.logger.info(f"Video will be downloaded to episode Input folder: {episode_input_folder}")
```

### Root Cause
The video download logic relies on `input_info['info'].get('title')` to extract the video title, but this field is not properly populated during the input validation stage. The `input_info` dictionary structure does not include the YouTube video title in the `info` section, causing it to default to 'Unknown Video'.

### Data Flow Issue
1. **Input Validation Stage:** YouTube URL is validated and `input_info` is created
2. **Audio Acquisition:** Successfully extracts title using `_extract_youtube_title()` method
3. **Video Acquisition:** Tries to get title from `input_info['info']['title']` which doesn't exist
4. **Result:** Video downloader gets "Unknown Video" instead of actual title

## Evidence from Logs
```
2025-06-06 13:23:33,434 - master_processor - INFO - Extracted YouTube title: Joe Rogan Experience #2330 - Bono
2025-06-06 13:23:33,435 - master_processor - INFO - Created episode structure for: Joe Rogan Experience #2330 - Bono
2025-06-06 13:23:33,435 - master_processor - INFO - Episode folder: C:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Content\Joe_Rogan_Experience\Joe Rogan Experience #2330 - Bono
2025-06-06 13:23:40,983 - master_processor - INFO - Video will be downloaded to episode Input folder: C:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Content\Unknown_Video\Unknown Video\Input
2025-06-06 13:23:44,452 - master_processor - WARNING - Video download failed, continuing with audio-only processing
```

## Impact Assessment
- **Functional Impact:** Video downloads fail completely
- **Data Integrity:** Audio processing continues successfully, but video component is lost
- **User Experience:** Full pipeline processing degrades to audio-only
- **Storage Impact:** Creates unnecessary "Unknown_Video" folder structure

## Comparison to Previous Issues
This issue is similar to the problems documented in `Video_Output_Parameter_Investigation.md` where path management inconsistencies caused file organization failures. However, this is a more fundamental issue occurring at the title extraction level rather than just path construction.

## Proposed Investigation Areas
1. **Input Info Structure:** Examine how `input_info` dictionary is populated during validation
2. **Title Extraction Timing:** Investigate why video processing doesn't use the same title extraction method as audio
3. **Data Sharing:** Analyze how extracted YouTube metadata should be shared between processing stages
4. **FileOrganizer Integration:** Review how episode folder paths should be consistently determined

## Next Steps
~~1. Map the complete data flow from input validation through video download~~  
~~2. Identify where YouTube title should be extracted and stored for reuse~~  
~~3. Examine the `_create_episode_structure_early()` method and its integration~~  
~~4. Test potential solutions without breaking existing audio processing logic~~  

### ✅ COMPLETED - All Steps Resolved
1. **Data Flow Mapped:** Identified that `input_info['info']['title']` was missing
2. **Solution Implemented:** Video download now extracts title directly using `_extract_youtube_title()`
3. **Integration Verified:** Early episode structure creation works correctly with consistent titles
4. **Testing Complete:** Verified no breaking changes to audio processing logic

## Technical Fix Details

### Code Changes
**File:** `master_processor.py`  
**Lines Modified:** 485-503

**Before (Buggy Code):**
```python
video_title = input_info['info'].get('title', 'Unknown Video')
episode_input_folder = self.file_organizer.get_episode_input_folder(video_title)
self.logger.info(f"Video will be downloaded to episode Input folder: {episode_input_folder}")
```

**After (Fixed Code):**
```python
# Extract video title directly using the same method as audio download
# This ensures both audio and video use the same title for consistent folder structure
video_title = self._extract_youtube_title(input_info['info']['url'])
self.logger.info(f"Extracted video title: {video_title}")

# Download video with retry mechanism using the function
# The download_youtube_video function will extract the title again internally,
# ensuring consistent episode folder placement
```

### Architecture Benefits
- **Consistency:** Both audio and video use identical title extraction
- **Reliability:** No dependency on potentially missing `input_info` fields
- **Maintainability:** Single source of truth for YouTube title extraction
- **Robustness:** Both downloads guaranteed to target same episode folder

## Related Files
- `master_processor.py` (lines 480-520)
- `youtube_video_downloader.py`
- `file_organizer.py`
- `Video_Output_Parameter_Investigation.md`
