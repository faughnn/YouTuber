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

# Extract JSON content
json_start_pos = content.find('```json')
json_end_pos = content.find('```', json_start_pos + 7)
json_start = content.find('\n', json_start_pos) + 1
json_content = content[json_start:json_end_pos].strip()

# Fix the malformed timestamps by adding quotes around timestamp values
# This regex finds timestamp entries like "timestamp": 1.0.8, and quotes the value
fixed_content = re.sub(
    r'"timestamp":\s*([0-9]+\.[0-9]+\.[0-9]+),',
    r'"timestamp": "\1",',
    json_content
)

# Also fix simple decimal timestamps that might not be quoted
fixed_content = re.sub(
    r'"timestamp":\s*([0-9]+\.[0-9]+),',
    r'"timestamp": "\1",',
    fixed_content
)

print("Attempting to parse fixed JSON...")

try:
    data = json.loads(fixed_content)
    print(f"Successfully parsed! Found {len(data)} segments")
    
    # Show structure
    for i, segment in enumerate(data[:3]):  # Show first 3 segments
        print(f"\nSegment {i+1}:")
        print(f"  Title: {segment.get('narrativeSegmentTitle', 'No title')}")
        print(f"  Severity: {segment.get('severityRating', 'Unknown')}")
        timestamps = segment.get('fullerContextTimestamps', {})
        print(f"  Timestamps: {timestamps}")
        
except json.JSONDecodeError as e:
    print(f"Still have JSON Error at line {e.lineno}, column {e.colno}: {e.msg}")
    
    # Show context around error
    lines = fixed_content.split('\n')
    error_line = e.lineno - 1
    start_line = max(0, error_line - 2)
    end_line = min(len(lines), error_line + 3)
    
    print(f"\nContext around error (lines {start_line+1}-{end_line}):")
    for i in range(start_line, end_line):
        marker = " --> " if i == error_line else "     "
        line_content = lines[i] if i < len(lines) else ''
        print(f"{marker}Line {i+1}: {repr(line_content[:100])}")

# Save the fixed JSON for testing
with open(r"c:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Scripts\Video Clipper\fixed_analysis.json", 'w', encoding='utf-8') as f:
    f.write(fixed_content)
    
print("\nSaved fixed JSON to fixed_analysis.json")
