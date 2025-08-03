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
import time
from functools import wraps

# Add path for file organizer
current_dir = os.path.dirname(os.path.abspath(__file__))
utils_dir = os.path.join(current_dir, '..', 'Utils')
sys.path.append(utils_dir)

try:
    from file_organizer import FileOrganizer
except ImportError as e:
    print(f"Warning: Could not import FileOrganizer: {e}")
    print("Falling back to original output behavior")
    FileOrganizer = None

# Set up console logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Console output instead of file
    ]
)
logger = logging.getLogger(__name__)

# Configuration
API_KEY = "AIzaSyCsti0qnCEKOgzAnG_w41IfMNMxkyl3ysw"

def load_episode_metadata_from_path(transcript_path):
    """
    Load episode metadata from Input/episode_metadata.json based on transcript file path.
    
    Args:
        transcript_path: Path to transcript file or any file within episode folder
        
    Returns:
        Dict: Episode metadata, or None if not found
    """
    try:
        import json
        
        # Navigate up the directory tree to find the episode root folder
        current_path = os.path.abspath(transcript_path)
        
        # If it's a file, get its directory
        if os.path.isfile(current_path):
            current_path = os.path.dirname(current_path)
        
        # Look for episode folder structure (should contain Input, Processing, Output folders)
        while current_path and current_path != os.path.dirname(current_path):
            input_folder = os.path.join(current_path, 'Input')
            processing_folder = os.path.join(current_path, 'Processing')
            output_folder = os.path.join(current_path, 'Output')
            
            # Check if this looks like an episode folder
            if (os.path.exists(input_folder) and 
                os.path.exists(processing_folder) and 
                os.path.exists(output_folder)):
                
                # Try to load metadata from Input folder
                metadata_path = os.path.join(input_folder, 'episode_metadata.json')
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    logger.info(f"✅ Loaded episode metadata from: {metadata_path}")
                    return metadata
                else:
                    logger.warning(f"Episode structure found but no metadata file: {metadata_path}")
                    return None
            
            # Move up one directory level
            current_path = os.path.dirname(current_path)
        
        logger.warning(f"No episode metadata found for path: {transcript_path}")
        return None
        
    except Exception as e:
        logger.error(f"Failed to load episode metadata: {e}")
        return None

def extract_host_and_guest_names(file_path):
    """
    Extract host and guest names from folder structure.
    
    The folder format is ALWAYS: Content/{HOST}/{HOST}_{GUEST}/...
    Example: C:/Users/nfaug/OneDrive - LIR/Desktop/YouTuber/Content/Tucker_Carlson/Tucker_Carlson_RFK_Jr
    
    Args:
        file_path: Path to the transcript file or any file in the episode folder
        
    Returns:
        tuple: (host_name, guest_name) with underscores replaced by spaces
               Returns ("Unknown Host", "Unknown Guest") if parsing fails
    """
    try:
        # Convert to forward slashes for consistent parsing
        normalized_path = file_path.replace('\\', '/')
        logger.info(f"Extracting names from path: {normalized_path}")
        
        # Find the Content folder and extract the structure after it
        content_index = normalized_path.find('/Content/')
        if content_index == -1:
            logger.warning("Could not find '/Content/' in path")
            return ("Unknown Host", "Unknown Guest")
        
        # Extract the part after Content/
        path_after_content = normalized_path[content_index + 9:]  # 9 = len('/Content/')
        path_parts = path_after_content.split('/')
        
        if len(path_parts) < 2:
            logger.warning(f"Insufficient path parts after Content/: {path_parts}")
            return ("Unknown Host", "Unknown Guest")
        
        # First part is host folder name
        host_folder = path_parts[0]
        # Second part is the host_guest combination
        host_guest_folder = path_parts[1]
        
        logger.info(f"Host folder: {host_folder}, Host_Guest folder: {host_guest_folder}")
        
        # Extract guest name by removing the host prefix and underscore
        if host_guest_folder.startswith(host_folder + '_'):
            guest_part = host_guest_folder[len(host_folder) + 1:]  # +1 for the underscore
            
            # Format names by replacing underscores with spaces
            host_name = host_folder.replace('_', ' ')
            guest_name = guest_part.replace('_', ' ')
            
            logger.info(f"Extracted host: '{host_name}', guest: '{guest_name}'")
            return (host_name, guest_name)
        else:
            logger.warning(f"Host_Guest folder '{host_guest_folder}' does not start with host folder '{host_folder}'")
            return ("Unknown Host", "Unknown Guest")
            
    except Exception as e:
        logger.error(f"Error extracting names from path: {e}")
        return ("Unknown Host", "Unknown Guest")

def retry_gemini_call(max_retries=5, base_delay=1, backoff_factor=2):
    """
    Decorator to retry Gemini API calls with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 5)
        base_delay: Base delay in seconds between retries (default: 1)
        backoff_factor: Multiplier for delay on each retry (default: 2)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):  # +1 for initial attempt
                try:
                    if attempt > 0:
                        delay = base_delay * (backoff_factor ** (attempt - 1))
                        logger.info(f"Retrying {func.__name__} (attempt {attempt + 1}/{max_retries + 1}) after {delay} seconds...")
                        time.sleep(delay)
                    else:
                        logger.info(f"Attempting {func.__name__} (attempt {attempt + 1}/{max_retries + 1})")
                    
                    result = func(*args, **kwargs)
                    
                    # Check if result indicates success
                    if result is not None and result != "ERROR: Could not access response text":
                        if attempt > 0:
                            logger.info(f"✅ {func.__name__} succeeded on attempt {attempt + 1}")
                        return result
                    else:
                        raise Exception("Gemini API returned null or error response")
                        
                except Exception as e:
                    last_exception = e
                    error_msg = str(e).lower()
                    
                    # Check for specific error types that should trigger retry
                    retryable_errors = [
                        "500", "internal server error", "service unavailable", 
                        "timeout", "connection", "network", "temporary",
                        "rate limit", "quota", "unavailable"
                    ]
                    
                    is_retryable = any(err in error_msg for err in retryable_errors)
                    
                    if attempt < max_retries and is_retryable:
                        logger.warning(f"❌ {func.__name__} failed on attempt {attempt + 1}: {e}")
                        logger.info(f"Error appears retryable, will retry...")
                        continue
                    elif attempt < max_retries:
                        logger.error(f"❌ {func.__name__} failed on attempt {attempt + 1} with non-retryable error: {e}")
                        break
                    else:
                        logger.error(f"❌ {func.__name__} failed on final attempt {attempt + 1}: {e}")
            
            # All retries exhausted
            logger.error(f"🚫 {func.__name__} failed after {max_retries + 1} attempts. Last error: {last_exception}")
            return None
            
        return wrapper
    return decorator

def create_file_organizer():
    """Create and configure the FileOrganizer."""
    try:
        # Define base paths for the YouTuber project
        base_paths = {
            'episode_base': os.path.join(os.path.dirname(__file__), '..', '..', 'Content'),
            'analysis_rules': os.path.join(os.path.dirname(__file__), 'Rules')
        }
        
        # Convert to absolute paths
        for key, path in base_paths.items():
            base_paths[key] = os.path.abspath(path)
        
        return FileOrganizer(base_paths)
    except Exception as e:
        logger.error(f"Failed to create FileOrganizer: {e}")
        return None

def get_organized_output_path(transcript_file, file_organizer=None):
    """
    Get organized output path using FileOrganizer if available.
    Falls back to original behavior if FileOrganizer is not available.
    """
    if file_organizer and FileOrganizer:
        try:
            # Use FileOrganizer to get the analysis output path
            analysis_path = file_organizer.get_analysis_output_path(transcript_file)
            logger.info(f"Using organized output path: {analysis_path}")
            return analysis_path
        except Exception as e:
            logger.warning(f"FileOrganizer failed, using fallback: {e}")
    
    # Fallback to original behavior
    base_name = os.path.splitext(os.path.basename(transcript_file))[0]
    transcript_dir = os.path.dirname(transcript_file)
    fallback_path = os.path.join(transcript_dir, f"{base_name}_improved_analysis.txt")
    logger.info(f"Using fallback output path: {fallback_path}")
    return fallback_path

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



def save_prompt_to_file(prompt_content, output_dir):
    """Save the Gemini prompt to a file in the episode's Processing folder."""
    try:
        prompt_filename = "gemini_prompt_analyze_initial_transcripts_for_misinfo.txt"
        prompt_path = os.path.join(output_dir, prompt_filename)
        
        with open(prompt_path, 'w', encoding='utf-8') as f:
            f.write(prompt_content)
        
        logger.info(f"Prompt saved to: {prompt_path}")
        return prompt_path
    except Exception as e:
        logger.error(f"Failed to save prompt: {e}")
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
        if "expecting ',' delimiter" in error:
            # Add missing commas
            json_content = re.sub(r'}\s*{', r'}, {', json_content)
            json_content = re.sub(r']\s*{', r'], {', json_content)
        
        if "expecting property name" in error:
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
    """Save analysis results to three separate files in organized structure."""
    logger.info("Saving analysis results to organized structure")
    
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.info(f"Created output directory: {output_dir}")
        
        # Generate base filename without extension - use transcript name for consistency
        transcript_base = os.path.splitext(os.path.basename(transcript_file))[0]
        
        # File paths for the three output files in Processing folder
        prompt_file = os.path.join(output_dir, f"{transcript_base}_analysis_prompt.txt")
        json_file = os.path.join(output_dir, f"{transcript_base}_analysis_results.json")
        combined_file = os.path.join(output_dir, f"{transcript_base}_analysis_combined.txt")
        
        print(f"📁 Saving analysis files to: {output_dir}")
        print(f"   • Prompt: {os.path.basename(prompt_file)}")
        print(f"   • JSON: {os.path.basename(json_file)}")
        print(f"   • Combined: {os.path.basename(combined_file)}")
        
        # 1. Create prompt/instructions file
        prompt_content = f"""TRANSCRIPT ANALYSIS PROMPT/INSTRUCTIONS
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Source File: {os.path.basename(transcript_file)}
Output Directory: {output_dir}

ANALYSIS RULES USED:
{'-' * 40}
{rules if rules else 'No specific rules file provided - using default analysis'}
{'-' * 40}
"""
        
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(prompt_content)
        logger.info(f"Prompt saved to: {prompt_file}")
          # 2. Save clean JSON file - analysis_result is already cleaned JSON
        if analysis_result and analysis_result.strip().startswith('['):
            # analysis_result is already cleaned JSON from validate_and_clean_json
            with open(json_file, 'w', encoding='utf-8') as f:
                f.write(analysis_result)
            logger.info(f"Clean JSON saved to: {json_file}")
        else:
            logger.warning("Could not save JSON - analysis result is not valid JSON format")
        
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

def detect_episode_type_and_rules(transcript_file):
    """
    Detect the episode type from the transcript file path and return appropriate rules file.
    
    Args:
        transcript_file: Path to the transcript file
        
    Returns:
        Tuple of (episode_type, rules_file_path) or (None, None) if no specific rules
    """
    try:
        # Normalize path for consistent checking
        normalized_path = os.path.normpath(transcript_file).lower()
        
        # Define rules directory
        rules_dir = os.path.join(os.path.dirname(__file__), 'Analysis_Guidelines')
        
        # Check for Joe Rogan Experience
        if 'joe_rogan_experience' in normalized_path or 'joe rogan experience' in normalized_path:
            jre_rules_file = os.path.join(rules_dir, 'Joe_Rogan_selective_analysis_rules.txt')
            if os.path.exists(jre_rules_file):
                logger.info(f"Detected Joe Rogan Experience episode - using specific rules")
                return 'Joe_Rogan_Experience', jre_rules_file
        
        # Check for other podcast types (can be extended later)
        if 'lex_fridman' in normalized_path:
            # Could add Lex Fridman specific rules if needed
            pass
        
        # No specific rules found
        return None, None
        
    except Exception as e:
        logger.warning(f"Error detecting episode type: {e}")
        return None, None

def get_rules_file_with_auto_detection(transcript_file, provided_rules_file):
    """
    Get the rules file to use, with auto-detection for specific podcast types.
    
    Args:
        transcript_file: Path to the transcript file
        provided_rules_file: Rules file provided by user (takes priority)
        
    Returns:
        Path to rules file to use, or None if no rules
    """
    # If user provided a rules file, use it
    if provided_rules_file and os.path.exists(provided_rules_file):
        logger.info(f"Using user-provided rules file: {provided_rules_file}")
        return provided_rules_file
    
    # Try auto-detection
    episode_type, auto_rules_file = detect_episode_type_and_rules(transcript_file)
    
    if auto_rules_file:
        logger.info(f"Auto-detected {episode_type} episode - using rules: {auto_rules_file}")
        return auto_rules_file
    
    # No specific rules found
    logger.info("No specific rules file found - will use default analysis")
    return None

@retry_gemini_call()
def upload_transcript_to_gemini(transcript_path, display_name):
    """Upload JSON transcript file to Gemini and return file reference (required - no fallback)."""
    logger.info(f"Starting REQUIRED file upload to Gemini: {transcript_path}")
    logger.info("File upload method is mandatory to avoid safety blocks with large transcripts")
    try:
        # Validate file exists and is readable
        if not os.path.exists(transcript_path):
            raise FileNotFoundError(f"Transcript file not found: {transcript_path}")
        
        # Get file size for logging
        file_size = os.path.getsize(transcript_path)
        if file_size > 2 * 1024 * 1024 * 1024:  # 2GB limit
            raise ValueError(f"File too large: {file_size} bytes (max 2GB)")
        
        logger.info(f"Uploading file: {file_size} bytes")
          # Validate JSON structure before upload with double-encoding repair
        try:
            with open(transcript_path, 'r', encoding='utf-8') as f:
                transcript_data = json.load(f)
                if not transcript_data.get('segments'):
                    raise ValueError("Invalid transcript format: no segments found")
        except json.JSONDecodeError as e:
            # Try to repair double-encoded JSON (common issue from master_processor_v2.py Stage 2)
            logger.warning(f"Initial JSON parsing failed: {e}")
            logger.info("Attempting to repair potentially double-encoded JSON...")
            
            try:
                with open(transcript_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                # Check if the content is a JSON string (starts and ends with quotes)
                if content.startswith('"') and content.endswith('"'):
                    logger.info("Detected double-encoded JSON - attempting repair")
                    
                    # First parse: convert JSON string to actual string
                    json_string = json.loads(content)
                    
                    # Second parse: convert string to JSON object
                    transcript_data = json.loads(json_string)
                    
                    # Validate the repaired data
                    if not transcript_data.get('segments'):
                        raise ValueError("Repaired transcript format invalid: no segments found")
                    
                    # Save the repaired JSON back to the file
                    logger.info("Repairing transcript file with properly formatted JSON...")
                    with open(transcript_path, 'w', encoding='utf-8') as f:
                        json.dump(transcript_data, f, indent=2, ensure_ascii=False)
                    
                    logger.info("✅ Successfully repaired double-encoded JSON transcript")
                else:
                    # Not double-encoded, re-raise original error
                    raise ValueError(f"Invalid JSON format: {e}")
                    
            except (json.JSONDecodeError, ValueError) as repair_error:
                logger.error(f"Failed to repair JSON: {repair_error}")
                raise ValueError(f"Invalid JSON format - original error: {e}, repair failed: {repair_error}")
          # Upload file to Gemini using the correct API
        logger.info(f"Uploading to Gemini with display name: {display_name}")
          # Perform the upload - use text/plain MIME type to avoid analysis errors
        # Note: JSON files work perfectly when uploaded with text/plain MIME type
        file_object = genai.upload_file(
            path=transcript_path,
            mime_type="text/plain",
            display_name=display_name
        )
        
        logger.info(f"File uploaded successfully: {file_object.name}")
        logger.info(f"File URI: {file_object.uri}")
        
        return file_object
        
    except Exception as e:
        logger.error(f"CRITICAL: File upload to Gemini failed: {e}")
        logger.error("File upload is required to avoid safety blocks - analysis cannot proceed")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None

def create_file_based_prompt(analysis_rules, file_path=None):
    """Create clean analysis prompt without embedded transcript content."""
    logger.info("Creating file-based analysis prompt")
    
    # Extract participant names if file_path is provided
    participant_info = ""
    if file_path:
        # Try to load from metadata first, fallback to extraction
        metadata = load_episode_metadata_from_path(file_path)
        if metadata and metadata.get('verified_names'):
            host_name = metadata['verified_names']['host']
            guest_name = metadata['verified_names']['guest']
            verification_method = metadata['verified_names'].get('verification_method', 'unknown')
            logger.info(f"✅ Using verified names from metadata: Host='{host_name}', Guest='{guest_name}' (Method: {verification_method})")
        else:
            # Fallback to folder structure extraction
            logger.warning("⚠️  No metadata found, falling back to folder structure extraction")
            host_name, guest_name = extract_host_and_guest_names(file_path)
            logger.info(f"📁 Extracted from folder structure: Host='{host_name}', Guest='{guest_name}'")
        
        participant_info = f"""
## PARTICIPANT INFORMATION

**Host Name:** {host_name}
**Guest Name:** {guest_name}

**CRITICAL INSTRUCTION:** Use "{host_name}" as the host's name and "{guest_name}" as the guest's name throughout your analysis. These are the authoritative names extracted from the episode metadata.

---

"""
    
    prompt = f"""
{participant_info}
ANALYSIS RULES:
{analysis_rules}

The transcript file contains a JSON structure with segments. Analyze the transcript content according to the rules above and return only valid JSON without any markdown formatting or explanations.
"""

    logger.info(f"File-based prompt created: {len(prompt)} characters")
    return prompt

@retry_gemini_call()
def analyze_with_gemini_file_upload(file_object, analysis_rules, output_dir=None, file_path=None):
    """Analyze transcript using file upload method (REQUIRED to avoid safety blocks)."""
    logger.info("Starting Gemini analysis with file upload method (only supported method)")
    logger.info("This method avoids safety blocks by separating content from analysis instructions")
    try:
        # Create file-based prompt
        prompt_text = create_file_based_prompt(analysis_rules, file_path)
        logger.info(f"Prompt length: {len(prompt_text)} characters")
        
        # Save the prompt to the episode's Processing folder if output_dir is provided
        if output_dir:
            try:
                # Create the prompt filename
                prompt_filename = "gemini_prompt_file_upload_analysis.txt"
                prompt_path = os.path.join(output_dir, prompt_filename)
                
                # Create header with metadata
                header = f"""GEMINI FILE UPLOAD ANALYSIS PROMPT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Model: gemini-2.5-flash-preview-05-20
Method: File Upload API
Prompt Length: {len(prompt_text)} characters
File Object: {file_object.name}
File URI: {file_object.uri}
Safety Settings: All categories set to BLOCK_NONE
Output Format: JSON
Temperature: 0.1

FULL PROMPT SENT TO GEMINI:
{'=' * 60}

"""
                
                # Save prompt with header
                with open(prompt_path, 'w', encoding='utf-8') as f:
                    f.write(header + prompt_text)
                
                logger.info(f"Saved file upload prompt to: {prompt_path}")
            except Exception as e:
                logger.warning(f"Failed to save prompt file: {e}")
          # Generate response with file and prompt using correct API
        logger.info("Sending request to Gemini with uploaded file")
          # Create model with optimized configuration (no safety settings, no token limits)
        model = genai.GenerativeModel(
            #'gemini-2.5-flash-preview-05-20',
            'gemini-2.5-pro-preview-06-05',
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                top_p=0.9,
                # Removed top_k to allow more flexibility in token selection
                # Removed max_output_tokens to allow unlimited response length
                candidate_count=1,
                response_mime_type="application/json"
            )
            # Removed all safety_settings to eliminate potential blocking issues
        )
        
        # Generate response with file and prompt
        response = model.generate_content([prompt_text, file_object])
        
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
        logger.error(f"Error in Gemini file upload analysis: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None    
    finally:
        # Cleanup: Delete uploaded file with retry mechanism
        cleanup_uploaded_file(file_object)

def cleanup_uploaded_file(file_object, max_retries=3):
    """
    Clean up uploaded file with retry mechanism.
    
    Args:
        file_object: The file object returned from genai.upload_file()
        max_retries: Maximum number of retry attempts for deletion
    """
    if not file_object:
        return
    
    for attempt in range(max_retries):
        try:
            genai.delete_file(name=file_object.name)
            logger.info(f"✅ Uploaded file deleted successfully: {file_object.name}")
            return
        except Exception as e:
            if attempt < max_retries - 1:
                delay = 1 * (2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                logger.warning(f"❌ File deletion attempt {attempt + 1} failed: {e}")
                logger.info(f"Retrying file deletion in {delay} seconds...")
                time.sleep(delay)
            else:
                logger.error(f"🚫 Failed to delete uploaded file after {max_retries} attempts: {e}")
                logger.error(f"File may remain in Gemini storage: {file_object.name}")

def main():
    """Main function with improved error handling and organized output."""
    logger.info("=== IMPROVED TRANSCRIPT ANALYZER STARTED ===")
    
    if len(sys.argv) < 2:
        print("Usage: python transcript_analyzer.py <transcript_json_file> [analysis_rules_file] [output_file]")
        sys.exit(1)
    transcript_file = sys.argv[1]
    provided_rules_file = sys.argv[2] if len(sys.argv) > 2 else None
    output_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Auto-detect episode type and get appropriate rules file
    rules_file = get_rules_file_with_auto_detection(transcript_file, provided_rules_file)
    
    # Create file organizer
    file_organizer = create_file_organizer()
    if file_organizer:
        print("✅ FileOrganizer initialized - using organized output structure")
    else:
        print("⚠️  FileOrganizer not available - using fallback output behavior")
      # Generate organized output file path
    if not output_file:
        output_file = get_organized_output_path(transcript_file, file_organizer)
    
    print(f"🚀 Starting Improved Transcript Analysis")
    print(f"📁 Transcript: {transcript_file}")
    if rules_file:
        if provided_rules_file and rules_file == provided_rules_file:
            print(f"📋 Rules: {rules_file} (user-provided)")
        else:
            print(f"📋 Rules: {rules_file} (auto-detected)")
    else:
        print(f"📋 Rules: None (using default analysis)")
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
      # Analyze with file upload method (required for large transcripts)
    print("\n🤖 Analyzing with file upload method...")
    
    # Step 1: Upload transcript to Gemini
    print("📤 Uploading transcript to Gemini...")
    display_name = f"transcript_{os.path.basename(transcript_file)}"
    file_object = upload_transcript_to_gemini(transcript_file, display_name)
    
    if not file_object:
        print("❌ Failed to upload transcript to Gemini")
        sys.exit(1)
    print(f"✅ Transcript uploaded successfully: {file_object.name}")
    
    # Step 2: Analyze using uploaded file
    print("🔍 Analyzing uploaded transcript...")
    output_dir = os.path.dirname(output_file)
    analysis_result = analyze_with_gemini_file_upload(file_object, analysis_rules, output_dir, transcript_file)
    
    if not analysis_result:
        print("❌ Analysis failed")
        sys.exit(1)
      # Save results
    print("\n💾 Saving analysis...")
    if save_analysis_improved(analysis_result, output_file, transcript_file, rules_file):
        output_dir = os.path.dirname(output_file)
        print(f"🎉 Analysis complete! Results saved to organized structure:")
        print(f"   📁 Output directory: {output_dir}")
        print(f"   📄 Three files created: *_prompt.txt, *_results.json, *_combined.txt")
        
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
