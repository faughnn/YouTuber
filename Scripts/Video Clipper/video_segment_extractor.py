\
import argparse
import re
import os
import json
import subprocess
from pathlib import Path

# Default buffer time in seconds to add to the end of each clip's last timestamp
DEFAULT_END_TIME_BUFFER_SECONDS = 7.0

def sanitize_filename(name: str) -> str:
    """Cleans a string to be suitable for use as a filename."""
    name = name.strip()
    # Replace problematic characters often found in titles
    name = name.replace(":", "_")
    name = name.replace("/", "_")
    name = name.replace("\\\\", "_") # Corrected to match a single backslash
    name = name.replace("\"", "'") # Replace double quotes with single

    # Remove characters forbidden in Windows filenames (excluding those already handled)
    name = re.sub(r'[<>|?*]', '', name)
    
    # Replace multiple spaces/underscores with a single underscore
    name = re.sub(r'[\\s_]+', '_', name)
    
    # Remove leading/trailing underscores or periods that might result from replacements
    name = name.strip('_.')
    
    # Limit length to avoid issues (e.g. 150 chars for the base name)
    # If too long, try to cut at a word boundary (underscore)
    max_len = 150
    if len(name) > max_len:
        name_part = name[:max_len]
        if '_' in name_part:
            name = name_part.rsplit('_', 1)[0]
        else:
            name = name_part

    return name if name else "untitled_clip"

def parse_segments_file(file_path: Path) -> list[dict]:
    """
    Parses the JSON segments file to extract titles and their associated timestamps.
    
    Expected JSON format:
    [
      {
        "title": "Segment Title",
        "timestamps": [123.45, 234.56, 345.67],
        "quotes": ["SPEAKER_01: \"Quote 1\"", "SPEAKER_02: \"Quote 2\"", ...]
      },
      ...
    ]
    
    Returns a list of segments, each with a title and timestamps.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            segments_data = json.load(f)
            
        segments = []
        for segment in segments_data:
            title = segment.get('title')
            timestamps = segment.get('timestamps', [])
            
            if not title:
                print(f"Warning: Skipping segment without a title: {segment}")
                continue
                
            if not timestamps:
                print(f"Warning: Skipping segment '{title}' without timestamps")
                continue
                
            # Ensure timestamps are sorted and contain only unique values
            timestamps = sorted(list(set(timestamps)))
            
            segments.append({
                "title": title,
                "timestamps": timestamps
            })
            
        return segments
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in segments file {file_path}: {e}")
        print("Make sure your segments file uses proper JSON syntax.")
        return []
    except FileNotFoundError:
        print(f"Error: Segments file not found at {file_path}")
        return []
    except Exception as e:
        print(f"Error reading or parsing segments file {file_path}: {e}")
        return []

def main():
    parser = argparse.ArgumentParser(
        description="Extracts video clips based on a JSON segments file using ffmpeg.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("video_path", type=Path, help="Path to the source video file.")
    parser.add_argument("segments_file_path", type=Path, 
                      help="Path to the JSON file describing segments and timestamps.\n"
                           "Expected format:\n"
                           "[\n"
                           "  {\n"
                           "    \"title\": \"Segment Title\",\n"
                           "    \"timestamps\": [123.45, 234.56, 345.67],\n"
                           "    \"quotes\": [\"SPEAKER_01: \\\"Quote 1\\\"\", ...] (optional)\n"
                           "  },\n"
                           "  ...\n"
                           "]")
    parser.add_argument(
        "--buffer", 
        type=float, 
        default=DEFAULT_END_TIME_BUFFER_SECONDS, 
        help=f"Buffer in seconds to add to the end of each clip's last timestamp. Default: {DEFAULT_END_TIME_BUFFER_SECONDS}s"
    )
    parser.add_argument(
        "--output_dir_name",
        type=str,
        default="Clips",
        help="Name of the subdirectory within the video's folder to save clips. Default: Clips"
    )

    args = parser.parse_args()

    if not args.video_path.is_file():
        print(f"Error: Source video file not found at '{args.video_path}'")
        return
    if not args.segments_file_path.is_file():
        print(f"Error: Segments description file not found at '{args.segments_file_path}'")
        return

    segments = parse_segments_file(args.segments_file_path)
    
    if not segments:
        print("No valid segments with timestamps found or parsed from the file.")
        return

    video_file_path_abs = args.video_path.resolve()
    video_base_name = args.video_path.stem 
    
    # Determine workspace root assuming script is in YouTuber/Scripts/Video Clipper/
    # and Video Rips is at YouTuber/Video Rips/
    try:
        script_dir = Path(__file__).parent.resolve()
        workspace_root = script_dir.parent.parent 
    except NameError: # __file__ is not defined if running in some interactive environments
        workspace_root = Path.cwd() # Fallback to current working directory
        print(f"Warning: Could not determine script directory, using CWD '{workspace_root}' as workspace root.")


    # Output directory: YouTuber/Video Rips/[video_base_name]/[output_dir_name]/
    output_clips_main_dir = workspace_root / "Video Rips" / video_base_name / args.output_dir_name

    try:
        output_clips_main_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"Error: Could not create output directory '{output_clips_main_dir}': {e}")
        return

    print(f"Source Video: {video_file_path_abs}")
    print(f"Segments File: {args.segments_file_path.resolve()}")
    print(f"Outputting clips to: {output_clips_main_dir.resolve()}")
    print(f"End time buffer: {args.buffer}s")

    successful_clips = 0
    for i, segment in enumerate(segments):
        title = segment["title"]
        timestamps = segment["timestamps"]

        if not timestamps:
            # This case should ideally be filtered by parse_segments_file, but double-check.
            print(f"Skipping segment '{title}' as it has no timestamps.")
            continue

        start_time = timestamps[0]  # Timestamps are already sorted and unique
        end_time = timestamps[-1] + args.buffer

        base_clip_name = sanitize_filename(title)
        # Using a numeric prefix for ordering and uniqueness
        output_filename = f"{i+1:03d}_{base_clip_name}.mp4" 
        output_clip_path_abs = (output_clips_main_dir / output_filename).resolve()

        ffmpeg_command = [
            "ffmpeg",
            "-i", str(video_file_path_abs), # Input file
            "-ss", str(start_time),         # Start time
            "-to", str(end_time),           # End time
            "-c", "copy",                   # Copy codecs (fast, no re-encoding)
            "-y",                           # Overwrite output files without asking
            str(output_clip_path_abs)       # Output file
        ]

        print(f"\\nProcessing clip {i+1}/{len(segments)}: {output_filename}")
        print(f"  Segment Title: {title}")
        print(f"  Calculated Start: {start_time:.2f}s, End: {end_time:.2f}s (includes {args.buffer:.2f}s buffer)")
        # For debugging the command:
        # print(f"  FFmpeg Command: {' '.join(ffmpeg_command)}")

        try:
            process = subprocess.run(ffmpeg_command, check=True, capture_output=True, text=True, encoding='utf-8')
            # ffmpeg often prints informational messages to stderr
            if process.stderr and "error" not in process.stderr.lower(): # Show stderr if not clearly an error message
                 # Limit printing potentially long ffmpeg output
                stderr_lines = process.stderr.strip().split('\\n')
                print(f"  ffmpeg output (last 5 lines):\\n    " + "\\n    ".join(stderr_lines[-5:]))
            elif process.stderr: # If "error" is in stderr, print it more prominently
                print(f"  ffmpeg stderr:\\n{process.stderr.strip()}")

            print(f"  Successfully created: {output_clip_path_abs}")
            successful_clips += 1
        except FileNotFoundError:
            print("Fatal Error: ffmpeg command not found. Please ensure ffmpeg is installed and in your system's PATH.")
            return # Stop processing if ffmpeg is not found
        except subprocess.CalledProcessError as e:
            print(f"  Error during ffmpeg execution for '{title}':")
            print(f"  Command: {' '.join(e.cmd)}")
            print(f"  Return code: {e.returncode}")
            # print(f"  Stdout: {e.stdout.strip() if e.stdout else 'N/A'}") # Often empty for -c copy
            print(f"  Stderr: {e.stderr.strip() if e.stderr else 'N/A'}")
        except Exception as e:
            print(f"  An unexpected error occurred while processing '{title}': {e}")
            import traceback
            traceback.print_exc()

    print(f"\\nFinished processing. {successful_clips}/{len(segments)} clips created successfully.")

if __name__ == "__main__":
    main()
