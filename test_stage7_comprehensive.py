#!/usr/bin/env python3
"""Comprehensive test for Stage 7 video compilation"""

import sys
import os
sys.path.append('Code')

print("Starting comprehensive Stage 7 test...")

# Test the existing Joe Rogan episode with Stage 7
episode_dir = r'C:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Content\Joe_Rogan_Experience\Joe Rogan Experience #2334 - Kash Patel'
audio_dir = os.path.join(episode_dir, 'Output', 'Audio')
video_dir = os.path.join(episode_dir, 'Output', 'Video')

print(f"Episode directory: {episode_dir}")
print(f"Audio directory exists: {os.path.exists(audio_dir)}")
print(f"Video directory exists: {os.path.exists(video_dir)}")

if os.path.exists(audio_dir) and os.path.exists(video_dir):
    # Count audio and video files
    audio_files = [f for f in os.listdir(audio_dir) if f.endswith('.wav')]
    video_files = [f for f in os.listdir(video_dir) if f.endswith('.mp4')]
    
    print(f"Audio files found: {len(audio_files)}")
    print(f"Video files found: {len(video_files)}")
    
    if len(audio_files) > 0 and len(video_files) > 0:
        print("\nImporting MasterProcessorV2...")
        from master_processor_v2 import MasterProcessorV2
        
        print("Creating processor instance...")
        processor = MasterProcessorV2()
        processor.episode_dir = episode_dir
        
        # Create mock Stage 5 result (audio paths)
        stage5_result = {
            'status': 'success',
            'total_sections': len(audio_files),
            'successful_sections': len(audio_files),
            'output_directory': audio_dir,
            'generated_files': audio_files
        }
        
        # Create mock Stage 6 result (video clips manifest)
        stage6_result = {
            'status': 'completed',
            'total_clips': len(video_files),
            'clips_failed': 0,
            'output_directory': video_dir,
            'success_rate': '100%'
        }
        
        print(f"Mock Stage 5 data: {len(audio_files)} audio files")
        print(f"Mock Stage 6 data: {len(video_files)} video clips")
        
        try:
            print("\nRunning Stage 7 video compilation...")
            result = processor._stage_7_video_compilation(stage5_result, stage6_result)
            
            print(f"✅ SUCCESS: Stage 7 completed!")
            print(f"📄 Final video path: {result}")
            print(f"📁 Final video exists: {os.path.exists(result)}")
            
            if os.path.exists(result):
                file_size_mb = os.path.getsize(result) / (1024 * 1024)
                print(f"📊 Final video size: {file_size_mb:.1f} MB")
                print("\n🎉 TASK 3.2 - VIDEO COMPILATION STAGE IMPLEMENTATION: COMPLETED!")
            else:
                print("❌ Final video was not created")
                
        except Exception as e:
            print(f"❌ ERROR: Stage 7 failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("❌ Not enough audio or video files for testing")
        print(f"   Audio files: {len(audio_files)}")
        print(f"   Video files: {len(video_files)}")
else:
    print("❌ Required directories not found")
    if not os.path.exists(audio_dir):
        print(f"   Missing: {audio_dir}")
    if not os.path.exists(video_dir):
        print(f"   Missing: {video_dir}")
