'''
Enhanced Gemini Transcript Analyzer with Improved JSON Handling

This script analyzes JSON transcript files using Google's Gemini API with better
JSON validation and formatting to prevent malformed output.

Usage:
    python transcript_analyzer.py <transcript_json_file> [analysis_rules_file] [output_file]
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
        logging.FileHandler('transcript_analyzer.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Configuration
API_KEY = "AIzaSyCsti0qnCEKOgzAnG_w41IfMNMxkyl3ysw"

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

def analyze_with_gemini(transcript_text, analysis_rules):
    """Analyze transcript with improved JSON handling."""
    logger.info("Starting improved Gemini analysis")
    
    try:
        # Create model with specific generation config for JSON and adjusted safety settings
        model = genai.GenerativeModel(
            'gemini-2.5-flash-preview-05-20',
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,  # Lower temperature for more consistent output
                top_p=0.9,
                top_k=40,
                max_output_tokens=8000,  # Reasonable limit for JSON
                candidate_count=1,
                response_mime_type="application/json"  # Request JSON response
            ),
            safety_settings={
                'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
                'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
                'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE',
                'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE'
            }
        )
        
        prompt = create_enhanced_prompt(transcript_text, analysis_rules)
        logger.info(f"Prompt length: {len(prompt)} characters")
          # Generate response
        response = model.generate_content(prompt)
        
        # Check for safety-related blocks or empty responses
        if not response:
            logger.error("No response from Gemini")
            return None
            
        # Check finish reason before accessing text
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'finish_reason'):
                finish_reason = candidate.finish_reason
                logger.info(f"Gemini finish reason: {finish_reason}")
                
                # Handle different finish reasons
                if finish_reason == 2:  # SAFETY
                    logger.warning("Gemini blocked response due to safety concerns")
                    logger.warning("This might be due to sensitive content in the transcript")
                    return "SAFETY_BLOCKED: Content was blocked by Gemini's safety filters"
                elif finish_reason == 3:  # RECITATION
                    logger.warning("Gemini blocked response due to recitation concerns")
                    return "RECITATION_BLOCKED: Content was blocked due to potential recitation"
                elif finish_reason != 1:  # 1 = STOP (successful completion)
                    logger.warning(f"Unexpected finish reason: {finish_reason}")
                    return f"BLOCKED: Finish reason {finish_reason}"
        
        # Try to get response text
        try:
            if not response.text:
                logger.error("Empty response text from Gemini")
                return None
            response_text = response.text.strip()
        except ValueError as e:
            # This handles the "response.text quick accessor" error
            logger.error(f"Could not access response text: {e}")
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'finish_reason'):
                    logger.error(f"Finish reason: {candidate.finish_reason}")
            return "ERROR: Could not access response text"
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

def extract_and_fix_json(analysis_text):
    """Extract JSON from analysis response and fix timestamp formatting with improved validation."""
    
    try:
        logger.info("Starting JSON extraction and fixing")
        
        # Find JSON content between ```json and ```
        json_start_pos = analysis_text.find('```json')
        if json_start_pos == -1:
            # Try without backticks - look for array start
            json_start_pos = analysis_text.find('[')
            if json_start_pos == -1:
                logger.warning("No JSON content found in analysis response")
                return None
            json_start = json_start_pos
            json_end_pos = analysis_text.rfind(']') + 1
        else:
            json_end_pos = analysis_text.find('```', json_start_pos + 7)
            if json_end_pos == -1:
                # JSON continues to end of response
                json_start = analysis_text.find('\n', json_start_pos) + 1
                json_content = analysis_text[json_start:].strip()
            else:
                json_start = analysis_text.find('\n', json_start_pos) + 1
                json_content = analysis_text[json_start:json_end_pos].strip()
        
        if json_start_pos != -1 and json_end_pos != -1:
            if json_start_pos == analysis_text.find('['):
                json_content = analysis_text[json_start:json_end_pos]
            else:
                json_content = analysis_text[json_start:json_end_pos].strip()
        else:
            logger.warning("Could not find JSON boundaries")
            return None
        
        logger.info(f"Extracted JSON content (length: {len(json_content)})")
        
        # Clean and fix the JSON
        json_content = clean_json_comprehensive(json_content)
        
        # Validate the JSON
        try:
            parsed_json = json.loads(json_content)
            logger.info("JSON validation successful")
            # Re-serialize to ensure proper formatting
            return json.dumps(parsed_json, indent=2, ensure_ascii=False)
        except json.JSONDecodeError as e:
            logger.error(f"JSON validation failed: {e}")
            # Try to repair the JSON
            repaired_json = attempt_json_repair(json_content, str(e))
            if repaired_json:
                return repaired_json
            else:
                logger.error("Could not repair JSON")
                return None
                
    except Exception as e:
        logger.error(f"Error extracting JSON: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None

def clean_json_comprehensive(json_content):
    """Comprehensive JSON cleaning function."""
    logger.info("Applying comprehensive JSON cleaning")
    
    # Fix malformed timestamps by adding quotes around numeric timestamp values
    # Handle various timestamp formats: 45.31, 1.04.19, 2:45.31, etc.
    
    # Fix simple decimal timestamps (e.g., "timestamp": 45.31,)
    json_content = re.sub(
        r'"timestamp":\s*([0-9.:]+),',
        r'"timestamp": "\1",',
        json_content
    )
    
    # Fix start/end timestamps in fullerContextTimestamps
    json_content = re.sub(
        r'"start":\s*([0-9.:]+)([,}])',
        r'"start": "\1"\2',
        json_content
    )
    
    json_content = re.sub(
        r'"end":\s*([0-9.:]+)([,}])',
        r'"end": "\1"\2',
        json_content
    )
    
    # Fix trailing commas before closing brackets/braces
    json_content = re.sub(r',(\s*[}\]])', r'\1', json_content)
    
    # Fix missing commas between objects
    json_content = re.sub(r'}\s*{', r'}, {', json_content)
    
    # Fix incomplete arrays - ensure proper closure
    if json_content.strip().startswith('[') and not json_content.strip().endswith(']'):
        json_content = json_content.rstrip() + '\n]'
    
    # Fix escaped quotes in strings
    json_content = re.sub(r'\\+"', r'"', json_content)
    
    return json_content

def attempt_json_repair(json_content, error):
    """Attempt to repair JSON based on specific error."""
    logger.info(f"Attempting JSON repair for error: {error}")
    
    try:
        # Try common repairs based on error type
        if "Expecting ',' delimiter" in error:
            # Add missing commas
            json_content = re.sub(r'}\s*{', r'}, {', json_content)
            json_content = re.sub(r']\s*{', r'], {', json_content)
        
        if "Expecting property name" in error:
            # Fix unquoted property names
            json_content = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_content)
        
        # Try to parse the repaired JSON
        parsed = json.loads(json_content)
        logger.info("JSON repair successful")
        return json.dumps(parsed, indent=2, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"JSON repair failed: {e}")
    
    return None

def save_analysis_improved(analysis_result, output_file, transcript_file, rules):
    """Save analysis results to three separate files."""
    logger.info("Saving analysis results")
    
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Generate base filename without extension
        base_name = os.path.splitext(output_file)[0]
        
        # File paths for the three output files
        prompt_file = f"{base_name}_prompt.txt"
        json_file = f"{base_name}_analysis.json"
        combined_file = output_file  # Keep original name for compatibility
        
        # 1. Create prompt/instructions file
        prompt_content = f"""TRANSCRIPT ANALYSIS PROMPT/INSTRUCTIONS
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Source File: {os.path.basename(transcript_file)}

ANALYSIS RULES USED:
{'-' * 40}
{rules}
{'-' * 40}
"""
        
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(prompt_content)
        logger.info(f"Prompt saved to: {prompt_file}")
        
        # 2. Extract and save clean JSON file
        json_content = extract_and_fix_json(analysis_result)
        if json_content:
            with open(json_file, 'w', encoding='utf-8') as f:
                f.write(json_content)
            logger.info(f"Clean JSON saved to: {json_file}")
        else:
            logger.warning("Could not extract valid JSON from analysis response")
        
        # 3. Create combined analysis report (original format)
        header = f"""TRANSCRIPT ANALYSIS REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Source File: {os.path.basename(transcript_file)}
Analysis Rules Used: {os.path.basename(rules) if rules else 'Default'}

ANALYSIS RESULTS:
{'=' * 60}

"""
        
        full_output = header + analysis_result
        
        with open(combined_file, 'w', encoding='utf-8') as f:
            f.write(full_output)
        logger.info(f"Combined analysis saved to: {combined_file}")
        
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
    analysis_result = analyze_with_gemini(transcript_text, analysis_rules)
    
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
