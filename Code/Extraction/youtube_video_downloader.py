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

# Handle both relative and absolute imports
try:
    from .youtube_url_utils import YouTubeUrlUtils
except ImportError:
    from youtube_url_utils import YouTubeUrlUtils

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
        print(f"Output will be saved to: {output_path}")
          # Comprehensive format selection strategies organized by quality tiers
        # Based on systematic testing of 39 different methods
        quality_tiers = [
            # Tier 1: Maximum Quality (4K, unrestricted best)
            [
                "best",                                    # Best available quality
                "bestvideo+bestaudio",                     # Best video + best audio
                "bestvideo+bestaudio/best",               # Combined with single file fallback
            ],
            
            # Tier 2: High Quality (1080p optimized)
            [
                "best[height<=1080]",                     # Best up to 1080p
                "bestvideo[height<=1080]+bestaudio",      # Best 1080p video + audio
                "270+233",                                # 1080p HLS + audio
                "137+140",                                # 1080p video + 128k audio
                "best[ext=mp4]",                          # Best MP4 format
                "best[vcodec^=avc]",                      # Best H.264 video
            ],
            
            # Tier 3: Good Quality (720p reliable)
            [
                "best[height<=720]",                      # Best up to 720p
                "bestvideo[height<=720]+bestaudio",       # Best 720p video + audio
                "232+233",                                # 720p HLS + audio
                "136+140",                                # 720p video + 128k audio
                "22",                                     # 720p MP4 (format 22)
                "best[acodec^=mp4a]",                     # Best AAC audio
            ],
            
            # Tier 4: Fallback Quality (480p and below)
            [
                "best[height<=480]",                      # Best up to 480p
                "18",                                     # 360p MP4 (format 18)
                "worst",                                  # Worst available quality
                "best/worst",                             # Best with worst fallback
            ],
            
            # Tier 5: Protocol-specific fallbacks
            [
                "best[protocol^=https]",                  # HTTPS protocols only
                "best[protocol^=m3u8]",                   # HLS streams only
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
                
                command = [
                    'yt-dlp',
                    '-f', format_selector,
                    '-o', output_path,
                    '--merge-output-format', 'mp4',  # Ensure output is MP4
                    '--no-warnings',
                    '--extractor-retries', '3',
                    '--fragment-retries', '3',
                    normalized_url
                ]
                
                subprocess.run(command, check=True, capture_output=True, text=True)
                
                if os.path.exists(output_path):
                    download_success = True
                    print(f"Video downloaded successfully with format option {i+1}")
                    break
                    
            except subprocess.CalledProcessError as e:
                last_error = e
                error_output = e.stderr if e.stderr else e.stdout
                print(f"Format option {i+1} failed: {error_output}")
                if i < len(format_options) - 1:
                    print("Trying next format option...")
                continue
        
        if not download_success:
            if last_error:
                error_output = last_error.stderr if last_error.stderr else last_error.stdout
                raise subprocess.CalledProcessError(last_error.returncode, last_error.cmd, error_output)
            else:
                raise Exception("All format options failed")

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
