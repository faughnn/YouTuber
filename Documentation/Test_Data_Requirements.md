# Test Data Requirements - YouTube Content Processing Pipeline

**Created:** June 5, 2025  
**Purpose:** Comprehensive specification of test fixtures, sample data, and mock services required for testing  
**Target:** Support 90%+ test coverage across all pipeline stages  

## 📋 Overview

This document specifies all test data, fixtures, and mock services required to implement comprehensive testing for the YouTube content processing pipeline. Currently, the `tests/fixtures/` directory is empty, representing a critical gap in test infrastructure.

### Current State
```
tests/fixtures/     # ❌ COMPLETELY EMPTY
└── (no files)      # No test data exists
```

### Target State
```
tests/fixtures/
├── youtube_urls/           # YouTube URL test cases
├── audio_files/           # Sample audio files
├── video_files/           # Sample video files  
├── transcripts/           # Sample transcript data
├── analysis_data/         # Sample analysis results
├── configs/               # Configuration variants
├── episode_structures/    # File organization samples
└── mock_responses/        # API response mocks
```

---

## 🔗 YouTube URL Test Data

### Valid YouTube URLs
**File:** `tests/fixtures/youtube_urls/valid_urls.json`

```json
{
  "standard_urls": [
    {
      "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
      "video_id": "dQw4w9WgXcQ",
      "title": "Rick Astley - Never Gonna Give You Up",
      "description": "Standard YouTube URL format"
    },
    {
      "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
      "video_id": "dQw4w9WgXcQ", 
      "title": "Rick Astley - Never Gonna Give You Up",
      "description": "Without www prefix"
    }
  ],
  "short_urls": [
    {
      "url": "https://youtu.be/dQw4w9WgXcQ",
      "video_id": "dQw4w9WgXcQ",
      "title": "Rick Astley - Never Gonna Give You Up",
      "description": "Short URL format"
    }
  ],
  "embed_urls": [
    {
      "url": "https://www.youtube.com/embed/dQw4w9WgXcQ",
      "video_id": "dQw4w9WgXcQ",
      "title": "Rick Astley - Never Gonna Give You Up", 
      "description": "Embed URL format"
    }
  ],
  "mobile_urls": [
    {
      "url": "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
      "video_id": "dQw4w9WgXcQ",
      "title": "Rick Astley - Never Gonna Give You Up",
      "description": "Mobile URL format"
    }
  ],
  "shorts_urls": [
    {
      "url": "https://www.youtube.com/shorts/dQw4w9WgXcQ",
      "video_id": "dQw4w9WgXcQ", 
      "title": "Sample YouTube Short",
      "description": "YouTube Shorts format"
    }
  ],
  "urls_with_params": [
    {
      "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=30s",
      "video_id": "dQw4w9WgXcQ",
      "title": "Rick Astley - Never Gonna Give You Up",
      "description": "URL with timestamp parameter"
    },
    {
      "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ&feature=share",
      "video_id": "dQw4w9WgXcQ",
      "title": "Rick Astley - Never Gonna Give You Up", 
      "description": "URL with share parameter"
    }
  ],
  "direct_video_ids": [
    {
      "url": "dQw4w9WgXcQ",
      "video_id": "dQw4w9WgXcQ",
      "title": "Rick Astley - Never Gonna Give You Up",
      "description": "Direct video ID"
    }
  ]
}
```

### Invalid YouTube URLs
**File:** `tests/fixtures/youtube_urls/invalid_urls.json`

```json
{
  "wrong_platform": [
    {
      "url": "https://vimeo.com/123456789",
      "expected_error": "Invalid YouTube URL",
      "description": "Vimeo URL instead of YouTube"
    },
    {
      "url": "https://twitch.tv/example",
      "expected_error": "Invalid YouTube URL", 
      "description": "Twitch URL instead of YouTube"
    }
  ],
  "malformed_urls": [
    {
      "url": "not_a_url_at_all",
      "expected_error": "Invalid YouTube URL",
      "description": "Not a URL format"
    },
    {
      "url": "https://youtube.com/watch?v=",
      "expected_error": "Invalid YouTube URL",
      "description": "Missing video ID"
    },
    {
      "url": "https://youtube.com/watch",
      "expected_error": "Invalid YouTube URL", 
      "description": "Missing video parameter"
    }
  ],
  "invalid_video_ids": [
    {
      "url": "aBcDeFgHiJk",
      "expected_error": "Invalid video ID length",
      "description": "10 characters (too short)"
    },
    {
      "url": "aBcDeFgHiJkL1",
      "expected_error": "Invalid video ID length", 
      "description": "12 characters (too long)"
    },
    {
      "url": "invalid@chars!",
      "expected_error": "Invalid video ID format",
      "description": "Invalid characters in ID"
    }
  ]
}
```

### Playlist URLs 
**File:** `tests/fixtures/youtube_urls/playlist_urls.json`

```json
{
  "playlist_with_video": [
    {
      "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLrZ9z-FXWr8dQw4w9WgXcQ&index=1",
      "expected_video_id": "dQw4w9WgXcQ",
      "description": "Playlist URL with specific video"
    }
  ],
  "pure_playlists": [
    {
      "url": "https://www.youtube.com/playlist?list=PLrZ9z-FXWr8dQw4w9WgXcQ",
      "expected_behavior": "extract_first_video", 
      "description": "Pure playlist URL"
    }
  ]
}
```

---

## 🎵 Audio File Test Data

### Sample Audio Files
**Directory:** `tests/fixtures/audio_files/`

#### Valid Audio Files
```
valid_audio/
├── sample_short.mp3        # 10 seconds, 128kbps
├── sample_medium.wav       # 2 minutes, 16-bit/44.1kHz  
├── sample_long.flac        # 10 minutes, lossless
├── sample_podcast.m4a      # 30 minutes, speech content
├── sample_music.aac        # 3 minutes, music content
├── sample_speech.ogg       # 5 minutes, single speaker
└── sample_dialogue.mp3     # 8 minutes, multiple speakers
```

#### Edge Case Audio Files
```
edge_cases/
├── empty_file.mp3          # 0 bytes
├── very_small.mp3          # < 1KB
├── corrupted_header.mp3    # Invalid MP3 header
├── wrong_extension.txt     # Text file with .mp3 extension
├── unicode_name_测试.mp3   # Unicode characters in filename
├── spaces in name.mp3      # Spaces in filename
└── very_long_filename_that_exceeds_normal_limits.mp3
```

#### File Properties Reference
**File:** `tests/fixtures/audio_files/file_properties.json`

```json
{
  "sample_short.mp3": {
    "duration_seconds": 10,
    "file_size_bytes": 160000,
    "format": "mp3",
    "bitrate": "128kbps",
    "sample_rate": "44100Hz",
    "channels": 2,
    "description": "Short test audio for quick tests"
  },
  "sample_medium.wav": {
    "duration_seconds": 120,
    "file_size_bytes": 21168000,
    "format": "wav", 
    "bitrate": "1411kbps",
    "sample_rate": "44100Hz",
    "channels": 2,
    "description": "Medium duration uncompressed audio"
  },
  "corrupted_header.mp3": {
    "expected_error": "Corrupted or unreadable file",
    "description": "File with invalid MP3 header for error testing"
  }
}
```

---

## 🎬 Video File Test Data

### Sample Video Files
**Directory:** `tests/fixtures/video_files/`

```
video_samples/
├── sample_short.mp4        # 30 seconds, 720p
├── sample_medium.mp4       # 5 minutes, 1080p
├── sample_long.mp4         # 20 minutes, 720p (for performance testing)
├── sample_4k.mp4           # 1 minute, 4K (large file testing)
├── sample_no_audio.mp4     # Video without audio track
└── sample_corrupted.mp4    # Corrupted video file
```

#### Video Properties Reference
**File:** `tests/fixtures/video_files/video_properties.json`

```json
{
  "sample_short.mp4": {
    "duration_seconds": 30,
    "resolution": "1280x720",
    "fps": 30,
    "file_size_mb": 25,
    "has_audio": true,
    "codec": "H.264",
    "description": "Short video for basic testing"
  },
  "sample_no_audio.mp4": {
    "duration_seconds": 60,
    "resolution": "1920x1080", 
    "fps": 30,
    "file_size_mb": 45,
    "has_audio": false,
    "expected_error": "No audio track available",
    "description": "Video without audio for error testing"
  }
}
```

---

## 📝 Transcript Test Data

### Sample Transcripts
**Directory:** `tests/fixtures/transcripts/`

#### Valid Transcript Files
```
valid_transcripts/
├── simple_transcript.json          # Basic 2-speaker conversation
├── complex_transcript.json         # Multiple speakers, overlaps
├── single_speaker.json             # Monologue/lecture format
├── interview_transcript.json       # Q&A format
└── podcast_transcript.json         # Podcast with intro/outro
```

#### Sample Transcript Structure
**File:** `tests/fixtures/transcripts/simple_transcript.json`

```json
{
  "segments": [
    {
      "start": 0.0,
      "end": 5.2,
      "text": "Hello and welcome to today's episode.",
      "speaker": "SPEAKER_00"
    },
    {
      "start": 5.5,
      "end": 10.8, 
      "text": "Thanks for having me on the show.",
      "speaker": "SPEAKER_01"
    },
    {
      "start": 11.0,
      "end": 18.3,
      "text": "Let's dive right into the main topic we wanted to discuss today.",
      "speaker": "SPEAKER_00"
    }
  ],
  "speakers": {
    "SPEAKER_00": {
      "name": "Host",
      "segments": 2
    },
    "SPEAKER_01": {
      "name": "Guest", 
      "segments": 1
    }
  },
  "metadata": {
    "total_duration": 18.3,
    "total_segments": 3,
    "speaker_count": 2,
    "source": "test_audio"
  }
}
```

#### Invalid Transcript Files
```
invalid_transcripts/
├── malformed_json.json             # Invalid JSON syntax
├── missing_required_fields.json    # Missing speaker or text fields
├── invalid_timestamps.json         # Negative or overlapping times
├── empty_transcript.json           # Empty segments array
└── corrupted_transcript.json       # Partially corrupted data
```

---

## 🧠 Analysis Data Test Fixtures

### Sample Analysis Results
**Directory:** `tests/fixtures/analysis_data/`

#### Complete Analysis Files
```
analysis_results/
├── podcast_analysis.json           # Complete podcast analysis
├── interview_analysis.json         # Interview format analysis  
├── lecture_analysis.json           # Educational content analysis
└── conversation_analysis.json      # Casual conversation analysis
```

#### Sample Analysis Structure
**File:** `tests/fixtures/analysis_data/podcast_analysis.json`

```json
{
  "summary": {
    "main_topics": [
      "Technology trends",
      "Artificial intelligence", 
      "Future predictions"
    ],
    "key_insights": [
      "AI will transform content creation",
      "Human creativity remains essential"
    ],
    "duration_minutes": 45
  },
  "speakers": [
    {
      "id": "SPEAKER_00",
      "role": "Host",
      "speaking_time": 1200,
      "personality": "Curious, engaging"
    },
    {
      "id": "SPEAKER_01", 
      "role": "Expert Guest",
      "speaking_time": 1500,
      "personality": "Knowledgeable, thoughtful"
    }
  ],
  "segments": [
    {
      "start_time": 0,
      "end_time": 300,
      "topic": "Introduction",
      "importance": "medium",
      "summary": "Host introduces guest and topic"
    },
    {
      "start_time": 300,
      "end_time": 1800,
      "topic": "AI in Content Creation", 
      "importance": "high",
      "summary": "Discussion of current AI capabilities"
    }
  ],
  "clips": [
    {
      "start_time": 450,
      "end_time": 480,
      "reason": "Key insight about AI limitations",
      "importance": "high"
    }
  ]
}
```

---

## ⚙️ Configuration Test Data

### Configuration Variants
**Directory:** `tests/fixtures/configs/`

```
config_variants/
├── minimal_config.yaml             # Minimal required settings
├── full_config.yaml                # All possible settings
├── invalid_config.yaml             # Invalid settings for error testing
├── missing_keys_config.yaml        # Missing required keys
└── tts_config.yaml                 # TTS-specific configuration
```

#### Sample Configuration Files
**File:** `tests/fixtures/configs/minimal_config.yaml`

```yaml
# Minimal configuration for testing
output_base_path: "test_output"
processing_stages: [1, 2, 3, 4, 5]

apis:
  huggingface_token: "test_token"
  gemini_api_key: "test_key"

file_organization:
  create_episode_structure: true
  clean_filenames: true
```

**File:** `tests/fixtures/configs/invalid_config.yaml`

```yaml
# Invalid configuration for error testing
output_base_path: 12345  # Should be string
processing_stages: "invalid"  # Should be array

apis:
  # Missing required keys
  invalid_key: "value"

unknown_section:
  unexpected_key: "value"
```

---

## 📁 Episode Structure Test Data

### Sample Episode Structures
**Directory:** `tests/fixtures/episode_structures/`

```
episode_examples/
├── standard_episode/               # Complete episode structure
│   ├── Input/
│   │   ├── original_audio.mp3
│   │   └── original_video.mp4
│   ├── Processing/
│   │   ├── transcript.json
│   │   └── analysis.json
│   └── Output/
│       ├── Audio/
│       ├── Scripts/
│       ├── Video/
│       └── Timelines/
├── audio_only_episode/             # Audio-only processing
└── incomplete_episode/             # Partial structure for error testing
```

---

## 🔄 Mock API Responses

### Mock Service Data
**Directory:** `tests/fixtures/mock_responses/`

#### YouTube API Responses
**File:** `tests/fixtures/mock_responses/youtube_responses.json`

```json
{
  "valid_video_info": {
    "id": "dQw4w9WgXcQ",
    "title": "Rick Astley - Never Gonna Give You Up",
    "duration": "PT3M33S",
    "description": "Official music video",
    "uploader": "Rick Astley",
    "upload_date": "20091025",
    "view_count": 1400000000,
    "availability": "public"
  },
  "private_video": {
    "error": "Video unavailable",
    "reason": "Private video",
    "status_code": 403
  },
  "region_blocked": {
    "error": "Video unavailable",
    "reason": "Not available in your country",
    "status_code": 451
  },
  "video_not_found": {
    "error": "Video not found",
    "reason": "Video does not exist",
    "status_code": 404
  }
}
```

#### Gemini API Responses
**File:** `tests/fixtures/mock_responses/gemini_responses.json`

```json
{
  "successful_analysis": {
    "candidates": [
      {
        "content": {
          "parts": [
            {
              "text": "{\n  \"summary\": \"Discussion about AI trends\",\n  \"topics\": [\"AI\", \"Technology\"]\n}"
            }
          ]
        }
      }
    ]
  },
  "api_error": {
    "error": {
      "code": 429,
      "message": "Rate limit exceeded",
      "status": "RESOURCE_EXHAUSTED"
    }
  }
}
```

#### HuggingFace API Responses  
**File:** `tests/fixtures/mock_responses/huggingface_responses.json`

```json
{
  "successful_diarization": {
    "segments": [
      {
        "start": 0.0,
        "end": 5.2,
        "text": "Hello everyone",
        "speaker": "SPEAKER_00"
      }
    ]
  },
  "auth_error": {
    "error": "Invalid authentication token",
    "status_code": 401
  }
}
```

---

## 🧪 Test Data Generation Scripts

### Automated Test Data Creation
**File:** `tests/generate_test_data.py`

```python
#!/usr/bin/env python3
"""
Generate test data for YouTube content processing pipeline tests.

Usage:
    python tests/generate_test_data.py
"""

import os
import json
import yaml
import shutil
from pathlib import Path

def create_directory_structure():
    """Create the complete test fixtures directory structure."""
    base_dir = Path("tests/fixtures")
    
    directories = [
        "youtube_urls",
        "audio_files/valid_audio",
        "audio_files/edge_cases", 
        "video_files",
        "transcripts/valid_transcripts",
        "transcripts/invalid_transcripts",
        "analysis_data",
        "configs",
        "episode_structures/standard_episode/Input",
        "episode_structures/standard_episode/Processing", 
        "episode_structures/standard_episode/Output",
        "mock_responses"
    ]
    
    for directory in directories:
        (base_dir / directory).mkdir(parents=True, exist_ok=True)
        
def generate_sample_audio_files():
    """Generate sample audio files for testing."""
    # Note: This would use audio generation libraries
    # For now, create placeholder files
    audio_dir = Path("tests/fixtures/audio_files/valid_audio")
    
    # Create small test files (would be actual audio in real implementation)
    test_files = [
        "sample_short.mp3",
        "sample_medium.wav",
        "sample_long.flac"
    ]
    
    for filename in test_files:
        (audio_dir / filename).write_bytes(b"fake_audio_data")

def main():
    """Generate all test data."""
    print("Generating test data structure...")
    create_directory_structure()
    generate_sample_audio_files()
    print("Test data generation complete!")

if __name__ == "__main__":
    main()
```

---

## 📊 Data Maintenance & Updates

### Test Data Versioning
- **Version Control:** All test data files tracked in git
- **Size Limits:** Audio/video files < 10MB each for repository efficiency
- **Update Process:** Quarterly review and refresh of test data

### Automated Data Validation
```python
# Script to validate test data integrity
def validate_test_data():
    """Validate all test fixtures are present and valid."""
    required_files = [
        "youtube_urls/valid_urls.json",
        "audio_files/file_properties.json", 
        "transcripts/simple_transcript.json",
        "configs/minimal_config.yaml"
    ]
    
    for file_path in required_files:
        full_path = Path(f"tests/fixtures/{file_path}")
        assert full_path.exists(), f"Missing required test file: {file_path}"
```

### Test Data Security
- **No Real API Keys:** All API keys in test data are fake/test values
- **No Personal Data:** All names, content, and URLs are fictional or public domain
- **Safe URLs:** All YouTube URLs point to safe, appropriate content

---

*This test data specification provides the complete foundation for implementing comprehensive test coverage across the YouTube content processing pipeline. All fixtures and mock data are designed to support realistic testing scenarios while maintaining security and performance.*
