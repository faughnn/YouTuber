#!/usr/bin/env python3
import sys
import os
sys.path.append('Code')

try:
    from master_processor_v2 import MasterProcessorV2
    print("✅ Import successful")
    
    # Test basic instantiation
    processor = MasterProcessorV2()
    print("✅ Processor created")
    
    # Test Stage 7 method exists
    if hasattr(processor, '_stage_7_video_compilation'):
        print("✅ Stage 7 method exists")
    else:
        print("❌ Stage 7 method missing")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
