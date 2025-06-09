# Create Audio Files from Script using TTS - Fresh Implementation

## Project Overview
This plan outlines the development of a **completely new** TTS system to automatically generate multiple audio clips from Gemini response files. The system will be built from scratch, designed specifically for the new JSON format with `podcast_sections[]` array, without reusing existing TTS infrastructure.

## Design Philosophy
- **Clean Architecture**: Build new modules with clear separation of concerns
- **Single Format Focus**: Support only the new `podcast_sections[]` JSON format
- **Modern Patterns**: Use contemporary Python practices and patterns
- **Extensible Design**: Easy to add new features and TTS providers
- **Robust Error Handling**: Comprehensive logging and recovery mechanisms

## Target JSON Format Analysis

### Source Data Structure
The Gemini response files contain a `podcast_sections` array with different section types:

**Audio Sections** (Processed by TTS):
```json
{
  "section_type": "intro|pre_clip|post_clip|outro",
  "section_id": "intro_001|pre_clip_001|post_clip_001|outro_001",
  "script_content": "Text to convert to audio",
  "audio_tone": "Natural language tone description",
  "estimated_duration": "30 seconds"
}
```

**Video Sections** (Skipped by TTS):
```json
{
  "section_type": "video_clip",
  "section_id": "video_clip_001",
  "clip_id": "reference_id",
  "start_time": "00:05:30",
  "end_time": "00:06:45",
  "title": "Video clip title",
  "selection_reason": "Why this clip was selected",
  "severity_level": "impact_rating",
  "key_claims": ["claim1", "claim2"],
  "estimated_duration": "75 seconds"
}
```

### Target Output Structure
```
Content/{Series}/{Episode}/Output/Audio/{section_id}.wav
```

Example:
```
Content/Joe_Rogan_Experience/Joe Rogan Experience #2330 - Bono/Output/Audio/
├── intro_001.wav
├── pre_clip_001.wav
├── post_clip_001.wav
├── pre_clip_002.wav
├── post_clip_002.wav
├── outro_001.wav
```

## New Architecture Design

### Module 1: JSON Parser and Validator
**File**: `Code/Audio_Generation/json_parser.py`

**Purpose**: Parse and validate Gemini response files for new format
**Responsibilities**:
- Extract JSON from debug response text files
- Validate required fields and structure
- Filter sections by type (audio vs video)
- Prepare data for TTS processing

**Key Classes**:
```python
class GeminiResponseParser:
    def parse_response_file(self, file_path: str) -> Dict
    def validate_podcast_sections(self, data: Dict) -> ValidationResult
    def extract_audio_sections(self, sections: List[Dict]) -> List[AudioSection]
    def extract_episode_metadata(self, data: Dict) -> EpisodeInfo

class AudioSection:
    section_id: str
    section_type: str
    script_content: str
    audio_tone: str
    estimated_duration: str

class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    audio_section_count: int
    video_section_count: int
```

### Module 2: TTS Engine
**File**: `Code/Audio_Generation/tts_engine.py`

**Purpose**: Core TTS functionality using Gemini API
**Responsibilities**:
- Generate audio from text with tone instructions
- Handle Gemini API communication
- Manage audio file creation and saving
- Apply voice tone descriptions

**Key Classes**:
```python
class GeminiTTSEngine:
    def __init__(self, config_path: str)
    def generate_audio(self, text: str, tone: str, output_path: str) -> TTSResult
    def format_tone_instruction(self, tone: str, text: str) -> str
    def _create_audio_file(self, audio_data: bytes, output_path: str) -> bool
    def _validate_audio_output(self, file_path: str) -> bool

class TTSResult:
    success: bool
    output_path: str
    error_message: str
    audio_duration: float
    file_size: int
```

### Module 3: Audio File Manager
**File**: `Code/Audio_Generation/audio_file_manager.py`

**Purpose**: Manage audio file organization and metadata
**Responsibilities**:
- Create episode directory structure
- Generate appropriate file names from section_id
- Track generated files and metadata
- Handle file system operations

**Key Classes**:
```python
class AudioFileManager:
    def __init__(self, content_root: str)
    def create_episode_structure(self, episode_info: EpisodeInfo) -> str
    def get_audio_output_path(self, episode_path: str, section_id: str) -> str
    def save_generation_metadata(self, results: List[GenerationResult]) -> str
    def validate_output_directory(self, path: str) -> bool

class GenerationResult:
    section_id: str
    section_type: str
    audio_file_path: str
    success: bool
    error_message: str
    generation_time: float
    file_size: int
```

### Module 4: Batch Processor
**File**: `Code/Audio_Generation/batch_processor.py`

**Purpose**: Process multiple sections and coordinate the pipeline
**Responsibilities**:
- Orchestrate the full audio generation pipeline
- Process all audio sections from parsed JSON
- Handle errors and continue processing
- Generate comprehensive reports

**Key Classes**:
```python
class AudioBatchProcessor:
    def __init__(self, config_path: str)
    def process_episode_script(self, script_path: str) -> ProcessingReport
    def process_audio_sections(self, sections: List[AudioSection], output_dir: str) -> List[GenerationResult]
    def _process_single_section(self, section: AudioSection, output_dir: str) -> GenerationResult
    def generate_processing_report(self, results: List[GenerationResult]) -> ProcessingReport

class ProcessingReport:
    episode_info: EpisodeInfo
    total_sections: int
    successful_sections: int
    failed_sections: int
    generated_files: List[str]
    errors: List[str]
    processing_time: float
    output_directory: str
```

### Module 5: CLI Interface
**File**: `Code/Audio_Generation/cli.py`

**Purpose**: Command-line interface for manual and batch processing
**Responsibilities**:
- Provide user-friendly CLI for script processing
- Support batch discovery and processing
- Allow configuration overrides
- Display progress and results

**Key Features**:
```python
class AudioGenerationCLI:
    def run_single_script(self, script_path: str, options: Dict) -> None
    def run_batch_processing(self, content_root: str, options: Dict) -> None
    def discover_pending_scripts(self, content_root: str) -> List[str]
    def display_processing_progress(self, current: int, total: int, section: str) -> None
```

**Usage Examples**:
```powershell
# Process single script
python -m Code.Audio_Generation.cli --script "path/to/debug_gemini_response.txt"

# Process all scripts in content directory
python -m Code.Audio_Generation.cli --batch --content-root "Content/"

# Override voice and add custom processing options
python -m Code.Audio_Generation.cli --script "script.txt" --voice "Algenib" --concurrent 2 --retry 3
```

### Module 6: Configuration Manager
**File**: `Code/Audio_Generation/config.py`

**Purpose**: Handle configuration loading and validation
**Responsibilities**:
- Load TTS configuration from existing config files
- Validate configuration parameters
- Provide default values and overrides
- Support multiple TTS providers

**Key Classes**:
```python
class AudioGenerationConfig:
    def __init__(self, config_path: str = None)
    def load_gemini_config(self) -> GeminiConfig
    def load_api_keys(self) -> Dict[str, str]
    def get_audio_settings(self) -> AudioSettings
    def validate_configuration(self) -> ConfigValidation

class GeminiConfig:
    model: str = "gemini-2.5-flash-preview-tts"
    voice_name: str = "Algenib"
    audio_format: str = "wav"
    sample_rate: int = 24000
    channels: int = 1
    sample_width: int = 2

class AudioSettings:
    max_concurrent: int = 3
    retry_attempts: int = 2
    delay_between_requests: float = 1.5
    tone_instruction_prefix: str = "Say with this tone - "
    fallback_tone: str = "a natural conversational tone"
```

## Implementation Plan

### Phase 1: Core Infrastructure (Days 1-2)
1. **Create module structure** in `Code/Audio_Generation/`
2. **Implement Configuration Manager** - Reuse existing API keys and settings
3. **Build JSON Parser** - Handle new format parsing and validation
4. **Create TTS Engine** - Core Gemini API integration with tone support

### Phase 2: File Management and Processing (Days 3-4)
1. **Implement Audio File Manager** - Directory structure and file operations
2. **Build Batch Processor** - Coordinate pipeline and error handling
3. **Integration testing** - Test with sample JSON files

### Phase 3: CLI and Enhancement (Days 5-6)
1. **Create CLI Interface** - User-friendly command-line tool
2. **Add batch discovery** - Automatically find pending scripts
3. **Comprehensive error handling** - Robust failure recovery
4. **Performance optimization** - Concurrent processing and rate limiting

### Phase 4: Testing and Documentation (Day 7)
1. **End-to-end testing** - Test with real episode files
2. **Performance validation** - Test with multiple files
3. **Documentation** - API docs and usage examples
4. **Integration validation** - Ensure compatibility with existing project structure

## Key Features and Benefits

### Clean Architecture Benefits
- **No Legacy Code**: Built specifically for new JSON format
- **Modern Patterns**: Clean separation of concerns and testable design
- **Extensible**: Easy to add new TTS providers or features
- **Maintainable**: Clear module boundaries and responsibilities

### Advanced Features
- **Flexible Tone Processing**: Any natural language tone description
- **Section Filtering**: Automatic skipping of video_clip sections
- **Robust Error Handling**: Continue processing on individual failures
- **Concurrent Processing**: Process multiple sections simultaneously
- **Progress Tracking**: Real-time processing status and reporting
- **Validation**: Comprehensive input validation and error detection

### Configuration and Integration
- **Reuse Existing Config**: Leverage current Gemini API keys and settings
- **Episode Structure**: Compatible with existing Content/ directory structure
- **File Organization**: Uses existing file_organizer.py patterns for consistency

## Dependencies

### Required Packages
```python
# Core dependencies (install via pip)
google-genai>=0.1.0    # Gemini API
pathlib               # File path handling (standard library)
json                  # JSON processing (standard library)
wave                  # Audio file creation (standard library)
argparse              # CLI interface (standard library)
logging               # Logging and debugging (standard library)
asyncio               # Concurrent processing (standard library)
dataclasses           # Data structures (standard library)
typing                # Type hints (standard library)
```

### External Dependencies
- **Gemini API Access**: Use existing API key from `Code/Config/default_config.yaml`
- **Content Directory Structure**: Compatible with existing `Content/` organization
- **Episode Directory Pattern**: Follows existing series/episode structure

## Testing Strategy

### Unit Tests
- JSON parsing accuracy with various input formats
- TTS engine functionality with different tone descriptions
- File manager directory creation and organization
- Configuration loading and validation

### Integration Tests
- Full pipeline with sample Gemini response files
- Error handling with malformed inputs
- Concurrent processing with multiple sections
- File system operations and cleanup

### End-to-End Tests
- Process real episode files with multiple sections
- Verify audio file quality and organization
- Test CLI interface with various options
- Performance testing with large batches

## Success Criteria

1. **Functional Requirements**:
   - ✅ Parse new JSON format with `podcast_sections[]`
   - ✅ Filter out `video_clip` sections automatically
   - ✅ Generate high-quality audio with flexible tone descriptions
   - ✅ Organize files in proper episode directory structure
   - ✅ Handle errors gracefully and continue processing

2. **Quality Requirements**:
   - ✅ Clean, maintainable code with clear module separation
   - ✅ Comprehensive error handling and logging
   - ✅ Efficient processing with concurrent capabilities
   - ✅ User-friendly CLI interface

3. **Integration Requirements**:
   - ✅ Compatible with existing project structure
   - ✅ Reuse existing configuration and API keys
   - ✅ Follow established patterns for file organization

## Future Enhancements

### Phase 2 Considerations
- **Multiple TTS Providers**: Add OpenAI, Azure, or other TTS services
- **Voice Cloning**: Support for custom voice models
- **Audio Post-Processing**: Normalization, noise reduction, effects
- **Real-Time Monitoring**: Web dashboard for processing status
- **Advanced Scheduling**: Queue management and batch scheduling
- **Quality Metrics**: Audio quality analysis and optimization

## Risk Mitigation

### Development Risks
- **API Rate Limiting**: Implement request throttling and retry logic
- **File System Issues**: Handle permissions, disk space, and path length limitations
- **Audio Quality**: Validate generated files and implement quality checks
- **Configuration Issues**: Robust error handling for missing or invalid config

### Operational Risks
- **Scalability**: Design for processing large numbers of episodes
- **Reliability**: Comprehensive error recovery and logging
- **Performance**: Optimize for speed while maintaining quality
- **Maintenance**: Clear documentation and modular design for easy updates

## Implementation Timeline

**Total Estimate**: 7 days for complete implementation

- **Days 1-2**: Core infrastructure and TTS engine
- **Days 3-4**: File management and batch processing
- **Days 5-6**: CLI interface and optimization
- **Day 7**: Testing, documentation, and validation

This fresh implementation approach provides a clean, modern solution specifically designed for the new JSON format while maintaining compatibility with the existing project structure and configuration.