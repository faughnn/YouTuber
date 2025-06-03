'''
Enhanced Gemini Transcript Analyzer

This script analyzes JSON transcript files using Google's Gemini API.
It can handle large transcripts by chunking them and supports custom analysis rules.

Usage:
    python transcript_analyzer.py <transcript_json_file> [analysis_rules_file] [output_file]

Arguments:
    transcript_json_file: Path to the JSON transcript file to analyze
    analysis_rules_file: Optional. Path to a text file containing analysis instructions.
                         If omitted, will use 'AnalysisRules.txt' in the script directory,
                         or prompt for interactive input if that file doesn't exist.
    output_file: Optional. Path to save the analysis results.
                If omitted, results will be saved as <transcript_name>_analysis.txt

Examples:
    python transcript_analyzer.py "transcript.json"
    python transcript_analyzer.py "transcript.json" "my_rules.txt"
    python transcript_analyzer.py "transcript.json" "my_rules.txt" "analysis_output.txt"
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

print("=== TRANSCRIPT ANALYZER STARTUP ===")
logger.info("Starting transcript analyzer script")
logger.info(f"Python version: {sys.version}")
logger.info(f"Script arguments: {sys.argv}")
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"Script path: {__file__ if '__file__' in globals() else 'Unknown'}")

# Configuration
API_KEY = "AIzaSyCsti0qnCEKOgzAnG_w41IfMNMxkyl3ysw"  # Your existing API key
MAX_CHUNK_SIZE = 800000  # Characters per chunk - Gemini 1.5 Flash can handle ~1M tokens (roughly 4M chars)
OVERLAP_SIZE = 2000      # Characters to overlap between chunks for context

def sanitize_audio_filename(name: str) -> str:
    """Cleans a string to be suitable for use as a folder/filename."""
    name = name.strip()
    # Replace problematic characters often found in titles
    name = name.replace(":", "_")
    name = name.replace("/", "_")
    name = name.replace("\\", "_")
    name = name.replace("\"", "'") # Replace double quotes with single

    # Remove characters forbidden in Windows filenames
    name = re.sub(r'[<>|?*]', '', name)
    
    # Replace multiple spaces/underscores with a single underscore
    name = re.sub(r'[\s_]+', '_', name)
    
    # Remove leading/trailing underscores or periods that might result from replacements
    name = name.strip('_.')
    
    # Limit length to avoid issues (e.g. 150 chars for the base name)
    max_len = 150
    if len(name) > max_len:
        name_part = name[:max_len]
        if '_' in name_part:
            name = name_part.rsplit('_', 1)[0]
        else:
            name = name_part

    return name if name else "untitled_audio"

def configure_gemini():
    """Configure the Gemini API key."""
    logger.info("Starting Gemini API configuration")
    try:
        if API_KEY:
            logger.info("Using hardcoded API key")
            genai.configure(api_key=API_KEY)
            logger.info("Gemini API configured successfully with hardcoded key")
            return True
        elif "GOOGLE_API_KEY" in os.environ:
            logger.info("Using environment variable API key")
            genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
            logger.info("Gemini API configured successfully with environment key")
            return True
        else:
            logger.error("No Gemini API key found")
            print("❌ Error: No Gemini API key found.")
            print("Please set the API_KEY variable in the script or set GOOGLE_API_KEY environment variable.")
            return False
    except Exception as e:
        logger.error(f"Error configuring Gemini API: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        print(f"❌ Error configuring Gemini API: {e}")
        return False

def load_transcript(file_path):
    """Load and parse the JSON transcript file."""
    logger.info(f"Loading transcript from: {file_path}")
    logger.info(f"File exists: {os.path.exists(file_path)}")
    
    if os.path.exists(file_path):
        logger.info(f"File size: {os.path.getsize(file_path)} bytes")
    
    try:
        logger.info("Opening file for reading")
        with open(file_path, 'r', encoding='utf-8') as f:
            logger.info("Reading JSON data")
            transcript_data = json.load(f)
        
        logger.info(f"JSON loaded successfully. Keys: {list(transcript_data.keys())}")
        
        # Extract text from segments
        segments = transcript_data.get('segments', [])
        logger.info(f"Found {len(segments)} segments")
        
        if not segments:
            logger.error("No segments found in transcript file")
            raise ValueError("No segments found in transcript file")
        
        logger.info("Building full transcript text")
        # Build full transcript text with speaker labels and timestamps
        full_text = ""
        metadata = transcript_data.get('metadata', {})
        logger.info(f"Metadata: {metadata}")
        
        # Add metadata header
        full_text += f"TRANSCRIPT METADATA:\n"
        full_text += f"Language: {metadata.get('language', 'unknown')}\n"
        full_text += f"Total Segments: {metadata.get('total_segments', len(segments))}\n"
        full_text += f"Model Used: {metadata.get('model_used', 'unknown')}\n"
        full_text += f"Processing Device: {metadata.get('device', 'unknown')}\n\n"
        full_text += "TRANSCRIPT:\n\n"
        
        # Add each segment with speaker and timestamp
        logger.info("Processing segments")
        processed_segments = 0
        for i, segment in enumerate(segments):
            speaker = segment.get('speaker', 'UNKNOWN')
            text = segment.get('text', '').strip()
            start_time = segment.get('start_time_formatted', segment.get('start_time', ''))
            
            if text:  # Only include segments with actual text
                full_text += f"[{start_time}] {speaker}: {text}\n"
                processed_segments += 1
            
            if i % 100 == 0:  # Log progress every 100 segments
                logger.debug(f"Processed {i}/{len(segments)} segments")
        
        logger.info(f"Processed {processed_segments} segments with text")
        logger.info(f"Full transcript length: {len(full_text)} characters")
        
        return full_text, metadata
    
    except FileNotFoundError:
        logger.error(f"Transcript file not found: {file_path}")
        print(f"❌ Error: Transcript file not found: {file_path}")
        return None, None
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in transcript file: {e}")
        print(f"❌ Error: Invalid JSON in transcript file: {e}")
        return None, None
    except Exception as e:
        logger.error(f"Error loading transcript: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        print(f"❌ Error loading transcript: {e}")
        return None, None

def load_analysis_rules(rules_file=None):
    """Load analysis rules from file or get them interactively."""
    logger.info(f"Loading analysis rules from: {rules_file}")
    
    if rules_file and os.path.exists(rules_file):
        logger.info(f"Rules file exists: {rules_file}")
        try:
            with open(rules_file, 'r', encoding='utf-8') as f:
                raw_content = f.read()
                rules = raw_content.strip()
            logger.info(f"Raw content length: {len(raw_content)}, stripped length: {len(rules)}")
            logger.debug(f"First 200 chars of raw content: {repr(raw_content[:200])}")
            logger.info(f"✅ Loaded analysis rules from: {rules_file} ({len(rules)} characters)")
            print(f"✅ Loaded analysis rules from: {rules_file}")
            return rules
        except Exception as e:
            logger.error(f"Could not load rules file {rules_file}: {e}")
            print(f"⚠️ Warning: Could not load rules file {rules_file}: {e}")
    else:
        logger.info(f"Rules file not found or not specified: {rules_file}")
    
    # Interactive input
    logger.info("Prompting for interactive rule input")
    print("\n📝 Enter your analysis rules/instructions:")
    print("(You can paste multiple lines. Press Ctrl+Z then Enter on Windows when done)")
    print("-" * 60)
    
    rules_lines = []
    try:
        while True:
            line = input()
            rules_lines.append(line)
    except EOFError:
        logger.info("EOF received, finishing interactive input")
        pass
    
    rules = '\n'.join(rules_lines).strip()
    if not rules:
        logger.info("No rules provided, using default")
        rules = "Please provide a comprehensive analysis of this transcript, including key topics, main points, and interesting insights."
    
    logger.info(f"Final rules length: {len(rules)} characters")
    return rules

def chunk_transcript(text, max_size=MAX_CHUNK_SIZE, overlap=OVERLAP_SIZE):
    """Force processing of entire transcript as single chunk for Gemini 2.5 Pro's large context window."""
    # Always return the entire text as a single chunk since Gemini 2.5 Pro can handle very large inputs
    logger.info(f"Processing entire transcript as single chunk (length: {len(text)} characters)")
    return [text]

def analyze_with_gemini(text, rules, chunk_number=None, total_chunks=None):
    """Send text to Gemini for analysis."""
    logger.info(f"Starting Gemini analysis for chunk {chunk_number or 'single'}")    
    logger.info(f"Text length: {len(text)}, Rules length: {len(rules)}")
    
    try:
        logger.info("Creating Gemini model instance")
        model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')  # Using Gemini 2.5 Flash Preview with latest capabilities
        
        # Build the prompt
        if chunk_number and total_chunks:
            prompt = f"""ANALYSIS RULES:
{rules}

INSTRUCTIONS: This is chunk {chunk_number} of {total_chunks} from a larger transcript. Please analyze this portion according to the rules above, but keep in mind this is part of a larger conversation.

TRANSCRIPT CHUNK:
{text}"""
        else:        prompt = f"""You are an expert content analyst. Analyze the following transcript using the provided rules.

CRITICAL JSON OUTPUT REQUIREMENTS:
1. Output MUST be valid JSON array format starting with [ and ending with ]
2. Maximum 20 segments total (as specified in rules)
3. If response approaches character limits, STOP immediately and close JSON properly with ]
4. Each entry MUST have ALL required fields with proper JSON syntax
5. Use proper JSON escaping for quotes in text (use \\" for quotes inside strings)
6. All timestamps should be strings in quotes (e.g., "1:23.45" or "45.31")
7. Ensure all objects are properly closed with }}
8. Separate objects with commas
9. No trailing commas before ] or }}

ANALYSIS RULES:
{rules}

TRANSCRIPT TO ANALYZE:
{text}

Return ONLY the JSON array - no explanatory text before or after:"""
        
        logger.info(f"Prompt length: {len(prompt)} characters")
        print(f"🤖 Sending to Gemini for analysis{'(chunk ' + str(chunk_number) + '/' + str(total_chunks) + ')' if chunk_number else ''}...")
        
        logger.info("Sending request to Gemini API")
        response = model.generate_content(prompt)
        
        # Check if response was blocked by safety filters
        if not response.text:
            logger.warning("Response blocked or empty")
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                finish_reason = getattr(candidate, 'finish_reason', None)
                safety_ratings = getattr(candidate, 'safety_ratings', [])
                
                logger.error(f"Response blocked. Finish reason: {finish_reason}")
                logger.error(f"Safety ratings: {[(rating.category, rating.probability) for rating in safety_ratings]}")
                
                if finish_reason == 2:  # SAFETY
                    error_msg = (
                        "❌ Content was blocked by Gemini's safety filters.\n\n"
                        "This typically happens when the analysis rules or content contain:\n"
                        "- References to controversial topics\n"
                        "- Mentions of extremist content\n"
                        "- Potentially harmful language\n\n"
                        "Suggested solutions:\n"
                        "1. Modify the analysis rules to use more neutral language\n"
                        "2. Remove specific references to harmful content categories\n"
                        "3. Use more academic/research-oriented phrasing\n"
                        "4. Try analyzing smaller segments separately\n"
                        "5. Use a different AI model if available\n\n"
                        "The content itself is likely fine - it's the analysis prompt that's triggering the filters."
                    )
                elif finish_reason == 3:  # RECITATION
                    error_msg = "❌ Content was blocked due to potential copyright or recitation concerns."
                elif finish_reason == 4:  # OTHER
                    error_msg = "❌ Content was blocked for other safety reasons."
                else:
                    error_msg = f"❌ Content was blocked with finish_reason: {finish_reason}"
                
                print(error_msg)
                return error_msg
            else:
                error_msg = "❌ Empty response received from Gemini with no explanation."
                print(error_msg)
                return error_msg
        
        logger.info(f"Received response from Gemini (length: {len(response.text)})")
        return response.text
    
    except Exception as e:
        error_msg = f"❌ Error during Gemini analysis: {e}"
        logger.error(f"Gemini analysis error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        print(error_msg)
        return error_msg

def save_analysis(analysis_text, output_file, transcript_file, rules):
    """Save the analysis results to three separate files."""
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
        print(f"✅ Prompt saved to: {prompt_file}")
        
        # 2. Extract and fix JSON, then save clean JSON file
        json_content = extract_and_fix_json(analysis_text)
        if json_content:
            with open(json_file, 'w', encoding='utf-8') as f:
                f.write(json_content)
            print(f"✅ Clean JSON saved to: {json_file}")
        else:
            print(f"⚠️ Could not extract valid JSON from analysis response")
        
        # 3. Create combined analysis report (original format)
        header = f"""TRANSCRIPT ANALYSIS REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Source File: {os.path.basename(transcript_file)}
Analysis Rules Used:
{'-' * 40}
{rules}
{'-' * 40}

ANALYSIS RESULTS:
{'=' * 60}

"""
        
        full_output = header + analysis_text
        
        with open(combined_file, 'w', encoding='utf-8') as f:
            f.write(full_output)
        print(f"✅ Combined analysis saved to: {combined_file}")
        
        return True
    
    except Exception as e:
        print(f"❌ Error saving analysis: {e}")
        logger.error(f"Error saving analysis: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False


def extract_and_fix_json(analysis_text):
    """Extract JSON from analysis response and fix timestamp formatting with improved validation."""
    import re
    import json
    
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
        
        if json_end_pos != -1:
            json_content = analysis_text[json_start:json_end_pos].strip()
        else:
            json_content = analysis_text[json_start:].strip()
        
        logger.info(f"Extracted JSON content length: {len(json_content)}")
        
        # Enhanced JSON cleaning
        json_content = clean_json_comprehensive(json_content)
        
        # Validate the JSON
        try:
            parsed_json = json.loads(json_content)
            
            # Additional validation - ensure it's an array
            if not isinstance(parsed_json, list):
                logger.error("JSON is not an array as expected")
                return json_content  # Return for manual inspection
            
            # Validate each entry has minimum required fields
            required_fields = ['narrativeSegmentTitle', 'severityRating', 'harmPotential']
            valid_entries = []
            
            for i, entry in enumerate(parsed_json):
                if isinstance(entry, dict):
                    # Check if entry has required fields
                    missing_fields = [field for field in required_fields if field not in entry]
                    if not missing_fields:
                        valid_entries.append(entry)
                    else:
                        logger.warning(f"Entry {i} missing required fields: {missing_fields}")
                else:
                    logger.warning(f"Entry {i} is not a dictionary: {type(entry)}")
            
            logger.info(f"Validated {len(valid_entries)} out of {len(parsed_json)} entries")
            
            # Return prettified JSON
            final_json = json.dumps(valid_entries, indent=2, ensure_ascii=False)
            return final_json
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed after fixes: {e}")
            logger.error(f"JSON content length: {len(json_content)}")
            logger.error(f"Error at position: {e.pos if hasattr(e, 'pos') else 'unknown'}")
            
            # Try to find and fix the specific error
            fixed_json = attempt_json_repair(json_content, e)
            if fixed_json:
                return fixed_json
            
            # Return the fixed content even if it doesn't parse, for manual inspection
            return json_content
            
    except Exception as e:
        logger.error(f"Error extracting/fixing JSON: {e}")
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
        # Find the last complete object
        last_brace = json_content.rfind('}')
        if last_brace > 0:
            json_content = json_content[:last_brace + 1] + '\n]'
    
    # Fix escaped quotes in strings
    json_content = re.sub(r'\\+"', r'"', json_content)
    
    return json_content

def attempt_json_repair(json_content, error):
    """Attempt to repair JSON based on specific error."""
    logger.info(f"Attempting JSON repair for error: {error}")
    
    try:
        # Common fixes for JSON errors
        if "Expecting ',' delimiter" in str(error):
            # Try to add missing commas
            repaired = re.sub(r'"\s*"', r'", "', json_content)
            try:
                json.loads(repaired)
                return repaired
            except:
                pass
        
        if "Unterminated string" in str(error):
            # Try to fix unterminated strings by adding closing quotes
            lines = json_content.split('\n')
            for i, line in enumerate(lines):
                # Count quotes in line
                quote_count = line.count('"') - line.count('\\"')
                if quote_count % 2 != 0:  # Odd number of quotes
                    lines[i] = line + '"'
            
            repaired = '\n'.join(lines)
            try:
                json.loads(repaired)
                return repaired
            except:
                pass
        
        # If all else fails, try to extract just the valid portion
        if json_content.startswith('['):
            # Find the last valid complete object
            brace_count = 0
            last_valid_pos = 0
            
            for i, char in enumerate(json_content):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        last_valid_pos = i + 1
            
            if last_valid_pos > 0:
                truncated = json_content[:last_valid_pos] + '\n]'
                try:
                    json.loads(truncated)
                    logger.info("Successfully repaired JSON by truncating")
                    return truncated
                except:
                    pass
        
    except Exception as e:
        logger.error(f"JSON repair attempt failed: {e}")
    
    return None

def main():
    logger.info("=== MAIN FUNCTION STARTED ===")
    logger.info(f"sys.argv: {sys.argv}")
    logger.info(f"sys.argv length: {len(sys.argv)}")
    
    print("🚀 Starting Transcript Analysis")
    
    if len(sys.argv) < 2:
        logger.warning("Insufficient arguments provided")
        print("Usage: python transcript_analyzer.py <transcript_json_file> [analysis_rules_file] [output_file]")
        print("\nArguments:")
        print("  transcript_json_file: Path to the JSON transcript file to analyze (required)")
        print("  analysis_rules_file:  Optional. Path to a text file containing analysis instructions")
        print("                        (defaults to 'AnalysisRules.txt' in script directory)")
        print("  output_file:          Optional. Path to save the analysis results")
        print("\nExamples:")
        print('  python transcript_analyzer.py "transcript.json"')
        print('  python transcript_analyzer.py "transcript.json" "my_rules.txt"')
        print('  python transcript_analyzer.py "transcript.json" "my_rules.txt" "analysis_output.txt"')
        sys.exit(1)
    
    # Parse arguments
    transcript_file = sys.argv[1]
    rules_file = sys.argv[2] if len(sys.argv) > 2 else None
    output_file = sys.argv[3] if len(sys.argv) > 3 else None
      # Set default rules file to AnalysisRules.txt if none specified
    if not rules_file:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        default_rules_file = os.path.join(script_dir, "sample_analysis_rules.txt")
        if os.path.exists(default_rules_file):
            rules_file = default_rules_file
            logger.info(f"Using default rules file: {rules_file}")
    
    logger.info(f"Parsed arguments:")
    logger.info(f"  transcript_file: {transcript_file}")
    logger.info(f"  rules_file: {rules_file}")
    logger.info(f"  output_file: {output_file}")
      # Default output file
    if not output_file:
        base_name = os.path.splitext(os.path.basename(transcript_file))[0]
        transcript_dir = os.path.dirname(transcript_file)
        
        # Check if the transcript file is already in a subfolder structure
        # If it's in a Transcripts/[folder_name]/ structure, use the same folder
        if os.path.basename(transcript_dir) != "Transcripts":
            # The transcript is in a subfolder - use the same directory
            output_file = os.path.join(transcript_dir, f"{base_name}_analysis.txt")
        else:
            # The transcript is directly in Transcripts folder - maintain the flat structure for now
            output_file = os.path.join(transcript_dir, f"{base_name}_analysis.txt")
        
        logger.info(f"Generated default output file: {output_file}")
    else:
        # If user specified an output file, ensure it goes to the same folder as the transcript
        transcript_dir = os.path.dirname(transcript_file)
        if not os.path.isabs(output_file):
            # Relative path - put it in the same directory as the transcript
            output_file = os.path.join(transcript_dir, os.path.basename(output_file))
        # For absolute paths, respect user's choice but warn if it's not in the transcript folder
        elif not output_file.startswith(transcript_dir):
            logger.warning(f"Output file {output_file} is not in the same directory as transcript {transcript_file}")
            print(f"⚠️  Warning: Output file is not in the same directory as the transcript file.")
    
    print(f"📁 Transcript file: {transcript_file}")
    print(f"📄 Output file: {output_file}")
    
    # Configure Gemini
    logger.info("Configuring Gemini API")
    if not configure_gemini():
        logger.error("Failed to configure Gemini API")
        sys.exit(1)
    
    # Load transcript
    print("\n📖 Loading transcript...")
    logger.info("Loading transcript file")
    transcript_text, metadata = load_transcript(transcript_file)
    if not transcript_text:
        logger.error("Failed to load transcript")
        sys.exit(1)
    
    print(f"✅ Loaded transcript with {len(transcript_text)} characters")
    logger.info(f"Transcript loaded successfully: {len(transcript_text)} characters")
    
    # Load analysis rules
    print("\n📋 Loading analysis rules...")
    logger.info("Loading analysis rules")
    analysis_rules = load_analysis_rules(rules_file)
    if not analysis_rules:
        logger.error("No analysis rules provided")
        print("❌ No analysis rules provided.")
        sys.exit(1)
    
    print(f"✅ Analysis rules loaded ({len(analysis_rules)} characters)")
    logger.info(f"Analysis rules loaded: {len(analysis_rules)} characters")
    
    # Check if chunking is needed
    logger.info("Checking if chunking is needed")
    chunks = chunk_transcript(transcript_text)
    print(f"\n🔄 Processing transcript in {len(chunks)} chunk(s)")
    logger.info(f"Transcript split into {len(chunks)} chunks")
    
    # Analyze each chunk
    logger.info("Starting analysis of chunks")
    all_analyses = []
    for i, chunk in enumerate(chunks, 1):
        logger.info(f"Analyzing chunk {i}/{len(chunks)} (length: {len(chunk)})")
        chunk_analysis = analyze_with_gemini(
            chunk, 
            analysis_rules, 
            chunk_number=i if len(chunks) > 1 else None,
            total_chunks=len(chunks) if len(chunks) > 1 else None
        )
        all_analyses.append(chunk_analysis)
        logger.info(f"Chunk {i} analysis completed (result length: {len(chunk_analysis)})")
    
    # Combine analyses if multiple chunks
    if len(chunks) > 1:
        print("\n🔄 Generating final consolidated analysis...")
        logger.info("Consolidating multiple chunk analyses")
        
        # Create a summary prompt
        combined_chunks = "\n\n" + "="*80 + "\n\n".join([
            f"CHUNK {i+1} ANALYSIS:\n{analysis}" 
            for i, analysis in enumerate(all_analyses)
        ])
        
        consolidation_prompt = f"""Please provide a consolidated analysis by synthesizing the following chunk analyses into a comprehensive, coherent report. Remove redundancies and create a unified analysis.

ORIGINAL ANALYSIS RULES:
{analysis_rules}

CHUNK ANALYSES TO CONSOLIDATE:
{combined_chunks}

Please provide a single, comprehensive analysis that combines insights from all chunks."""
        
        logger.info("Running consolidation analysis")
        final_analysis = analyze_with_gemini(consolidation_prompt, "Consolidate the provided chunk analyses into a comprehensive report.")
        logger.info(f"Consolidation completed (result length: {len(final_analysis)})")
        
    else:
        final_analysis = all_analyses[0]
        logger.info("Using single chunk analysis as final result")
    
    # Save results
    print("\n💾 Saving analysis...")
    logger.info("Saving analysis results")
    if save_analysis(final_analysis, output_file, transcript_file, analysis_rules):
        print(f"\n🎉 Analysis complete! Results saved to: {output_file}")
        logger.info(f"Analysis saved successfully to: {output_file}")
        
        # Show a preview
        print("\n📄 Preview of analysis:")
        print("-" * 60)
        preview = final_analysis[:500] + "..." if len(final_analysis) > 500 else final_analysis
        print(preview)
        print("-" * 60)
        logger.info("Preview shown to user")
    else:
        logger.error("Failed to save analysis")
        print("\n❌ Failed to save analysis, but here are the results:")
        print("=" * 60)
        print(final_analysis)
        print("=" * 60)
    
    logger.info("=== MAIN FUNCTION COMPLETED ===")

if __name__ == "__main__":
    try:
        logger.info("Script started as main module")
        print("DEBUG: About to call main()")
        main()
        print("DEBUG: main() completed successfully")
        logger.info("Script completed successfully")
    except Exception as e:
        logger.error(f"Unhandled exception in main: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        print(f"❌ Fatal error: {e}")
        print("Full traceback:")
        traceback.print_exc()
        sys.exit(1)
