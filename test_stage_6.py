#!/usr/bin/env python3
"""Test Stage 6 video clipping implementation"""

import sys
import os
sys.path.append('Code')

# Test the existing Joe Rogan episode with Stage 6
episode_dir = r'C:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Content\Joe_Rogan_Experience\Joe Rogan Experience #2334 - Kash Patel'
script_path = os.path.join(episode_dir, 'Output', 'Scripts', 'unified_podcast_script.json')

print(f"Testing Stage 6 video clipping...")
print(f"Episode directory: {episode_dir}")
print(f"Script path: {script_path}")
print(f"Script exists: {os.path.exists(script_path)}")

# Check if original video exists
video_path = os.path.join(episode_dir, 'Input', 'original_video.mp4')
print(f"Video path: {video_path}")
print(f"Video exists: {os.path.exists(video_path)}")

if os.path.exists(script_path) and os.path.exists(video_path):
    print("\n" + "="*50)
    print("TESTING STAGE 6 VIDEO CLIPPING")
    print("="*50)
    
    from master_processor_v2 import MasterProcessorV2
    
    try:
        # Initialize processor
        processor = MasterProcessorV2()
        processor.episode_dir = episode_dir
        processor.original_video_path = video_path
        
        # Test Stage 6
        result = processor._stage_6_video_clipping(script_path)
        
        print("SUCCESS: Stage 6 completed!")
        print(f"Result type: {type(result)}")
        print(f"Status: {result.get('status', 'Unknown')}")
        print(f"Total clips: {result.get('total_clips', 0)}")
        print(f"Output directory: {result.get('output_directory', 'Not specified')}")
        print(f"Success rate: {result.get('success_rate', 'Unknown')}")
        
        if result.get('total_clips', 0) > 0:
            print("\nStage 6 video clipping implementation is working correctly!")
        else:
            print("\nNo clips were extracted - this may be expected if no video clips are in the script.")
            
    except Exception as e:
        print(f"ERROR: Stage 6 failed: {e}")
        import traceback
        traceback.print_exc()
else:
    print("ERROR: Required files not found for testing")
    if not os.path.exists(script_path):
        print(f"  Missing script file: {script_path}")
    if not os.path.exists(video_path):
        print(f"  Missing video file: {video_path}")
