# Video Compilator Development Plan

## Overview
The Video Compilator takes the unified podcast script and combines audio/video assets to create a final, seamless video compilation. This system uses FFmpeg to stitch together audio narration and video clips according to the script's sequence and timing.

## Project Structure & Integration
```
YouTuber/
├── Code/
│   └── Video_Compilator/              # New component
│       ├── __init__.py
│       ├── main.py                    # Entry point
│       ├── script_parser.py           # Parse unified JSON script
│       ├── asset_validator.py         # Pre-flight asset validation
│       ├── background_processor.py    # Handle static image backgrounds
│       ├── timeline_builder.py        # Create compilation timeline
│       ├── ffmpeg_orchestrator.py     # Execute FFmpeg commands
│       └── config.py                  # Configuration settings
├── Content/[Episode]/Output/
│   ├── Scripts/unified_podcast_script.json  # Input script
│   ├── Audio/[section_id].wav               # TTS narration files
│   └── Video/
│       ├── [clip_id].mp4                    # Extracted video clips
│       ├── temp/                            # Temporary compilation files
│       └── Final/[episode]_compiled.mp4     # Final output
└── Assets/Chris_Morris_Images/bloody_hell.jpg  # Static background
```

## Finalized Design Decisions

### Visual Treatment
- **Narration Segments**: Static background image (`bloody_hell.jpg`)
- **Video Segments**: Original podcast video clips
- **Resolution**: 1080p (1920x1080)
- **Quality**: High (CRF 18, libx264 high preset)

### Audio Treatment
- **Transitions**: Hard cuts (no crossfades)
- **Normalization**: Disabled (preserves original audio characteristics)
- **Format**: AAC 320kbps, 48kHz sample rate

### Processing Approach
- **Mode**: Single episode processing
- **Validation**: Fail-fast with comprehensive error reporting
- **Temp Files**: Preserved by default for inspection
- **Progress**: Clean, minimal console output

## Component Specifications

### 1. Script Parser (`script_parser.py`)
**Purpose**: Parse and validate the unified podcast script
```python
class ScriptParser:
    def parse_script(self, script_path: Path) -> Dict
    def get_section_sequence(self) -> List[Dict]
    def map_assets(self, audio_dir: Path, video_dir: Path) -> Dict
    def validate_script_structure(self) -> bool
```

**Responsibilities**:
- Load and parse `unified_podcast_script.json`
- Extract section sequence (intro → pre_clip → video_clip → post_clip → outro)
- Map section_ids to corresponding audio/video files
- Validate JSON structure and required fields

### 2. Asset Validator (`asset_validator.py`)
**Purpose**: Pre-flight validation of all required assets
```python
class AssetValidator:
    def validate_all_assets(self, script_data: Dict, paths: Dict) -> ValidationResult
    def check_audio_files(self, sections: List, audio_dir: Path) -> List[str]
    def check_video_files(self, sections: List, video_dir: Path) -> List[str]
    def check_background_image(self, image_path: Path) -> bool
    def generate_error_report(self, missing_assets: Dict) -> str
```

**Validation Checks**:
- Script file exists and valid JSON
- All audio files exist (intro_001.wav, pre_clip_001.wav, etc.)
- All video clips exist (video_clip_001.mp4, etc.)
- Background image exists and readable
- File format compatibility with FFmpeg

### 3. Background Processor (`background_processor.py`)
**Purpose**: Create video streams from static image + TTS audio
```python
class BackgroundProcessor:
    def create_narration_video(self, audio_path: Path, output_path: Path) -> bool
    def prepare_background_image(self) -> str
    def get_audio_duration(self, audio_path: Path) -> float
    def generate_ffmpeg_command(self, audio_path: Path, duration: float) -> List[str]
```

**Process**:
1. Load static background image (`bloody_hell.jpg`)
2. Scale/crop to 1920x1080 maintaining aspect ratio
3. Combine with TTS audio to create video segment
4. Output temporary video file for timeline

### 4. Timeline Builder (`timeline_builder.py`)
**Purpose**: Orchestrate the sequence and create FFmpeg input list
```python
class TimelineBuilder:
    def build_compilation_timeline(self, script_sections: List) -> Timeline
    def create_concat_file(self, timeline: Timeline, temp_dir: Path) -> Path
    def calculate_total_duration(self, timeline: Timeline) -> float
    def validate_segment_order(self, timeline: Timeline) -> bool
```

**Timeline Structure**:
```
1. temp_intro_001.mp4          # Static bg + TTS
2. video_clip_001.mp4          # Original podcast clip
3. temp_pre_clip_001.mp4       # Static bg + TTS
4. video_clip_002.mp4          # Original podcast clip
5. temp_post_clip_001.mp4      # Static bg + TTS
...
N. temp_outro_001.mp4          # Static bg + TTS
```

### 5. FFmpeg Orchestrator (`ffmpeg_orchestrator.py`)
**Purpose**: Execute the final compilation
```python
class FFmpegOrchestrator:
    def compile_final_video(self, concat_file: Path, output_path: Path) -> bool
    def execute_ffmpeg_command(self, command: List[str]) -> CompileResult
    def handle_compilation_errors(self, stderr: str) -> str
    def verify_output_quality(self, output_path: Path) -> bool
```

**FFmpeg Process**:
1. Use concat demuxer for seamless joining
2. Apply consistent encoding settings
3. Handle mixed video/audio-only segments
4. Generate high-quality MP4 output

## Configuration Settings (`config.py`)

### Video Output Configuration
```python
VIDEO_CONFIG = {
    "resolution": "1920x1080",
    "codec": "libx264",
    "preset": "high",
    "crf": 18,  # High quality
    "frame_rate": 30,
    "pixel_format": "yuv420p"
}

AUDIO_CONFIG = {
    "codec": "aac",
    "bitrate": "320k",
    "sample_rate": 48000,
    "channels": 2
}
```

### Processing Configuration
```python
PROCESSING_CONFIG = {
    "cleanup_temp_files": False,  # Keep temp files for inspection
    "fail_on_missing_assets": True,
    "background_image_path": "C:/Users/nfaug/OneDrive - LIR/Desktop/YouTuber/Assets/Chris_Morris_Images/bloody_hell.jpg",
    "temp_dir_name": "temp"
}

TRANSITIONS_CONFIG = {
    "type": "hard_cut",  # Future: crossfade, fade_in_out
    "duration": 0  # Future: configurable fade duration
}
```

## Error Handling Strategy

### Pre-Flight Validation Errors
```
ERROR: Video Compilator Pre-Flight Check Failed

Missing Audio Assets:
- intro_001.wav (required for section: intro_001)
- pre_clip_003.wav (required for section: pre_clip_003)

Missing Video Assets:
- video_clip_005.mp4 (required for section: video_clip_005)

Background Image Issues:
- File not found: C:/Users/nfaug/OneDrive - LIR/Desktop/YouTuber/Assets/Chris_Morris_Images/bloody_hell.jpg

Please resolve these issues before running compilation.
```

### Runtime Error Handling
- **FFmpeg Errors**: Capture and parse stderr for diagnostics
- **Disk Space**: Verify sufficient space before compilation
- **File Permissions**: Check write access to output directories
- **Process Interruption**: Preserve temp files for debugging

## Implementation Workflow

### Phase 1: Asset Preparation
```
[1/4] Validating assets...
├── Parsing unified_podcast_script.json
├── Checking audio files (8 found)
├── Checking video clips (7 found)
├── Verifying background image
└── ✓ All assets validated
```

### Phase 2: Background Video Generation
```
[2/4] Generating narration videos...
├── Creating temp_intro_001.mp4
├── Creating temp_pre_clip_001.mp4
├── Creating temp_post_clip_001.mp4
├── Creating temp_pre_clip_002.mp4
└── ✓ 8 narration videos created
```

### Phase 3: Timeline Assembly
```
[3/4] Building timeline...
├── Sequencing 15 total segments
├── Creating concat_list.txt
├── Estimated total duration: 18m 34s
└── ✓ Timeline ready for compilation
```

### Phase 4: Final Compilation
```
[4/4] Compiling final video...
├── Executing FFmpeg concat demuxer
├── Applying 1080p/30fps encoding
├── Output: Joe_Rogan_2330_Bono_compiled.mp4
└── ✓ Compilation complete (142.3 MB)
```

## Temporary Files Structure
```
/Output/Video/temp/
├── temp_intro_001.mp4           # Static bg + intro TTS
├── temp_pre_clip_001.mp4        # Static bg + pre-clip TTS
├── temp_post_clip_001.mp4       # Static bg + post-clip TTS
├── temp_pre_clip_002.mp4        # Static bg + pre-clip TTS
├── temp_post_clip_002.mp4       # Static bg + post-clip TTS
├── ...
├── temp_outro_001.mp4           # Static bg + outro TTS
└── concat_list.txt              # FFmpeg input file list
```

## Usage Example
```python
from Video_Compilator import VideoCompilator

# Initialize with episode path
episode_path = "C:/Users/nfaug/OneDrive - LIR/Desktop/YouTuber/Content/Joe_Rogan_Experience/Joe Rogan Experience #2330 - Bono"

compiler = VideoCompilator()
result = compiler.compile_episode(episode_path)

if result.success:
    print(f"✓ Compilation complete: {result.output_path}")
else:
    print(f"✗ Compilation failed: {result.error_message}")
```

## Dependencies
- **FFmpeg**: External binary for video processing
- **Python Libraries**: 
  - `pathlib` - Path handling
  - `json` - Script parsing
  - `subprocess` - FFmpeg execution
  - `logging` - Progress reporting
  - `typing` - Type hints

## Future Enhancements
- **Audio Normalization**: Configurable volume leveling
- **Transition Effects**: Crossfades and fade in/out options
- **Batch Processing**: Multiple episode compilation
- **Custom Backgrounds**: Dynamic background selection
- **Quality Presets**: Multiple output quality options
- **Progress Callbacks**: Integration with GUI progress bars