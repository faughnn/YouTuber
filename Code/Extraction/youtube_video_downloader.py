'''
This script downloads a YouTube video using the yt-dlp library.

To use this script:
1. Install the yt-dlp library: pip install yt-dlp
2. Ensure ffmpeg is installed and in your system's PATH, as yt-dlp might need it for merging formats.
   You can download ffmpeg from https://ffmpeg.org/download.html.
3. Run the script from your terminal: python youtube_video_downloader.py <video_url_or_id>
   Replace <video_url_or_id> with the URL or ID of the YouTube video.
   The video will be saved as an MP4 file in the 'Video Rips' folder,
   with the video title as the filename.
'''
import sys
import subprocess
import os

# Define the target directory for video rips
VIDEO_RIPS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Video Rips")

def download_video(video_url_or_id):
    """Downloads the video from a YouTube video using yt-dlp and saves it as MP4 in the Video Rips folder."""
    try:
        # Ensure the Video Rips folder exists
        if not os.path.exists(VIDEO_RIPS_FOLDER):
            os.makedirs(VIDEO_RIPS_FOLDER)
            print(f"Created directory: {VIDEO_RIPS_FOLDER}")

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
          # Sanitize the title to create a valid filename and folder name
        safe_filename = "".join([c for c in video_title if c.isalnum() or c in (' ', '-', '_')]).rstrip()
        
        # Create episode-specific folder
        episode_folder = os.path.join(VIDEO_RIPS_FOLDER, safe_filename)
        if not os.path.exists(episode_folder):
            os.makedirs(episode_folder)
            print(f"Created episode directory: {episode_folder}")
        
        # Create Clips subfolder within the episode folder
        clips_folder = os.path.join(episode_folder, "Clips")
        if not os.path.exists(clips_folder):
            os.makedirs(clips_folder)
            print(f"Created clips directory: {clips_folder}")
        
        output_filename = f"{safe_filename}.mp4" # Save as .mp4
        # Construct the full output path within the episode folder
        output_path_template = os.path.join(episode_folder, output_filename)

        print(f"Downloading video for: {video_title}")
        print(f"Output will be saved to: {output_path_template}")
        
        # Command to download video, preferring MP4 format.
        # -f 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best': 
        #   Selects best MP4 video and M4A audio, or best MP4 overall, or best available.
        #   yt-dlp will attempt to mux these into an MP4 container specified by -o.
        command = [
            'yt-dlp',
            '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            '-o', output_path_template, # Output template with .mp4 extension
            '--no-warnings',
            video_url_or_id
        ]
        
        subprocess.run(command, check=True)
        
        downloaded_file_path = output_path_template

        if os.path.exists(downloaded_file_path):
            print(f"Video downloaded successfully: {downloaded_file_path}")
            return downloaded_file_path
        else:
            return f"Video download failed, file not found at: {downloaded_file_path}"

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
