# Segment Review Tool - Development Plan

## Overview
A command line tool for reviewing and filtering segments from `original_audio_analysis_results.json` before regenerating the final video. This solves the current manual refinement process that requires:
1. Watching generated video to identify unwanted segments
2. Manually editing JSON files with segment ID matching between different files
3. Re-running pipeline from narrative generation stage

## Problem Context
Currently, segment refinement is time-consuming and error-prone because:
- Manual JSON editing is tedious and risky
- `segment_id` mapping between `original_audio_analysis_results.json` and `unified_podcast_script.json` (different order)
- No visual/audio context during JSON editing
- Risk of corrupting JSON structure
- Need to re-run entire pipeline after changes

## Core Requirements

### 1. Video-First Review Workflow
- Load `unified_podcast_script.json` to get video sequence order
- For each video_clip section, play the 3-part sequence: pre_clip → video_clip → post_clip
- Present segment context from analysis results during/after playback
- Keyboard-driven interface for keep/remove decisions after watching
- Remove corresponding segment from `original_audio_analysis_results.json` when rejected
- Keep unified script intact (it will be regenerated in pipeline restart)

### 2. Safety and Data Integrity
- Create timestamped backups of both JSON files before modifications
- Validate JSON structure after modifications
- Preserve original data integrity
- Enable rollback to previous versions
- Handle file corruption gracefully

### 3. Intelligent Pipeline Integration
- Auto-detect and map segment IDs between analysis results and unified script
- Output filtered results maintaining proper relationships
- Enable seamless continuation from narrative generation stage
- Provide detailed summary of changes made
- Validate segment consistency across files

## Technical Design

### File Structure
```
Code/
├── segment_reviewer.py          # Main CLI tool
├── Utils/
│   ├── segment_review_utils.py  # Review logic utilities
│   ├── segment_id_mapper.py     # Handle ID mapping between JSON files
│   ├── backup_manager.py        # Backup/restore functionality
│   └── json_validator.py        # JSON structure validation
```

### Data Flow - Video-First Review Process
```
Input Files:
├── unified_podcast_script.json              (defines video sequence)
└── original_audio_analysis_results.json     (harmful segments metadata)

Video Files:
└── Output/Video/temp/                        (pre/video/post clip files)

Process:
    ↓ (1. Create backup of analysis results)
original_audio_analysis_results_backup_YYYY-MM-DD_HH-MM-SS.json
    ↓ (2. Load unified script to get video sequence)
video_clip_001 → video_clip_002 → video_clip_003...
    ↓ (3. For each video sequence, play clips and review)
Play: pre_clip_001.mp4 → video_clip_001.mp4 → post_clip_001.mp4
Show: Analysis metadata for Harmful_Segment_02
Decide: Keep or Remove from analysis results
    ↓ (4. Generate filtered analysis results)
original_audio_analysis_results_filtered.json
    ↓ (5. Restart pipeline from Stage 4)
Narrative Generation → New unified script → Continue to Stage 5-7
```

## Feature Specifications

### Core Features

#### 1. Video Sequence Player & Review Interface
- **Video Playback Workflow**: 
  - Load unified script to determine clip sequence
  - For each video_clip section, auto-play 3-clip sequence: `pre_clip_XXX.mp4` → `video_clip_XXX.mp4` → `post_clip_XXX.mp4`
  - Show analysis context during/after playback
  - **Clip Context Display**: Segment ID, title, severity rating, harm category, reasoning
  - **Visual Progress**: Show current position in sequence (e.g., "Reviewing clip sequence 3 of 12")

- **Review Actions** (After Watching Sequence):
  - `k` - Keep segment (preserve in analysis results, continue to next sequence)
  - `r` - Remove segment (remove from analysis results, continue to next sequence)
  - `p` - Replay current 3-clip sequence
  - `v` - View full analysis details for current segment
  - `n` - Next clip sequence (skip review decision)
  - `b` - Previous clip sequence
  - `s` - Show overall progress and statistics
  - `q` - Quit and auto-restart pipeline from narrative generation
  - `x` - Quit without saving or restarting pipeline

#### 2. Video-to-Analysis Mapping System
- **Script-First Loading**: Parse unified script to get clip sequence order
- **Clip-to-Segment Mapping**: Map video_clip sections to analysis results via `clip_id`
- **Sequence Validation**: Verify all 3 video files exist for each sequence (pre/video/post)
- **Analysis Context**: Load corresponding analysis metadata for each video sequence
- **Missing File Handling**: Skip sequences where video files are missing, report at end

#### 3. Video Sequence Navigation
- **Sequential Video Review**: Present video clips in unified script order (as they appear in final video)
- **Auto-play 3-clip sequences**: Automatic progression through pre → video → post clips
- **Manual replay controls**: Replay current sequence, jump to next/previous
- **Progress tracking**: Show current sequence position and review completion status
- **Sequence-based filtering**: Option to filter by severity while maintaining video sequence order

#### 4. Video Playback Integration
- **3-Clip Sequence Playback**:
  - Auto-play sequence: `seg_XXX_pre_clip_XXX.mp4` → `seg_XXX_video_clip_XXX.mp4` → `seg_XXX_post_clip_XXX.mp4`
  - Seamless transitions between clips in sequence
  - Display current clip type during playback (Pre-Context / Main Content / Post-Analysis)
  - Option to pause between clips for analysis
  - Simple playback controls (play/pause/stop/replay sequence)

### Workflow Design Decisions - REVISED

#### Review Mode: Video-First Sequential Review
- **Decision**: Watch video sequences first, then decide based on visual content
- **Rationale**: Matches natural review process - see it, then judge it
- **Benefits**: Context-aware decisions, no guessing from text descriptions
- **Implementation**: Load unified script first, play video sequences, modify analysis results

#### Segment Order: Video Sequence Order (Unified Script)
- **Decision**: Review in video playback order (unified script sequence)
- **Rationale**: Natural viewing experience, see content as audience will see it
- **Benefits**: Better context understanding, logical flow assessment
- **Implementation**: Parse unified script video_clip sections, play corresponding file sequences

#### File Modification: Analysis Results Only
- **Decision**: Only modify `original_audio_analysis_results.json`, leave unified script unchanged
- **Rationale**: Unified script will be regenerated in pipeline restart anyway
- **Benefits**: Simpler logic, no complex cross-file synchronization needed
- **Implementation**: Remove segments from analysis results, pipeline regenerates everything else

### Critical Features for Video-First Review

#### 1. Video Sequence Mapping
```python
# Example mapping from unified script to video files and analysis data
video_sequence = {
    "video_clip_001": {
        "clip_id": "Harmful_Segment_02",
        "files": {
            "pre": "seg_002_pre_clip_001.mp4",
            "video": "seg_003_video_clip_001.mp4", 
            "post": "seg_004_post_clip_001.mp4"
        },
        "analysis_data": {
            "title": "Dismissal of Mainstream Economics",
            "severity": "MEDIUM",
            "reasoning": "Claims economists are incompetent..."
        }
    }
}
```

#### 2. Analysis Results Modification Only
- When user chooses "Remove" after watching sequence → Remove segment from analysis results
- Keep unified script unchanged (will be regenerated when pipeline restarts)  
- No complex cross-file synchronization needed
- Simpler error handling and validation

#### 3. Video Sequence Validation
- **Pre-Review Check**: Verify all video files exist for each sequence
- **Missing File Handling**: Skip sequences with missing files, report at end
- **File Path Resolution**: Handle absolute paths to temp folder
- **Playback Error Recovery**: Continue to next sequence if playback fails

### Advanced Features (Future Enhancements)

#### 1. Batch Operations
- Mark multiple segments for removal
- Undo last action
- Preview final count before saving

#### 2. Quality Metrics
- Track removal statistics by harm category
- Show segment duration impact
- Export review summary report

#### 3. Review Notes
- Add comments to kept segments
- Flag segments for manual editing
- Export review decisions log

## Implementation Plan

### Phase 1: Core Video Review Functionality (Days 1-3)
- [ ] **Unified Script Parser**: Load and parse video_clip sequences from unified script
- [ ] **Video File Detection**: Map script sequences to actual video files in temp folder
- [ ] **3-Clip Sequence Player**: Auto-play pre → video → post clip sequences
- [ ] **Basic Review Interface**: Display analysis context during/after video playback
- [ ] **Analysis Results Modification**: Remove segments from analysis results based on decisions

### Phase 2: Enhanced Playback & Navigation (Days 4-5)
- [ ] **Seamless Video Transitions**: Smooth playback between 3-clip sequences
- [ ] **Playback Controls**: Pause, replay sequence, manual navigation
- [ ] **Progress Tracking**: Show current sequence position and completion status
- [ ] **Missing File Handling**: Skip sequences with missing files gracefully

### Phase 3: Pipeline Integration (Days 6-7)
- [ ] **Auto-restart Functionality**: Trigger narrative generation after review
- [ ] **Backup System**: Create timestamped backup of analysis results
- [ ] **Pipeline Command Integration**: Execute master_processor_v2.py with parameters
- [ ] **Progress Validation**: Ensure filtered analysis results ready for pipeline

### Phase 4: Polish & Testing (Days 8-10)
- [ ] **Error Recovery**: Handle video playback failures, file corruption
- [ ] **Comprehensive Testing**: Test with real Gary Stevenson video sequences
- [ ] **Performance Optimization**: Efficient video loading and playback
- [ ] **Documentation**: Usage guide and troubleshooting

## Technical Considerations

### Dependencies
- `json` - File parsing for unified script and analysis results
- `subprocess` - Video playback using system video player
- `pathlib` - File path handling for video files
- `datetime` - Timestamp generation for backups
- `argparse` - CLI argument handling
- `colorama` - Terminal colors for better UX
- **Video Playback**: `os.startfile()` (Windows) or `subprocess` with system video player

### Critical Error Handling
- **Video File Validation**: Check that all 3 video files exist before starting sequence
- **Playback Error Recovery**: Continue to next sequence if video player fails
- **Analysis Results Integrity**: Validate JSON structure after modifications
- **Missing File Reporting**: Summary of sequences that couldn't be reviewed due to missing files
- **Keyboard Interrupt**: Graceful exit with option to save partial progress
- **File Lock Detection**: Handle cases where analysis results file is open elsewhere

### Performance Optimizations
- **Lazy Loading**: Load segments on-demand for large datasets
- **Efficient JSON Operations**: Minimize file I/O with batch updates
- **Audio Caching**: Pre-extract commonly reviewed segments
- **Memory Management**: Handle large audio files without memory issues
- **Index Building**: Create search indexes for fast segment lookup

## Usage Examples

### Basic Video Review Session
```bash
python segment_reviewer.py --script "unified_podcast_script.json" --analysis "original_audio_analysis_results.json" --clips-folder "Output/Video/temp"
```

### Auto-restart Pipeline After Review
```bash
python segment_reviewer.py --script "script.json" --analysis "results.json" --clips-folder "temp" --auto-restart
```

### Validation Mode (Check Video Files Without Review)
```bash
python segment_reviewer.py --script "script.json" --clips-folder "temp" --validate-only
```

## Output Format

### Filtered Results File
- Only `original_audio_analysis_results.json` is modified
- Same JSON structure as original, with removed segments excluded
- Preserves all original metadata for kept segments
- Unified script remains unchanged (will be regenerated by pipeline)

### Video Review Session Report
```
Video Sequence Review Session Complete
=====================================
Video Sequences Reviewed: 10 of 12 available
- Successfully reviewed: 10 sequences
- Skipped (missing files): 2 sequences

Review Results:
Original analysis segments: 12
Kept segments: 7
Removed segments: 5

Removed by Category:
- HIGH severity: 3 segments (Harmful_Segment_05, Harmful_Segment_10, Harmful_Segment_14)
- MEDIUM severity: 2 segments (Harmful_Segment_02, Harmful_Segment_11)

Video Files Impact:
- Video sequences removed: 5 (corresponding pre/video/post clips will be excluded from regeneration)
- Estimated duration removed: 4m 12s
- Remaining estimated duration: 7m 45s

Files Modified:
- original_audio_analysis_results.json → original_audio_analysis_results_filtered.json

Backup Created:
- original_audio_analysis_results_backup_2025-07-28_14-30-15.json

Next Steps:
✓ Filtered analysis results ready for pipeline restart
✓ Auto-restarting pipeline: python master_processor_v2.py --start-from narrative_generation
✓ Pipeline restart initiated successfully
✓ New unified script and video compilation will exclude removed segments
```

## Key Questions for Implementation - ANSWERED

1. **Unified Script Structure**: ✅ **RESOLVED** 
   - Structure: `podcast_sections` array with `section_type`, `section_id`, `clip_reference`/`clip_id`
   - Video clips have `clip_id` that matches `segment_id` from analysis results
   - Sections ordered sequentially (intro → pre_clip → video_clip → post_clip → repeat → outro)

2. **Segment Dependencies**: ✅ **RESOLVED**
   - Each video_clip section has corresponding pre_clip and post_clip sections
   - When removing a segment, must remove: video_clip + pre_clip + post_clip (3 sections total)
   - Sequence integrity must be maintained

3. **Pipeline Integration**: ⚠️ **NEEDS IMPLEMENTATION**
   - Current `master_processor_v2.py` doesn't have `--start-from` parameter
   - Need to add resume capability for narrative generation stage (Stage 4)
   - Pipeline stages: 1. Download → 2. Transcription → 3. Analysis → **4. Narrative Generation** ← START HERE

4. **Audio File Location**: ✅ **RESOLVED**
   - Generated clips in: `Output/Video/temp/` folder
   - Format: `seg_XXX_section_type_XXX.mp4` (e.g., `seg_002_pre_clip_001.mp4`)
   - Can play sequential pre_clip → video_clip (actual harmful content) → post_clip

5. **Review Priorities**: ✅ **RESOLVED**
   - Review in unified script order (chronological sequence as viewer sees them)
   - Load unified script, iterate through video_clip sections in order

6. **Orphaned Entries**: ✅ **RESOLVED**
   - Orphaned sections are intro/outro/pre_clip/post_clip without corresponding analysis segments
   - Keep these sections (they're generated content, not harmful content identification)

## Critical Implementation Details

### Unified Script Mapping Structure
```python
# Example of how sections map to analysis results
{
  "section_type": "video_clip",
  "section_id": "video_clip_001", 
  "clip_id": "Harmful_Segment_02",    # ← MAPS TO analysis results segment_id
  "start_time": "464.178",
  "end_time": "513.012"
}
```

### Removal Logic (When segment is removed)
```python
# For each harmful segment removal, remove 3 unified script sections:
sections_to_remove = [
    f"pre_clip_{clip_number}",      # e.g., "pre_clip_001"
    f"video_clip_{clip_number}",    # e.g., "video_clip_001" 
    f"post_clip_{clip_number}"      # e.g., "post_clip_001"
]
```

### Pipeline Resume Implementation Required
- **Current**: No resume capability in `master_processor_v2.py`
- **Needed**: Add `--resume-from narrative_generation` parameter 
- **Implementation**: Modify `create_argument_parser()` and add resume logic
- **Alternative**: Create separate script that calls `_stage_4_narrative_generation()` directly

## Immediate Next Steps - REVISED

1. **✅ File Structure Analysis**: Complete - Unified script structure mapped and understood
2. **⚠️ Pipeline Resume Capability**: Add `--resume-from` parameter to master_processor_v2.py OR create dedicated resume script
3. **🚀 Ready to Start**: Begin development of segment reviewer with these specifications:

### Confirmed Technical Specifications

**Input Files:**
- `original_audio_analysis_results.json` (12 harmful segments)
- `unified_podcast_script.json` (35+ sections including pre/post clips)

**Clip Files:**
- Location: `Output/Video/temp/seg_XXX_section_type_XXX.mp4`
- Play sequence: `pre_clip_001.mp4` → `video_clip_001.mp4` → `post_clip_001.mp4`

**Removal Impact:**
- Remove 1 analysis segment → Remove 3 unified script sections → Remove 3 video files

**Pipeline Restart:**
- Target: Stage 4 (Narrative Generation) 
- Input: Filtered `original_audio_analysis_results.json`
- Output: New `unified_podcast_script.json` → Continue to Stage 5-7

---

**Ready to proceed with development? The plan is now fully specified with real file structures and confirmed requirements.**
