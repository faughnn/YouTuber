#!/usr/bin/env python3
"""
Test script for SimpleTTSEngine
Quick validation of the implementation before full integration
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

def test_simple_tts_engine():
    """Test the SimpleTTSEngine implementation"""
    print("=== SimpleTTSEngine Test ===")
    
    # Test script path
    script_path = "c:\\Users\\nfaug\\OneDrive - LIR\\Desktop\\YouTuber\\Content\\Joe_Rogan_Experience\\Joe Rogan Experience #2335 - Dr. Mary Talley Bowden\\Output\\Scripts\\unified_podcast_script.json"
    
    try:
        # Initialize engine
        print("1. Initializing SimpleTTSEngine...")
        engine = SimpleTTSEngine()
        print("✅ Engine initialized successfully")
        
        # Test parsing (but not actual API calls for now)
        print("2. Testing script parsing...")
        json_data = engine.parser.parse_response_file(script_path)
        print(f"✅ Script parsed successfully: {len(json_data.get('podcast_sections', []))} sections found")
        
        # Test audio section extraction
        print("3. Testing audio section extraction...")
        all_sections = json_data.get('podcast_sections', [])
        audio_sections = engine.parser.extract_audio_sections(all_sections)
        print(f"✅ Audio sections extracted: {len(audio_sections)} sections")
        
        for section in audio_sections:
            print(f"   - {section.section_id} ({section.section_type})")
        
        # Test episode discovery
        print("4. Testing episode directory discovery...")
        episode_dir = engine.file_manager.discover_episode_from_script(script_path)
        print(f"✅ Episode directory discovered: {episode_dir}")
        
        # Test directory structure creation
        print("5. Testing directory structure creation...")
        output_dir = engine.file_manager.create_episode_structure(episode_dir)
        print(f"✅ Directory structure created: {output_dir}")
        
        print("\\n🎉 All tests passed! SimpleTTSEngine is ready for integration.")
        print("\\nNote: API calls not tested - ensure TTS API server is running before full processing.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_tts_engine()
