"""
TTS Module Demonstration
Shows how to use the new TTS module structure
"""

import sys
from pathlib import Path

# Add Code directory to path
sys.path.append('Code')

from TTS import SimpleTTSGenerator

def main():
    print("🎙️ TTS Module Demonstration")
    print("=" * 40)
    
    # Initialize TTS generator
    print("🔧 Initializing TTS generator...")
    tts = SimpleTTSGenerator()
    
    # Generate a sample audio file
    test_text = "Welcome to the new TTS module! This is a demonstration of our reorganized text-to-speech functionality."
    output_file = "demo_audio.wav"
    
    print(f"🎵 Generating audio: '{test_text[:50]}...'")
    
    try:
        audio_path = tts.generate_audio(test_text, output_file, voice_style="enthusiastic")
        print(f"✅ Audio generated successfully!")
        print(f"📁 File saved to: {audio_path}")
        
        # Show file size
        file_size = Path(audio_path).stat().st_size / 1024  # KB
        print(f"📊 File size: {file_size:.1f} KB")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
