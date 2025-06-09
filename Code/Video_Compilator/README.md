# Video Compilator

A streamlined video compilation system that converts audio segments to video (with static backgrounds) and seamlessly concatenates them with video clips using the proven working FFmpeg concatenation technique.

## Overview

Based on successful testing of the simple FFmpeg concatenation technique, this system implements:

1. **Convert Audio to Video**: Create video segments from TTS audio files using Chris Morris background image
2. **Standardize Formats**: Ensure all segments have consistent video/audio parameters
3. **Sequential Concatenation**: Use FFmpeg's concat filter to join segments in sequence

## Key Features

- ✅ **Proven Working Method**: Based on successful 56-second audio + 19-second video test
- ✅ **No Video Re-encoding**: Original video files remain untouched for quality preservation
- ✅ **Static Background**: Uses Chris Morris "bloody hell" image for audio segments
- ✅ **Format Standardization**: 1920x1080 resolution, 44.1kHz stereo audio
- ✅ **Automatic Format Handling**: FFmpeg concat filter handles differences automatically

## Installation

No installation required - just ensure you have:

- **FFmpeg** installed and available in your PATH
- **Python 3.8+** with standard library

## Quick Start

### Basic Usage

```python
from pathlib import Path
from Video_Compilator import SimpleCompiler

# Initialize compiler
compiler = SimpleCompiler()

# Compile episode
episode_path = Path("Content/Joe_Rogan_Experience/Episode_Directory")
result = compiler.compile_episode(episode_path)

if result.success:
    print(f"✓ Video compiled: {result.output_path}")
    print(f"Duration: {result.duration}s, Size: {result.file_size/1024/1024:.1f}MB")
else:
    print(f"✗ Compilation failed: {result.error}")
```

### Command Line Interface

```bash
# Compile an episode
python cli.py compile "C:/path/to/episode/directory"

# Compile with custom output name
python cli.py compile "C:/path/to/episode" --output "my_episode.mp4"

# List available episodes
python cli.py list

# Compile with verbose logging
python cli.py compile "C:/path/to/episode" --verbose --keep-temp
```

## Expected Directory Structure

```
Episode_Directory/
├── Scripts/
│   └── unified_podcast_script.json     # Episode script (preferred)
├── Audio/ (or Output/Audio/)
│   ├── intro_001.wav                   # TTS audio files
│   ├── narration_001.wav
│   └── outro_001.wav
└── Video/ (or Output/Video/)
    ├── clip_001.mp4                    # Video clips
    └── clip_002.mp4
```

## Processing Workflow

### Phase 1: Audio-to-Video Conversion
```
[1/2] Converting audio segments to video...
├── Converting intro_001.wav → seg_001_intro.mp4 (Chris Morris image + audio)
├── Converting narration_001.wav → seg_002_narration.mp4 (Chris Morris image + audio)
└── ✓ Audio segments converted (original video files UNTOUCHED)
```

### Phase 2: Direct Concatenation
```
[2/2] Concatenating all segments directly...
├── Building sequence: seg_001_intro → clip_001.mp4 → seg_002_narration → clip_002.mp4
├── Using concat filter (exactly like successful test)
├── Letting concat filter handle format differences automatically
└── ✓ Final video: Episode_compiled.mp4
```

## Components

### AudioToVideoConverter
Converts TTS audio files to video segments with static backgrounds.

```python
from Video_Compilator import AudioToVideoConverter

converter = AudioToVideoConverter()
success = converter.convert_audio_segment(
    audio_path=Path("audio.wav"),
    output_path=Path("audio_as_video.mp4")
)
```

### DirectConcatenator
Concatenates video segments using FFmpeg's concat filter.

```python
from Video_Compilator import DirectConcatenator

concatenator = DirectConcatenator()
result = concatenator.concatenate_mixed_segments(
    segment_sequence=[Path("seg1.mp4"), Path("seg2.mp4")],
    output_path=Path("final.mp4")
)
```

### SimpleCompiler
Main orchestration class that handles the complete workflow.

```python
from Video_Compilator import SimpleCompiler

compiler = SimpleCompiler(
    keep_temp_files=True,     # Keep intermediate files for debugging
    validate_segments=True    # Validate segments before concatenation
)
```

## Configuration

### Video Standards
- **Resolution**: 1920x1080
- **Frame Rate**: 29.97 fps
- **Codec**: libx264

### Audio Standards
- **Sample Rate**: 44.1kHz
- **Channels**: 2 (stereo)
- **Codec**: AAC

### Background Image
- **Path**: `Assets/Chris_Morris_Images/bloody_hell.jpg`
- **Usage**: Static background for audio-to-video conversion

## Testing

Run the test suite to validate the installation:

```bash
python test_video_compilator.py
```

## Troubleshooting

### Common Issues

1. **FFmpeg not found**
   - Ensure FFmpeg is installed and in your system PATH
   - Test with: `ffmpeg -version`

2. **Background image not found**
   - Verify the Chris Morris image exists at the expected path
   - Path: `C:/Users/nfaug/OneDrive - LIR/Desktop/YouTuber/Assets/Chris_Morris_Images/bloody_hell.jpg`

3. **Audio files not found**
   - Check that audio files exist in `Audio/` or `Output/Audio/` directories
   - Supported formats: `.wav`, `.mp3`, `.aac`, `.m4a`

4. **Video files not found**
   - Check that video files exist in `Video/` or `Output/Video/` directories
   - Supported formats: `.mp4`, `.avi`, `.mov`, `.mkv`

### Debug Mode

Enable verbose logging and keep temporary files:

```python
compiler = SimpleCompiler(keep_temp_files=True, validate_segments=True)
# Or via CLI:
# python cli.py compile episode_path --verbose --keep-temp
```

## Performance

### Typical Processing Times
- **Audio-to-Video**: ~2-3x real-time (e.g., 60s audio → 2-3 minutes processing)
- **Concatenation**: ~1-2 minutes for typical episode
- **Memory Usage**: Minimal (streaming processing)

### Optimization Tips
- Use SSD storage for temp files
- Ensure sufficient disk space (2-3x final video size)
- Close other video editing applications during processing

## Why This Approach Works

### Proven in Live Testing
- ✅ Direct validation with real files (intro_001.wav + video_clip_001.mp4)
- ✅ No video file modification preserves original quality
- ✅ Concat filter automatically handles format differences
- ✅ Simple, fast, and reliable

### Technical Advantages
- **No Re-encoding**: Original video quality preserved
- **Format Flexibility**: Concat filter handles differences automatically
- **Speed**: Minimal processing overhead
- **Reliability**: Based on proven FFmpeg techniques

## License

This project is part of the YouTuber automation system.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Run tests with `python test_video_compilator.py`
3. Use verbose mode for detailed error information
