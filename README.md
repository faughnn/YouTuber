# YouTuber Pipeline

A complete YouTube video processing system that transforms YouTube content into polished podcast-style compilations with AI-powered analysis and quality control.

## 🎬 What It Does

Takes a YouTube URL and produces a professional podcast video through a 7-stage pipeline:

1. **Media Extraction** - Downloads audio/video from YouTube
2. **Transcript Generation** - Creates speaker-diarized transcripts with timestamps  
3. **AI Content Analysis** - Uses Google Gemini to identify key moments and themes
4. **Narrative Generation** - Creates engaging podcast-style scripts with commentary
5. **Audio Generation** - Converts scripts to speech using TTS (Chatterbox or ElevenLabs)
6. **Video Clipping** - Extracts relevant video segments based on analysis
7. **Video Compilation** - Combines everything into polished final video

## ✨ Key Features

- **Two-Pass AI Quality Control** - Advanced filtering system ensures only high-quality segments
- **Multiple TTS Engines** - Local Chatterbox TTS or premium ElevenLabs integration
- **Automated Fact-Checking** - Verifies and rewrites generated commentary for accuracy
- **Interactive Menu System** - User-friendly interface with Rich-formatted progress tracking
- **Smart Name Extraction** - Automatically identifies hosts and guests from YouTube metadata
- **Flexible Output Formats** - Full pipeline, audio-only, or script-only generation

## 🚀 Installation

### Prerequisites

- Python 3.9+
- FFmpeg (for video/audio processing)
- Git

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/YouTuber.git
   cd YouTuber
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up API keys**
   
   Set these environment variables:
   ```bash
   # Required for AI analysis
   export GEMINI_API_KEY="your_gemini_api_key"
   
   # Optional for better TTS diarization
   export HuggingFaceToken="your_hf_token"
   
   # Optional for premium TTS
   export ELEVENLABS_API_KEY="your_elevenlabs_key"
   ```

4. **Run the pipeline**
   ```bash
   python run_pipeline.py
   ```

## 🎮 Usage

### Interactive Menu

```bash
python run_pipeline.py
```

Follow the interactive prompts to:
- Enter YouTube URL
- Choose TTS provider (Chatterbox/ElevenLabs)
- Select pipeline mode (full/audio-only/script-only)
- Configure quality settings

## 🎤 TTS Options

### Chatterbox TTS (Local)
- **Cost**: Free
- **Setup**: Requires [Chatterbox TTS API](https://github.com/travisvn/chatterbox-tts-api) running locally
- **Voice Cloning**: Needs a short audio clip to clone voice
- **Quality**: Mediocre output, good for testing, struggles with Irish accents as it's trained on American accents
- **Management**: Pipeline automatically starts/stops the local server

### ElevenLabs TTS (Cloud)
- **Cost**: Paid subscription required
- **Setup**: Just add API key to environment variables
- **Voice Cloning**: Requires hours of audio for high-quality cloning
- **Quality**: Professional-grade, works flawlessly
- **Management**: Direct API integration, no server management needed

## 📁 Output Structure

Each processed episode creates an organized directory structure:

```
Content/
└── Host_Name/
    └── Host_Guest_Episode/
        ├── Input/                    # Downloaded media
        │   ├── original_audio.mp3
        │   └── original_video.mp4
        ├── Processing/               # Analysis results
        │   ├── original_audio_transcript.json
        │   └── original_audio_analysis_results.json
        └── Output/
            ├── Scripts/              # Generated scripts
            │   ├── unified_podcast_script.json
            │   └── verified_unified_script.json
            ├── Audio/                # TTS-generated audio
            ├── Video/                # Video clips
            └── Final/                # Compiled videos
```

## 🏗️ Architecture

### Pipeline Stages

- **Stage 1-2**: Media extraction and transcription (local processing)
- **Stage 3-4**: AI analysis and script generation (Gemini API)
- **Stage 5**: Audio synthesis (Chatterbox/ElevenLabs)
- **Stage 6-7**: Video processing and compilation (FFmpeg)

### Two-Pass Quality Control

1. **Pass 1**: Initial content analysis identifies potential segments
2. **Pass 2**: 5-dimension quality scoring filters and ranks segments
3. **Verification**: Fact-checks and rewrites generated commentary

## 🤝 Contributing

This is a personal learning project focused on AI and video processing exploration. Feedback and suggestions are welcome through GitHub issues.

---

**Built by a solo developer learning AI and video processing**

*This project represents hands-on exploration of AI-powered content creation, with each feature added through experimentation and learning.*