# Chatterbox TTS Module

A local Text-to-Speech module for the YouTube video processing pipeline, replacing the Gemini TTS API with local Chatterbox TTS capabilities.

## Overview

This module provides a complete TTS solution using Chatterbox TTS models for generating high-quality speech audio from text content. It integrates seamlessly with the existing YouTube video processing workflow, specifically replacing Stage 5 (Audio Generation) with local TTS processing.

## Module Structure

```
Code/Chatterbox/
├── __init__.py                 # Module initialization and exports
├── config.py                   # Configuration classes and settings
├── tts_engine.py              # Core TTS processing engine
├── json_parser.py             # JSON content parsing for TTS requests
├── audio_file_manager.py      # Audio file management and organization
├── batch_processor.py         # Batch processing and queue management
├── TrainingSamples/           # Voice model files
│   └── Harvard1_2.wav         # Primary voice model
└── README.md                  # This documentation file
```

## Key Components

### TTSEngine (`tts_engine.py`)
- Core text-to-speech processing engine
- Manages Chatterbox TTS model loading and inference
- Handles speech generation with configurable parameters
- Optimized for YouTube content processing

### JSONParser (`json_parser.py`)
- Processes JSON data from the video processing pipeline
- Extracts text segments for TTS generation
- Creates structured TTS requests with metadata
- Validates input data format

### AudioFileManager (`audio_file_manager.py`)
- Manages generated audio files and metadata
- Organizes output files for pipeline integration
- Handles file validation and cleanup
- Provides audio file analysis capabilities

### BatchProcessor (`batch_processor.py`)
- Manages batch processing of multiple TTS requests
- Implements parallel processing for efficiency
- Provides progress tracking and error handling
- Supports cancellation and status monitoring

## Configuration

The module uses a comprehensive configuration system defined in `config.py`:

### ChatterboxParameters
- `exaggeration`: 0.7 (optimal tested value)
- `temperature`: 0.5 (optimal tested value)  
- `cfg_weight`: 0.7 (optimal tested value)

### ChatterboxConfig
- Voice model path: `TrainingSamples/Harvard1_2.wav`
- Device preference: CUDA/MPS/CPU auto-detection
- Performance settings and timeouts
- Optional tone mapping capabilities

## Usage

### Basic Usage
```python
from Code.Chatterbox import ChatterboxConfig, TTSEngine

# Initialize with default configuration
config = ChatterboxConfig()
tts_engine = TTSEngine(config)

# Load the TTS model
tts_engine.load_model()

# Generate speech
audio_path = tts_engine.generate_speech("Hello, this is a test.")
```

### Batch Processing
```python
from Code.Chatterbox import BatchProcessor, JSONParser

# Parse content for TTS requests
parser = JSONParser()
requests = parser.parse_content_file("content.json")

# Process batch
processor = BatchProcessor()
results = processor.process_batch(requests)
```

## Integration with Video Pipeline

This module integrates with the YouTube video processing pipeline at Stage 5 (Audio Generation):

1. **Input**: Processed JSON content from earlier pipeline stages
2. **Processing**: Text extraction, TTS generation, audio file management
3. **Output**: Organized audio files ready for video compilation

## Voice Model

The module uses `Harvard1_2.wav` as the primary voice model, located in `TrainingSamples/`. This model has been tested and optimized for YouTube content generation.

## Performance Considerations

- **Local Processing**: No API calls or network dependencies
- **Model Caching**: Keeps TTS model loaded in memory for efficiency
- **Batch Processing**: Supports parallel processing of multiple requests
- **Resource Management**: Automatic cleanup of temporary files

## Development Status

**Current Phase**: Directory Structure Setup (Phase 1, Task 1.2)

### Completed
- ✅ Directory structure created
- ✅ Voice model file copied and verified
- ✅ Python module initialization
- ✅ Placeholder component files with proper structure
- ✅ Configuration system verified
- ✅ Documentation framework established

### Next Steps
- Implementation of core TTS engine functionality
- JSON parsing for video pipeline integration
- Audio file management system
- Batch processing implementation
- Testing and validation

## Requirements

- Python 3.8+
- Chatterbox TTS dependencies (to be added during implementation)
- CUDA/PyTorch for GPU acceleration (optional)
- Audio processing libraries (to be specified)

## Testing

A verification script will be created to test:
- Module import functionality
- Voice model file accessibility
- Basic configuration loading
- Directory structure validation

## Contributing

This module follows the APM (Agentic Project Management) development process. All changes should be logged in the Memory Bank and follow the established task assignment workflow.

## License

Part of the YouTuber Project - see main project license.
