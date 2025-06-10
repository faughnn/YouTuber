#!/usr/bin/env python3
"""Test Stage 5 with existing Joe Rogan script"""

import sys
import os
sys.path.append('Code')
from master_processor_v2 import MasterProcessorV2

# Test with existing Joe Rogan script
joe_rogan_dir = r'C:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Content\Joe_Rogan_Experience\Joe Rogan Experience #2334 - Kash Patel'
script_path = os.path.join(joe_rogan_dir, 'Output', 'Scripts', 'unified_podcast_script.json')

try:
    # Initialize processor
    processor = MasterProcessorV2()
    processor.episode_dir = joe_rogan_dir
    
    print(f"Testing Stage 5 with script file: {script_path}")
    
    # Test Stage 5
    audio_results = processor._stage_5_audio_generation(script_path)
    print(f"SUCCESS: Stage 5 completed!")
    print(f"Audio results: {audio_results}")
    
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
