#!/usr/bin/env python3
"""
Test script to demonstrate the new clip order debugging functionality.
This script will compile an existing episode and create the debugging text file.
"""

import os
import sys
from pathlib import Path

# Add the Code directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "Code"))

from Code.Video_Compilator.simple_compiler import SimpleCompiler

def test_clip_order_debug():
    """Test the new clip order debugging functionality"""
    
    # Find an existing episode to test with
    content_dir = Path("Content/Joe_Rogan_Experience")
    
    if not content_dir.exists():
        print("❌ Content directory not found")
        return False
    
    # Look for an episode with existing files
    episodes = list(content_dir.iterdir())
    test_episode = None
    
    for episode in episodes:
        if episode.is_dir():
            # Check if it has the required structure
            audio_dir = episode / "Output" / "Audio"
            video_dir = episode / "Output" / "Video"
            if audio_dir.exists() and video_dir.exists():
                # Check if it has some files
                audio_files = list(audio_dir.glob("*.wav")) + list(audio_dir.glob("*.mp3"))
                video_files = list(video_dir.glob("*.mp4"))
                if audio_files or video_files:
                    test_episode = episode
                    break
    
    if not test_episode:
        print("❌ No suitable test episode found")
        return False
    
    print(f"🎬 Testing with episode: {test_episode.name}")
    
    # Initialize the compiler
    compiler = SimpleCompiler(keep_temp_files=True, validate_segments=True)
    
    # Create a test output filename
    output_filename = f"{test_episode.name}_debug_test.mp4"
    
    print(f"📝 Compiling episode (this will create the debug file)...")
    
    try:
        # This will create both the video and the debug file
        result = compiler.compile_episode(test_episode, output_filename)
        
        if result.success:
            print(f"✅ Compilation successful!")
            print(f"📄 Video created: {result.output_path}")
            
            # Check if the debug file was created
            debug_filename = output_filename.replace('.mp4', '_clip_order.txt')
            debug_path = test_episode / "Output" / "Video" / "Final" / debug_filename
            
            if debug_path.exists():
                print(f"✅ Debug file created: {debug_path}")
                
                # Show first few lines of the debug file
                print("\n📋 Debug file contents (first 20 lines):")
                print("-" * 60)
                with open(debug_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines[:20], 1):
                        print(f"{i:2d}: {line.rstrip()}")
                    if len(lines) > 20:
                        print(f"... ({len(lines) - 20} more lines)")
                print("-" * 60)
                
                return True
            else:
                print(f"❌ Debug file was not created at: {debug_path}")
                return False
        else:
            print(f"❌ Compilation failed: {result.error}")
            return False
            
    except Exception as e:
        print(f"❌ Error during compilation: {e}")
        return False

def main():
    print("🧪 Testing Clip Order Debug Functionality")
    print("=" * 50)
    
    success = test_clip_order_debug()
    
    if success:
        print("\n🎉 Test completed successfully!")
        print("✅ The clip order debug file functionality is working correctly.")
        print("📝 Each video compilation will now create a '_clip_order.txt' file")
        print("   in the Final/ directory alongside the video file.")
    else:
        print("\n❌ Test failed!")
        print("Please check the error messages above.")

if __name__ == "__main__":
    main()
