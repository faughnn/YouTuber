# ElevenLabs TTS Integration

This module provides ElevenLabs Text-to-Speech integration for the YouTuber pipeline.

## Setup

1. **Install Dependencies**:
   ```bash
   pip install elevenlabs>=0.2.0
   ```

2. **Set API Key**:
   Set your ElevenLabs API key as an environment variable:
   ```bash
   set ELEVENLABS_API_KEY=your_api_key_here
   ```

## Usage

The ElevenLabs TTS engine is automatically available when you run the pipeline and select Stage 5 (Audio Generation). You'll be prompted to choose between Chatterbox TTS and ElevenLabs TTS at the start of pipeline execution.

### Voice Configuration

The voice is hardcoded to use voice ID `0DxQtWphUO5YNcF7UOm1` (Aria) with the following settings:
- **Speed**: 1.00
- **Stability**: 50%
- **Similarity**: 75%
- **Style**: 0% (default)

### Audio Output

- **Format**: MP3 (matching Chatterbox output)
- **Naming**: Identical to Chatterbox files for seamless pipeline integration
- **Quality**: High-quality ElevenLabs voice synthesis

## Error Handling

If ElevenLabs API fails, the pipeline will fail with the raw API error message. There is no fallback to Chatterbox TTS.

## Configuration Files

- `elevenlabs_tts_engine.py` - Main TTS engine class
- `config_elevenlabs.py` - Configuration constants
- `__init__.py` - Package initialization
