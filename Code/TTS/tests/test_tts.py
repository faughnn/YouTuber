"""
TTS Module Tests
Basic tests for TTS functionality
"""

import sys
import os
from pathlib import Path

# Add the Code directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

def test_tts_import():
    """Test that TTS module can be imported"""
    try:
        from TTS import SimpleTTSGenerator, TTSSetup
        print("✅ TTS module imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import TTS module: {e}")
        return False

def test_tts_generator():
    """Test basic TTS generator functionality"""
    try:
        from TTS import SimpleTTSGenerator
        
        print("🔧 Testing TTS generator initialization...")
        generator = SimpleTTSGenerator()
        print("✅ TTS generator initialized successfully")
        
        # Test a short audio generation
        test_text = "Hello! This is a test of the TTS system."
        output_filename = "tts_test.wav"
        
        print("🎙️ Testing audio generation...")
        audio_path = generator.generate_audio(test_text, output_filename)
        
        if audio_path and os.path.exists(audio_path):
            print(f"✅ Audio generated successfully: {audio_path}")
            return True
        else:
            print("❌ Audio file was not created")
            return False
            
    except Exception as e:
        print(f"❌ TTS generator test failed: {e}")
        return False

def test_tts_setup():
    """Test TTS setup functionality"""
    try:
        from TTS import TTSSetup
        
        print("🔧 Testing TTS setup...")
        setup = TTSSetup()
        print("✅ TTS setup initialized successfully")
        
        # Test configuration loading
        print(f"📋 Current provider: {setup.config.get('provider', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ TTS setup test failed: {e}")
        return False

def main():
    """Run all TTS tests"""
    print("🧪 Running TTS Module Tests")
    print("=" * 40)
    
    tests = [
        ("Import Test", test_tts_import),
        ("Setup Test", test_tts_setup),
        ("Generator Test", test_tts_generator),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}:")
        if test_func():
            passed += 1
        
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed")
        return 1

if __name__ == "__main__":
    exit(main())
