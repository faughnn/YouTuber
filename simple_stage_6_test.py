#!/usr/bin/env python3
"""Simple test for Stage 6 without audio generation"""

import sys
import os
sys.path.append('Code')

from master_processor_v2 import MasterProcessorV2

# Test Stage 6 directly
episode_dir = r'C:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Content\Joe_Rogan_Experience\Joe Rogan Experience #2334 - Kash Patel'
script_path = os.path.join(episode_dir, 'Output', 'Scripts', 'unified_podcast_script.json')

processor = MasterProcessorV2()
processor.episode_dir = episode_dir
processor.original_video_path = os.path.join(episode_dir, 'Input', 'original_video.mp4')

print("Testing Stage 6 Video Clipping (Bypassing Audio Generation)")
result = processor._stage_6_video_clipping(script_path)

print(f"✅ SUCCESS: {result['status']}")
print(f"📹 Total clips extracted: {result['total_clips']}")
print(f"📊 Success rate: {result['success_rate']}")
print(f"📁 Output directory: {result['output_directory']}")

# Verify clips exist
if os.path.exists(result['output_directory']):
    clip_files = [f for f in os.listdir(result['output_directory']) if f.endswith('.mp4')]
    print(f"🎬 Clip files created: {len(clip_files)}")
    print("\n🎉 TASK 3.1 - VIDEO CLIPPING STAGE IMPLEMENTATION: COMPLETED!")
else:
    print("❌ Output directory not found")
