import sys
sys.path.append('../Content_Analysis')

try:
    from simple_tts_generator import SimpleTTSGenerator
    print("TTS import successful")
    
    # Test creating the TTS generator
    tts = SimpleTTSGenerator()
    print("TTS generator created successfully")
    
except Exception as e:
    print(f"TTS import/creation failed: {e}")
    import traceback
    traceback.print_exc()
