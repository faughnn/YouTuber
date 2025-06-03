#!/usr/bin/env python3
"""
Analysis Continuation Script

This script detects incomplete analysis files and continues the analysis from where it was cut off.
It specifically handles cases where Gemini's response was truncated due to length limits.
"""

import sys
import os
import json
import google.generativeai as genai
import re
from datetime import datetime
import logging
import traceback

# API Key (same as main analyzer)
API_KEY = "AIzaSyCsti0qnCEKOgzAnG_w41IfMNMxkyl3ysw"

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('continue_analysis.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def configure_gemini():
    """Configure the Gemini API key."""
    try:
        genai.configure(api_key=API_KEY)
        return True
    except Exception as e:
        logger.error(f"Error configuring Gemini API: {e}")
        return False

def load_transcript(file_path):
    """Load and parse the JSON transcript file."""
    try:
        logger.info(f"Loading transcript from: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
          # Convert to text format with timestamps
        transcript_lines = []
        for segment in data.get('segments', []):
            start_time = segment.get('start_time', 0)  # Fixed: use 'start_time' not 'start'
            speaker = segment.get('speaker', 'UNKNOWN')
            text = segment.get('text', '').strip()
            if text:
                transcript_lines.append(f"{start_time:.2f} | {speaker}: {text}")
        
        transcript_text = '\n'.join(transcript_lines)
        logger.info(f"Transcript loaded successfully ({len(transcript_text)} characters)")
        return transcript_text, data
    except Exception as e:
        logger.error(f"Error loading transcript: {e}")
        return None, None

def find_last_complete_timestamp(analysis_content):
    """Find the last complete timestamp in the analysis to determine where to continue."""
    # Look for timestamp patterns in the analysis
    timestamp_matches = re.findall(r'"timestamp":\s*([\d.]+)', analysis_content)
    if timestamp_matches:
        last_timestamp = float(timestamp_matches[-1])
        logger.info(f"Last complete timestamp found: {last_timestamp}")
        return last_timestamp
    return 0

def get_transcript_from_timestamp(transcript_text, start_timestamp):
    """Get the portion of transcript starting from a specific timestamp."""
    lines = transcript_text.split('\n')
    remaining_lines = []
    
    for line in lines:
        if '|' in line:
            timestamp_part = line.split('|')[0].strip()
            try:
                line_timestamp = float(timestamp_part)
                if line_timestamp >= start_timestamp:
                    remaining_lines.append(line)
            except ValueError:
                continue
    
    return '\n'.join(remaining_lines)

def continue_analysis_with_gemini(remaining_transcript, analysis_rules, last_timestamp):
    """Continue the analysis from where it left off."""
    try:
        model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
        
        prompt = f"""You are continuing a comprehensive analysis that was cut off due to length limits. 

ANALYSIS RULES:
{analysis_rules}

CONTEXT: You were analyzing a Joe Rogan Experience transcript and your response was cut off at timestamp {last_timestamp}. Please continue the analysis from this point forward, maintaining the same JSON format and style.

IMPORTANT: Pick up exactly where the previous analysis left off. Do not restart or repeat earlier content. Continue with the same JSON structure.

REMAINING TRANSCRIPT TO ANALYZE (starting from timestamp {last_timestamp}):
{remaining_transcript}

Please continue the analysis in the same JSON format, starting immediately with the continuation of the analysis."""

        logger.info(f"Sending continuation prompt to Gemini (length: {len(prompt)} characters)")
        response = model.generate_content(prompt)
        
        if response.text:
            logger.info(f"Received continuation response ({len(response.text)} characters)")
            return response.text
        else:
            logger.error("Empty response from Gemini")
            return None
            
    except Exception as e:
        logger.error(f"Error during continuation analysis: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python continue_analysis.py <incomplete_analysis_file>")
        sys.exit(1)
    
    analysis_file = sys.argv[1]
    
    if not os.path.exists(analysis_file):
        print(f"Error: Analysis file not found: {analysis_file}")
        sys.exit(1)
    
    # Determine the transcript file path
    analysis_dir = os.path.dirname(analysis_file)
    episode_name = os.path.basename(analysis_file).replace('_analysis.txt', '')
    transcript_file = os.path.join(analysis_dir, f"{episode_name}.json")
    
    if not os.path.exists(transcript_file):
        print(f"Error: Transcript file not found: {transcript_file}")
        sys.exit(1)
    
    # Load the analysis rules (look for JoeRoganAnalysisRules.txt in the script directory)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    rules_file = os.path.join(script_dir, "JoeRoganAnalysisRules.txt")
    
    if not os.path.exists(rules_file):
        print(f"Error: Analysis rules file not found: {rules_file}")
        sys.exit(1)
    
    print(f"🔄 Continuing analysis for: {episode_name}")
    print(f"📄 Incomplete analysis: {analysis_file}")
    print(f"📋 Transcript file: {transcript_file}")
    print(f"📜 Rules file: {rules_file}")
    
    # Configure Gemini
    if not configure_gemini():
        print("❌ Failed to configure Gemini API")
        sys.exit(1)
    
    # Load existing analysis
    print("\n📖 Loading incomplete analysis...")
    with open(analysis_file, 'r', encoding='utf-8') as f:
        existing_analysis = f.read()
    
    # Find where it was cut off
    last_timestamp = find_last_complete_timestamp(existing_analysis)
    print(f"⏰ Last complete timestamp: {last_timestamp}")
    
    # Load transcript
    print("📖 Loading transcript...")
    transcript_text, _ = load_transcript(transcript_file)
    if not transcript_text:
        print("❌ Failed to load transcript")
        sys.exit(1)
    
    # Get remaining transcript
    remaining_transcript = get_transcript_from_timestamp(transcript_text, last_timestamp)
    print(f"📊 Remaining transcript length: {len(remaining_transcript)} characters")
    
    # Load analysis rules
    print("📋 Loading analysis rules...")
    with open(rules_file, 'r', encoding='utf-8') as f:
        analysis_rules = f.read()
    
    # Continue analysis
    print("\n🤖 Continuing analysis with Gemini...")
    continuation = continue_analysis_with_gemini(remaining_transcript, analysis_rules, last_timestamp)
    
    if continuation:
        # Create backup of original
        backup_file = analysis_file + f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(existing_analysis)
        print(f"💾 Created backup: {backup_file}")
        
        # Append continuation to original file
        with open(analysis_file, 'a', encoding='utf-8') as f:
            f.write(continuation)
        
        print(f"✅ Analysis continued successfully!")
        print(f"📄 Updated file: {analysis_file}")
        print(f"📊 Added {len(continuation)} characters")
        
        # Check if this continuation also appears incomplete
        if not continuation.strip().endswith('}') and not continuation.strip().endswith(']'):
            print("\n⚠️  Warning: The continuation may also be incomplete.")
            print("You can run this script again to continue further.")
    else:
        print("❌ Failed to continue analysis")
        sys.exit(1)

if __name__ == "__main__":
    main()
