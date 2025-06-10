#!/usr/bin/env python3
"""Test Stages 4 and 5 with Joe Rogan episode"""

import sys
import os
sys.path.append('Code')
from master_processor_v2 import MasterProcessorV2

# Test with existing Joe Rogan analysis
joe_rogan_dir = r'C:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Content\Joe_Rogan_Experience\Joe Rogan Experience #2334 - Kash Patel'
analysis_path = os.path.join(joe_rogan_dir, 'Processing', 'original_audio_full_transcript_analysis_results.json')

try:
    # Initialize processor
    processor = MasterProcessorV2()
    processor.episode_dir = joe_rogan_dir
    
    print(f"Testing Stage 4 with analysis file: {analysis_path}")
    
    # Test Stage 4
    script_path = processor._stage_4_narrative_generation(analysis_path)
    print(f"SUCCESS: Stage 4 completed! Script path: {script_path}")
    
    # Test Stage 5
    print(f"Testing Stage 5 with script file: {script_path}")
    audio_results = processor._stage_5_audio_generation(script_path)
    print(f"SUCCESS: Stage 5 completed! Audio results: {audio_results}")
    
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
