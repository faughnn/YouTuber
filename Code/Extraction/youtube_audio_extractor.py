"""
This script provides a function to download audio from a YouTube video 
using the yt-dlp library. It has been refactored to be a simple, 
path-based utility.
"""
import sys
import os
from tqdm import tqdm
import yt_dlp

# Handle both relative and absolute imports for utility functions
try:
    from .youtube_url_utils import YouTubeUrlUtils
except ImportError:
    # This allows the script to be run directly for testing
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    from Utils.youtube_url_utils import YouTubeUrlUtils

def progress_hook(d):
    """Progress hook for yt-dlp audio downloads."""
    if d['status'] == 'downloading':
        total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
        downloaded_bytes = d.get('downloaded_bytes', 0)
        
        if total_bytes:
            if not hasattr(progress_hook, 'pbar_audio'):
                progress_hook.pbar_audio = tqdm(total=total_bytes, unit='B', unit_scale=True, desc="Downloading audio")
            
            progress_hook.pbar_audio.n = downloaded_bytes
            progress_hook.pbar_audio.refresh()
            
    elif d['status'] == 'finished':
        if hasattr(progress_hook, 'pbar_audio'):
            progress_hook.pbar_audio.close()
            delattr(progress_hook, 'pbar_audio')

def download_audio(url_or_id, output_path):
    """
    Downloads audio from a YouTube video to a specific path.
    This function is simplified to only handle the download, not path creation.

    Args:
        url_or_id (str): The YouTube URL or video ID.
        output_path (str): The absolute path where the audio should be saved.

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

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'extractaudio': True,
        'audioformat': 'mp3',
        'progress_hooks': [progress_hook],
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([normalized_url])
        
        # yt-dlp may add the .mp3 extension itself. We need to find the correct final path.
        final_path = output_path
        if not os.path.exists(final_path):
            # Check if the file exists with the added extension
            base, _ = os.path.splitext(output_path)
            if os.path.exists(base + ".mp3"):
                final_path = base + ".mp3"
            # yt-dlp might also replace the extension
            elif os.path.exists(base.replace(".mp3", "") + ".mp3"):
                 final_path = base.replace(".mp3", "") + ".mp3"
            else:
                # If it's still not found, something went wrong.
                 return f"Error: Audio download failed, file not found at or near: {output_path}"

        print(f"Audio downloaded successfully: {final_path}")
        return final_path

    except Exception as e:
        return f"An error occurred with yt-dlp during audio download: {e}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python youtube_audio_extractor.py <youtube_url_or_id>")
        sys.exit(1)

    video_input = sys.argv[1]

    print("--- Testing Audio Download ---")
    # Create a dummy output path for testing
    test_output_path = os.path.abspath(os.path.join("test_output", "downloaded_audio.mp3"))
    print(f"Test download path: {test_output_path}")
    result = download_audio(video_input, test_output_path)
    print(f"Download result: {result}")
