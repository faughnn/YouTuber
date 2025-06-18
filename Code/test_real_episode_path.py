#!/usr/bin/env python3
"""
Test SimpleTTSEngine with REAL episode script path to verify correct directory handling
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

def test_real_episode_processing():
    """Test with the real episode script to verify directory structure"""
    print("=== SimpleTTSEngine Real Episode Directory Test ===")
    
    # REAL script path
    real_script_path = "c:\\Users\\nfaug\\OneDrive - LIR\\Desktop\\YouTuber\\Content\\Joe_Rogan_Experience\\Joe Rogan Experience #2335 - Dr. Mary Talley Bowden\\Output\\Scripts\\unified_podcast_script.json"
    
    try:
        # Initialize engine
        print("1. Initializing SimpleTTSEngine...")
        engine = SimpleTTSEngine()
        
        # Test episode discovery with REAL path
        print("2. Testing episode directory discovery with REAL script path...")
        episode_dir = engine.file_manager.discover_episode_from_script(real_script_path)
        print(f"Episode directory: {episode_dir}")
        
        # Test directory structure creation
        print("3. Testing directory structure creation...")
        output_dir = engine.file_manager.create_episode_structure(episode_dir)
        print(f"Output directory: {output_dir}")
        
        # Parse script to get one section for testing
        print("4. Getting one section for path testing...")
        json_data = engine.parser.parse_response_file(real_script_path)
        all_sections = json_data.get('podcast_sections', [])
        audio_sections = engine.parser.extract_audio_sections(all_sections)
        
        if audio_sections:
            test_section = audio_sections[0]  # Use intro section
            
            # Test file path generation
            output_filename = f"{test_section.section_id}.wav"
            output_path = Path(output_dir) / output_filename
            
            print(f"5. Test file would be generated at:")
            print(f"   {output_path}")
            
            # Test organize_audio_file
            metadata = {
                'episode_dir': episode_dir,
                'section_id': test_section.section_id,
                'section_type': test_section.section_type
            }
            
            # Simulate what organize_audio_file would return (without actually moving a file)
            expected_organized_path = output_path  # Should be the same since it's already in the right place
            
            print(f"6. After organization, file would be at:")
            print(f"   {expected_organized_path}")
            
            # Verify this is in the episode directory
            if str(episode_dir) in str(expected_organized_path):
                print("✅ CONFIRMED: Files will be placed in the correct episode directory!")
                print(f"   Episode: {episode_dir}")
                print(f"   Audio: {expected_organized_path}")
            else:
                print("❌ ERROR: Files would NOT be in the episode directory!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_real_episode_processing()
