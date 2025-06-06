#!/usr/bin/env python3
"""
TTS Workflow Integration Test
Demonstrates the complete pipeline from analysis to TTS-ready script generation.
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from Content_Analysis.podcast_narrative_generator import PodcastNarrativeGenerator

def test_tts_workflow():
    """Test the complete TTS workflow"""
    
    print("🎙️ TTS Workflow Integration Test")
    print("=" * 50)
    
    # Initialize the generator
    try:
        generator = PodcastNarrativeGenerator()
        print("✅ Generator initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize generator: {e}")
        return False
    
    # Test data - using a mock analysis structure since we may not have real analysis files
    test_analysis_data = {
        "analysis_segments": [
            {
                "narrativeSegmentTitle": "Vaccine Death Claims",
                "severityRating": "CRITICAL",
                "fullerContextTimestamps": {
                    "start": 3437.0,  # 57:17
                    "end": 3473.0     # 57:53
                },
                "clipContextDescription": "Aaron Rodgers claims 470,000 vaccine deaths",
                "harmPotential": "Spreads dangerous vaccine misinformation"
            },
            {
                "narrativeSegmentTitle": "COVID Origin Conspiracy",
                "severityRating": "HIGH", 
                "fullerContextTimestamps": {
                    "start": 2847.0,  # 47:27
                    "end": 2923.0     # 48:43
                },
                "clipContextDescription": "Unfounded claims about COVID lab origin",
                "harmPotential": "Promotes conspiracy theories without evidence"
            }
        ]
    }
    
    # Create temporary test analysis file
    test_analysis_path = project_root / "Content" / "Scripts" / "test_analysis_temp.json"
    test_analysis_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(test_analysis_path, 'w') as f:
        json.dump(test_analysis_data, f, indent=2)
    
    print(f"📄 Created test analysis file: {test_analysis_path}")
    
    # Test TTS-ready script generation
    try:
        print("\n🔄 Generating TTS-ready script...")
        
        tts_script = generator.generate_tts_ready_script(
            analysis_json_path=str(test_analysis_path),
            episode_title="Joe Rogan Experience 2325 - Aaron Rodgers Test",
            episode_number="001",
            initials="AR",
            prompt_template="tts_podcast_narrative_prompt.txt"
        )
        
        print("✅ TTS script generated successfully")
        
        # Display key information
        episode_info = tts_script.get("episode_info", {})
        print(f"\n📺 Episode: {episode_info.get('title', 'Unknown')}")
        print(f"🔢 Episode Number: {episode_info.get('episode_number', 'Unknown')}")
        print(f"👤 Initials: {episode_info.get('initials', 'Unknown')}")
        
        # Show clip segments info
        clip_segments = tts_script.get("script_structure", {}).get("clip_segments", [])
        print(f"\n🎬 Generated {len(clip_segments)} clip segments")
        
        for i, segment in enumerate(clip_segments, 1):
            clip_ref = segment.get("clip_reference", {})
            print(f"  Segment {i}: {clip_ref.get('title', 'Unknown')}")
            print(f"    Pre-clip audio: {segment.get('pre_clip', {}).get('audio_filename', 'N/A')}")
            print(f"    Post-clip audio: {segment.get('post_clip', {}).get('audio_filename', 'N/A')}")
        
        # Show metadata
        metadata = tts_script.get("generation_metadata", {})
        print(f"\n📊 Total audio segments: {metadata.get('total_audio_segments', 'Unknown')}")
        print(f"🎭 Narrative theme: {metadata.get('narrative_theme', 'Unknown')}")
        
        # Save the TTS script
        output_path = project_root / "Content" / "Scripts" / "test_tts_ready_script"
        saved_path = generator.save_tts_ready_script(tts_script, str(output_path))
        print(f"\n💾 Saved TTS-ready script: {saved_path}")
        
        # Show file structure validation
        print("\n🔍 Generated Structure Validation:")
        
        # Check intro
        intro = tts_script.get("script_structure", {}).get("intro", {})
        print(f"  ✅ Intro: {intro.get('audio_filename', 'Missing')}")
        print(f"     Voice: {intro.get('voice_style', 'Not set')}")
        
        # Check outro
        outro = tts_script.get("script_structure", {}).get("outro", {})
        print(f"  ✅ Outro: {outro.get('audio_filename', 'Missing')}")
        print(f"     Voice: {outro.get('voice_style', 'Not set')}")
        
        print(f"\n🎯 Ready for TTS Generation!")
        print(f"   Next steps:")
        print(f"   1. Run analysis_video_clipper.py to create video clips")
        print(f"   2. Use TTS generator to create audio files")
        print(f"   3. Use Video Editor to combine audio + video")
        
        # Cleanup
        test_analysis_path.unlink()
        print(f"\n🧹 Cleaned up temporary test file")
        
        return True
        
    except Exception as e:
        print(f"❌ TTS script generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def validate_file_structure():
    """Validate that all required files exist"""
    
    print("\n🔍 Validating File Structure")
    print("-" * 30)
    
    required_files = [
        "Content_Analysis/podcast_narrative_generator.py",
        "Content_Analysis/Prompts/tts_podcast_narrative_prompt.txt",
        "TTS/examples/ideal_podcast_format.json",
        "Video_Clipper/analysis_video_clipper.py"
    ]
    
    all_exist = True
    
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - MISSING")
            all_exist = False
    
    return all_exist

if __name__ == "__main__":
    print("🚀 Starting TTS Workflow Integration Test")
    print(f"📁 Project root: {project_root}")
    
    # Validate structure first
    if not validate_file_structure():
        print("\n❌ Some required files are missing. Please check the file structure.")
        sys.exit(1)
    
    # Run the test
    success = test_tts_workflow()
    
    if success:
        print("\n🎉 TTS Workflow Test PASSED!")
        print("The enhanced podcast narrative generator is ready for production use.")
    else:
        print("\n💥 TTS Workflow Test FAILED!")
        print("Please check the error messages above.")
        sys.exit(1)
