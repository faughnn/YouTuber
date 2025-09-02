#!/usr/bin/env python3
"""
Pipeline Launcher - Run from root YouTuber directory
Launches the pipeline menu from the Code subfolder
"""
import sys
import os
import subprocess
from pathlib import Path

def main():
    # Get the root directory (where this script is located)
    root_dir = Path(__file__).parent.absolute()
    code_dir = root_dir / "Code"
    
    # Verify Code directory exists
    if not code_dir.exists():
        print(f"Error: Code directory not found at {code_dir}")
        print("Make sure you're running this from the YouTuber root directory")
        return 1
    
    # Verify run_pipeline_menu.py exists
    menu_script = code_dir / "run_pipeline_menu.py"
    if not menu_script.exists():
        print(f"Error: Pipeline menu script not found at {menu_script}")
        return 1
    
    print(f"Launching pipeline from: {root_dir}")
    print(f"Code directory: {code_dir}")
    
    try:
        # The pipeline expects to be run from the Code directory for imports
        # but some config files expect paths relative to the root
        print(f"Changing to Code directory for execution")
        
        # Run from the Code directory (needed for imports to work)
        result = subprocess.run([sys.executable, "run_pipeline_menu.py"], 
                              cwd=code_dir)
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n\nPipeline interrupted by user")
        return 0
    except Exception as e:
        print(f"❌ Error running pipeline: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())