'''
This script extracts the audio from a YouTube video using the yt-dlp library.

To use this script:
1. Install the yt-dlp library: pip install yt-dlp
2. Ensure ffmpeg is installed and in your system's PATH, as yt-dlp uses it for audio extraction and conversion.
   You can download ffmpeg from https://ffmpeg.org/download.html.
3. Run the script from your terminal: python youtube_audio_extractor.py <video_url_or_id>
   Replace <video_url_or_id> with the URL or ID of the YouTube video.
   The audio will be saved as an MP3 file in the same directory where the script is run,
   with the video title as the filename.
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
import yaml

def get_episode_input_folder(episode_title):
    """Get the Input folder for a specific episode, creating the structure if needed."""
    # Import FileOrganizer using absolute path
    from Utils.file_organizer import FileOrganizer
    
    # Load config to get base paths
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Config", "default_config.yaml")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Expand relative paths to absolute paths (same logic as master_processor)
    script_dir = os.path.dirname(os.path.abspath(__file__))  # This script's directory (Extraction)
    code_dir = os.path.dirname(script_dir)  # Go up one level to Code directory
    base_dir = os.path.dirname(code_dir)  # Go up one level from Code to YouTuber directory
    
    # Resolve relative paths to absolute paths
    for key, path in config['paths'].items():
        if not os.path.isabs(path):
            config['paths'][key] = os.path.normpath(os.path.join(base_dir, path))
      # Create file organizer and get episode structure
    file_organizer = FileOrganizer(config['paths'])
    dummy_audio_name = f"{episode_title}.mp3"
    episode_paths = file_organizer.get_episode_paths(dummy_audio_name)
    
    return episode_paths['input_folder']

def progress_hook(d):
    """Progress hook for yt-dlp downloads"""
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
                    desc="Downloading audio"
                )
            
            # Update progress
            progress_hook.pbar.n = downloaded
            progress_hook.pbar.refresh()
        else:
            # Handle unknown total size
            if not hasattr(progress_hook, 'pbar_unknown'):
                progress_hook.pbar_unknown = tqdm(
                    unit='B',
                    unit_scale=True,
                    desc="Downloading audio"
                )
            
            progress_hook.pbar_unknown.update(downloaded - getattr(progress_hook, 'last_downloaded', 0))
            progress_hook.last_downloaded = downloaded
            
    elif d['status'] == 'finished':
        # Close progress bar when download is complete
        if hasattr(progress_hook, 'pbar'):
            progress_hook.pbar.close()
            delattr(progress_hook, 'pbar')
        if hasattr(progress_hook, 'pbar_unknown'):
            progress_hook.pbar_unknown.close()
            delattr(progress_hook, 'pbar_unknown')
        print(f"\n✓ Audio download completed: {d['filename']}")

def download_audio(video_url_or_id):
    """Downloads the audio from a YouTube video using yt-dlp and saves it as MP3 directly to the episode Input folder."""
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
                print(f"Warning: {warning}")        # Get video title for the filename using yt-dlp
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            try:
                info = ydl.extract_info(normalized_url, download=False)
                video_title = info.get('title', 'Unknown Title')
            except Exception as e:
                print(f"Warning: Could not extract video title: {e}")
                video_title = f"Audio_{video_id}"
        
        # Get episode Input folder using the video title
        episode_input_folder = get_episode_input_folder(video_title)
        
        # Sanitize the title to create a valid filename
        safe_filename = "".join([c for c in video_title if c.isalnum() or c in (' ', '-', '_')]).rstrip()
        # Use standardized filename
        output_filename = f"original_audio.mp3"
        # Construct the full output path
        output_path_template = os.path.join(episode_input_folder, output_filename)

        print(f"Downloading audio for: {video_title}")
        print(f"Output will be saved to: {output_path_template}")
        
        # Reset progress bar for new download
        if hasattr(progress_hook, 'pbar'):
            progress_hook.pbar.close()
            delattr(progress_hook, 'pbar')
        if hasattr(progress_hook, 'pbar_unknown'):
            progress_hook.pbar_unknown.close()
            delattr(progress_hook, 'pbar_unknown')
        
        # Configure yt-dlp options for audio extraction with progress hook
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path_template,
            'extractaudio': True,
            'audioformat': 'mp3',
            'progress_hooks': [progress_hook],
            'quiet': True,
            'no_warnings': True,
        }
        
        # Download and extract audio using yt-dlp Python API
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([normalized_url])
        
        # yt-dlp creates the file directly, so we just confirm its existence
        # The downloaded_file_path is now output_path_template
        downloaded_file_path = output_path_template

        if os.path.exists(downloaded_file_path):
            print(f"Audio downloaded successfully: {downloaded_file_path}")
            return downloaded_file_path
        else:
            return "Audio download failed, file not found."

    except subprocess.CalledProcessError as e:
        return f"An error occurred with yt-dlp: {e.stderr if e.stderr else e.stdout}"
    except FileNotFoundError:
        return "Error: yt-dlp command not found. Please ensure yt-dlp is installed and in your PATH."
    except Exception as e:
        return f"An unexpected error occurred: {e}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python youtube_audio_extractor.py <video_url_or_id>")
        print("Example (URL): python youtube_audio_extractor.py https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        print("Example (ID): python youtube_audio_extractor.py dQw4w9WgXcQ")
        sys.exit(1)

    video_input = sys.argv[1]
    result = download_audio(video_input)
    print(result)
