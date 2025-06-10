#!/usr/bin/env python3
"""Test Stage 4 narrative generation with Joe Rogan analysis file"""

import sys
import os
sys.path.append('Code')
from Content_Analysis.podcast_narrative_generator import NarrativeCreatorGenerator

# Test with Joe Rogan analysis file
analysis_path = r'C:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Content\Joe_Rogan_Experience\Joe Rogan Experience #2334 - Kash Patel\Processing\original_audio_full_transcript_analysis_results.json'
episode_title = 'Joe Rogan Experience #2334 - Kash Patel'

try:
    generator = NarrativeCreatorGenerator()
    script_data = generator.generate_unified_narrative(analysis_path, episode_title)
    print('SUCCESS: Narrative generation worked!')
    print(f'Script data type: {type(script_data)}')
    if isinstance(script_data, dict) and 'podcast_sections' in script_data:
        print(f'Number of podcast sections: {len(script_data["podcast_sections"])}')
    else:
        print('Script data structure:', list(script_data.keys()) if isinstance(script_data, dict) else 'Not a dict')
    
    # Now save the script to file
    episode_output_path = r'C:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Content\Joe_Rogan_Experience\Joe Rogan Experience #2334 - Kash Patel\Output'
    saved_path = generator.save_unified_script(script_data, episode_output_path)
    print(f'SUCCESS: Script saved to {saved_path}')
    
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
