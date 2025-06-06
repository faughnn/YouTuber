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

# Import FileOrganizer for consistent path management
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from Utils.file_organizer import FileOrganizer
from .youtube_url_utils import YouTubeUrlUtils
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
                print(f"Warning: {warning}")

        # Get video title for the filename using yt-dlp
        get_title_command = [
            'yt-dlp',
            '--get-title',
            '--no-warnings',
            normalized_url
        ]
        process = subprocess.run(get_title_command, capture_output=True, text=True, check=True, encoding='utf-8')
        video_title = process.stdout.strip()
        
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
        
        # Command to download and extract audio as MP3
        # -x: extract audio
        # --audio-format mp3: specify mp3 as the audio format
        # -o "%(title)s.%(ext)s": output template for filename
        # --no-warnings: suppress warnings
        # --quiet: suppress console output from yt-dlp itself during download
        command = [
            'yt-dlp',
            '-x', # Extract audio
            '--audio-format', 'mp3',
            '-o', output_path_template, # Use the full path for output
            '--no-warnings',
            '--quiet',
            normalized_url
        ]
        
        subprocess.run(command, check=True)
        
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
