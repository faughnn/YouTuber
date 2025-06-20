# YouTube Pipeline UI Development Plan

**Date Created:** June 19, 2025  
**Status:** Planning Phase  

## Overview

Creating a web-based UI for the 7-stage YouTube video processing pipeline to provide better control, visibility, and user interaction with the pipeline execution.

## Current Pipeline Architecture Advantages for UI

The existing `master_processor_v2.py` is well-suited for UI integration because:

1. **Modular Stage Design**: Each stage is a separate method with clear inputs/outputs
2. **File-Based State Tracking**: Can determine completion status by checking for expected files
3. **Organized Directory Structure**: Each episode creates predictable folder structure
4. **Existing Caching Logic**: Stages already check if files exist before re-running

## Core UI Requirements

### 1. Pipeline Status Dashboard
- Visual indicators for each of the 7 stages showing completion status
- File existence checks to determine what's already been completed
- Estimated processing times and current stage progress

### 2. Flexible Stage Execution
- **Run any part of the pipeline**: Start from any stage, stop at any stage
- **Preset execution modes**: 
  - Full Pipeline (stages 1-7)
  - Audio Only (stages 1-5) 
  - Script Only (stages 1-4)
- **Custom stage selection**: Checkboxes for individual stages

### 3. Manual Segment Selection Feature ⭐ **KEY ENHANCEMENT**

**Problem**: Content analysis (Stage 3) outputs 20 segments, but AI automatically selects which ones to use for script generation (Stage 4). Need manual control over this selection.

**Solution**: Interactive segment selection interface between stages 3 and 4:

#### Segment Selection UI Components:
- **Segment Preview Cards**: Display each of the 20 segments with:
  - Segment title/topic
  - Key content summary
  - Timestamp range
  - Speaker information
  - Relevance score (if available)
  
- **Selection Interface**:
  - Checkboxes for each segment
  - "Select All" / "Deselect All" buttons
  - Filter options (by speaker, topic, duration, etc.)
  - Drag-and-drop reordering for selected segments
  
- **Preview Functionality**:
  - Expandable content preview for each segment
  - Audio snippet playback (if possible)
  - Visual indicators of segment quality/importance

#### Technical Implementation for Manual Selection:
1. **Pipeline Modification**: Add optional parameter to Stage 4 for selected segments
2. **Intermediate Processing**: Create filtered analysis file with only selected segments
3. **UI State Management**: Store user selections and pass to narrative generation
4. **Fallback Behavior**: If no manual selection made, use AI automatic selection

### 4. Real-time Monitoring
- Live log output display
- File creation notifications
- Error alerts with actionable suggestions
- Processing time tracking per stage

### 5. Results Management
- Episode directory browser
- File previews (scripts, analysis results, audio files)
- Download links for outputs
- Episode history and management

## Enhanced Creative Control Requirements

### Multiple Workflow Paths
The UI needs to support different creative approaches:

1. **Fully Automated Path** (Current): 
   - Stage 3: Auto-analysis with standard prompt
   - Stage 4: Auto-narrative with current TTS prompt
   - Stage 5: AI-generated TTS audio

2. **Manual Segment Selection Path**:
   - Stage 3: Auto-analysis with standard prompt
   - Stage 4: Manual segment selection → Custom narrative prompt
   - Stage 5: AI-generated TTS audio OR manual audio import

3. **Fully Manual Creative Path**:
   - Stage 3: Custom analysis prompt selection
   - Stage 4: Manual segment selection → Custom narrative prompt
   - Stage 5: Manual audio import (bypass TTS entirely)

### Prompt Management System

#### Current Prompt Structure Analysis:
Based on `tts_podcast_narrative_prompt.txt`, the current prompt:
- Assumes AI will automatically select best segments from all 20
- Uses specific voice/character profile (sarcastic YouTuber)
- Has detailed content structure requirements
- Includes specific timing guidelines (30s-1min opening, etc.)

#### New Prompt Requirements:
**Manual Selection Prompt** needs to:
- Handle pre-selected segments instead of choosing from all 20
- Maintain same voice/character profile
- Adapt structure based on number of selected segments
- Account for user's manual curation decisions

#### UI Prompt Management Features:
1. **Prompt Library Interface**:
   - Dropdown/selection for Stage 3 analysis prompts
   - Dropdown/selection for Stage 4 narrative prompts
   - Preview/edit capability for selected prompts
   - Save custom prompt variations

2. **Prompt Categories**:
   - **Analysis Prompts** (Stage 3):
     - Default Joe Rogan analysis rules
     - Custom analysis focus (medical, political, etc.)
     - Different severity thresholds
   - **Narrative Prompts** (Stage 4):
     - Auto-selection narrative (current)
     - Manual-selection narrative (new)
     - Different voice/style variations
     - Different timing/structure templates

### Manual Audio Import System (Stage 5 Alternative)

#### Problem with Current TTS:
- AI-generated audio is obviously artificial
- Lacks human emotional nuance
- User wants option for professional quality narration

#### Manual Audio Import Features:
1. **Audio File Upload Interface**:
   - Drag-and-drop audio file upload
   - Support for common formats (MP3, WAV, M4A, etc.)
   - Audio preview/playback capability
   - Duration validation against script

2. **Audio Synchronization Tools**:
   - Script-to-audio alignment interface
   - Timing validation tools
   - Audio segment management
   - Quality check indicators

3. **Audio Processing Options**:
   - Normalization settings
   - Format conversion if needed
   - Integration with existing pipeline structure

### Updated UI Workflow Design

#### Stage Configuration Panel:
- **Stage 3 Options**:
  - [ ] Use default analysis prompt
  - [ ] Select custom analysis prompt: [Dropdown]
  - [ ] Edit selected prompt [Button]

- **Stage 4 Options**:
  - [ ] Auto-select segments (use current prompt)
  - [ ] Manual segment selection (use manual prompt)
  - [ ] Custom narrative prompt: [Dropdown]
  - [ ] Edit selected prompt [Button]

- **Stage 5 Options**:
  - [ ] Generate TTS audio (current method)
  - [ ] Import manual audio file
  - [ ] Audio file: [Upload/Browse]

#### Manual Segment Selection Interface:
**Enhanced for Manual Workflow**:
- Clear indication that selected segments will be used with manual prompt
- Preview of how segments will be structured in narrative
- Drag-and-drop reordering for segment sequence
- Timing estimates based on selected segments

#### Prompt Editor Interface:
- **Syntax highlighting** for prompt structure
- **Variable preview** showing available data fields
- **Template system** for common prompt variations
- **Validation** to ensure prompt compatibility with data structure

## Technical Architecture

### Recommended Framework: Flask Web UI

**Why Flask:**
- Easy integration with existing Python codebase
- Great for real-time updates with Flask-SocketIO
- Perfect for file system interaction
- Simple to implement progressively

### Directory Structure:
```
Code/UI/
├── app.py                 # Flask app main file
├── pipeline_controller.py # Interface between UI and master_processor_v2
├── segment_selector.py    # Manual segment selection logic
├── static/
│   ├── css/
│   │   ├── main.css
│   │   └── segments.css   # Styling for segment selection
│   ├── js/
│   │   ├── pipeline.js
│   │   └── segments.js    # Segment selection interactions
│   └── images/
└── templates/
    ├── index.html         # Main dashboard
    ├── pipeline.html      # Pipeline execution page
    ├── segments.html      # Manual segment selection page
    └── results.html       # Results viewer
```

### Key Technical Components:

1. **State Management**: SQLite database or session storage for pipeline state
2. **Async Processing**: Flask-SocketIO for real-time pipeline updates
3. **File Monitoring**: Watch for file creation to update UI status automatically
4. **Segment Data Processing**: Parse analysis JSON to extract and display segment information
5. **Pipeline Integration**: Modify existing pipeline to accept manual segment selections

## Implementation Phases

### Phase 1: Basic Pipeline Control UI
- [ ] Create basic Flask app structure
- [ ] Implement pipeline status dashboard
- [ ] Add stage selection and execution controls
- [ ] Basic real-time logging display

### Phase 2: Manual Segment Selection
- [ ] Parse content analysis output to extract segments
- [ ] Create segment selection interface
- [ ] Implement segment filtering and preview
- [ ] Integrate selected segments with narrative generation

### Phase 3: Enhanced Features
- [ ] Episode management and history
- [ ] Advanced file previews
- [ ] Configuration management through UI
- [ ] Export/import of pipeline configurations

### Phase 4: Polish and Optimization
- [ ] Responsive design for different screen sizes
- [ ] Performance optimization for large files
- [ ] Error handling and recovery features
- [ ] User documentation and help system

## Challenges and Considerations

### Manual Segment Selection Challenges:
1. **Data Structure**: Need to understand exact format of the 20 segments from analysis
2. **Pipeline Modification**: May need to modify `NarrativeCreatorGenerator` to accept segment selection
3. **State Persistence**: Store user selections across UI sessions
4. **Preview Quality**: How much content to show without overwhelming the user

### General UI Challenges:
1. **Async Operations**: Long-running pipeline stages need proper async handling
2. **Error Recovery**: Graceful handling of pipeline failures mid-execution
3. **File Size Management**: Some outputs might be very large for web display
4. **Cross-Platform Compatibility**: Ensure UI works across different browsers and systems

## Next Steps

1. **Investigate Analysis Output Structure**: Examine actual content analysis JSON files to understand segment format
2. **Create Basic Prototype**: Start with simple Flask app showing pipeline status
3. **Design Segment Selection Mockup**: Create visual design for segment selection interface
4. **Test Pipeline Integration**: Ensure UI can properly interface with existing pipeline code

---

## Questions for Further Discussion

1. **Segment Selection UX**: What information is most important to show for each segment when making selection decisions?
2. **Pipeline Execution**: Should the UI allow pausing/resuming long-running stages?
3. **Multi-Episode Management**: Do we need to handle multiple episodes simultaneously?
4. **Advanced Features**: Any other manual override points in the pipeline that would benefit from UI control?

## Content Analysis JSON Structure Analysis

Based on examination of actual analysis results, each segment contains rich structured data:

### Segment Data Fields Available for UI Display:
- **segment_id**: Unique identifier (e.g., "JRE_Harmful_Segment_01")
- **narrativeSegmentTitle**: Descriptive title of the segment content
- **guest_name**: Participating guests
- **primary_speaker_of_quote**: Main speaker for the segment
- **severityRating**: Rating level (CRITICAL, HIGH, etc.)
- **harm_category**: Categorization with primary_type and subtypes
- **identified_rhetorical_strategies**: List of rhetorical techniques used
- **potential_societal_impacts**: Array of potential impact categories
- **confidence_in_classification**: AI confidence level
- **brief_reasoning_for_classification**: Explanation of classification
- **clipContextDescription**: Context surrounding the segment
- **suggestedClip**: Array of timestamped quotes with speakers
- **fullerContextTimestamps**: Start/end timestamps for broader context
- **segmentDurationInSeconds**: Length of segment

### Manual Segment Selection UI Features

#### Advanced Sorting and Filtering Options:
1. **By Severity Rating**: CRITICAL → HIGH → MEDIUM → LOW
2. **By Duration**: Shortest to longest segments
3. **By Primary Speaker**: Group by main speaker
4. **By Harm Category**: 
   - Dangerous Misinformation
   - Societal Damage Contribution  
   - Conspiracy Theory
   - (Other categories as they appear)
5. **By Confidence Level**: High confidence classifications first
6. **By Timestamp**: Chronological order in the episode
7. **By Rhetorical Strategies**: Group by similar techniques
8. **By Potential Impact**: Sort by societal impact severity

#### Segment Selection Interface Design:

**Overview Panel:**
- Total segments: 20
- Selected count with dynamic updates
- Quick stats (severity distribution, duration totals)
- Bulk selection controls (All/None/By Category)

**Individual Segment Cards:**
- **Header**: Title + Severity Badge + Duration
- **Meta Info**: Speaker, Confidence, Category
- **Content Preview**: Brief reasoning + context description  
- **Timestamp Info**: Start/end times with duration
- **Action Controls**: 
  - Select checkbox
  - Expand for full details
  - Preview quotes button
  - Context player (if audio preview possible)

**Detailed Expansion View:**
- Full reasoning text
- Complete suggested clip with all quotes
- Rhetorical strategies tags
- Potential impacts list
- Broader context timestamps

#### Interactive Features:
- **Live Search**: Filter segments by keywords in titles or content
- **Multi-sort**: Primary and secondary sorting criteria
- **Preview Mode**: Quick scan without full expansion
- **Selection Memory**: Remember selections across sessions
- **Export Selection**: Save segment choices for reuse

#### Technical Implementation Notes:
- **Data Loading**: Parse JSON and create searchable/sortable data structure
- **Performance**: Lazy loading for segment details to handle large datasets
- **State Management**: Track selection state, sort preferences, filter settings
- **Responsive Design**: Card layout that works on different screen sizes

### Implementation Clarifications

#### Prompt Management:
- **Manual-selection prompt**: User will create custom prompt for manual segment workflow
- **Audio timing**: Record audio after script generation (script-first approach)
- **Workflow presets**: Implement saved configurations for different creative modes

### Additional Design Questions

**1. Manual Audio Integration:**
- When you record your audio based on the script, do you want the UI to show the script sections alongside a recording interface, or will you record externally and just import the final file?
- Should the UI provide any timing guides or cues to help match your recording to the expected script pacing?
- Do you want the ability to record in segments (intro, segment 1, segment 2, outro) or as one continuous file?

**2. Segment Selection Workflow:**
- When manually selecting segments, do you want to see how your selection affects the estimated final video length?
- Should there be warnings if you select segments that might create awkward transitions or timing issues?
- Do you want the ability to add notes/comments to your selected segments for reference during recording?

**3. Script Review and Editing:**
- After the AI generates the script based on your manual segment selection, do you want the ability to edit the script before recording?
- Should there be a script annotation system where you can add recording notes, emphasis markers, or timing adjustments?
- Do you want multiple script versions/iterations saved for comparison?

**4. Quality Control and Preview:**
- Do you want preview capabilities to see how your manual selections will flow together before generating the full script?
- Should there be a "dry run" mode where you can test different segment combinations quickly?
- Do you want the UI to provide content warnings or suggestions based on your manual selections?

**5. Episode Management:**
- How do you want to handle multiple episodes? Should each episode remember its workflow settings?
- Do you want the ability to clone settings from one episode to another?
- Should there be episode templates based on different types of content or guests?

**6. Advanced Features:**
- Do you want the ability to bookmark or favorite certain segments across different episodes for reuse?
- Should there be analytics showing which types of segments you tend to select most often?
- Do you want collaborative features where you could share segment selections or get input from others?

### User Requirements Clarification

#### Workflow Presets:
- **Preset Names**: Auto-generated suitable names (e.g., "Quick Auto Mode", "Manual Curation", "Full Creative Control")
- **Preset Components**: 
  - Stage selections (which stages to run)
  - Segment selection mode (automatic vs manual)
  - Prompt selections (analysis and narrative prompts)
- **Custom Presets**: Ability to save and name custom preset configurations
- **No Content-Specific Presets**: Keep presets workflow-focused, not content-focused

#### Error Handling:
- **Script Generation Failures**: User prefers to fix root cause rather than implement recovery mechanisms
- **Audio Timing Mismatches**: Not a concern - final video timing depends on actual audio clips, not script estimates
- **Pipeline Pause/Resume**: Not required

#### Stage Integration:
- **Video Clipping Logic**: Manual segment selection → Script generation → Video clipper uses script (clipper remains agnostic to selection method)
- **Final Compilation**: No manual control needed for Stage 7

#### Feature Scope Decisions:
- **Cross-Episode Features**: Not needed (too complex)
- **AI Learning/Suggestions**: Not wanted
- **Bulk Selection**: Sorting functionality sufficient
- **Keyboard Shortcuts**: Not needed
- **Export/Sharing**: Not required
- **Analytics/Reporting**: Not needed

### Simplified UI Focus Areas

Based on user feedback, the UI should focus on:

1. **Clean Workflow Management**:
   - Simple preset system with save/name capability
   - Clear stage selection interface
   - Prompt selection dropdowns

2. **Effective Segment Selection**:
   - Rich sorting and filtering capabilities
   - Clear segment preview cards
   - Simple selection checkboxes

3. **Streamlined Audio Integration**:
   - Script-first workflow (generate script, then record audio)
   - Simple audio file import
   - Integration with existing pipeline structure

4. **Pipeline Status and Control**:
   - Clear visual indicators of stage completion
   - Simple start/stop controls
   - Real-time progress monitoring

### Technical Implementation Priorities

1. **Preset System**: Save/load workflow configurations with custom names
2. **Segment Selection UI**: Focus on sorting, filtering, and clear presentation
3. **Pipeline Integration**: Ensure manual selections flow seamlessly through existing stages
4. **Audio Import**: Simple file upload that integrates with episode directory structure

### Final Implementation Details

#### Pipeline Execution:
- **Automatic Sequential Execution**: All selected stages run automatically in sequence
- **Error Handling**: Pipeline stops on failure and waits for user input
- **No Pipeline Resume**: User will fix root causes rather than implement resume functionality

#### Audio Format Support:
Based on codebase analysis, supported audio formats:
- **TTS Generated**: `.wav` format (current standard)
- **Manual Import Supported**: `.mp3`, `.wav`, `.aac`, `.m4a` (from Video_Compilator analysis)
- **File Validation**: Check file exists and is readable before proceeding
- **No Format Conversion**: Use files as-is (no automatic conversion needed)

#### Preset System Structure:
- **Storage Format**: JSON files for preset configurations
- **Preset Components**:
  - Stage selections (which stages 1-7 to run)
  - Segment selection mode (automatic/manual)  
  - Prompt references (by name, not embedded content)
- **Preset Management**:
  - Save current configuration with custom name
  - Load existing presets
  - Overwrite existing presets (with confirmation)
  - Delete presets
- **File Location**: Store presets in `Code/UI/presets/` directory

#### Manual Audio Integration:
- **Recording Workflow**: User records externally after script generation
- **File Placement**: Manual audio files placed in `Content/Episode/Output/Audio/` directory
- **Naming Convention**: Follow same pattern as TTS files (`{section_id}.wav`)
- **File Organization**: Maintain compatibility with existing Video_Compilator expectations

#### Simplified Feature Set:
- **No Recording Interface**: User handles recording externally
- **No Cross-Episode Features**: Keep episodes independent
- **No Analytics/Learning**: Static interface without usage tracking
- **No Collaboration Features**: Single-user focused
- **No Bulk Actions**: Sorting/filtering sufficient

### Technical Implementation Summary

#### Core UI Components:
1. **Main Dashboard**: Pipeline status, episode selection, workflow presets
2. **Stage Configuration Panel**: Stage selection, prompt selection, audio method selection
3. **Manual Segment Selection Interface**: Rich segment display with sorting/filtering
4. **Pipeline Execution Monitor**: Real-time progress, logs, error display
5. **Preset Management**: Save/load/manage workflow configurations

#### Backend Integration Points:
1. **Pipeline Controller**: Interface between UI and `master_processor_v2.py`
2. **Segment Parser**: Process analysis JSON for UI display
3. **Preset Manager**: Handle JSON-based preset storage/retrieval
4. **File Monitor**: Watch for stage completion via file creation
5. **Audio Validator**: Check manual audio files before pipeline execution

### Deployment Architecture

#### Technology Stack:
- **Backend**: Flask web application with Flask-SocketIO for real-time updates
- **Frontend**: HTML/CSS/JavaScript with Tailwind CSS for styling
- **Database**: SQLite for session and preset storage
- **Real-time Communication**: WebSockets via Flask-SocketIO
- **Remote Access**: Tailscale for secure remote connectivity

#### Tailscale Integration Benefits:
- **Secure Remote Access**: Access UI from anywhere without exposing to public internet
- **No Port Forwarding**: Tailscale handles networking automatically
- **Device Authentication**: Built-in authentication through Tailscale network
- **Cross-Platform**: Access from phones, tablets, other computers
- **Private Network**: UI remains on private Tailscale network

#### Flask Application Structure:
```
Code/UI/
├── app.py                    # Main Flask application
├── config.py                 # Configuration management
├── requirements.txt          # Python dependencies
├── run_server.py            # Server startup script with Tailscale integration
├── routes/
│   ├── __init__.py
│   ├── main.py              # Main dashboard routes
│   ├── pipeline.py          # Pipeline execution routes
│   ├── segments.py          # Segment selection routes
│   └── presets.py           # Preset management routes
├── static/
│   ├── css/
│   │   └── tailwind.min.css # Tailwind CSS framework
│   ├── js/
│   │   ├── main.js          # Core JavaScript functionality
│   │   ├── pipeline.js      # Pipeline control logic
│   │   ├── segments.js      # Segment selection interface
│   │   └── socketio.js      # Real-time communication
│   └── images/
│       └── favicon.ico
├── templates/
│   ├── base.html            # Base template with Tailwind
│   ├── index.html           # Main dashboard
│   ├── pipeline.html        # Pipeline execution page
│   ├── segments.html        # Manual segment selection
│   └── presets.html         # Preset management
├── services/
│   ├── __init__.py
│   ├── pipeline_controller.py  # Interface to master_processor_v2
│   ├── segment_parser.py       # Analysis JSON processing
│   ├── preset_manager.py       # Preset storage/retrieval
│   └── file_monitor.py         # File system monitoring
├── database/
│   ├── models.py            # SQLite database models
│   └── pipeline_sessions.db # SQLite database file
└── presets/
    ├── quick_auto.json      # Default preset files
    ├── manual_curation.json
    └── full_creative.json
```

#### Server Configuration for Tailscale:
```python
# run_server.py
import os
import subprocess
from app import create_app, socketio

def get_tailscale_ip():
    """Get the Tailscale IP address for this machine"""
    try:
        result = subprocess.run(['tailscale', 'ip'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return None
    except FileNotFoundError:
        print("Tailscale not found. Install Tailscale for remote access.")
        return None

def main():
    app = create_app()
    
    # Get Tailscale IP
    tailscale_ip = get_tailscale_ip()
    
    if tailscale_ip:
        print(f"Starting Flask server on Tailscale network")
        print(f"Access locally: http://localhost:5000")
        print(f"Access remotely: http://{tailscale_ip}:5000")
        # Bind to all interfaces to allow Tailscale access
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
    else:
        print("Starting Flask server (localhost only)")
        print("Access locally: http://localhost:5000")
        socketio.run(app, host='localhost', port=5000, debug=True)

if __name__ == '__main__':
    main()
```

#### Remote Access Features:
- **Mobile Responsive**: Tailwind CSS ensures good mobile experience
- **Touch-Friendly**: Large buttons and touch targets for mobile/tablet use
- **Offline Resilience**: Handle network disconnections gracefully
- **Session Persistence**: Maintain state across connections
- **Security**: No public exposure, only accessible via Tailscale network

#### Development Workflow:
1. **Local Development**: Run Flask app locally for development
2. **Tailscale Setup**: Install and configure Tailscale on host machine
3. **Remote Testing**: Access UI from mobile devices via Tailscale IP
4. **Production Mode**: Run server bound to Tailscale interface

#### Tailscale Setup Steps:
1. Install Tailscale on the machine running the UI
2. Authenticate with Tailscale account
3. Configure Flask to bind to all interfaces (0.0.0.0)
4. Access UI from any device on Tailscale network using machine's Tailscale IP

#### Security Considerations:
- **No Public Exposure**: UI only accessible via Tailscale private network
- **Device Authentication**: Tailscale handles device authentication
- **Encrypted Connections**: All traffic encrypted via Tailscale
- **Access Control**: Manage access through Tailscale admin console
