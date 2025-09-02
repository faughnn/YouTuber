'''
This script extracts the transcript from a YouTube video using the youtube_transcript_api.
Now includes caching functionality to avoid redundant API calls.

To use this script:
1. Install the youtube_transcript_api library: pip install youtube_transcript_api
2. Run the script from your terminal: python youtube_transcript_extractor.py <video_id>
   Replace <video_id> with the ID of the YouTube video.
   For example, if the YouTube video URL is https://www.youtube.com/watch?v=dQw4w9WgXcQ,
   the video ID is dQw4w9WgXcQ.
'''
import sys
import os
import json
import logging
from datetime import datetime
from typing import List, Optional
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

# Setup logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

def _get_file_organizer():
    """Get FileOrganizer instance with proper import handling."""
    try:
        # Try relative import first
        from ..Utils.file_organizer import FileOrganizer
        from ..Utils.project_paths import get_file_organizer_config
        return FileOrganizer(get_file_organizer_config())
    except ImportError:
        try:
            # Try adding parent directory to path
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            utils_path = os.path.join(parent_dir, 'Utils')
            if utils_path not in sys.path:
                sys.path.insert(0, utils_path)
            from file_organizer import FileOrganizer
            from project_paths import get_file_organizer_config
            return FileOrganizer(get_file_organizer_config())
        except ImportError:
            logger.warning("FileOrganizer not available, caching will be disabled")
            return None

def _check_cache(cache_file_path: str, video_id: str) -> Optional[str]:
    """Check if valid cached transcript exists."""
    if not os.path.exists(cache_file_path):
        return None
    
    try:
        with open(cache_file_path, 'r', encoding='utf-8') as f:
            cached_data = json.load(f)
        
        # Validate cache integrity
        if cached_data.get('metadata', {}).get('video_id') == video_id:
            return cached_data.get('full_text', '')
    except (json.JSONDecodeError, OSError) as e:
        # Handle corrupted cache files
        logger.warning(f"Corrupted cache file: {cache_file_path}, error: {e}")
        return None
    
    return None

def _save_cache(cache_file_path: str, video_id: str, video_title: str, 
                segments: List, full_text: str, language: str, is_manual: bool):
    """Save transcript data to cache file."""
    cache_data = {
        "metadata": {
            "video_id": video_id,
            "video_title": video_title or f"Video_{video_id}",
            "language": language,
            "extraction_date": datetime.utcnow().isoformat() + "Z",
            "source": "youtube_transcript_api",
            "manual_transcript": is_manual,
            "total_segments": len(segments)
        },
        "segments": segments,
        "full_text": full_text
    }
    
    # Ensure directory exists
    try:
        os.makedirs(os.path.dirname(cache_file_path), exist_ok=True)
        
        with open(cache_file_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Cached transcript for video {video_id} at {cache_file_path}")
    except OSError as e:
        logger.warning(f"Failed to save cache: {e}")

def _get_cache_path(video_title: str, file_organizer) -> Optional[str]:
    """Get cache file path using FileOrganizer."""
    if not file_organizer or not video_title:
        return None
        
    try:
        # Use video title as if it were an audio file to get episode paths
        dummy_filename = f"{video_title}.mp3"
        episode_paths = file_organizer.get_episode_paths(dummy_filename)
        return os.path.join(episode_paths['processing_folder'], 'original_audio_transcript.json')
    except Exception as e:
        logger.warning(f"Failed to get cache path: {e}")
        return None

def get_transcript(video_id, language_codes=None, video_title=None, cache_enabled=True):
    """
    Fetches and returns the transcript for a given YouTube video ID with caching support.
    
    Args:
        video_id: YouTube video ID
        language_codes: List of language codes to try (default: ['en'])
        video_title: Video title for cache path generation (optional)
        cache_enabled: Whether to use caching (default: True)
        
    Returns:
        str: Full transcript text (maintains backward compatibility)
    """
    if language_codes is None:
        language_codes = ['en']  # Default to English if no languages are specified
    
    # Initialize file organizer and cache path
    file_organizer = None
    cache_file_path = None
    
    if cache_enabled and video_title:
        file_organizer = _get_file_organizer()
        cache_file_path = _get_cache_path(video_title, file_organizer)
        
        # Check cache first
        if cache_file_path:
            cached_transcript = _check_cache(cache_file_path, video_id)
            if cached_transcript:
                logger.info(f"Using cached transcript for video {video_id}")
                return cached_transcript
    
    # If no cache hit, extract from YouTube
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Try to find a manually created transcript first
        is_manual = True
        try:
            transcript = transcript_list.find_manually_created_transcript(language_codes)
        except NoTranscriptFound:
            # If no manual transcript, try to find a generated transcript
            is_manual = False
            try:
                transcript = transcript_list.find_generated_transcript(language_codes)
            except NoTranscriptFound:
                return f"No transcript found for this video in languages: {language_codes} (neither manual nor generated)."

        # Fetch transcript segments
        fetched_transcript_segments = transcript.fetch()
        
        # Build full transcript text
        full_transcript = ""
        segments_for_cache = []
        
        for entry in fetched_transcript_segments:
            text_content = entry.text
            full_transcript += text_content + " "
            
            # Prepare segment data for cache
            if cache_enabled and cache_file_path:
                segments_for_cache.append({
                    "text": text_content,
                    "start": entry.start,
                    "duration": entry.duration
                })
        
        # Save to cache if enabled
        if cache_enabled and cache_file_path:
            language = transcript.language_code if hasattr(transcript, 'language_code') else language_codes[0]
            _save_cache(
                cache_file_path=cache_file_path,
                video_id=video_id,
                video_title=video_title,
                segments=segments_for_cache,
                full_text=full_transcript.strip(),
                language=language,
                is_manual=is_manual
            )
        
        return full_transcript.strip()

    except TranscriptsDisabled:
        return "Transcripts are disabled for this video."
    except Exception as e:
        return f"An error occurred: {e}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python youtube_transcript_extractor.py <video_id> [language_code_1 language_code_2 ...]")
        print("Example: python youtube_transcript_extractor.py dQw4w9WgXcQ en")
        print("Example (multiple languages): python youtube_transcript_extractor.py dQw4w9WgXcQ en es fr")
        sys.exit(1)

    video_id_to_fetch = sys.argv[1]
    # Get language codes from command line arguments, if provided
    # Defaults to ['en'] in the get_transcript function if not provided here
    lang_codes_to_try = sys.argv[2:] if len(sys.argv) > 2 else None

    print(f"Fetching transcript for video ID: {video_id_to_fetch}")
    if lang_codes_to_try:
        print(f"Attempting to find transcript in languages: {lang_codes_to_try}")
    else:
        print("Attempting to find transcript in default language (English).")
    
    transcript_text = get_transcript(video_id_to_fetch, lang_codes_to_try)
    print("\nTranscript:\n")
    print(transcript_text)
