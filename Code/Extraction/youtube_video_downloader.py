"""
This script provides functions to download YouTube videos and fetch their metadata
using the yt-dlp library. It has been refactored to support a metadata-first
pipeline workflow.
"""
import sys
import subprocess
import os
import json
from tqdm import tqdm
import yt_dlp

# Handle both relative and absolute imports for utility functions
try:
    from .youtube_url_utils import YouTubeUrlUtils
except ImportError:
    # This allows the script to be run directly for testing
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    from Utils.youtube_url_utils import YouTubeUrlUtils

def get_video_metadata(url_or_id):
    """
    Fetches video metadata from YouTube without downloading the video.
    This is the first step in the pipeline.

    Args:
        url_or_id (str): The YouTube URL or video ID.

    Returns:
        dict: A dictionary containing the video's metadata (e.g., title, uploader).
              Returns None if metadata extraction fails.
    """
    validation_result = YouTubeUrlUtils.validate_input(url_or_id)
    if not validation_result['valid']:
        raise ValueError(f"Invalid YouTube URL or video ID: {'; '.join(validation_result['errors'])}")
    
    normalized_url = validation_result['sanitized_url']
    
    ydl_opts = {'quiet': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(normalized_url, download=False)
            return info
    except Exception as e:
        print(f"Error fetching metadata: {e}")
        return None

def progress_hook(d):
    """Progress hook for yt-dlp video downloads."""
    if d['status'] == 'downloading':
        total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
        downloaded_bytes = d.get('downloaded_bytes', 0)
        
        if total_bytes:
            if not hasattr(progress_hook, 'pbar'):
                progress_hook.pbar = tqdm(total=total_bytes, unit='B', unit_scale=True, desc="Downloading video")
            
            progress_hook.pbar.n = downloaded_bytes
            progress_hook.pbar.refresh()
            
    elif d['status'] == 'finished':
        if hasattr(progress_hook, 'pbar'):
            progress_hook.pbar.close()
            delattr(progress_hook, 'pbar')

def download_video(url_or_id, output_path):
    """
    Downloads a video from YouTube to a specific path.
    This function is simplified to only handle the download, not path creation.

    Args:
        url_or_id (str): The YouTube URL or video ID.
        output_path (str): The absolute path where the video should be saved.

    Returns:
        str: The output path if successful, otherwise an error message string.
    """
    validation_result = YouTubeUrlUtils.validate_input(url_or_id)
    if not validation_result['valid']:
        raise ValueError(f"Invalid YouTube URL or video ID: {'; '.join(validation_result['errors'])}")
    
    normalized_url = validation_result['sanitized_url']
    
    # Ensure the output directory exists
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)

    # Format selection prioritizing 1080p
    format_selector = "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best"

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

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([normalized_url])
        
        if os.path.exists(output_path):
            print(f"Video downloaded successfully: {output_path}")
            # Optional: ensure 1080p resolution after download
            ensure_1080p_resolution(output_path)
            return output_path
        else:
            return f"Error: Video download failed, file not found at: {output_path}"

    except Exception as e:
        return f"An error occurred with yt-dlp: {e}"

def ensure_1080p_resolution(video_path):
    """
    Ensures the video is exactly 1920x1080. If not, scales it using FFmpeg.
    (This function remains largely unchanged but is kept for utility).
    """
    try:
        probe_command = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', video_path]
        result = subprocess.run(probe_command, capture_output=True, text=True, check=True)
        video_info = json.loads(result.stdout)
        
        video_stream = next((s for s in video_info['streams'] if s['codec_type'] == 'video'), None)
        if not video_stream:
            print("Warning: No video stream found, skipping resolution check.")
            return video_path
            
        width, height = int(video_stream['width']), int(video_stream['height'])
        if width == 1920 and height == 1080:
            return video_path
        
        print(f"Scaling video from {width}x{height} to 1920x1080...")
        base, ext = os.path.splitext(video_path)
        temp_path = f"{base}_temp{ext}"
        
        scale_command = [
            'ffmpeg', '-i', video_path,
            '-vf', 'scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black',
            '-c:a', 'copy', '-y', temp_path
        ]
        subprocess.run(scale_command, check=True, capture_output=True)
        
        os.replace(temp_path, video_path)
        print("Video successfully scaled.")
        return video_path
            
    except Exception as e:
        print(f"Warning: Failed to check/scale video resolution: {e}")
        return video_path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python youtube_video_downloader.py <youtube_url_or_id>")
        sys.exit(1)

    video_input = sys.argv[1]

    print("--- Testing Metadata Fetch ---")
    metadata = get_video_metadata(video_input)
    if metadata:
        print(f"Title: {metadata.get('title')}")
        print(f"Uploader: {metadata.get('uploader')}")
    else:
        print("Could not fetch metadata.")

    print("\n--- Testing Video Download ---")
    # Create a dummy output path for testing
    test_output_path = os.path.abspath(os.path.join("test_output", "downloaded_video.mp4"))
    print(f"Test download path: {test_output_path}")
    result = download_video(video_input, test_output_path)
    print(f"Download result: {result}")
