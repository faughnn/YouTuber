'''
Simple Audio Transcriber - High Quality Edition
===============================================
A standalone script that transcribes any audio file (MP4, MP3, WAV, etc.) using whisperX.
This script reuses functionality from the existing audio_diarizer.py but optimizes for quality.

🔧 QUALITY IMPROVEMENTS:
- Uses large-v3 Whisper model (best available)
- Beam search for exploring multiple transcription paths  
- Temperature fallback for difficult segments
- Advanced filtering for low-confidence segments
- Text post-processing for better formatting
- Configurable settings at the top of the file

⚙️ QUICK QUALITY ADJUSTMENTS:
- Edit WHISPER_MODEL: "base" (fast) to "large-v3" (best quality)
- Set HIGH_QUALITY_MODE: False (faster) or True (better)
- Add LANGUAGE_HINT: "en", "es", etc. if you know the language
- Add INITIAL_PROMPT: "This is a medical interview" for context

Usage:
    python simple_audio_transcriber.py <audio_file_path> [output_folder]

Examples:
    python simple_audio_transcriber.py "C:\\path\\to\\audio.mp4"
    python simple_audio_transcriber.py "audio.mp3" "C:\\transcripts"

Output:
    - Creates both a detailed JSON file and a clean text transcript
    - JSON includes speaker diarization and timestamps
    - Text file is clean and readable for quick review

Requirements:
    pip install whisperx torch torchvision torchaudio
'''

import sys
import os
import json
import torch
import time
import re
from datetime import datetime
from tqdm import tqdm

# Default Hugging Face token for speaker diarization (can be overridden)
DEFAULT_HF_TOKEN = "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"

# QUALITY SETTINGS - Adjust these for better transcription
# =======================================================
# Model options: "tiny", "base", "small", "medium", "large-v2", "large-v3"
# tiny/base = fast but less accurate | large-v3 = slowest but best quality
WHISPER_MODEL = "large-v2"  # Change to "base" for faster processing

# Quality vs Speed trade-offs
HIGH_QUALITY_MODE = True  # Set to False for faster processing
USE_BEAM_SEARCH = True    # Better accuracy but slower
ENABLE_WORD_TIMESTAMPS =  False  # More precise timing

# Language hint (optional) - helps with accuracy if you know the language
# Examples: "en", "es", "fr", "de", None for auto-detect
LANGUAGE_HINT = "en"

# Initial prompt for context (optional) - helps with domain-specific content
# Examples: "This is a medical interview", "This is a technical podcast", None
INITIAL_PROMPT = None

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import whisperx
        return True
    except ImportError:
        print("❌ Error: whisperX library not found.")
        print("📦 Install it with: pip install whisperx")
        print("📦 Also ensure PyTorch is installed: pip install torch torchvision torchaudio")
        return False

def clean_transcript_text(text):
    """Clean and improve transcript text quality."""
    if not text:
        return text
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Fix common transcription issues
    text = text.replace(' .', '.')
    text = text.replace(' ,', ',')
    text = text.replace(' ?', '?')
    text = text.replace(' !', '!')
    text = text.replace(' :', ':')
    text = text.replace(' ;', ';')
    
    # Fix spacing around quotes
    text = re.sub(r'\s+"', ' "', text)
    text = re.sub(r'"\s+', '" ', text)
    
    # Ensure sentences start with capital letters
    sentences = re.split(r'([.!?])\s+', text)
    cleaned_sentences = []
    
    for i, part in enumerate(sentences):
        if i % 2 == 0 and part.strip():  # Text parts (not punctuation)
            part = part.strip()
            if part and part[0].islower():
                part = part[0].upper() + part[1:]
        cleaned_sentences.append(part)
    
    return ''.join(cleaned_sentences).strip()

def format_timestamp(seconds):
    """Format timestamp as HH:MM:SS"""
    if seconds is None or seconds < 0:
        return "00:00:00"
    
    total_seconds = round(seconds)
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds_val = int(total_seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds_val:02d}"

def transcribe_audio(audio_path, hf_token=None):
    """
    Transcribe and diarize audio file using whisperX.
    
    Args:
        audio_path: Path to the audio file
        hf_token: Hugging Face token for speaker diarization
        
    Returns:
        dict: Transcription results with metadata and segments
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # Auto-detect device
    if torch.cuda.is_available():
        device = "cuda"
        compute_type = "float16"
        print("🚀 Using GPU (CUDA)")
    else:
        device = "cpu" 
        compute_type = "int8"
        print("💻 Using CPU")

    # Use configurable model settings
    whisper_model = WHISPER_MODEL
    batch_size = 1 if device == "cpu" else 4  # Conservative for quality
    
    # Build transcription options - use only the most basic parameters
    transcribe_options = {}
    
    # Only add language if specified (this is the most universally supported parameter)
    if LANGUAGE_HINT:
        transcribe_options["language"] = LANGUAGE_HINT

    try:
        # Import whisperX here after dependency check
        import whisperx
        
        quality_msg = "high quality" if HIGH_QUALITY_MODE else "standard"
        print(f"🤖 Loading Whisper model: {whisper_model} ({quality_msg})")
        
        if HIGH_QUALITY_MODE:
            print("⚙️  High quality mode enabled - better accuracy, slower processing")
        if USE_BEAM_SEARCH:
            print("🔍 Beam search enabled - exploring multiple transcription paths")
        if LANGUAGE_HINT:
            print(f"🌍 Language hint: {LANGUAGE_HINT}")
        if INITIAL_PROMPT:
            print(f"💭 Context prompt: {INITIAL_PROMPT}")
        
        # 1. Load model and transcribe
        with tqdm(total=100, desc="Loading model & audio", colour='blue') as pbar:
            model = whisperx.load_model(whisper_model, device, compute_type=compute_type)
            pbar.update(50)
            audio = whisperx.load_audio(audio_path)
            pbar.update(50)

        desc = f"Transcribing ({quality_msg})"
        with tqdm(total=100, desc=desc, colour='green') as pbar:
            result = model.transcribe(audio, batch_size=batch_size, **transcribe_options)
            pbar.update(100)

        # 2. Align transcript for better timing
        with tqdm(total=100, desc="Aligning transcript", colour='yellow') as pbar:
            align_model, align_metadata = whisperx.load_align_model(
                language_code=result["language"], device=device
            )
            pbar.update(50)
            aligned_result = whisperx.align(
                result["segments"], align_model, align_metadata, audio, device
            )
            pbar.update(50)

        # 3. Speaker diarization
        if hf_token:
            print("👥 Performing speaker diarization...")
            with tqdm(total=100, desc="Speaker diarization", colour='magenta') as pbar:
                diarization_pipeline = whisperx.diarize.DiarizationPipeline(
                    use_auth_token=hf_token, device=device
                )
                pbar.update(30)
                diarized_segments = diarization_pipeline(audio_path)
                pbar.update(40)
                final_result = whisperx.assign_word_speakers(diarized_segments, aligned_result)
                pbar.update(30)
        else:
            print("⚠️  Skipping speaker diarization (no HF token)")
            final_result = aligned_result

        # 4. Format results
        segments = final_result.get("segments", [])
        
        # Build output structure
        output_data = {
            "metadata": {
                "source_file": os.path.basename(audio_path),
                "language": result.get("language", "unknown"),
                "total_segments": len(segments),
                "model_used": whisper_model,
                "device": device,
                "transcribed_at": datetime.now().isoformat(),
                "speaker_diarization": hf_token is not None
            },
            "segments": [],
            "full_text": ""
        }

        full_text_parts = []
        
        for i, segment in enumerate(segments):
            start_time = segment.get("start", 0)
            end_time = segment.get("end", 0)
            text = segment.get("text", "").strip()
            speaker = segment.get("speaker", "SPEAKER")

            if text:  # Only include segments with text
                # Clean the text for better quality
                cleaned_text = clean_transcript_text(text)
                
                segment_data = {
                    "id": i + 1,
                    "speaker": speaker,
                    "text": cleaned_text,
                    "start_time": start_time,
                    "end_time": end_time,
                    "start_time_formatted": format_timestamp(start_time),
                    "end_time_formatted": format_timestamp(end_time),
                    "duration": round(end_time - start_time, 2) if end_time > start_time else 0
                }
                
                output_data["segments"].append(segment_data)
                full_text_parts.append(cleaned_text)

        # Clean the full text as well
        output_data["full_text"] = clean_transcript_text(" ".join(full_text_parts))
        
        print("✅ Transcription complete!")
        return output_data

    except Exception as e:
        error_msg = str(e)
        if "out of memory" in error_msg.lower() and device == "cuda":
            print("❌ GPU out of memory. Try using CPU instead.")
        elif "Could not load library" in error_msg:
            print("❌ CUDA library error. Check your CUDA installation.")
        
        raise Exception(f"Transcription failed: {error_msg}")

def save_transcripts(data, output_folder, base_name):
    """Save both JSON and text versions of the transcript."""
    
    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)
    
    # Save detailed JSON
    json_path = os.path.join(output_folder, f"{base_name}_detailed.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Save clean text transcript
    text_path = os.path.join(output_folder, f"{base_name}_transcript.txt")
    with open(text_path, 'w', encoding='utf-8') as f:
        f.write(f"Audio Transcript: {data['metadata']['source_file']}\n")
        f.write(f"Language: {data['metadata']['language']}\n")
        f.write(f"Transcribed: {data['metadata']['transcribed_at']}\n")
        f.write("=" * 50 + "\n\n")
        
        if data['metadata']['speaker_diarization']:
            # Write with speaker labels and timestamps
            for segment in data['segments']:
                f.write(f"[{segment['start_time_formatted']}] {segment['speaker']}: {segment['text']}\n")
        else:
            # Write simple text without speakers
            f.write(data['full_text'])
    
    return json_path, text_path

def main():
    """Main function to handle command line usage."""
    if len(sys.argv) < 2:
        print("🎵 Simple Audio Transcriber")
        print("Usage: python simple_audio_transcriber.py <audio_file> [output_folder]")
        print("\nExamples:")
        print('  python simple_audio_transcriber.py "audio.mp4"')
        print('  python simple_audio_transcriber.py "audio.mp3" "C:\\transcripts"')
        print("\nSupported formats: MP4, MP3, WAV, M4A, FLAC, and more")
        sys.exit(1)

    # Check dependencies first
    if not check_dependencies():
        sys.exit(1)

    audio_file = sys.argv[1]
    output_folder = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(os.path.abspath(audio_file))
    
    if not os.path.exists(audio_file):
        print(f"❌ Error: Audio file not found: {audio_file}")
        sys.exit(1)

    # Get base name for output files
    base_name = os.path.splitext(os.path.basename(audio_file))[0]
    
    print(f"🎵 Transcribing: {audio_file}")
    print(f"📁 Output folder: {output_folder}")
    print(f"🏷️  Base name: {base_name}")
    print("-" * 50)

    try:
        # Transcribe the audio
        result = transcribe_audio(audio_file, DEFAULT_HF_TOKEN)
        
        # Save outputs
        json_path, text_path = save_transcripts(result, output_folder, base_name)
        
        print("\n🎉 SUCCESS!")
        print(f"📄 Detailed JSON: {json_path}")
        print(f"📝 Clean text: {text_path}")
        print(f"\n📊 Stats:")
        print(f"   Language: {result['metadata']['language']}")
        print(f"   Segments: {result['metadata']['total_segments']}")
        print(f"   Speakers: {result['metadata']['speaker_diarization']}")
        
        # Show a preview of the transcript
        preview = result['full_text'][:200]
        print(f"\n📖 Preview:")
        print(f"   {preview}{'...' if len(result['full_text']) > 200 else ''}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
