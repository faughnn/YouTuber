"""
Edge TTS Configuration

Edge TTS uses Microsoft Edge's online neural TTS service.
No API key required - completely free to use.
"""

# Voice Configuration
# Format: {locale}-{Name}Neural

# Recommended English US voices:
# Male: en-US-GuyNeural, en-US-ChristopherNeural, en-US-EricNeural, en-US-RogerNeural, en-US-SteffanNeural
# Female: en-US-AriaNeural, en-US-JennyNeural, en-US-MichelleNeural, en-US-AnaNeural

# Recommended English UK voices:
# Male: en-GB-RyanNeural, en-GB-ThomasNeural
# Female: en-GB-LibbyNeural, en-GB-SoniaNeural, en-GB-MaisieNeural

# Default voice - en-US-GuyNeural is a good male narration voice
DEFAULT_VOICE = "en-US-GuyNeural"

# Voice adjustment parameters
VOICE_RATE = "+0%"      # Speech rate: -50% to +100% (e.g., "+10%", "-20%")
VOICE_VOLUME = "+0%"    # Volume: -50% to +50% (e.g., "+20%", "-10%")
VOICE_PITCH = "+0Hz"    # Pitch adjustment: -50Hz to +50Hz (e.g., "+5Hz", "-10Hz")

# Audio Output Configuration
OUTPUT_FORMAT = "mp3"   # MP3 format for consistency with other TTS engines

# Available voice presets (for reference)
VOICE_PRESETS = {
    # Narration voices (recommended for podcasts)
    "male_narrator_us": "en-US-GuyNeural",
    "male_narrator_uk": "en-GB-RyanNeural",
    "female_narrator_us": "en-US-JennyNeural",
    "female_narrator_uk": "en-GB-SoniaNeural",

    # Conversational voices
    "male_casual_us": "en-US-ChristopherNeural",
    "female_casual_us": "en-US-AriaNeural",

    # Professional voices
    "male_professional_us": "en-US-RogerNeural",
    "female_professional_us": "en-US-MichelleNeural",
}
