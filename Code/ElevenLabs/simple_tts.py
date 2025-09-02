#!/usr/bin/env python3
"""
Simple ElevenLabs Text-to-Speech Script
Just run: python simple_tts.py
"""

from elevenlabs import VoiceSettings, play, save
from elevenlabs.client import ElevenLabs
import os

# Set your API key here
API_KEY = os.getenv('ELEVENLABS_API_KEY')

def main():
    print("🎤 Simple ElevenLabs TTS")
    print("=" * 30)
    
    # Initialize client
    client = ElevenLabs(api_key=API_KEY)
    
    # Get text from user
    text = input("Enter text to convert to speech: ").strip()
    if not text:
        print("No text entered. Exiting.")
        return
    
    # Default voice: Niall Pro
    voice_id = "0DxQtWphUO5YNcF7UOm1"
    
    try:
        print(f"\n🔄 Converting: '{text[:50]}{'...' if len(text) > 50 else ''}'")
        print("🎵 Using voice: Aria")
        
        # Generate speech
        audio = client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            voice_settings=VoiceSettings(
                stability=0.75,
                similarity_boost=0.5,
                style=0.0,
                use_speaker_boost=True
            )
        )
        
        # Save to file
        filename = "output.mp3"
        save(audio, filename)
        print(f"💾 Saved audio to: {filename}")
        
        # Play audio
        print("🔊 Playing audio...")
        play(audio)
        print("✅ Done!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
