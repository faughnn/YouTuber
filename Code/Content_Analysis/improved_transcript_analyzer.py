'''
Enhanced Gemini Transcript Analyzer with Improved JSON Handling

This script analyzes JSON transcript files using Google's Gemini API with better
JSON validation and formatting to prevent malformed output.

Usage:
    python improved_transcript_analyzer.py <transcript_json_file> [analysis_rules_file] [output_file]
'''

import sys
import os
import json
import google.generativeai as genai
from datetime import datetime
import logging
import traceback
import re

# Set up extensive logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('improved_transcript_analyzer.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Configuration
API_KEY = "AIzaSyCsti0qnCEKOgzAnG_w41IfMNMxkyl3ysw"
MAX_CHUNK_SIZE = 800000
OVERLAP_SIZE = 2000

def configure_gemini():
    """Configure the Gemini API key."""
    logger.info("Starting Gemini API configuration")
    try:
        if API_KEY:
            genai.configure(api_key=API_KEY)
            logger.info("Gemini API configured successfully")
            return True
        else:
            logger.error("No API key found")
            return False
    except Exception as e:
        logger.error(f"Error configuring Gemini API: {e}")
        return False

def load_transcript(file_path):
    """Load and parse the JSON transcript file."""
    logger.info(f"Loading transcript from: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            transcript_data = json.load(f)
        
        segments = transcript_data.get('segments', [])
        if not segments:
            raise ValueError("No segments found in transcript file")
        
        # Build full transcript text
        full_text = "TRANSCRIPT METADATA:\n"
        metadata = transcript_data.get('metadata', {})
        full_text += f"Language: {metadata.get('language', 'unknown')}\n"
        full_text += f"Total Segments: {len(segments)}\n\n"
        full_text += "TRANSCRIPT:\n\n"
        
        for segment in segments:
            start_time = segment.get('start', 0)
            minutes = int(start_time // 60)
            seconds = start_time % 60
            timestamp = f"{minutes}:{seconds:05.2f}"
            
            text = segment.get('text', '').strip()
            if text:
                full_text += f"[{timestamp}] {text}\n"
        
        logger.info(f"Full transcript length: {len(full_text)} characters")
        return full_text, metadata
        
    except Exception as e:
        logger.error(f"Error loading transcript: {e}")
        return None, None

def load_analysis_rules(rules_file):
    """Load analysis rules from file."""
    logger.info(f"Loading analysis rules from: {rules_file}")
    
    try:
        with open(rules_file, 'r', encoding='utf-8') as f:
            rules = f.read().strip()
        logger.info(f"Loaded analysis rules: {len(rules)} characters")
        return rules
        
    except Exception as e:
        logger.error(f"Error loading analysis rules: {e}")
        return None

def create_enhanced_prompt(transcript_text, analysis_rules):
    """Create an enhanced prompt with strict JSON formatting instructions."""
    
    prompt = f"""You are an expert content analyst. Analyze the following transcript using the provided rules.

CRITICAL INSTRUCTIONS FOR JSON OUTPUT:
1. MUST output valid JSON array format
2. MAXIMUM 20 segments total (as specified in rules)
3. If approaching character limits, stop immediately and close JSON properly with ]
4. Each entry MUST have ALL required fields
5. Use proper JSON escaping for quotes in text
6. Timestamps should be strings (e.g., "1:23.45")
7. End with a complete, valid JSON array

ANALYSIS RULES:
{analysis_rules}

TRANSCRIPT TO ANALYZE:
{transcript_text}

OUTPUT FORMAT - Return ONLY valid JSON (no markdown, no explanations):
[
  {{
    "narrativeSegmentTitle": "Brief title",
    "severityRating": "HIGH/CRITICAL",
    "relevantChecklistTheme": "Theme from rules",
    "relevantChecklistIndicator": "Indicator from rules", 
    "indicatorEvidenceFromChecklist": "Evidence explanation",
    "clipContextDescription": "Context description",
    "reasonForSelection": "Why selected",
    "suggestedClip": [
      {{
        "timestamp": "MM:SS.ss",
        "speaker": "SPEAKER_XX (Name)",
        "quote": "Exact quote"
      }}
    ],
    "fullerContextTimestamps": {{
      "start": "MM:SS.ss",
      "end": "MM:SS.ss"
    }},
    "segmentDurationInSeconds": 60.0,
    "harmPotential": "Harm explanation"
  }}
]

Begin JSON output now:"""
    
    return prompt

def analyze_with_gemini_improved(transcript_text, analysis_rules):
    """Analyze transcript with improved JSON handling."""
    logger.info("Starting improved Gemini analysis")
    
    try:
        # Create model with specific generation config for JSON
        model = genai.GenerativeModel(
            'gemini-1.5-flash',
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,  # Lower temperature for more consistent output
                top_p=0.9,
                top_k=40,
                max_output_tokens=8000,  # Reasonable limit for JSON
                candidate_count=1,
                response_mime_type="application/json"  # Request JSON response
            )
        )
        
        prompt = create_enhanced_prompt(transcript_text, analysis_rules)
        logger.info(f"Prompt length: {len(prompt)} characters")
        
        # Generate response
        response = model.generate_content(prompt)
        
        if not response or not response.text:
            logger.error("Empty response from Gemini")
            return None
            
        response_text = response.text.strip()
        logger.info(f"Received response length: {len(response_text)} characters")
        
        # Validate and clean JSON
        cleaned_json = validate_and_clean_json(response_text)
        
        if cleaned_json:
            logger.info("JSON validation successful")
            return cleaned_json
        else:
            logger.error("JSON validation failed")
            return response_text  # Return raw response for manual inspection
            
    except Exception as e:
        logger.error(f"Error in Gemini analysis: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None

def validate_and_clean_json(response_text):
    """Validate and clean JSON response."""
    logger.info("Validating and cleaning JSON")
    
    try:
        # Try to parse as-is first
        try:
            parsed = json.loads(response_text)
            logger.info("JSON parsed successfully without cleaning")
            return json.dumps(parsed, indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            logger.info("Initial JSON parse failed, attempting to clean")
        
        # Extract JSON if wrapped in markdown
        json_content = response_text
        if '```json' in response_text:
            start = response_text.find('```json') + 7
            end = response_text.find('```', start)
            if end == -1:
                json_content = response_text[start:].strip()
            else:
                json_content = response_text[start:end].strip()
        
        # Clean common JSON issues
        json_content = clean_json_issues(json_content)
        
        # Validate the cleaned JSON
        parsed = json.loads(json_content)
        
        # Additional validation - ensure it's an array and has required fields
        if not isinstance(parsed, list):
            logger.error("JSON is not an array")
            return None
            
        # Validate each entry has required fields
        required_fields = [
            'narrativeSegmentTitle', 'severityRating', 'relevantChecklistTheme',
            'relevantChecklistIndicator', 'harmPotential'
        ]
        
        valid_entries = []
        for entry in parsed:
            if isinstance(entry, dict) and all(field in entry for field in required_fields):
                valid_entries.append(entry)
            else:
                logger.warning(f"Skipping invalid entry: {entry}")
        
        if not valid_entries:
            logger.error("No valid entries found")
            return None
            
        logger.info(f"Validated {len(valid_entries)} entries")
        return json.dumps(valid_entries, indent=2, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"JSON validation error: {e}")
        return None

def clean_json_issues(json_content):
    """Clean common JSON formatting issues."""
    logger.info("Cleaning JSON formatting issues")
    
    # Fix unquoted timestamps
    json_content = re.sub(r'"timestamp":\s*([0-9]+[:.][0-9]+[:.]*[0-9]*),', r'"timestamp": "\1",', json_content)
    json_content = re.sub(r'"start":\s*([0-9]+[:.][0-9]+[:.]*[0-9]*),', r'"start": "\1",', json_content)
    json_content = re.sub(r'"end":\s*([0-9]+[:.][0-9]+[:.]*[0-9]*)', r'"end": "\1"', json_content)
    
    # Fix trailing commas
    json_content = re.sub(r',(\s*[}\]])', r'\1', json_content)
    
    # Fix missing commas between objects
    json_content = re.sub(r'}\s*{', r'}, {', json_content)
    
    # Ensure proper array closure
    if not json_content.strip().endswith(']'):
        json_content = json_content.rstrip() + '\n]'
    
    return json_content

def save_analysis_improved(analysis_result, output_file, transcript_file, rules):
    """Save analysis with improved error handling."""
    logger.info("Saving analysis results")
    
    try:
        # Save raw analysis
        with open(output_file, 'w', encoding='utf-8') as f:
            header = f"""TRANSCRIPT ANALYSIS REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Source File: {os.path.basename(transcript_file)}
Analysis Rules Used: {os.path.basename(rules) if rules else 'Default'}

ANALYSIS RESULTS:
{'=' * 60}

{analysis_result}
"""
            f.write(header)
        
        # Try to save JSON version
        if analysis_result.strip().startswith('['):
            try:
                json_file = output_file.replace('.txt', '_analysis.json')
                with open(json_file, 'w', encoding='utf-8') as f:
                    f.write(analysis_result)
                logger.info(f"JSON analysis saved to: {json_file}")
            except Exception as e:
                logger.warning(f"Could not save JSON version: {e}")
        
        logger.info(f"Analysis saved to: {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving analysis: {e}")
        return False

def main():
    """Main function with improved error handling."""
    logger.info("=== IMPROVED TRANSCRIPT ANALYZER STARTED ===")
    
    if len(sys.argv) < 2:
        print("Usage: python improved_transcript_analyzer.py <transcript_json_file> [analysis_rules_file] [output_file]")
        sys.exit(1)
    
    transcript_file = sys.argv[1]
    rules_file = sys.argv[2] if len(sys.argv) > 2 else None
    output_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Generate default output file
    if not output_file:
        base_name = os.path.splitext(os.path.basename(transcript_file))[0]
        transcript_dir = os.path.dirname(transcript_file)
        output_file = os.path.join(transcript_dir, f"{base_name}_improved_analysis.txt")
    
    print(f"🚀 Starting Improved Transcript Analysis")
    print(f"📁 Transcript: {transcript_file}")
    print(f"📋 Rules: {rules_file}")
    print(f"📄 Output: {output_file}")
    
    # Configure Gemini
    if not configure_gemini():
        sys.exit(1)
    
    # Load transcript
    print("\n📖 Loading transcript...")
    transcript_text, metadata = load_transcript(transcript_file)
    if not transcript_text:
        print("❌ Failed to load transcript")
        sys.exit(1)
    print(f"✅ Loaded transcript ({len(transcript_text)} characters)")
    
    # Load analysis rules
    print("\n📋 Loading analysis rules...")
    analysis_rules = load_analysis_rules(rules_file) if rules_file else ""
    if not analysis_rules and rules_file:
        print("❌ Failed to load analysis rules")
        sys.exit(1)
    print(f"✅ Loaded analysis rules ({len(analysis_rules)} characters)")
    
    # Analyze with improved method
    print("\n🤖 Analyzing with improved JSON handling...")
    analysis_result = analyze_with_gemini_improved(transcript_text, analysis_rules)
    
    if not analysis_result:
        print("❌ Analysis failed")
        sys.exit(1)
    
    # Save results
    print("\n💾 Saving analysis...")
    if save_analysis_improved(analysis_result, output_file, transcript_file, rules_file):
        print(f"🎉 Analysis complete! Results saved to: {output_file}")
        
        # Show preview
        print("\n📄 Preview of analysis:")
        print("-" * 60)
        preview = analysis_result[:500] + "..." if len(analysis_result) > 500 else analysis_result
        print(preview)
        print("-" * 60)
    else:
        print("❌ Failed to save analysis")
        print(analysis_result)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"❌ Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)
