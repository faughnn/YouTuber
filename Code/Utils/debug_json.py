import re
import json
import sys
import os

# Add project paths for portable path discovery
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project_paths import get_transcripts_dir

# Use discoverable path instead of hardcoded absolute path
transcripts_dir = get_transcripts_dir()
sample_file = transcripts_dir / "Joe_Rogan_Experience" / "Joe Rogan Experience 2325 - Aaron Rodgers" / "Joe_Rogan_Experience_2325_TOP10_WORST.txt"

# Check if file exists before trying to read it
if not sample_file.exists():
    print(f"Sample file not found at: {sample_file}")
    print("This debug utility requires existing episode data to work.")
    sys.exit(1)

# Read the analysis file
with open(sample_file, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"File length: {len(content)} characters")

# Look for JSON markers
json_start_pos = content.find('```json')
json_end_pos = content.find('```', json_start_pos + 7)

print(f"JSON start position: {json_start_pos}")
print(f"JSON end position: {json_end_pos}")

if json_start_pos != -1 and json_end_pos != -1:
    # Extract the content between markers
    json_start = content.find('\n', json_start_pos) + 1
    json_content = content[json_start:json_end_pos].strip()
    
    print(f"JSON content length: {len(json_content)}")
    print("First 200 characters:")
    print(repr(json_content[:200]))
    
    # Try to parse
    try:
        data = json.loads(json_content)
        print(f"Successfully parsed! Found {len(data)} segments")
        
        # Show first segment structure
        if data:
            print("\nFirst segment keys:")
            print(list(data[0].keys()))
            
    except json.JSONDecodeError as e:
        print(f"JSON Error at line {e.lineno}, column {e.colno}: {e.msg}")
        
        # Show context around error
        lines = json_content.split('\n')
        error_line = e.lineno - 1
        start_line = max(0, error_line - 2)
        end_line = min(len(lines), error_line + 3)
        
        print(f"\nContext around error (lines {start_line+1}-{end_line}):")
        for i in range(start_line, end_line):
            marker = " --> " if i == error_line else "     "
            line_content = lines[i] if i < len(lines) else ''
            print(f"{marker}Line {i+1}: {repr(line_content)}")
else:
    print("Could not find JSON markers")
