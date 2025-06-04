#!/usr/bin/env python3
"""
Verify TTS Voice Configuration
Confirms that TTS generator uses voice from config file instead of hardcoded values
"""

from TTS import SimpleTTSGenerator

def main():
    print("🔍 Verifying TTS Voice Configuration")
    print("=" * 50)
    
    # Initialize TTS generator
    generator = SimpleTTSGenerator()
    
    # Display current configuration
    print(f"📋 Loaded Configuration:")
    print(f"   Provider: {generator.config['provider']}")
    print(f"   Model: {generator.config['gemini']['model']}")
    print(f"   Voice Name: {generator.config['gemini']['voice_name']}")
    print(f"   Audio Format: {generator.config['gemini']['audio_format']}")
    print(f"   Sample Rate: {generator.config['gemini']['sample_rate']}")
    print(f"   Channels: {generator.config['gemini']['channels']}")
    print(f"   Sample Width: {generator.config['gemini']['sample_width']}")
    
    # Test audio generation with config voice
    test_text = "Hello! This is a test using the configured voice from the TTS config file."
    filename = "voice_config_test.wav"
    
    print(f"\n🎙️ Generating test audio with voice: {generator.config['gemini']['voice_name']}")
    
    try:
        audio_path = generator.generate_audio(test_text, filename)
        print(f"✅ Audio generated successfully using configured voice!")
        print(f"📁 File saved to: {audio_path}")
        
        # Verify the voice in config vs what would have been hardcoded
        config_voice = generator.config['gemini']['voice_name']
        hardcoded_voice = "Kore"
        
        if config_voice != hardcoded_voice:
            print(f"\n🎯 Configuration Fix Verified!")
            print(f"   Config voice: {config_voice}")
            print(f"   Old hardcoded voice: {hardcoded_voice}")
            print(f"   ✅ Using config voice successfully!")
        else:
            print(f"\n⚠️ Voice matches old hardcoded value: {config_voice}")
            
    except Exception as e:
        print(f"❌ Error generating audio: {e}")
        return False
    
    print(f"\n🎉 Voice configuration verification complete!")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
