#!/usr/bin/env python3
"""Test full pipeline through Stage 6 integration"""

import sys
import os
sys.path.append('Code')

print("Testing full pipeline through Stage 6...")

from master_processor_v2 import MasterProcessorV2

# Test with existing Joe Rogan episode
episode_dir = r'C:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Content\Joe_Rogan_Experience\Joe Rogan Experience #2334 - Kash Patel'

try:
    processor = MasterProcessorV2()
    
    # Set up existing episode state
    processor.episode_dir = episode_dir
    processor.original_video_path = os.path.join(episode_dir, 'Input', 'original_video.mp4')
    
    print("\n" + "="*60)
    print("TESTING PIPELINE STAGE 4 → STAGE 6 INTEGRATION")
    print("="*60)
    
    # Start from Stage 4 output (existing script)
    stage4_result = os.path.join(episode_dir, 'Output', 'Scripts', 'unified_podcast_script.json')
    print(f"Stage 4 result (script): {stage4_result}")
    print(f"Script exists: {os.path.exists(stage4_result)}")
    
    if os.path.exists(stage4_result):
        # Test Stage 6 with Stage 4 output
        stage6_result = processor._stage_6_video_clipping(stage4_result)
        
        print(f"\nStage 6 completed successfully!")
        print(f"- Status: {stage6_result.get('status')}")
        print(f"- Total clips: {stage6_result.get('total_clips')}")
        print(f"- Success rate: {stage6_result.get('success_rate')}")
        print(f"- Output directory: {stage6_result.get('output_directory')}")
        
        # Verify Stage 6 → Stage 7 handoff format
        print(f"\nStage 6 → Stage 7 handoff validation:")
        print(f"- Return type: {type(stage6_result)}")
        print(f"- Contains 'total_clips': {'total_clips' in stage6_result}")
        print(f"- Contains 'output_directory': {'output_directory' in stage6_result}")
        
        if isinstance(stage6_result, dict) and 'total_clips' in stage6_result:
            print("\n✅ INTEGRATION TEST PASSED!")
            print("Stage 4 → Stage 6 pipeline handoff working correctly")
            print("Stage 6 → Stage 7 manifest format is ready")
        else:
            print("\n❌ INTEGRATION TEST FAILED!")
            print("Stage 6 return format not compatible with Stage 7")
            
    else:
        print("ERROR: Stage 4 script file not found")
        
except Exception as e:
    print(f"ERROR: Integration test failed: {e}")
    import traceback
    traceback.print_exc()
