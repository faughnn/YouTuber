# Automated Video Editor Planning Document

## Overview
Build an automated system that combines narrator audio clips with video clips based on structured script data to create final video content. The system should be general-purpose, working with any video source and script structure, not just Joe Rogan content.

## Current Script Structure Analysis

Based on `test_podcast_script.json`, our scripts contain:

### Key Data Elements:
1. **Video Clip References**: Each clip has `start_time`, `end_time`, and `clip_id`
2. **Script Structure**: Contains `CLIP_MARKER` tags like `[CLIP_MARKER: 0:57:17-0:57:53, "Claim of 470,000 Vaccine Deaths in US"]`
3. **Narrative Sections**: 
   - INTRO
   - PRE-CLIP SETUP (narrator commentary)
   - CLIP insertion point
   - POST-CLIP ANALYSIS (narrator commentary)
   - CONCLUSION

### Timeline Flow:
```
[Narrator: INTRO] → [Narrator: PRE-CLIP SETUP] → [Video: CLIP 1] → [Narrator: POST-CLIP ANALYSIS] → 
[Narrator: PRE-CLIP SETUP] → [Video: CLIP 2] → [Narrator: POST-CLIP ANALYSIS] → ... → [Narrator: CONCLUSION]
```

## System Architecture

### 1. Core Components

#### A. Script Parser (`script_parser.py`)
**Purpose**: Parse structured script data and extract timeline information
**Input**: JSON script file
**Output**: Timeline data structure

```python
class ScriptParser:
    def parse_script(self, script_path):
        # Parse JSON script
        # Extract CLIP_MARKER references
        # Build timeline with narrator segments and video clip insertion points
        # Return structured timeline data
```

**Key Functions**:
- Extract video clip metadata (start_time, end_time, clip_id)
- Parse narrator text segments
- Identify CLIP_MARKER insertion points
- Build sequential timeline structure

#### B. Audio Manager (`audio_manager.py`)
**Purpose**: Handle narrator audio files and synchronization
**Input**: Narrator audio files, timeline data
**Output**: Sequenced audio timeline

```python
class AudioManager:
    def __init__(self, audio_directory):
        # Directory containing narrator audio clips
        
    def match_audio_to_script(self, timeline_data):
        # Match audio files to script segments
        # Handle missing audio files
        # Calculate timing and transitions
```

**Key Functions**:
- Audio file discovery and matching
- Duration calculation
- Audio quality normalization
- Transition handling (fade in/out, silence padding)

#### C. Video Clipper (`video_clipper.py`)
**Purpose**: Extract video segments based on timestamps
**Input**: Source video file, clip metadata
**Output**: Individual video clips

```python
class VideoClipper:
    def extract_clips(self, source_video, clip_data):
        # Extract video segments based on timestamps
        # Handle format conversions
        # Apply any necessary processing
```

**Key Functions**:
- Precise timestamp extraction
- Format standardization
- Quality preservation
- Clip validation

#### D. Timeline Builder (`timeline_builder.py`)
**Purpose**: Combine audio and video into final timeline
**Input**: Audio timeline, video clips, timeline data
**Output**: Final video project file

```python
class TimelineBuilder:
    def build_timeline(self, audio_timeline, video_clips, timeline_data):
        # Create video editing project
        # Sequence audio and video segments
        # Handle transitions and effects
        # Export final video
```

### 2. File Structure & Organization

```
Code/
└── Video_Editor/
    ├── __init__.py
    ├── script_parser.py
    ├── audio_manager.py
    ├── video_clipper.py
    ├── timeline_builder.py
    ├── video_editor_main.py
    └── config/
        ├── editor_config.yaml
        └── templates/
            ├── transition_templates.json
            └── effect_presets.json

Content/
├── Audio/
│   └── Narrator/
│       ├── intro_001.wav
│       ├── pre_clip_setup_001.wav
│       ├── post_clip_analysis_001.wav
│       └── conclusion_001.wav
├── Video/
│   ├── Source/
│   │   └── joe_rogan_2325_full.mp4
│   └── Clips/
│       └── extracted/
│           ├── claim_470k_vaccine_deaths.mp4
│           └── covid_vaccine_side_effects.mp4
└── Output/
    └── final_videos/
        └── bullseye_episode_001.mp4
```

## 3. Detailed Workflow

### Phase 1: Script Analysis & Preparation
1. **Parse Script File**
   - Load JSON script data
   - Extract video clip references and timestamps
   - Identify narrator segments between clips
   - Build preliminary timeline structure

2. **Audio File Discovery**
   - Scan narrator audio directory
   - Match audio files to script segments using naming conventions
   - Validate audio file quality and format
   - Calculate total narrator audio duration

3. **Video Clip Validation**
   - Verify source video file exists
   - Validate timestamp ranges don't exceed video duration
   - Check for overlapping clips
   - Estimate total video clip duration

### Phase 2: Content Extraction
1. **Extract Video Clips**
   - Use FFmpeg to extract precise video segments
   - Apply consistent encoding settings
   - Generate thumbnails for verification
   - Store clips with standardized naming

2. **Process Narrator Audio**
   - Normalize audio levels across all clips
   - Add fade-in/fade-out transitions
   - Insert silence padding where needed
   - Export as consistent format (WAV/MP3)

### Phase 3: Timeline Assembly
1. **Create Base Timeline**
   - Start with narrator intro audio
   - Calculate insertion points for video clips
   - Add narrator commentary between clips
   - End with narrator conclusion

2. **Video Integration**
   - Insert video clips at precise timeline positions
   - Maintain audio sync
   - Add transition effects between segments
   - Handle audio ducking during video clips

3. **Final Assembly**
   - Render complete timeline
   - Apply final audio mastering
   - Export in multiple resolutions/formats
   - Generate preview clips for review

## 4. Configuration System

### Script Format Specifications
```yaml
# editor_config.yaml
script_formats:
  json:
    clip_marker_pattern: "\\[CLIP_MARKER: (.+?)\\]"
    timestamp_format: "H:MM:SS"
    required_fields: ["selected_clips", "clip_order", "full_script"]
  
audio_settings:
  format: "wav"
  sample_rate: 48000
  bit_depth: 24
  normalization_target: -23  # LUFS
  
video_settings:
  output_resolution: "1920x1080"
  frame_rate: 30
  codec: "h264"
  bitrate: "5M"

timeline_settings:
  fade_duration: 0.5  # seconds
  silence_padding: 0.2  # seconds
  transition_type: "cross_fade"
```

### Naming Conventions
```yaml
naming_conventions:
  narrator_audio:
    intro: "intro_{episode_number}.wav"
    pre_clip: "pre_clip_{clip_number}_{episode_number}.wav"
    post_clip: "post_clip_{clip_number}_{episode_number}.wav"
    conclusion: "conclusion_{episode_number}.wav"
  
  video_clips:
    extracted: "{clip_id}_{start_time}_{end_time}.mp4"
    
  output:
    final_video: "{show_name}_episode_{episode_number}.mp4"
    preview: "{show_name}_episode_{episode_number}_preview.mp4"
```

## 5. Advanced Features

### A. Intelligent Audio Matching
```python
class AudioMatcher:
    def match_by_content(self, text_segment, audio_files):
        # Use speech-to-text to verify audio matches script text
        # Handle variations in speech patterns
        # Suggest best matches for manual review
```

### B. Dynamic Timeline Adjustment
```python
class TimelineOptimizer:
    def optimize_pacing(self, timeline):
        # Analyze audio/video duration ratios
        # Suggest optimal timing adjustments
        # Handle cases where audio is longer/shorter than expected
```

### C. Quality Control System
```python
class QualityController:
    def validate_output(self, video_file):
        # Check audio levels and sync
        # Verify video quality and compression
        # Generate quality report
        # Flag potential issues
```

## 6. Error Handling & Resilience

### Common Failure Scenarios:
1. **Missing Audio Files**
   - Graceful degradation with text-to-speech backup
   - Clear error reporting with specific missing files
   - Ability to continue with available content

2. **Invalid Timestamps**
   - Timestamp validation against source video duration
   - Automatic adjustment for minor discrepancies
   - Warning system for potential issues

3. **Format Incompatibilities**
   - Automatic format conversion
   - Fallback encoding options
   - Comprehensive format support

4. **Memory/Performance Issues**
   - Chunked processing for large files
   - Progress tracking and resumable operations
   - Resource usage monitoring

## 7. Integration Points

### A. Master Processor Integration
```python
# Extend master_processor.py
class VideoEditingStep(ProcessingStep):
    def execute(self, context):
        # Called after script generation
        # Uses generated script as input
        # Produces final video as output
```

### B. Web Interface (Future)
```python
# Timeline preview and editing interface
class VideoEditorUI:
    def preview_timeline(self):
        # Show timeline with audio waveforms
        # Allow manual adjustments
        # Real-time preview capabilities
```

## 8. Testing Strategy

### Unit Tests
- Script parsing accuracy
- Audio file matching
- Video extraction precision
- Timeline calculation correctness

### Integration Tests
- End-to-end workflow with sample data
- Error handling scenarios
- Performance with large files
- Output quality validation

### Manual Testing
- Audio-video synchronization
- Transition smoothness
- Final output quality review
- Cross-platform compatibility

## 9. Implementation Phases & Current Status

### Phase 1: Core Engine ✅ COMPLETED
- ✅ Script parser (`script_parser.py`) - Full JSON parsing, episode info extraction, timeline building
- ✅ TTS Audio Generator (`tts_audio_generator.py`) - Integration with existing Gemini TTS system
- ✅ File structure and naming conventions established
- ✅ Test data and validation scripts created
- 🔄 Basic timeline assembly - IN PROGRESS

### Phase 2: Video Integration (CURRENT FOCUS)
- 🎯 **NEXT**: Create Video Timeline Builder using FFmpeg
- 🎯 **NEXT**: Implement audio-video synchronization
- 🎯 **NEXT**: Add basic transitions and effects
- 🎯 **NEXT**: End-to-end workflow testing

### Phase 3: Quality & Polish (PLANNED)
- Advanced error handling
- Quality control systems
- Configuration management
- Documentation

### Phase 4: Advanced Features (FUTURE)
- Intelligent matching algorithms
- Web interface
- Batch processing capabilities
- Advanced effects and transitions

## 10. Current Implementation Status (June 2025)

### ✅ COMPLETED COMPONENTS

#### A. Script Parser (`Code/Video_Editor/script_parser.py`)
- **Status**: Fully implemented and tested
- **Features**:
  - Parses JSON script files with embedded script content
  - Extracts episode information from titles (e.g., "Joe Rogan Experience 2325 - Aaron Rodgers" → "JRE2325-AR")
  - Builds complete timeline data structures
  - Generates standardized audio filenames based on episode info
  - Handles both simple test scripts and complex real podcast scripts
- **Key Methods**:
  - `parse_script_file()` - Main parsing function
  - `extract_episode_info()` - Episode metadata extraction
  - `generate_audio_filenames()` - Consistent naming conventions
  - `build_timeline()` - Sequential timeline construction

#### B. TTS Audio Generator (`Code/Video_Editor/tts_audio_generator.py`)
- **Status**: Implemented and integrated with existing TTS system
- **Features**:
  - Integrates with existing `SimpleTTSGenerator` from Content_Analysis directory
  - Generates narrator audio files for all script segments (intro, pre-clip setups, post-clip analyses, conclusion)
  - Implements intelligent text cleaning for TTS (removes markdown, stage directions)
  - Provides audio duration calculation and file existence checking
  - Uses standardized naming conventions matching script parser output
- **Integration**: Successfully imports and uses existing Gemini TTS infrastructure

#### C. File Structure & Organization
- **Status**: Established and organized
- **Structure**:
  ```
  Code/Video_Editor/
  ├── __init__.py ✅
  ├── script_parser.py ✅
  ├── tts_audio_generator.py ✅
  ├── test_simple_script.json ✅
  └── [timeline_builder.py] 🎯 NEXT
  
  Content/Audio/Generated/Narrator/ ✅
  Content/Scripts/Joe_Rogan_Experience/ ✅
  ```

#### D. Naming Conventions & Standards
- **Audio Files**: `intro_001_JRE2325-AR.wav`, `pre_clip_001_001_CLIP_NAME_JRE2325-AR.wav`
- **Episode Codes**: Extracted from titles (e.g., "JRE2325-AR" from "Joe Rogan Experience 2325 - Aaron Rodgers")
- **Consistent formatting** across all components

### 🎯 IMMEDIATE NEXT STEPS

#### 1. Video Timeline Builder (Priority 1)
- **File**: `Code/Video_Editor/timeline_builder.py`
- **Purpose**: FFmpeg-based module to combine audio and video clips
- **Key Features Needed**:
  - Load timeline data from script parser
  - Use generated narrator audio files from TTS generator
  - Extract video clips based on timestamps from source video
  - Stitch together: Narrator Audio → Video Clip → Narrator Audio → Video Clip → etc.
  - Export final video with proper synchronization

#### 2. End-to-End Testing (Priority 2)
- **Goal**: Test complete pipeline from script JSON to final video
- **Test Data**: Use existing `test_simple_script.json` and real podcast script
- **Validation**: Audio-video sync, proper sequencing, output quality

#### 3. Static Image Support (Priority 3)
- **Feature**: Display narrator image/avatar during audio-only segments
- **Implementation**: Overlay static image during narrator audio portions
- **Enhancement**: Makes video more engaging during non-clip segments

### 🔄 WORKFLOW IMPLEMENTATION STATUS

#### Current Workflow (Implemented):
1. ✅ **Extract Clips** - Parse script to identify video timestamps
2. ✅ **Create Script Timeline** - Build sequential structure with audio/video segments
3. ✅ **Generate Audio Files** - Create TTS narrator audio for all segments
4. 🎯 **Stitch Timeline** - Combine audio and video into final video (NEXT)

#### Planned Integration Points:
- **Master Processor**: Add video editing as final step in content pipeline
- **Existing TTS System**: Already integrated successfully
- **Video Clipper**: Will integrate with existing `Video_Clipper` directory modules

### 📋 TECHNICAL SPECIFICATIONS

#### Audio Requirements:
- **Format**: WAV, 48kHz, 24-bit (matching existing TTS output)
- **Naming**: Standardized based on episode info and segment type
- **Quality**: Normalized levels, fade transitions

#### Video Requirements:
- **Input**: Source video files (MP4, various resolutions)
- **Output**: 1920x1080, 30fps, H.264 encoding
- **Clips**: Precise timestamp extraction using FFmpeg
- **Sync**: Audio-video synchronization within ±50ms tolerance

#### Timeline Structure:
```
[Narrator: Intro Audio] → 
[Narrator: Pre-Clip Setup] → [Video: Clip 1] → [Narrator: Post-Clip Analysis] → 
[Narrator: Pre-Clip Setup] → [Video: Clip 2] → [Narrator: Post-Clip Analysis] → 
... → 
[Narrator: Conclusion Audio]
```

## 11. Success Metrics & Testing Status

### Technical Metrics:
- ✅ Script parsing accuracy: 100% for JSON format
- ✅ Audio file generation: Successfully integrated with existing TTS system
- ✅ Naming convention consistency: Implemented across all components
- 🎯 Audio-video sync accuracy: Target ±50ms (to be tested)
- 🎯 Processing time per minute of content: To be measured
- 🎯 Output quality scores: To be evaluated

### Content Metrics:
- 🎯 Manual editing time reduction: To be measured after implementation
- ✅ Consistency across episodes: Ensured through standardized naming and structure
- 🎯 Viewer engagement with generated content: Future evaluation
- 🎯 Production workflow efficiency: To be measured

### Current Test Results:
- ✅ **Script Parser**: Successfully parses both simple and complex podcast scripts
- ✅ **Episode Info Extraction**: Correctly extracts "JRE2325-AR" from "Joe Rogan Experience 2325 - Aaron Rodgers"
- ✅ **TTS Integration**: Successfully imports and uses existing Gemini TTS system
- ✅ **File Organization**: Proper directory structure and file naming implemented
- 🎯 **End-to-End Pipeline**: Awaiting timeline builder completion

## 12. Future Enhancements & Roadmap

### Immediate Priorities (Next 2 weeks):
1. **Complete Timeline Builder**: FFmpeg-based video assembly
2. **End-to-End Testing**: Full workflow validation
3. **Static Image Support**: Narrator avatars during audio segments
4. **Master Processor Integration**: Add to existing content pipeline

### Short-term Goals (Next month):
1. **Advanced Transitions**: Smooth fade effects, cross-dissolves
2. **Quality Control**: Automated sync checking, output validation
3. **Error Handling**: Robust failure recovery, detailed logging
4. **Performance Optimization**: Efficient processing for long videos

### Long-term Vision (3-6 months):
1. **Batch Processing**: Handle multiple episodes simultaneously
2. **Web Interface**: Visual timeline editor with preview
3. **AI-Powered Features**: Automatic clip selection, dynamic pacing
4. **Multi-format Support**: Different video sources, aspect ratios

## 13. Integration Strategy

### Current Integration Points:
- ✅ **Existing TTS System**: Successfully integrated with `Content_Analysis/simple_tts_generator.py`
- ✅ **File Organization**: Uses established `Content/` directory structure
- ✅ **Configuration**: Leverages existing `Config/default_config.yaml` for API keys

### Planned Integration Points:
- 🎯 **Master Processor**: Add video editing as final processing step
- 🎯 **Video Clipper**: Use existing video extraction modules
- 🎯 **Content Analysis**: Leverage existing analysis results for clip selection
- 🎯 **Web Interface**: Future dashboard for content management

### Integration Workflow:
```
Content Analysis → Script Generation → Audio Generation → Video Assembly → Final Output
     ✅               ✅                  ✅              🎯 NEXT         🎯 NEXT
```

### AI-Powered Features:
- Automatic clip selection based on engagement patterns
- Dynamic pacing optimization
- Intelligent thumbnail generation
- Automated subtitles and captions

### Advanced Editing:
- Multi-camera support
- Dynamic graphics and overlays
- Advanced color grading
- Interactive content elements

### Workflow Integration:
- Cloud processing capabilities
- Collaborative editing features
- Version control for projects
- Automated publishing workflows

---

## 14. Next Steps for Implementation

### Immediate Actions (This Week):
1. **Create Timeline Builder Module** (`Code/Video_Editor/timeline_builder.py`)
   - FFmpeg integration for video processing
   - Audio-video synchronization logic
   - Timeline assembly and export functionality

2. **Test End-to-End Workflow**
   - Use existing test script (`test_simple_script.json`)
   - Generate narrator audio files
   - Extract video clips from source
   - Assemble final video output

3. **Validate Integration**
   - Confirm TTS audio generation works correctly
   - Test video clip extraction accuracy
   - Verify final output quality and sync

### Medium-term Goals (Next 2 Weeks):
1. **Add Static Image Support**
   - Narrator avatar/image overlay during audio segments
   - Professional visual presentation

2. **Integrate with Master Processor**
   - Add video editing step to existing content pipeline
   - Automated workflow from analysis to final video

3. **Quality Assurance**
   - Comprehensive error handling
   - Output validation and quality checks
   - Performance optimization

### Project Status Summary:
- **Foundation**: ✅ Complete (Script parsing, TTS integration, file organization)
- **Core Functionality**: 🎯 50% Complete (Audio generation done, video assembly needed)
- **Integration**: 🎯 Next phase (Timeline builder, master processor integration)
- **Polish & Features**: 🔄 Future phases (UI, advanced features, optimization)

The automated video editing system is well-structured and ready for the final implementation phase. The core infrastructure is solid with successful script parsing and TTS integration. The main remaining task is creating the timeline builder to combine all components into final video output.
