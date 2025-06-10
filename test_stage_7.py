#!/usr/bin/env python3
"""Test Stage 7 video compilation implementation"""

import sys
import os
sys.path.append('Code')

# Test the existing Joe Rogan episode with Stage 7
episode_dir = r'C:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Content\Joe_Rogan_Experience\Joe Rogan Experience #2334 - Kash Patel'
script_path = os.path.join(episode_dir, 'Output', 'Scripts', 'unified_podcast_script.json')

print(f"Testing Stage 7 video compilation...")
print(f"Episode directory: {episode_dir}")
print(f"Script path: {script_path}")
print(f"Script exists: {os.path.exists(script_path)}")

# Check if audio files exist
audio_dir = os.path.join(episode_dir, 'Output', 'Audio')
print(f"Audio directory: {audio_dir}")
print(f"Audio directory exists: {os.path.exists(audio_dir)}")

# Check if video clips exist
video_dir = os.path.join(episode_dir, 'Output', 'Video')
print(f"Video clips directory: {video_dir}")
print(f"Video clips directory exists: {os.path.exists(video_dir)}")

if os.path.exists(audio_dir) and os.path.exists(video_dir):
    print("\n" + "="*50)
    print("TESTING STAGE 7 VIDEO COMPILATION")
    print("="*50)
    
    from master_processor_v2 import MasterProcessorV2
    
    try:
        # Initialize processor
        processor = MasterProcessorV2()
        processor.episode_dir = episode_dir
        
        # Create mock Stage 5 result (audio paths)
        audio_files = [f for f in os.listdir(audio_dir) if f.endswith('.wav')]
        stage5_result = {
            'status': 'success',
            'total_sections': len(audio_files),
            'successful_sections': len(audio_files),
            'output_directory': audio_dir,
            'generated_files': audio_files
        }
        
        # Create mock Stage 6 result (video clips manifest)
        video_files = [f for f in os.listdir(video_dir) if f.endswith('.mp4')]
        stage6_result = {
            'status': 'completed',
            'total_clips': len(video_files),
            'clips_failed': 0,
            'output_directory': video_dir,
            'success_rate': '100%'
        }
        
        print(f"Mock Stage 5 audio files: {len(audio_files)} files")
        print(f"Mock Stage 6 video clips: {len(video_files)} clips")
        print()
        
        # Test Stage 7
        print("Running Stage 7...")
        result = processor._stage_7_video_compilation(stage5_result, stage6_result)
        
        print("SUCCESS: Stage 7 completed!")
        print(f"Final video path: {result}")
        print(f"Final video exists: {os.path.exists(result)}")
        
        if os.path.exists(result):
            file_size_mb = os.path.getsize(result) / (1024 * 1024)
            print(f"Final video size: {file_size_mb:.1f} MB")
            print("\n🎉 TASK 3.2 - VIDEO COMPILATION STAGE IMPLEMENTATION: COMPLETED!")
        else:
            print("❌ Final video was not created")
            
    except Exception as e:
        print(f"ERROR: Stage 7 failed: {e}")
        import traceback
        traceback.print_exc()
else:
    print("ERROR: Required directories not found for testing")
    if not os.path.exists(audio_dir):
        print(f"  Missing audio directory: {audio_dir}")
    if not os.path.exists(video_dir):
        print(f"  Missing video directory: {video_dir}")
