# Video Clipping from Analysis Data - Project Plan

## Overview
Create a system to automatically generate video clips from the Joe Rogan Experience 2325 analysis file that identifies the "Top 10 Worst" segments with problematic content for academic research purposes.

## Current Resources Available

### Source Files
- **Analysis File**: `Joe_Rogan_Experience_2325_TOP10_WORST.txt`
  - Contains JSON data with 10+ problematic segments
  - Each segment has timestamps, quotes, context, and severity ratings
  - Duration data and harm potential assessments included

- **Source Video**: `Joe Rogan Experience 2325 - Aaron Rodgers.mp4`
  - Full episode video file
  - Located in Video Rips folder

- **Existing Video Processing Tool**: `video_segment_extractor.py`
  - Already has FFmpeg integration
  - Can extract clips based on timestamps
  - Has filename sanitization functions

### Analysis Data Structure (from examination)
Each segment in the JSON contains:
```json
{
  "narrativeSegmentTitle": "Title of the problematic segment",
  "severityRating": "HIGH/CRITICAL",
  "fullerContextTimestamps": {
    "start": 45.17,
    "end": 49.03,
    "start2": 56.0,    // Some segments have multiple time ranges
    "end2": 102.16
  },
  "segmentDurationInSeconds": 226.0,
  "suggestedClip": [
    {
      "timestamp": 19.33,
      "speaker": "SPEAKER_02 (Joe Rogan)",
      "quote": "Specific problematic quote"
    }
  ],
  "clipContextDescription": "Brief context description",
  "harmPotential": "Description of real-world harm potential"
}
```

## Implementation Plan

### Phase 1: Data Parser Development
**Goal**: Extract clip information from the analysis file

**Components Needed**:
1. **JSON Parser**
   - Parse the embedded JSON from the text file
   - Extract timestamp ranges for each segment
   - Handle segments with multiple time ranges (start/end and start2/end2)
   
2. **Timestamp Converter**
   - Convert time formats (45.17 = 45 seconds, 1.04.19 = 1 hour 4 minutes 19 seconds)
   - Handle various timestamp formats found in the data
   - Add buffer time before/after clips for context

3. **Clip Metadata Generator**
   - Generate descriptive filenames from segment titles
   - Include severity rating in filename
   - Create metadata files for each clip with context information

### Phase 2: Video Processing Enhancement
**Goal**: Extend existing video processing to handle analysis data

**Enhancements to `video_segment_extractor.py`**:
1. **Analysis File Support**
   - Add function to read analysis files
   - Parse JSON segments from text files
   - Map analysis data to clip extraction parameters

2. **Multi-Range Segment Handling**
   - Handle segments with multiple timestamp ranges
   - Option to create single clips or separate clips for each range
   - Merge multiple ranges into single clip with transitions

3. **Enhanced Filename Generation**
   - Include severity rating (HIGH/CRITICAL)
   - Include segment number (01-10)
   - Include brief description from title
   - Format: `[CRITICAL]_01_Cancer_Treatment_Misinformation.mp4`

### Phase 3: Output Organization
**Goal**: Create structured output with proper categorization

**Output Structure**:
```
Video Rips/Joe Rogan Experience 2325 - Aaron Rodgers/
├── Clips/
│   ├── Analysis_Based_Clips/
│   │   ├── CRITICAL_Segments/
│   │   │   ├── [CRITICAL]_01_Cancer_Treatment_Misinformation.mp4
│   │   │   ├── [CRITICAL]_02_COVID_Vaccine_Death_Claims.mp4
│   │   │   └── ...
│   │   ├── HIGH_Segments/
│   │   │   ├── [HIGH]_07_Flu_Shot_Misinformation.mp4
│   │   │   └── ...
│   │   ├── clip_metadata.json
│   │   └── segment_analysis_summary.txt
```

**Metadata Files**:
1. `clip_metadata.json` - Technical details for each clip
2. `segment_analysis_summary.txt` - Research context for each segment
3. Individual `.txt` files with full context for each clip

### Phase 4: Quality Control & Validation
**Goal**: Ensure clips accurately represent the analysis

**Validation Steps**:
1. **Timestamp Accuracy**
   - Verify clips start/end at correct times
   - Check audio sync
   - Validate duration matches analysis data

2. **Content Verification**
   - Sample clips to ensure they contain the problematic content
   - Check that quotes from analysis appear in clips
   - Verify speaker identification accuracy

3. **File Organization**
   - Confirm proper categorization by severity
   - Check filename conventions
   - Validate metadata completeness

## Technical Considerations

### Timestamp Format Challenges
- Analysis contains mixed formats: `45.17`, `1.04.19`, `2.40.0`
- Need robust parser for `HH.MM.SS` and `MM.SS` formats
- Handle edge cases like `1.0.8` (1 minute 8 seconds?)

### FFmpeg Command Structure
```bash
ffmpeg -i "source_video.mp4" -ss START_TIME -t DURATION -c copy "output_clip.mp4"
```

### Buffer Time Strategy
- Add 5-10 seconds before segment start for context
- Add 3-5 seconds after segment end to avoid abrupt cuts
- Configurable buffer times per clip based on content sensitivity

### File Size Management
- Some segments are quite long (226+ seconds)
- Consider compression settings for academic use
- Balance quality vs. file size for distribution

## Risk Mitigation

### Content Sensitivity
- All clips are for academic research/media criticism
- Include disclaimers in metadata about research purpose
- Clear labeling of problematic content nature

### Technical Risks
- Video file corruption during processing
- Timestamp misalignment
- Audio/video sync issues
- Large file sizes

### Process Validation
- Manual spot-checking of first few clips
- Automated validation of timestamp accuracy
- Backup original analysis data

## Success Criteria

1. **Accuracy**: 95%+ of clips accurately represent the timestamp ranges from analysis
2. **Completeness**: All 10+ segments from analysis successfully converted to clips
3. **Organization**: Clear, logical file structure with proper metadata
4. **Quality**: Clips maintain source video quality with proper audio sync
5. **Documentation**: Complete metadata and context information for each clip

## Next Steps

1. **Create Enhanced Parser Script**
   - Parse the analysis file JSON
   - Handle timestamp format conversion
   - Generate clip specifications

2. **Modify Video Extractor**
   - Add analysis file input support
   - Implement multi-range segment handling
   - Enhance filename generation

3. **Build Processing Pipeline**
   - Automated clip generation from analysis
   - Quality validation checks
   - Organized output structure

4. **Test & Validate**
   - Process sample segments first
   - Verify accuracy and quality
   - Refine based on results

## Estimated Timeline
- **Phase 1 (Parser)**: 2-3 hours
- **Phase 2 (Video Processing)**: 3-4 hours  
- **Phase 3 (Organization)**: 1-2 hours
- **Phase 4 (Validation)**: 1-2 hours
- **Total Estimated Time**: 7-11 hours

## Tools Required
- Python 3.x
- FFmpeg
- JSON parsing libraries
- File system utilities
- Video validation tools (optional)
