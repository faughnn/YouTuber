# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Running the Pipeline
```bash
# Interactive menu (recommended for development)
python run_pipeline.py

# Direct CLI usage
python Code/master_processor_v2.py "https://youtube.com/watch?v=..." --full-pipeline
python Code/master_processor_v2.py "https://youtube.com/watch?v=..." --audio-only --tts-provider elevenlabs
python Code/master_processor_v2.py "https://youtube.com/watch?v=..." --script-only
```

### Testing
```bash
# Run specific module tests
python -m pytest Code/Chatterbox/tests/test_master_processor_stage5.py
python -m pytest Code/Chatterbox/tests/test_pipeline_integration.py

# Run quality control tests
python -m pytest Code/Content_Analysis/test_rebuttal_verifier.py
```

### Installation
```bash
pip install -r requirements.txt
```

## Architecture Overview

This is a 7-stage YouTube video processing pipeline that transforms YouTube content into polished video compilations:

1. **Media Extraction** - Downloads audio/video from YouTube
2. **Transcript Generation** - Creates speaker-diarized transcripts  
3. **Content Analysis** - AI-powered analysis using Google Gemini API
4. **Narrative Generation** - Creates engaging podcast-style scripts
5. **Audio Generation** - TTS using Chatterbox (local) or ElevenLabs (cloud)
6. **Video Clipping** - Extracts relevant video segments
7. **Video Compilation** - Combines audio and video into final output

### Entry Points
- `run_pipeline.py` - Root launcher with interactive menu
- `Code/run_pipeline_menu.py` - Menu system implementation
- `Code/master_processor_v2.py` - Main orchestrator (CLI and programmatic)

### Content Organization
Episodes are organized as: `Content/{Host_Name}/{Host_Guest_Episode}/`
- `Input/` - Downloaded media and metadata
- `Processing/` - Intermediate analysis files  
- `Output/` - Generated audio, scripts, clips, final videos

## Key Architectural Patterns

### Pipeline-Driven Orchestration
- Direct delegation to working modules without abstraction layers
- Orchestrator adapts to modules, not vice versa
- Working modules define interaction patterns

### Enhanced Logging System
- Rich-based visual progress indicators
- Hierarchical stage contexts with specialized loggers
- Located in `Code/Utils/enhanced_pipeline_logger.py`

### Two-Pass AI Quality Control (Recent Addition)
- Pass 1: Initial content analysis
- Pass 2: 5-dimension quality assessment and filtering
- Automated rebuttal verification and rewriting
- Modules: `quality_assessor.py`, `rebuttal_verifier_rewriter.py`, `two_pass_controller.py`

### Automatic Service Management
- Chatterbox TTS server lifecycle management (startup/shutdown)
- Health checks and cleanup in `master_processor_v2.py`

## Configuration System

### Central Configuration: `Code/Config/default_config.yaml`
- API keys (Gemini, HuggingFace, ElevenLabs)
- Processing parameters (Whisper model, batch sizes)
- TTS settings (voice, speaking rate, device preferences)  
- File paths and episode organization

### Environment Override Pattern
API keys can be set via environment variables:
- `GEMINI_API_KEY`
- `HUGGINGFACE_TOKEN`
- `ELEVENLABS_API_KEY`

## Module Structure

### Core Processing Modules
- `Code/Extraction/` - YouTube download and audio diarization
- `Code/Content_Analysis/` - AI analysis and narrative generation
- `Code/Chatterbox/` - Local TTS engine
- `Code/ElevenLabs/` - Cloud TTS integration
- `Code/Video_Clipper/` - Video segment extraction
- `Code/Video_Compilator/` - Final video compilation

### Utility Infrastructure
- `Code/Utils/` - Logging, configuration, file management, validation
- Schema validation via `json_schema_validator.py`
- Episode organization via `file_organizer.py`
- Name extraction from YouTube metadata

### Testing Infrastructure
- Module-level tests in `{Module}/tests/`
- Integration tests using real episode data
- Performance benchmarking
- JSON schema validation testing

## Development Guidelines

### Working with This Codebase
- Use `run_pipeline.py` for testing workflows
- All modules expect episode directory structure
- JSON schemas define data format contracts between stages
- New modules should follow direct-delegation pattern

### Adding New Features
- Configuration changes go in `default_config.yaml`
- New stages integrate with `master_processor_v2.py`
- Add comprehensive tests following existing patterns
- Use Rich logging system for user feedback

### Key Integration Points
- Episode metadata flows through `unified_podcast_script.json`
- Quality control uses `verified_unified_script.json` 
- All video processing expects FFmpeg availability
- TTS modules use unified interface with progress callbacks

### Recent Quality Control System
The Two-Pass AI Quality Control system adds:
- 5-dimension quality scoring (Quote Strength, Factual Accuracy, Potential Impact, Content Specificity, Context Appropriateness)
- Evidence-based segment filtering and selection
- Automated rebuttal fact-checking and rewriting
- Maintains backward compatibility with existing pipeline