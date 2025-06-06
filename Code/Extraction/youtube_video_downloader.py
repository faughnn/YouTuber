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

# Import FileOrganizer for consistent path management
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from Utils.file_organizer import FileOrganizer
from .youtube_url_utils import YouTubeUrlUtils

def download_video(video_url_or_id):
    """Downloads the video from a YouTube video using yt-dlp and saves it as MP4 directly to the episode Input folder."""
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

        # Get video title first to determine episode structure
        get_title_command = [
            'yt-dlp',
            '--get-title',
            '--no-warnings',
            normalized_url
        ]
        process = subprocess.run(get_title_command, capture_output=True, text=True, check=True, encoding='utf-8')
        video_title = process.stdout.strip()
        
        # Get the episode Input folder using FileOrganizer
        file_organizer = FileOrganizer()
        episode_input_folder = file_organizer.get_episode_input_folder(video_title)
        
        # Create the Input folder if it doesn't exist
        os.makedirs(episode_input_folder, exist_ok=True)
        
        # Use standardized filename
        output_filename = "original_video.mp4"
        output_path = os.path.join(episode_input_folder, output_filename)

        print(f"Downloading video for: {video_title}")
        print(f"Output will be saved to: {output_path}")
          # Command to download video, preferring MP4 format.
        # -f 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best': 
        #   Selects best MP4 video and M4A audio, or best MP4 overall, or best available.
        #   yt-dlp will attempt to mux these into an MP4 container specified by -o.
        command = [
            'yt-dlp',
            '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            '-o', output_path, # Output template with .mp4 extension
            '--no-warnings',
            normalized_url
        ]
        
        subprocess.run(command, check=True)

        if os.path.exists(output_path):
            print(f"Video downloaded successfully: {output_path}")
            return output_path
        else:
            return f"Video download failed, file not found at: {output_path}"

    except subprocess.CalledProcessError as e:
        error_output = e.stderr if e.stderr else e.stdout
        if "no suitable format found" in error_output.lower():
             return f"An error occurred with yt-dlp: No suitable MP4 format found. Error: {error_output}"
        return f"An error occurred with yt-dlp: {error_output}"
    except FileNotFoundError:
        return "Error: yt-dlp command not found. Please ensure yt-dlp is installed and in your PATH."
    except Exception as e:
        return f"An unexpected error occurred: {e}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python youtube_video_downloader.py <video_url_or_id>")
        print("Example (URL): python youtube_video_downloader.py https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        print("Example (ID): python youtube_video_downloader.py dQw4w9WgXcQ")
        sys.exit(1)

    video_input = sys.argv[1]
    result = download_video(video_input)
    print(result)
