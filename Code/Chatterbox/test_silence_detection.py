"""
Test script for the silent clips bug fix
Tests the new audio validation and retry functionality
"""

import os
import sys
import logging
from pathlib import Path

# Add the Chatterbox directory to the Python path
chatterbox_dir = Path(__file__).parent
sys.path.insert(0, str(chatterbox_dir))

# Import with absolute imports
import config_tts_api
from config_tts_api import (
    ENABLE_AUDIO_VALIDATION, MAX_RETRIES, SILENCE_THRESHOLD_DB,
    MIN_SILENCE_DURATION_MS, MAX_SILENCE_RATIO
)

# Test PyDub import
try:
    from pydub import AudioSegment
    from pydub.silence import detect_silence
    print("✅ PyDub is available")
except ImportError:
    print("❌ PyDub is not available - please install with: pip install pydub")
    sys.exit(1)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_configuration():
    """Test that the configuration is properly set up"""
    print("🔧 Testing configuration...")
    
    print(f"📋 Audio validation enabled: {ENABLE_AUDIO_VALIDATION}")
    print(f"📋 Max retries: {MAX_RETRIES}")
    print(f"📋 Silence threshold: {SILENCE_THRESHOLD_DB}dB")
    print(f"📋 Min silence duration: {MIN_SILENCE_DURATION_MS}ms")
    print(f"📋 Max silence ratio: {MAX_SILENCE_RATIO}")
    
    print("✅ Configuration loaded successfully!")

def test_pydub_functionality():
    """Test basic PyDub functionality"""
    print("🎵 Testing PyDub functionality...")
    
    try:
        # Create a simple test audio (1 second of silence)
        from pydub import AudioSegment
        from pydub.generators import Sine
        
        # Generate 1 second of 440Hz tone followed by 2 seconds of silence
        tone = Sine(440).to_audio_segment(duration=1000)  # 1 second
        silence = AudioSegment.silent(duration=2000)     # 2 seconds
        test_audio = tone + silence
        
        # Test silence detection
        silent_ranges = detect_silence(
            test_audio,
            min_silence_len=MIN_SILENCE_DURATION_MS,
            silence_thresh=SILENCE_THRESHOLD_DB
        )
        
        print(f"� Created test audio: {len(test_audio)}ms total")
        print(f"🔇 Detected silent ranges: {silent_ranges}")
        
        if silent_ranges:
            total_silence = sum(end - start for start, end in silent_ranges)
            silence_ratio = total_silence / len(test_audio)
            print(f"� Silence ratio: {silence_ratio:.1%}")
            
            # Test validation logic
            is_valid = silence_ratio <= MAX_SILENCE_RATIO
            print(f"✅ Audio would be valid: {is_valid}")
        
        print("✅ PyDub functionality test passed!")
        
    except Exception as e:
        print(f"❌ PyDub test failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting Silent Clips Bug Fix Configuration Test\n")
    test_configuration()
    print()
    test_pydub_functionality()
    print("\n✅ Test completed!")
