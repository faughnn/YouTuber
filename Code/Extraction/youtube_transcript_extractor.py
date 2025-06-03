'''
This script extracts the transcript from a YouTube video using the youtube_transcript_api.

To use this script:
1. Install the youtube_transcript_api library: pip install youtube_transcript_api
2. Run the script from your terminal: python youtube_transcript_extractor.py <video_id>
   Replace <video_id> with the ID of the YouTube video.
   For example, if the YouTube video URL is https://www.youtube.com/watch?v=dQw4w9WgXcQ,
   the video ID is dQw4w9WgXcQ.
'''
import sys
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

def get_transcript(video_id, language_codes=None):
    """Fetches and returns the transcript for a given YouTube video ID."""
    if language_codes is None:
        language_codes = ['en']  # Default to English if no languages are specified
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Try to find a manually created transcript first
        try:
            transcript = transcript_list.find_manually_created_transcript(language_codes)
        except NoTranscriptFound:
            # If no manual transcript, try to find a generated transcript
            try:
                transcript = transcript_list.find_generated_transcript(language_codes)
            except NoTranscriptFound:
                return f"No transcript found for this video in languages: {language_codes} (neither manual nor generated)."

        full_transcript = ""
        fetched_transcript_segments = transcript.fetch()
        for entry in fetched_transcript_segments:
            full_transcript += entry.text + " "  # Changed from entry['text'] to entry.text
        return full_transcript

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
