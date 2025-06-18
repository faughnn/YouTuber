#!/usr/bin/env python3
"""
Limited end-to-end test for SimpleTTSEngine
Tests full processing pipeline with just 2 sections for validation
"""

import sys
import logging
import json
from pathlib import Path

# Add the Code directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from Chatterbox.simple_tts_engine import SimpleTTSEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def create_test_script():
    """Create a minimal test script with just 2 sections"""
    test_script = {
        "narrative_theme": "Test Theme",
        "podcast_sections": [
            {
                "section_type": "intro",
                "section_id": "intro_001",
                "script_content": "Welcome to this test episode. This is a short introduction to verify the SimpleTTSEngine works correctly.",
                "estimated_duration": "15s"
            },
            {
                "section_type": "outro",
                "section_id": "outro_001", 
                "script_content": "Thank you for listening to this test episode. The SimpleTTSEngine appears to be working as expected.",
                "estimated_duration": "15s"
            }
        ],
        "script_metadata": {
            "total_estimated_duration": "30s",
            "target_audience": "Test",
            "key_themes": ["Testing"],
            "total_clips_analyzed": 0,
            "tts_segments_count": 2,
            "timeline_ready": True
        }
    }
    
    # Create test script file
    test_script_path = "c:\\Users\\nfaug\\OneDrive - LIR\\Desktop\\YouTuber\\Code\\test_script.json"
    with open(test_script_path, 'w', encoding='utf-8') as f:
        json.dump(test_script, f, indent=2)
    
    return test_script_path

def test_limited_processing():
    """Test full processing pipeline with limited sections"""
    print("=== SimpleTTSEngine Limited Processing Test ===")
    
    try:
        # Create test script
        print("1. Creating test script...")
        test_script_path = create_test_script()
        print(f"✅ Test script created: {test_script_path}")
        
        # Initialize engine
        print("2. Initializing SimpleTTSEngine...")
        engine = SimpleTTSEngine()
        
        # Create a simple episode structure for testing
        test_episode_dir = "c:\\Users\\nfaug\\OneDrive - LIR\\Desktop\\YouTuber\\Content\\Test_Episode"
        test_scripts_dir = Path(test_episode_dir) / "Output" / "Scripts"
        test_scripts_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy test script to proper location
        test_script_proper_path = test_scripts_dir / "unified_podcast_script.json"
        import shutil
        shutil.copy2(test_script_path, test_script_proper_path)
        
        print(f"✅ Test episode created: {test_episode_dir}")
        
        # Process the test script
        print("3. Processing test script...")
        results = engine.process_episode_script(str(test_script_proper_path))
        
        print("\\n=== Processing Results ===")
        print(f"Total sections: {results.total_sections}")
        print(f"Successful sections: {results.successful_sections}")
        print(f"Failed sections: {results.failed_sections}")
        print(f"Generated files: {len(results.generated_files)}")
        print(f"Output directory: {results.output_directory}")
        print(f"Processing time: {results.processing_time:.2f}s")
        
        if results.successful_sections > 0:
            print("\\n✅ LIMITED PROCESSING TEST SUCCESSFUL!")
            print("Generated files:")
            for file_path in results.generated_files:
                if Path(file_path).exists():
                    size = Path(file_path).stat().st_size
                    print(f"  ✅ {file_path} ({size} bytes)")
                else:
                    print(f"  ❌ {file_path} (not found)")
        else:
            print("\\n❌ No sections processed successfully")
            
        # Clean up test files
        try:
            Path(test_script_path).unlink()
            Path(test_script_proper_path).unlink()
        except:
            pass
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_limited_processing()
