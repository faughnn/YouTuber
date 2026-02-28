# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Running the Pipeline

Always use the project venv and set UTF-8 encoding for Windows terminals:

```bash
cd "G:/YouTuber"
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 "G:/YouTuber/venv/Scripts/python.exe" Code/master_processor_v2.py <URL> <mode> [options]
```

### Modes
- `--full-pipeline` — All stages: download, transcribe, analyze, narrate, TTS audio, video clipping, video compilation
- `--audio-only` — Stages 1-5 (up to TTS audio generation, no video)
- `--script-only` — Stages 1-4 (up to narrative script generation, no audio/video)

### Options
- `--tts-provider {chatterbox,elevenlabs,edgetts}` — TTS engine (default: edgetts)
- `--host "Host Name"` — Override auto-detected host name
- `--guest "Guest Name"` — Override auto-detected guest name
- `--config PATH` — Custom config file (default: `Code/Config/default_config.yaml`)
- `-q` / `-v` / `--debug` — Quiet, verbose, or debug output

### Examples
```bash
# Full pipeline with Edge TTS
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 "G:/YouTuber/venv/Scripts/python.exe" Code/master_processor_v2.py "https://youtube.com/watch?v=..." --full-pipeline --tts-provider edgetts

# Script only, with name overrides
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 "G:/YouTuber/venv/Scripts/python.exe" Code/master_processor_v2.py "https://youtube.com/watch?v=..." --script-only --host "Joe Rogan" --guest "Elon Musk"
```

### Claude Code Workflow
When the user provides a YouTube URL:
1. Determine the host and guest from the video title/channel (or ask if ambiguous)
2. Check if a guest profile exists in `Code/Content_Analysis/Analysis_Guidelines/Guest_Profiles/`
3. If no profile exists, create one based on the guest's known public positions and history
4. Run the pipeline with appropriate arguments
5. Monitor output and fix any errors

### Pipeline Caching
Stages 1-3 cache results automatically. Re-runs skip completed stages, useful for iterating on later stages without re-downloading or re-transcribing.

## Python Environment

- **Venv**: `G:/YouTuber/venv/` — Python 3.13, CUDA-enabled PyTorch 2.6.0+cu124
- **GPU**: RTX 2070 Super (8GB VRAM)
- Always use the venv Python, never system Python
- `PYTHONIOENCODING=utf-8 PYTHONUTF8=1` required on Windows to avoid Rich emoji encoding crashes

## Architecture Overview

8-stage YouTube video processing pipeline:

1. **Media Extraction** — Downloads audio/video from YouTube via yt-dlp
2. **Transcript Generation** — Speaker-diarized transcripts via whisperX (GPU)
3. **Content Analysis** — AI analysis using Google Gemini API
4. **Narrative Generation** — Multi-pass binary filtering pipeline + script generation
5. **Audio Generation** — TTS (Edge TTS, Chatterbox, or ElevenLabs)
6. **Video Clipping** — Extracts relevant video segments via FFmpeg
7. **Video Compilation** — Combines narration audio + video clips into final output
8. **YouTube Description** — Generates upload-ready description

### Content Organization
Episodes are organized as: `Content/{Host_Name}/{Host_Guest_Episode}/`
- `Input/` — Downloaded media and metadata
- `Processing/` — Intermediate analysis, quality control debug files
- `Output/` — Generated audio, scripts, clips, final videos

### Key Files
- `Code/master_processor_v2.py` — Main orchestrator (CLI entry point)
- `Code/Config/default_config.yaml` — Central config (API keys, parameters)
- `Code/Content_Analysis/podcast_narrative_generator.py` — Script generation
- `Code/Content_Analysis/binary_segment_filter.py` — 5-gate segment filtering
- `Code/Content_Analysis/binary_rebuttal_verifier.py` — 4-gate rebuttal verification
- `Code/Content_Analysis/Analysis_Guidelines/Guest_Profiles/` — Guest-specific analysis profiles

### Environment Variables
- `GEMINI_API_KEY` — Google Gemini API (required)
- `HUGGINGFACE_TOKEN` — HuggingFace (required for speaker diarization)
- `ELEVENLABS_API_KEY` — ElevenLabs TTS (optional)

### Quality Control Pipeline (Stage 4)
- Binary 5-gate segment filtering (claim detection, verifiability, accuracy, harm, rebuttability)
- Diversity selection with round-robin topic balancing
- False negative recovery
- Recent events verification via web search
- Script generation (structure plan + creative script)
- Output quality gate
- Binary 4-gate rebuttal verification with self-correction
- External fact validation

### API Debug Logging
All Gemini API requests/responses are saved to `Processing/Quality_Control/` as debug JSON files for inspection.

## Testing
```bash
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 "G:/YouTuber/venv/Scripts/python.exe" -m pytest Code/Chatterbox/tests/test_master_processor_stage5.py
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 "G:/YouTuber/venv/Scripts/python.exe" -m pytest Code/Content_Analysis/test_rebuttal_verifier.py
```

## Known Issues
- Gemini API rejects combining `response_mime_type="application/json"` with `tools=[google_search]` — use one or the other, never both
- yt-dlp warns about missing JS runtime (deno) — non-fatal, downloads work without it
- Keep yt-dlp updated (`pip install --upgrade yt-dlp`) — older versions get 403s from YouTube
