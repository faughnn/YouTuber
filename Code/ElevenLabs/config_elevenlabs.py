"""
ElevenLabs TTS Configuration
"""

import os

# API Configuration
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')

# Voice Configuration (hardcoded as per requirements)
VOICE_ID = "0DxQtWphUO5YNcF7UOm1"  # Niall Pro Voice ID

# Voice Settings (as per requirements)
VOICE_SETTINGS = {
    'stability': 0.5,        # 50%
    'similarity_boost': 0.75, # 75%
    'style': 0.0,            # Default
    'use_speaker_boost': True
}

# Audio Output Configuration
OUTPUT_FORMAT = "mp3"  # MP3 format matching Chatterbox
