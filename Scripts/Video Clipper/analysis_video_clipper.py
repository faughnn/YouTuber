#!/usr/bin/env python3
"""
Analysis-Based Video Clipper
Extracts video clips from analysis files containing problematic segments with timestamps.
Handles multiple time ranges per segment by creating separate clips for each range.
"""

import argparse
import re
import os
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Default buffer time in seconds to add before start and after end of each clip
DEFAULT_START_BUFFER_SECONDS = 3.0
DEFAULT_END_BUFFER_SECONDS = 0.0

def sanitize_filename(name: str) -> str:
    """Cleans a string to be suitable for use as a filename."""
    name = name.strip()
    # Replace problematic characters often found in titles
    name = name.replace(":", "_")
    name = name.replace("/", "_")
    name = name.replace("\\", "_")
    name = name.replace("\"", "'")
    name = name.replace("?", "")
    name = name.replace("*", "")
    name = name.replace("<", "")
    name = name.replace(">", "")
    name = name.replace("|", "")
    
    # Replace multiple spaces/underscores with a single underscore
    name = re.sub(r'[\s_]+', '_', name)
    
    # Remove leading/trailing underscores or periods
    name = name.strip('_.')
    
    # Limit length to avoid filesystem issues
    max_len = 100
    if len(name) > max_len:
        name_part = name[:max_len]
        if '_' in name_part:
            name = name_part.rsplit('_', 1)[0]
        else:
            name = name_part
    
    return name if name else "untitled_clip"

def parse_timestamp(timestamp_str: str) -> float:
    """
    Parse various timestamp formats into seconds.
    Formats supported:
    - 45.17 (45.17 seconds)
    - 1.04.19 (1 hour 4 minutes 19 seconds)
    - 2.40.0 (2 hours 40 minutes 0 seconds)
    - 19.22 (19 minutes 22 seconds if > 60)
    - 0:57:17 (0 hours 57 minutes 17 seconds)
    - 1:23:45 (1 hour 23 minutes 45 seconds)
    - 23:45 (23 minutes 45 seconds)
    """
    try:
        # Handle H:MM:SS or MM:SS format (colon-separated)
        if ':' in timestamp_str:
            parts = timestamp_str.split(':')
            if len(parts) == 3:  # H:MM:SS
                hours, minutes, seconds = map(float, parts)
                return hours * 3600 + minutes * 60 + seconds
            elif len(parts) == 2:  # MM:SS
                minutes, seconds = map(float, parts)
                return minutes * 60 + seconds
        
        # Handle direct float format (seconds)
        if '.' in timestamp_str and timestamp_str.count('.') == 1:
            try:
                seconds = float(timestamp_str)
                # If less than 3600 and greater than 60, assume MM.SS format
                if 60 <= seconds < 3600:
                    minutes = int(seconds)
                    secs = (seconds - minutes) * 100  # Decimal part as seconds
                    return minutes * 60 + secs
                return seconds
            except ValueError:
                pass
        
        # Handle H.MM.SS or MM.SS format (dot-separated)
        parts = timestamp_str.split('.')
        if len(parts) == 3:  # H.MM.SS
            hours, minutes, seconds = map(float, parts)
            return hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:  # MM.SS
            minutes, seconds = map(float, parts)
            return minutes * 60 + seconds
        else:
            return float(timestamp_str)
    
    except (ValueError, TypeError):
        print(f"Warning: Could not parse timestamp '{timestamp_str}', defaulting to 0")
        return 0.0

def extract_json_from_analysis_file(file_path: Path) -> Optional[List[Dict]]:
    """Extract JSON data from the analysis text file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # First, try to parse the entire file as JSON (for clean JSON files)
        try:
            json_data = json.loads(content)
            print(f"Successfully parsed pure JSON file with {len(json_data)} segments")
            return json_data
        except json.JSONDecodeError:
            # File is not pure JSON, try to extract from markdown format
            pass
        
        # Find JSON content between ```json and ```
        json_match = re.search(r'```json\s*(\[.*?\])\s*```', content, re.DOTALL)
        if not json_match:
            print("Error: Could not find JSON data in analysis file")
            return None
        
        json_str = json_match.group(1)
        return json.loads(json_str)
    
    except FileNotFoundError:
        print(f"Error: Analysis file not found at {file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in analysis file: {e}")
        return None
    except Exception as e:
        print(f"Error reading analysis file: {e}")
        return None

def parse_analysis_segments(analysis_data: List[Dict]) -> List[Dict]:
    """
    Parse analysis data into clip specifications.
    Returns list of clips with start/end times and metadata.
    """
    clips = []
    
    for i, segment in enumerate(analysis_data, 1):
        title = segment.get('narrativeSegmentTitle', f'Segment_{i}')
        severity = segment.get('severityRating', 'UNKNOWN')
        timestamps = segment.get('fullerContextTimestamps', {})
        
        # Extract time ranges
        time_ranges = []
        
        # Primary time range
        if 'start' in timestamps and 'end' in timestamps:
            start_time = parse_timestamp(str(timestamps['start']))
            end_time = parse_timestamp(str(timestamps['end']))
            time_ranges.append((start_time, end_time))
        
        # Secondary time range (if exists)
        if 'start2' in timestamps and 'end2' in timestamps:
            start2_time = parse_timestamp(str(timestamps['start2']))
            end2_time = parse_timestamp(str(timestamps['end2']))
            time_ranges.append((start2_time, end2_time))
        
        # Create clips for each time range
        for range_idx, (start_time, end_time) in enumerate(time_ranges):
            clip_suffix = f"_Part{range_idx + 1}" if len(time_ranges) > 1 else ""
            
            clips.append({
                'segment_number': i,
                'title': f"{title}{clip_suffix}",
                'original_title': title,
                'severity': severity,
                'start_time': start_time,
                'end_time': end_time,
                'range_index': range_idx,
                'total_ranges': len(time_ranges),
                'context_description': segment.get('clipContextDescription', ''),
                'harm_potential': segment.get('harmPotential', '')
            })
    
    return clips

def create_clip_metadata(clips: List[Dict], output_dir: Path) -> None:
    """Create metadata files for the generated clips."""
    metadata = {
        'generation_info': {
            'timestamp': '2025-06-03',
            'total_clips': len(clips),
            'purpose': 'Academic research and media criticism'
        },
        'clips': []
    }
    
    for clip in clips:
        metadata['clips'].append({
            'filename': f"[{clip['severity']}]_{clip['segment_number']:02d}_{sanitize_filename(clip['title'])}.mp4",
            'original_title': clip['original_title'],
            'severity_rating': clip['severity'],
            'time_range': f"{clip['start_time']:.2f}s - {clip['end_time']:.2f}s",
            'duration': f"{clip['end_time'] - clip['start_time']:.2f}s",
            'context': clip['context_description'],
            'harm_potential': clip['harm_potential']
        })
    
    # Write metadata JSON
    metadata_file = output_dir / 'clip_metadata.json'
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    # Write summary text file
    summary_file = output_dir / 'clips_summary.txt'
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("VIDEO CLIPS GENERATED FROM ANALYSIS\n")
        f.write("=====================================\n\n")
        f.write(f"Total clips generated: {len(clips)}\n")
        f.write(f"Generation date: 2025-06-03\n")
        f.write(f"Purpose: Academic research and media criticism\n\n")
        
        for clip in clips:
            f.write(f"CLIP: [{clip['severity']}] {clip['original_title']}\n")
            f.write(f"  File: [{clip['severity']}]_{clip['segment_number']:02d}_{sanitize_filename(clip['title'])}.mp4\n")
            f.write(f"  Time: {clip['start_time']:.2f}s - {clip['end_time']:.2f}s ({clip['end_time'] - clip['start_time']:.2f}s)\n")
            f.write(f"  Context: {clip['context_description'][:100]}...\n")
            f.write(f"  Harm Potential: {clip['harm_potential'][:100]}...\n\n")

def create_video_clips(video_path: Path, clips: List[Dict], output_dir: Path, 
                      start_buffer: float, end_buffer: float) -> int:
    """Create video clips using FFmpeg."""
    successful_clips = 0
    
    # Group clips by severity for organization
    severity_dirs = {}
    for clip in clips:
        severity = clip['severity']
        if severity not in severity_dirs:
            severity_dir = output_dir / f"{severity}_Segments"
            severity_dir.mkdir(exist_ok=True)
            severity_dirs[severity] = severity_dir
    
    for i, clip in enumerate(clips):
        # Calculate actual start/end times with buffers
        actual_start = max(0, clip['start_time'] - start_buffer)
        actual_end = clip['end_time'] + end_buffer
        
        # Generate filename
        safe_title = sanitize_filename(clip['title'])
        filename = f"[{clip['severity']}]_{clip['segment_number']:02d}_{safe_title}.mp4"
        
        # Determine output directory based on severity
        output_clip_path = severity_dirs[clip['severity']] / filename
          # FFmpeg command - using accurate seeking and re-encoding for proper sync
        ffmpeg_command = [
            "ffmpeg",
            "-ss", str(actual_start),  # Seek before input for more accuracy
            "-i", str(video_path),
            "-t", str(actual_end - actual_start),  # Duration instead of end time
            "-c:v", "libx264",  # Re-encode video for accuracy
            "-c:a", "aac",      # Re-encode audio for accuracy
            "-crf", "23",       # Good quality setting
            "-preset", "fast",  # Balance between speed and compression
            "-avoid_negative_ts", "make_zero",  # Handle timing issues
            "-y",  # Overwrite existing files
            str(output_clip_path)
        ]
        
        print(f"\nProcessing clip {i+1}/{len(clips)}: {filename}")
        print(f"  Title: {clip['original_title']}")
        if clip['total_ranges'] > 1:
            print(f"  Part: {clip['range_index'] + 1} of {clip['total_ranges']}")
        print(f"  Severity: {clip['severity']}")
        print(f"  Time: {actual_start:.2f}s - {actual_end:.2f}s ({actual_end - actual_start:.2f}s)")
        print(f"  Buffer: -{start_buffer:.1f}s/+{end_buffer:.1f}s")
        
        try:
            result = subprocess.run(ffmpeg_command, capture_output=True, text=True, check=True)
            print(f"  ✓ Successfully created: {output_clip_path.name}")
            successful_clips += 1
            
        except FileNotFoundError:
            print("  ✗ ERROR: FFmpeg not found. Please install FFmpeg and add to PATH.")
            break
        except subprocess.CalledProcessError as e:
            print(f"  ✗ ERROR: FFmpeg failed for '{clip['title']}'")
            print(f"    Command: {' '.join(ffmpeg_command)}")
            print(f"    Error: {e.stderr.strip() if e.stderr else 'Unknown error'}")
        except Exception as e:
            print(f"  ✗ ERROR: Unexpected error for '{clip['title']}': {e}")
    
    return successful_clips

def main():
    parser = argparse.ArgumentParser(
        description="Extract video clips from analysis files with problematic content segments",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("video_path", type=Path, 
                       help="Path to the source video file")
    parser.add_argument("analysis_file", type=Path,
                       help="Path to the analysis file containing JSON segment data")
    parser.add_argument("--start-buffer", type=float, default=DEFAULT_START_BUFFER_SECONDS,
                       help=f"Buffer time (seconds) to add before clip start. Default: {DEFAULT_START_BUFFER_SECONDS}s")
    parser.add_argument("--end-buffer", type=float, default=DEFAULT_END_BUFFER_SECONDS,
                       help=f"Buffer time (seconds) to add after clip end. Default: {DEFAULT_END_BUFFER_SECONDS}s")
    parser.add_argument("--output-dir", type=str, default="Analysis_Based_Clips",
                       help="Name of output directory within video folder. Default: Analysis_Based_Clips")
    
    args = parser.parse_args()
    
    # Validate inputs
    if not args.video_path.exists():
        print(f"Error: Video file not found: {args.video_path}")
        return 1
    
    if not args.analysis_file.exists():
        print(f"Error: Analysis file not found: {args.analysis_file}")
        return 1
    
    # Extract and parse analysis data
    print(f"Reading analysis file: {args.analysis_file}")
    analysis_data = extract_json_from_analysis_file(args.analysis_file)
    if not analysis_data:
        return 1
    
    print(f"Found {len(analysis_data)} segments in analysis file")
    
    # Parse segments into clips
    clips = parse_analysis_segments(analysis_data)
    if not clips:
        print("No valid clips found in analysis data")
        return 1
    
    print(f"Generated {len(clips)} clips from {len(analysis_data)} segments")
    
    # Setup output directory
    video_name = args.video_path.stem
    output_base_dir = args.video_path.parent / "Clips" / args.output_dir
    output_base_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nSource video: {args.video_path}")
    print(f"Output directory: {output_base_dir}")
    print(f"Buffers: -{args.start_buffer:.1f}s / +{args.end_buffer:.1f}s")
    
    # Create clips
    successful_clips = create_video_clips(
        args.video_path, clips, output_base_dir, 
        args.start_buffer, args.end_buffer
    )
    
    # Generate metadata
    create_clip_metadata(clips, output_base_dir)
    
    print(f"\n{'='*50}")
    print(f"PROCESSING COMPLETE")
    print(f"{'='*50}")
    print(f"Successfully created: {successful_clips}/{len(clips)} clips")
    print(f"Output location: {output_base_dir}")
    print(f"Metadata files: clip_metadata.json, clips_summary.txt")
    
    # Summary by severity
    severity_counts = {}
    for clip in clips:
        severity_counts[clip['severity']] = severity_counts.get(clip['severity'], 0) + 1
    
    print(f"\nClips by severity:")
    for severity, count in severity_counts.items():
        print(f"  {severity}: {count} clips")
    
    return 0 if successful_clips == len(clips) else 1

if __name__ == "__main__":
    exit(main())
