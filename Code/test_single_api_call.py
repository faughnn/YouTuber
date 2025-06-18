#!/usr/bin/env python3
"""
End-to-end test for SimpleTTSEngine with single section
Tests actual API call with one small section
"""

import sys
import logging
from pathlib import Path

# Add the Code directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from Chatterbox.simple_tts_engine import SimpleTTSEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_single_section():
    """Test processing a single section with actual API call"""
    print("=== SimpleTTSEngine Single Section Test ===")
    
    try:
        # Initialize engine
        print("1. Initializing SimpleTTSEngine...")
        engine = SimpleTTSEngine()
        
        # Test generate_speech with simple text
        test_text = "Hello, this is a test of the SimpleTTSEngine API integration."
        output_path = "c:\\Users\\nfaug\\OneDrive - LIR\\Desktop\\YouTuber\\Code\\test_output.wav"
        
        print("2. Testing API call with simple text...")
        print(f"Text: {test_text}")
        print(f"Output: {output_path}")
        
        success = engine.generate_speech(test_text, output_path)
        
        if success:
            print("✅ API call successful!")
            
            # Check if file was created
            if Path(output_path).exists():
                file_size = Path(output_path).stat().st_size
                print(f"✅ Output file created: {file_size} bytes")
            else:
                print("❌ Output file not found")
        else:
            print("❌ API call failed")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_single_section()
