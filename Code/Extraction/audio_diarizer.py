'''
This script transcribes an audio file and performs speaker diarization 
using the whisperX library, outputting the result in JSON format.

To use this script:
1. Install dependencies:
   pip install whisperx torch torchvision torchaudio
   (Ensure ffmpeg is installed and in PATH)
2. Set up Hugging Face (Optional but Recommended for best diarization):
   - Create a Hugging Face account (huggingface.co).
   - Accept user conditions for:
     - https://huggingface.co/pyannote/speaker-diarization
     - https://huggingface.co/pyannote/segmentation
   - Generate a User Access Token: https://huggingface.co/settings/tokens
   - The script has a default token hardcoded. You can override it or skip its use via command line.

3. Run the script:
   python audio_diarizer.py <audio_file_path> [hugging_face_token_or_"None"] [output_json_file_path]
   
   - <audio_file_path>: Path to the audio file (required).
   - [hugging_face_token_or_"None"]: Optional. Provide your Hugging Face token to override the
     hardcoded default. Use the string "None" (case-insensitive) to explicitly skip using any token 
     (even the hardcoded one), which may affect diarization quality/speed.
     If omitted, the hardcoded token will be used.
   - [output_json_file_path]: Optional. Path to save the transcript. 
     If omitted, the transcript will be saved to a .json file with the same base name 
     as the audio file in the same directory (e.g., if audio is "my_audio.mp3", 
     output will be "my_audio.json").

   Examples:
   1. Use hardcoded token, auto-named JSON output:
      python audio_diarizer.py "C:\\\\path\\\\to\\\\audio.mp3"
   2. Override hardcoded token, auto-named JSON output:
      python audio_diarizer.py "C:\\\\path\\\\to\\\\audio.mp3" "hf_YOUR_NEW_TOKEN"
   3. Explicitly use NO token, auto-named JSON output:
      python audio_diarizer.py "C:\\\\path\\\\to\\\\audio.mp3" "None"
   4. Use hardcoded token, explicit JSON output file:
      python audio_diarizer.py "C:\\\\path\\\\to\\\\audio.mp3" "" "transcript.json" 
      (Empty string for token argument uses hardcoded if you want to specify output path directly after)
      Alternatively, to be more explicit for hardcoded token with explicit output:
      python audio_diarizer.py "C:\\\\path\\\\to\\\\audio.mp3" [leave_empty_or_provide_token] "transcript.json"
      (The script logic handles the argument positions carefully)
   5. Override token, explicit JSON output file:
      python audio_diarizer.py "C:\\\\path\\\\to\\\\audio.mp3" "hf_YOUR_NEW_TOKEN" "transcript.json"
   6. Explicitly use NO token, explicit JSON output file:
      python audio_diarizer.py "C:\\\\path\\\\to\\\\audio.mp3" "None" "transcript.json"
'''

import sys
import os
import json
import torch
import time
import re
from tqdm import tqdm

# Add parent directories to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Utils.project_paths import get_transcripts_dir

# Define the target directory for transcripts
TRANSCRIPTS_FOLDER = str(get_transcripts_dir())

# Attempt to import whisperx, provide guidance if not found
try:
    import whisperx
except ImportError:
    print("Error: whisperX library not found.")
    print("Please install it by running: pip install whisperx")
    print("Also ensure PyTorch is installed: pip install torch torchvision torchaudio")
    sys.exit(1)

# Attempt to import tqdm for progress bars
try:
    from tqdm import tqdm
except ImportError:
    print("Warning: tqdm not found. Installing for progress bars...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tqdm"])
    from tqdm import tqdm

DEFAULT_HF_TOKEN = os.getenv('HuggingFaceToken')  # Hugging Face token from environment variable

def sanitize_audio_filename(name: str) -> str:
    """Cleans a string to be suitable for use as a folder/filename."""
    name = name.strip()
    # Replace problematic characters often found in titles
    name = name.replace(":", "_")
    name = name.replace("/", "_")
    name = name.replace("\\", "_")
    name = name.replace("\"", "'") # Replace double quotes with single

    # Remove characters forbidden in Windows filenames
    name = re.sub(r'[<>|?*]', '', name)
    
    # Replace multiple spaces/underscores with a single underscore
    name = re.sub(r'[\s_]+', '_', name)
    
    # Remove leading/trailing underscores or periods that might result from replacements
    name = name.strip('_.')
      # Limit length to avoid issues (e.g. 150 chars for the base name)
    max_len = 150
    if len(name) > max_len:
        name_part = name[:max_len]
        if '_' in name_part:
            name = name_part.rsplit('_', 1)[0]
        else:
            name = name_part

    return name if name else "untitled_audio"

def extract_channel_name(filename: str) -> str:
    """Extract channel name from filename."""
    # Remove file extension
    base_name = os.path.splitext(filename)[0]
    
    # Remove analysis suffix if present
    if base_name.endswith('_analysis'):
        base_name = base_name[:-9]
    
    # Common channel patterns
    channel_patterns = [
        r'^(Joe Rogan Experience)',
        r'^(The Daily Show)',
        r'^(Saturday Night Live)',
        r'^(Conan)',
        r'^(The Tonight Show)',
        r'^(Late Night)',
        r'^(Jimmy Kimmel Live)',
        r'^([A-Za-z\s&]+)\s+\d+',  # Channel name followed by episode number
        r'^([A-Za-z\s&]+)\s+-',    # Channel name followed by dash
    ]
    
    for pattern in channel_patterns:
        match = re.match(pattern, base_name, re.IGNORECASE)
        if match:
            return sanitize_audio_filename(match.group(1))
    
    # If no pattern matches, use the first few words
    words = base_name.split()
    if len(words) >= 2:
        return sanitize_audio_filename(' '.join(words[:2]))
    
    return sanitize_audio_filename(base_name)

def _format_timestamp_srt(seconds: float) -> str:
    """Formats time in seconds to SRT timestamp format HH:MM:SS,ms."""
    if seconds is None or seconds < 0:
        # Fallback for potentially missing or invalid timestamps, though whisperX usually provides them.
        # Depending on strictness, could raise an error or return a default.
        # For SRT, a valid timestamp is crucial.
        print(f"Warning: Invalid or missing timestamp ({seconds}) encountered. Defaulting to 00:00:00,000.", file=sys.stderr)
        return "00:00:00,000"
        
    milliseconds = round(seconds * 1000.0)
    hours = int(milliseconds // 3_600_000)
    milliseconds %= 3_600_000
    minutes = int(milliseconds // 60_000)
    milliseconds %= 60_000
    seconds_val = int(milliseconds // 1_000)
    milliseconds %= 1_000
    return f"{hours:02d}:{minutes:02d}:{seconds_val:02d},{milliseconds:03d}"

def _format_timestamp_readable(seconds: float) -> str:
    """Formats time in seconds to readable timestamp format HH:MM:SS."""
    if seconds is None or seconds < 0:
        print(f"Warning: Invalid or missing timestamp ({seconds}) encountered. Defaulting to 00:00:00.", file=sys.stderr)
        return "00:00:00"
        
    total_seconds = round(seconds)
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds_val = int(total_seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds_val:02d}"

def diarize_audio(audio_path, hf_auth_token_to_use, output_file_path=None):
    """
    Transcribes and diarizes an audio file using whisperX, returning a JSON formatted string.
    
    Args:
        audio_path: Path to input audio file
        hf_auth_token_to_use: HuggingFace token for diarization models
        output_file_path: Explicit path where transcript should be saved
                         (caller is responsible for ensuring directory exists)
    
    Returns:
        JSON string with diarization results
    """
    if not os.path.exists(audio_path):
        return f"Error: Audio file not found at {audio_path}"

    # Auto-detect CUDA or fallback to CPU
    if torch.cuda.is_available():
        device = "cuda"
        compute_type = "float16" # Recommended for CUDA
        print("CUDA is available. Using GPU.")
    else:
        device = "cpu"
        compute_type = "int8"   # Recommended for CPU
        print("CUDA not available. Using CPU.")

    whisper_model_size = "medium"  # "base", "small", "medium", "large-v2", "large-v3"
                               # Larger models are more accurate but slower and require more memory.
    print(f"Using device: {device}")
    print(f"Loading Whisper model: {whisper_model_size} (compute_type: {compute_type})")

    try:
        # 1. Load Whisper model and transcribe
        transcribe_batch_size = 4 if device == "cpu" else 16 
        
        with tqdm(total=100, desc="🤖 Loading Whisper model", ncols=80, colour='blue') as pbar:
            model = whisperx.load_model(whisper_model_size, device, compute_type=compute_type)
            pbar.update(50)
            audio = whisperx.load_audio(audio_path)
            pbar.update(50)
        
        with tqdm(total=100, desc="📝 Transcribing audio", ncols=80, colour='green') as pbar:
            result = model.transcribe(audio, batch_size=transcribe_batch_size)
            pbar.update(100)
        print("✅ Transcription complete.")

        # 2. Align Whisper output
        with tqdm(total=100, desc="🔄 Aligning transcript", ncols=80, colour='yellow') as pbar:
            align_model, align_metadata = whisperx.load_align_model(language_code=result["language"], device=device)
            pbar.update(50)
            aligned_result = whisperx.align(result["segments"], align_model, align_metadata, audio, device, return_char_alignments=False)
            pbar.update(50)
        print("✅ Alignment complete.")

        # 3. Perform Speaker Diarization
        if not hf_auth_token_to_use:
            print("\\n⚠️ Warning: No Hugging Face token is being used for diarization.")
            print("Diarization may fail or use a less accurate model if the chosen diarization model requires it.")
            print("It is highly recommended to use a token after accepting pyannote.audio model terms for best results.")
        
        with tqdm(total=100, desc="👥 Speaker diarization", ncols=80, colour='magenta') as pbar:
            diarization_pipeline = whisperx.diarize.DiarizationPipeline(use_auth_token=hf_auth_token_to_use, device=device)
            pbar.update(30)
            diarized_segments = diarization_pipeline(audio_path) # Takes audio file path
            pbar.update(70)
        print("✅ Diarization complete.")        # 4. Assign word speakers
        with tqdm(total=100, desc="🎯 Assigning speakers", ncols=80, colour='cyan') as pbar:
            final_transcript_segments = whisperx.assign_word_speakers(diarized_segments, aligned_result)
            pbar.update(100)
        print("✅ Speaker assignment complete.")

        # 5. Format and return output as JSON
        with tqdm(total=100, desc="📄 Formatting JSON", ncols=80, colour='white') as pbar:
            segments = final_transcript_segments.get("segments", [])
            if not segments:
                return json.dumps({"error": "No transcript segments found after speaker assignment."}, indent=2)
            pbar.update(20)

            # Build JSON structure with both timestamp formats
            json_output = {
                "metadata": {
                    "language": result.get("language", "unknown"),
                    "total_segments": len(segments),
                    "model_used": whisper_model_size,
                    "device": device
                },
                "segments": []
            }
            pbar.update(30)

            # Process segments with progress updates
            for i, segment in enumerate(segments):
                start_time = segment.get("start")
                end_time = segment.get("end")
                
                # Ensure segments have valid start and end times
                if start_time is None or end_time is None or end_time < start_time:
                    print(f"Warning: Skipping segment with invalid start/end times: {segment}", file=sys.stderr)
                    continue

                text = segment.get("text", "").strip()
                speaker_label = segment.get("speaker", "UNKNOWN_SPEAKER")

                segment_data = {
                    "id": i + 1,
                    "speaker": speaker_label,
                    "text": text,
                    "start_time": start_time,  # Raw seconds (float)
                    "end_time": end_time,      # Raw seconds (float)
                    "start_time_formatted": _format_timestamp_readable(start_time),  # HH:MM:SS
                    "end_time_formatted": _format_timestamp_readable(end_time),      # HH:MM:SS
                    "duration": round(end_time - start_time, 2)
                }
                
                json_output["segments"].append(segment_data)
                
                # Update progress during processing
                if i % max(1, len(segments) // 10) == 0:  # Update every 10% of segments
                    pbar.update(5)
            
            # Final progress update
            pbar.update(100 - pbar.n)
        
        print("✅ JSON formatting complete.")
        
        if not json_output["segments"]:
            error_result = json.dumps({"error": "No valid transcript segments could be formatted for JSON output."}, indent=2)
            if output_file_path:
                try:
                    with open(output_file_path, "w", encoding="utf-8") as f:
                        f.write(error_result)
                except Exception as e:
                    print(f"Warning: Could not save error result to {output_file_path}: {e}")
            return error_result
            
        result_json = json.dumps(json_output, indent=2, ensure_ascii=False)
        
        # Save to file if output path is provided
        if output_file_path:
            try:
                with open(output_file_path, "w", encoding="utf-8") as f:
                    f.write(result_json)
                print(f"Transcript saved to: {output_file_path}")
            except Exception as e:
                print(f"Warning: Could not save transcript to {output_file_path}: {e}")
        
        return result_json

    except RuntimeError as e:
        error_data = {"error": str(e)}
        if "out of memory" in str(e).lower() and device == "cuda":
            error_data["suggestion"] = "CUDA out of memory. Try a smaller Whisper model or run on CPU."
        elif "Could not load library cudnn_ops_infer.dll" in str(e) or "Could not load library cublas64_11.dll" in str(e):
            error_data["suggestion"] = "CUDA library load error. Ensure CUDA toolkit is installed correctly and compatible with PyTorch."
        
        error_result = json.dumps(error_data, indent=2)
        if output_file_path:
            try:
                with open(output_file_path, "w", encoding="utf-8") as f:
                    f.write(error_result)
            except Exception as save_e:
                print(f"Warning: Could not save error result to {output_file_path}: {save_e}")
        return error_result
    except Exception as e:
        error_result = json.dumps({"error": f"An unexpected error occurred: {e}"}, indent=2)
        if output_file_path:
            try:
                with open(output_file_path, "w", encoding="utf-8") as f:
                    f.write(error_result)
            except Exception as save_e:
                print(f"Warning: Could not save error result to {output_file_path}: {save_e}")
        return error_result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python audio_diarizer.py <audio_file_path> [hugging_face_token_or_\\\"None\\\"] [output_json_file_path]")
        print("  <audio_file_path>: Path to the audio file (required).")
        print("  [hugging_face_token_or_\\\"None\\\"]: Optional. HF token or \\\"None\\\" to skip. Omit to use hardcoded default.")
        print("  [output_json_file_path]: Optional. Path to save the .json transcript.")
        print("    If omitted, defaults to <audio_file_name>.json in the same directory as the audio file.")
        print("\\nExamples:")
        print("  python audio_diarizer.py \\\"audio.mp3\\\"")
        print("  python audio_diarizer.py \\\"audio.mp3\\\" \\\"hf_YOURTOKEN\\\"")
        print("  python audio_diarizer.py \\\"audio.mp3\\\" \\\"None\\\"")
        print("  python audio_diarizer.py \\\"audio.mp3\\\" \\\"hf_YOURTOKEN\\\" \\\"custom_transcript.json\\\"")
        sys.exit(1)

    audio_file_path = sys.argv[1]
    
    # Determine Hugging Face token to use
    hugging_face_token_to_pass_to_function = None # Will be set based on logic below
    
    # Argument parsing:
    # sys.argv[0] is script name
    # sys.argv[1] is audio_file_path
    # sys.argv[2] (if exists) is token OR output_file (if token is meant to be default)
    # sys.argv[3] (if exists) is output_file

    # Default to using the hardcoded token
    hugging_face_token_to_pass_to_function = DEFAULT_HF_TOKEN
    token_message = f"Using hardcoded default Hugging Face token: {DEFAULT_HF_TOKEN}\\n(To override, provide a token or 'None' as the second argument.)"

    output_file_path_explicitly_provided = False
    output_file_path = None # Will be determined

    # Check for token/output file arguments
    if len(sys.argv) > 2:
        # sys.argv[2] could be a token, "None", or an output file if token is skipped
        arg2 = sys.argv[2]
        if arg2.lower() == "none":
            hugging_face_token_to_pass_to_function = None
            token_message = "Hugging Face token explicitly skipped via command line ('None')."
            if len(sys.argv) > 3: # Output file is sys.argv[3]
                output_file_path = sys.argv[3]
                output_file_path_explicitly_provided = True
        elif arg2.startswith("hf_") or (len(arg2) > 20 and not (".json" in arg2.lower() or ".txt" in arg2.lower())): # Heuristic: looks like a token
            hugging_face_token_to_pass_to_function = arg2
            token_message = f"Using Hugging Face token from command line: {hugging_face_token_to_pass_to_function}"
            if len(sys.argv) > 3: # Output file is sys.argv[3]
                output_file_path = sys.argv[3]
                output_file_path_explicitly_provided = True
        else: # sys.argv[2] is likely an output file, meaning token was omitted (use default)
            output_file_path = arg2
            output_file_path_explicitly_provided = True
            # token_message already set to use default
            if len(sys.argv) > 3: # User provided too many args if arg2 was output
                 print(f"Warning: Extra argument '{sys.argv[3]}' ignored. Interpreting '{sys.argv[2]}' as output file path.", file=sys.stderr)
    
    # Handle output file path
    if not output_file_path_explicitly_provided:
        # Default to audio file name with .json extension in same directory
        audio_base_name, _ = os.path.splitext(os.path.basename(audio_file_path))
        audio_dir = os.path.dirname(audio_file_path)
        output_file_path = os.path.join(audio_dir, audio_base_name + ".json")
        print(f"Output file path not specified. Defaulting to: {output_file_path}")
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_file_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        print(f"Created output directory: {output_dir}")

    print(f"Starting diarization for: {audio_file_path}")
    print(token_message) # Print token status
    
    if output_file_path_explicitly_provided: # Only print this if user specified it
        print(f"Output will be saved to: {output_file_path}")

    full_transcript_json = diarize_audio(audio_file_path, hugging_face_token_to_pass_to_function, output_file_path)

    # Function already saved the file, so just show completion message
    print(f"\\n--- JSON Transcript Generation Complete ---")
    print(f"--- End of Process ---")
