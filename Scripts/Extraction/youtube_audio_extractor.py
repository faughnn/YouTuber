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

# Define the target directory for audio rips
AUDIO_RIPS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Audio Rips")

def download_audio(video_url_or_id):
    """Downloads the audio from a YouTube video using yt-dlp and saves it as MP3 in the Audio Rips folder."""
    try:
        # Ensure the Audio Rips folder exists
        if not os.path.exists(AUDIO_RIPS_FOLDER):
            os.makedirs(AUDIO_RIPS_FOLDER)
            print(f"Created directory: {AUDIO_RIPS_FOLDER}")

        # Construct the full URL if only an ID is provided
        if not video_url_or_id.startswith(('http:', 'https:')) and len(video_url_or_id) == 11 and not '/' in video_url_or_id:
            video_url_or_id = f"https://www.youtube.com/watch?v={video_url_or_id}"

        # Get video title for the filename using yt-dlp
        get_title_command = [
            'yt-dlp',
            '--get-title',
            '--no-warnings',
            video_url_or_id
        ]
        process = subprocess.run(get_title_command, capture_output=True, text=True, check=True, encoding='utf-8')
        video_title = process.stdout.strip()
        
        # Sanitize the title to create a valid filename
        safe_filename = "".join([c for c in video_title if c.isalnum() or c in (' ', '-', '_')]).rstrip()
        # Output template will be just the filename, path will be prepended later
        output_filename = f"{safe_filename}.mp3"
        # Construct the full output path
        output_path_template = os.path.join(AUDIO_RIPS_FOLDER, output_filename)

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
            video_url_or_id
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
