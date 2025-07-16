# YouTube Pipeline UI - Final Implementation Plan

**Date Created:** June 19, 2025  
**Status:** Ready for Implementation  
**Technology Stack:** Flask + Tailwind CSS

## Project Overview

Create a web-based UI for the 7-stage YouTube video processing pipeline that provides:
- **Flexible Pipeline Control**: Run any combination of stages
- **Manual Segment Selection**: Choose specific content analysis segments for script generation
- **Multiple Creative Workflows**: Automated, semi-manual, and fully manual approaches

## Core Requirements Summary

### 1. Pipeline Status & Control
- **Visual Stage Indicators**: Show completion status for all 7 stages
- **Flexible Execution**: Select which stages to run (1-7 in any combination)
- **Automatic Sequential Execution**: Run selected stages automatically in sequence
- **Error Handling**: Stop pipeline on failure and wait for user input
- **Real-time Monitoring**: Live progress updates and log display

### 2. Manual Segment Selection ⭐ **KEY FEATURE**
- **Rich Segment Display**: Show all 20 analysis segments with detailed information
- **Advanced Sorting**: Sort by severity, duration, speaker, category, confidence, timestamp
- **Content Preview**: Expandable cards showing segment details, quotes, and context
- **Simple Selection**: Checkbox interface for segment selection
- **No Bulk Actions**: Sorting/filtering sufficient for selection needs
- **Intermediate File Format**: Selected segments saved in identical JSON format to original analysis file
- **Pipeline Integration**: Selection creates `selected_segments.json` maintaining exact original structure for Stage 4

### 3. Workflow Presets
- **Preset Components**: Stage selections + segment mode + prompt selections
- **Custom Presets**: Save and name workflow configurations
- **Preset Storage**: JSON files with references to prompts (not embedded content)
- **Preset Management**: Create, save, load, overwrite, delete presets

### 4. Prompt Management
- **Analysis Guidelines**: Dropdown selection for Stage 3 content analysis
- **Narrative Prompts**: Dropdown selection for Stage 4 script generation
- **Manual Selection Prompt**: User will create custom prompt for manual segment workflow
- **Prompt References**: Store prompt names in presets, not full content

### 5. Audio Integration Options
- **TTS Generation**: Current automated audio generation (Stage 5)
- **Manual Audio Import**: User-recorded audio file upload
- **Audio Validation**: Check file exists and is readable
- **Format Support**: `.mp3`, `.wav`, `.aac`, `.m4a` (based on Video_Compilator)
- **File Organization**: Place manual audio in same directory as TTS with same naming convention

## Technical Architecture

### Flask Application Structure
```
Code/UI/
├── app.py                      # Main Flask application
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
├── run_server.py              # Server startup script
├── routes/
│   ├── __init__.py
│   ├── main.py                # Dashboard and episode management
│   ├── pipeline.py            # Pipeline execution control
│   ├── segments.py            # Manual segment selection interface
│   └── presets.py             # Preset management
├── static/
│   ├── css/
│   │   └── tailwind.min.css   # Tailwind CSS framework
│   ├── js/
│   │   ├── main.js            # Core functionality
│   │   ├── pipeline.js        # Pipeline control logic
│   │   ├── segments.js        # Segment selection interface
│   │   └── socketio.js        # Real-time communication
│   └── images/
├── templates/
│   ├── base.html              # Base template with Tailwind
│   ├── index.html             # Main dashboard
│   ├── pipeline.html          # Pipeline execution interface
│   ├── segments.html          # Manual segment selection
│   └── presets.html           # Preset management
├── services/
│   ├── pipeline_controller.py # Interface to master_processor_v2
│   ├── segment_parser.py      # Process analysis JSON files
│   ├── preset_manager.py      # JSON preset storage/retrieval
│   └── file_monitor.py        # Monitor pipeline file creation
├── database/
│   ├── models.py              # SQLite database models
│   └── pipeline_sessions.db   # Session and state storage
└── presets/
    ├── quick_auto.json        # Full automated workflow
    ├── manual_curation.json   # Manual segment selection
    └── full_creative.json     # Manual segments + audio import
```

### Integration with Existing Pipeline
- **Direct Integration**: UI calls `master_processor_v2.py` methods directly
- **Segment Selection**: Pass selected segments to Stage 4 narrative generation
- **Audio Import**: Replace Stage 5 TTS with manual audio file integration
- **File Monitoring**: Watch for stage completion via expected file creation
- **Error Propagation**: Surface pipeline errors in UI with clear messaging

## Detailed Feature Specifications

### Manual Segment Selection Interface

#### Segment Data Display (from analysis JSON):
- **segment_id**: Unique identifier
- **narrativeSegmentTitle**: Descriptive title
- **severityRating**: CRITICAL, HIGH, etc.
- **harm_category**: Primary categorization
- **primary_speaker_of_quote**: Main speaker
- **confidence_in_classification**: AI confidence level
- **brief_reasoning_for_classification**: Selection rationale
- **clipContextDescription**: Broader context
- **segmentDurationInSeconds**: Length information
- **fullerContextTimestamps**: Start/end times

#### Sorting Options:
1. **By Severity**: CRITICAL → HIGH → MEDIUM → LOW
2. **By Duration**: Shortest to longest segments
3. **By Speaker**: Group by primary speaker
4. **By Category**: Group by harm type
5. **By Confidence**: High confidence first
6. **By Timestamp**: Chronological order

#### Interface Design:
- **Overview Panel**: Total segments, selected count, quick stats
- **Segment Cards**: Collapsible cards with key info and selection checkboxes
- **Detailed View**: Expandable sections showing full analysis data
- **No Bulk Actions**: Individual selection only (sorting provides sufficient filtering)

### Workflow Presets System

#### Preset Structure (JSON):
```json
{
  "name": "Manual Curation Workflow",
  "created_date": "2025-06-19",
  "stages": [1, 2, 3, 4, 5, 6, 7],
  "segment_selection_mode": "manual",
  "analysis_prompt": "default_joe_rogan_analysis",
  "narrative_prompt": "manual_selection_narrative",
  "audio_method": "tts_generation",
  "description": "Manual segment selection with TTS audio"
}
```

#### Preset Management:
- **Create**: Save current configuration with custom name
- **Load**: Apply saved preset to current session
- **Overwrite**: Update existing preset (with confirmation)
- **Delete**: Remove preset (with confirmation)
- **Export/Import**: Not required (too complex for current needs)

### Audio Integration Workflows

#### TTS Generation (Current):
1. Stage 4 generates script
2. Stage 5 creates audio via SimpleTTSEngine
3. Audio files saved as `{section_id}.wav` in `Output/Audio/`

#### Manual Audio Import:
1. Stage 4 generates script
2. User records audio externally based on script
3. User uploads audio file via UI
4. Audio file placed in `Output/Audio/` with correct naming
5. Pipeline continues with Stages 6-7

#### Audio File Handling:
- **Supported Formats**: `.mp3`, `.wav`, `.aac`, `.m4a`
- **File Validation**: Check existence and readability
- **Naming Convention**: Match TTS naming (`{section_id}.wav`)
- **No Format Conversion**: Use files as provided

## Implementation Phases

### Phase 1: Core Flask Application (Week 1)
- [ ] Set up Flask application structure
- [ ] Create basic routes and templates
- [ ] Implement Tailwind CSS styling
- [ ] Test basic local access

### Phase 2: Pipeline Integration (Week 2)
- [ ] Create pipeline controller service
- [ ] Implement stage status monitoring
- [ ] Add pipeline execution controls
- [ ] Integrate with master_processor_v2.py
- [ ] Add real-time progress updates via SocketIO

### Phase 3: Segment Selection Interface (Week 3)
- [ ] Parse analysis JSON files
- [ ] Create segment display cards
- [ ] Implement sorting and filtering
- [ ] Add segment selection functionality
- [ ] Integrate with narrative generation

### Phase 4: Preset Management (Week 4)
- [ ] Design preset JSON structure
- [ ] Implement preset storage/retrieval
- [ ] Create preset management interface
- [ ] Add preset import/export
- [ ] Test workflow configurations

### Phase 5: Audio Integration (Week 5)
- [ ] Add audio file upload interface
- [ ] Implement file validation
- [ ] Integrate with episode directory structure
- [ ] Test manual audio workflow
- [ ] Add audio preview capabilities

### Phase 6: Polish and Testing (Week 6)
- [ ] Responsive design testing
- [ ] Error handling improvements
- [ ] Performance optimization
- [ ] User experience refinements
- [ ] Documentation and help system

## User Interface Mockup Structure

### Main Dashboard
- **Header**: Episode selection, workflow preset dropdown
- **Pipeline Status**: 7-stage progress indicators with completion status
- **Quick Actions**: Start pipeline, select segments, manage presets
- **Recent Activity**: Last processed episodes and their status

### Pipeline Execution Page
- **Stage Configuration**: Checkboxes for stages 1-7
- **Prompt Selection**: Dropdowns for analysis and narrative prompts
- **Audio Method**: Radio buttons for TTS vs manual import
- **Execution Control**: Start/stop/pause buttons
- **Live Progress**: Real-time stage progress and log output

### Manual Segment Selection Page
- **Filter/Sort Controls**: Dropdown menus for sorting options
- **Segment Grid**: Cards showing segment information
- **Selection Summary**: Count of selected segments, estimated duration
- **Action Buttons**: Confirm selection, clear all, preview script

### Preset Management Page
- **Preset List**: Available presets with descriptions
- **Current Configuration**: Show active settings
- **Preset Actions**: Create, save, load, delete presets
- **Import/Export**: JSON file management (future enhancement)

## Simplified Feature Decisions

### Features NOT Included:
- ❌ **Cross-Episode Features**: Too complex, keep episodes independent
- ❌ **AI Learning/Suggestions**: No usage pattern analysis
- ❌ **Bulk Selection Actions**: Sorting provides sufficient filtering
- ❌ **Keyboard Shortcuts**: Not needed for web interface
- ❌ **Export/Sharing**: No collaborative features required
- ❌ **Analytics/Reporting**: No usage tracking or reports
- ❌ **Pipeline Pause/Resume**: User prefers to fix root causes
- ❌ **Recording Interface**: User handles recording externally
- ❌ **Script Editing**: Generated scripts used as-is
- ❌ **Video Compilation Control**: Stage 7 remains automatic

### Simplified Workflows:
- **Error Handling**: Stop on failure, no automatic retry logic
- **File Management**: Use existing episode directory structure
- **Prompt Management**: Reference by name, no embedded content
- **Audio Processing**: No format conversion, use files as provided

## Next Steps

1. **Set up Flask development environment** with required dependencies
2. **Create basic application structure** following outlined directory layout
3. **Implement core dashboard** with pipeline status display
4. **Begin Phase 1 implementation** with iterative development approach

## Success Criteria

- ✅ **Pipeline Control**: Successfully run any combination of stages
- ✅ **Segment Selection**: Choose specific segments for narrative generation
- ✅ **Workflow Presets**: Save and load complete workflow configurations
- ✅ **Audio Integration**: Successfully import manual audio files
- ✅ **Real-time Updates**: Live pipeline progress monitoring
- ✅ **Responsive Design**: Functional interface on different screen sizes
- ✅ **Error Handling**: Clear error messages and pipeline failure recovery
