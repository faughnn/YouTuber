'''
This script downloads a YouTube video using the yt-dlp library.

To use this script:
1. Install the yt-dlp library: pip install yt-dlp
2. Ensure ffmpeg is installed and in your system's PATH, as yt-dlp might need it for merging formats.
   You can download ffmpeg from https://ffmpeg.org/download.html.
3. Run the script from your terminal: python youtube_video_downloader.py <video_url_or_id>
   Replace <video_url_or_id> with the URL or ID of the YouTube video.
   The video will be saved as an MP4 file in the episode's Input folder,
   with a standardized filename.
'''
import sys
import subprocess
import os
from tqdm import tqdm
import yt_dlp

# Import FileOrganizer for consistent path management
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from Utils.file_organizer import FileOrganizer

# Handle both relative and absolute imports
try:
    from .youtube_url_utils import YouTubeUrlUtils
except ImportError:
    from youtube_url_utils import YouTubeUrlUtils

def progress_hook(d):
    """Progress hook for yt-dlp video downloads"""
    if d['status'] == 'downloading':
        if 'total_bytes' in d:
            total = d['total_bytes']
        elif 'total_bytes_estimate' in d:
            total = d['total_bytes_estimate']
        else:
            total = None
            
        downloaded = d.get('downloaded_bytes', 0)
        
        if total:
            # Update existing progress bar or create new one
            if not hasattr(progress_hook, 'pbar'):
                progress_hook.pbar = tqdm(
                    total=total,
                    unit='B',
                    unit_scale=True,
                    desc="Downloading video"
                )
            
            # Update progress
            progress_hook.pbar.n = downloaded
            progress_hook.pbar.refresh()
            
    elif d['status'] == 'finished':
        # Close progress bar when download is complete
        if hasattr(progress_hook, 'pbar'):
            progress_hook.pbar.close()
            delattr(progress_hook, 'pbar')

def ensure_1080p_resolution(video_path):
    """
    Ensures the video is exactly 1920x1080 resolution.
    If not, scales it using FFmpeg while maintaining aspect ratio with padding.
    
    Args:
        video_path: Path to the input video file
        
    Returns:
        Path to the output video (same as input if no scaling needed)
    """
    try:
        # Check current video resolution
        probe_command = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_streams',
            video_path
        ]
        
        result = subprocess.run(probe_command, capture_output=True, text=True, check=True)
        import json
        video_info = json.loads(result.stdout)
        
        # Find video stream
        video_stream = None
        for stream in video_info['streams']:
            if stream['codec_type'] == 'video':
                video_stream = stream
                break
        
        if not video_stream:
            print("Warning: No video stream found, skipping resolution check")
            return video_path
            
        current_width = int(video_stream['width'])
        current_height = int(video_stream['height'])
        
        # Check if already 1920x1080
        if current_width == 1920 and current_height == 1080:
            print(f"Video is already 1920x1080: {video_path}")
            return video_path
        
        print(f"Current resolution: {current_width}x{current_height}, scaling to 1920x1080")
        
        # Create output path for scaled video
        base_path, ext = os.path.splitext(video_path)
        temp_path = f"{base_path}_temp{ext}"
        
        # Scale video to 1920x1080 with proper aspect ratio and padding
        scale_command = [
            'ffmpeg',
            '-i', video_path,
            '-vf', 'scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black',
            '-c:a', 'copy',  # Copy audio without re-encoding
            '-y',  # Overwrite output file
            temp_path
        ]
        
        subprocess.run(scale_command, check=True, capture_output=True)
        
        # Replace original with scaled version
        if os.path.exists(temp_path):
            os.replace(temp_path, video_path)
            print(f"Video successfully scaled to 1920x1080: {video_path}")
            return video_path
        else:
            print("Warning: Scaling failed, using original video")
            return video_path
            
    except Exception as e:
        print(f"Warning: Failed to check/scale video resolution: {e}")
        return video_path

def download_video(video_url_or_id, file_organizer=None):
    """Downloads the video from a YouTube video using yt-dlp and saves it as MP4 directly to the episode Input folder.
    
    Args:
        video_url_or_id: YouTube URL or video ID
        file_organizer: Optional FileOrganizer instance. If not provided, will create one with default paths.
    """
    try:
        # Validate and normalize input using YouTubeUrlUtils
        validation_result = YouTubeUrlUtils.validate_input(video_url_or_id)
        if not validation_result['valid']:
            raise ValueError(f"Invalid YouTube URL or video ID: {'; '.join(validation_result['errors'])}")
        
        # Use the standardized URL
        normalized_url = validation_result['sanitized_url']
        video_id = validation_result['video_id']
        
        print(f"Validated input: {video_id}")
        if validation_result['warnings']:
            for warning in validation_result['warnings']:
                print(f"Warning: {warning}")        # Get video title first to determine episode structure
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            try:
                info = ydl.extract_info(normalized_url, download=False)
                video_title = info.get('title', 'Unknown Title')
            except Exception as e:
                print(f"Warning: Could not extract video title: {e}")
                video_title = f"Video_{video_id}"
        
        # Get the episode Input folder using FileOrganizer
        if file_organizer is None:
            # Create FileOrganizer with default paths if not provided
            default_base_paths = {
                'episode_base': 'Content',
                'analysis_rules': 'Code/Content_Analysis/Rules/Joe_Rogan_selective_analysis_rules.txt'
            }
            file_organizer = FileOrganizer(default_base_paths)
        
        episode_input_folder = file_organizer.get_episode_input_folder(video_title)
        
        # Create the Input folder if it doesn't exist
        os.makedirs(episode_input_folder, exist_ok=True)
          # Use standardized filename
        output_filename = "original_video.mp4"
        output_path = os.path.join(episode_input_folder, output_filename)

        print(f"Downloading video for: {video_title}")
        print(f"Output will be saved to: {output_path}")          # Format selection prioritizing 1920x1080 resolution for consistent video compilation
        # This ensures all downloaded videos match the resolution of generated audio segments
        quality_tiers = [
            # Tier 1: Exact 1080p targeting (1920x1080)
            [
                "bestvideo[height=1080]+bestaudio",       # Exact 1080p video + best audio
                "137+140",                                # 1080p MP4 video + 128k AAC audio
                "299+140",                                # 1080p60 MP4 video + 128k AAC audio
                "best[height=1080]",                      # Best exact 1080p
                "bestvideo[height=1080][ext=mp4]+bestaudio[ext=m4a]", # 1080p MP4 + M4A audio
            ],
            
            # Tier 2: 1080p range with upscaling preference
            [
                "bestvideo[height<=1080][height>=1080]+bestaudio", # Prefer 1080p, allow exact match
                "best[height<=1080][height>=720]",        # High quality range with 1080p preference
                "270+233",                                # 1080p HLS + audio
                "136+140",                                # 720p video + audio (will be upscaled)
            ],
            
            # Tier 3: High quality with upscaling capability  
            [
                "bestvideo[height<=1080]+bestaudio",      # Best up to 1080p + audio
                "best[height<=1080]",                     # Best up to 1080p
                "best[ext=mp4][height<=1080]",            # Best MP4 up to 1080p
                "bestvideo[vcodec^=avc][height<=1080]+bestaudio", # H.264 up to 1080p
            ],
            
            # Tier 4: Fallback with mandatory upscaling
            [
                "bestvideo[height<=720]+bestaudio",       # 720p or lower (will be upscaled)
                "22",                                     # 720p MP4 (format 22)
                "18",                                     # 360p MP4 (format 18) - will be upscaled
                "best",                                   # Any best available
                "worst",                                  # Last resort
            ]
        ]
        
        # Flatten tiers into single list for backward compatibility
        format_options = []
        for tier in quality_tiers:
            format_options.extend(tier)
        
        download_success = False
        last_error = None
        
        for i, format_selector in enumerate(format_options):
            try:
                print(f"Attempting download with format option {i+1}: {format_selector}")
                  # Reset progress bar for each attempt
                if hasattr(progress_hook, 'pbar'):
                    progress_hook.pbar.close()
                    delattr(progress_hook, 'pbar')
                
                # Configure yt-dlp options with progress hook
                ydl_opts = {
                    'format': format_selector,
                    'outtmpl': output_path,
                    'merge_output_format': 'mp4',
                    'progress_hooks': [progress_hook],
                    'quiet': True,
                    'no_warnings': True,
                    'retries': 3,
                    'fragment_retries': 3,
                }                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([normalized_url])
                    
                if os.path.exists(output_path):
                    download_success = True
                    print(f"\nVideo downloaded successfully with format option {i+1}")
                    
                    # Ensure video is exactly 1920x1080 for consistent compilation
                    scaled_path = ensure_1080p_resolution(output_path)
                    if scaled_path != output_path:
                        print(f"Video scaled to 1920x1080: {scaled_path}")
                    
                    break
                    
            except Exception as e:
                last_error = e
                print(f"Format option {i+1} failed: {str(e)}")
                if i < len(format_options) - 1:
                    print("Trying next format option...")
                continue
        
        if not download_success:
            if last_error:
                raise last_error
            else:
                raise Exception("All format options failed")

        if os.path.exists(output_path):
            print(f"Video downloaded successfully: {output_path}")
            return output_path
        else:
            return f"Video download failed, file not found at: {output_path}"

    except Exception as e:
        error_msg = str(e)
        if "no suitable format found" in error_msg.lower():
             return f"An error occurred with yt-dlp: No suitable MP4 format found. Error: {error_msg}"
        return f"An error occurred with yt-dlp: {error_msg}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python youtube_video_downloader.py <video_url_or_id>")
        print("Example (URL): python youtube_video_downloader.py https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        print("Example (ID): python youtube_video_downloader.py dQw4w9WgXcQ")
        sys.exit(1)

    video_input = sys.argv[1]
    result = download_video(video_input)
    print(result)
