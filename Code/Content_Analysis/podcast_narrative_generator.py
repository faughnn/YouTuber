import json
import google.generativeai as genai
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml
from datetime import datetime
import logging
import re

class PromptLoader:
    """Handle loading and formatting of prompt templates"""
    
    def __init__(self, prompts_dir: str):
        self.prompts_dir = Path(prompts_dir)
    
    def load_template(self, template_name: str) -> str:
        """Load a prompt template from file"""
        template_path = self.prompts_dir / template_name
        
        if not template_path.exists():
            raise FileNotFoundError(f"Prompt template not found: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def format_template(self, template: str, **kwargs) -> str:
        """Format template with provided variables"""
        return template.format(**kwargs)

class PodcastNarrativeGenerator:
    """Generate podcast scripts from analysis JSON using Gemini AI"""
    
    def __init__(self, config_path: str = None):
        # Default config path relative to the script location
        if config_path is None:
            config_path = Path(__file__).parent.parent / "Config" / "default_config.yaml"
        
        # Load existing config
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize Gemini
        genai.configure(api_key=self.config['api']['gemini_api_key'])
        self.model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
          # Initialize prompt loader
        prompts_dir = Path(__file__).parent / "Prompts"
        self.prompt_loader = PromptLoader(str(prompts_dir))
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def generate_podcast_script(
        self, 
        analysis_json_path: str, 
        episode_title: str,
        prompt_template: str = "podcast_narrative_prompt.txt",
        custom_instructions: str = ""
    ) -> Dict[str, Any]:
        """
        Generate podcast script from analysis JSON using specified prompt template
        
        Args:
            analysis_json_path: Path to the analysis JSON file
            episode_title: Title of the episode
            prompt_template: Name of prompt template to use
            custom_instructions: Additional instructions to add to prompt
            
        Returns:
            Dictionary containing script data and metadata
        """
        
        self.logger.info(f"Generating podcast script for: {episode_title}")
        self.logger.info(f"Using prompt template: {prompt_template}")
          # Load analysis data (handle both JSON and text format)
        analysis_data = self._load_analysis_data(analysis_json_path)
        
        # Build prompt from template
        narrative_prompt = self._build_prompt_from_template(
            analysis_data, 
            episode_title, 
            prompt_template,
            custom_instructions
        )
        
        # Generate with Gemini
        self.logger.info("Sending request to Gemini...")
        try:
            response = self.model.generate_content(narrative_prompt)
            self.logger.info("Received response from Gemini")
        except Exception as e:
            self.logger.error(f"Error generating content: {e}")
            raise
        
        # Parse and structure response
        script_data = self._parse_gemini_response(response.text, analysis_data, episode_title)
        
        return script_data
    
    def _build_prompt_from_template(
        self, 
        analysis_data: Dict, 
        episode_title: str, 
        template_name: str,
        custom_instructions: str = ""
    ) -> str:
        """Build prompt from external template file"""
        
        # Load template
        template = self.prompt_loader.load_template(template_name)
        
        # Prepare template variables
        template_vars = {
            'episode_title': episode_title,
            'analysis_json': json.dumps(analysis_data, indent=2),
            'custom_instructions': custom_instructions
        }
        
        # Add guest name if available
        if 'metadata' in analysis_data and 'guest' in analysis_data['metadata']:
            template_vars['guest_name'] = analysis_data['metadata']['guest']
          # Format template
        formatted_prompt = self.prompt_loader.format_template(template, **template_vars)
        
        return formatted_prompt
    
    def _parse_gemini_response(self, response_text: str, original_data: Dict, episode_title: str) -> Dict[str, Any]:
        """
        Parse Gemini's response and add metadata
        """
        try:
            # Try to parse as JSON first
            parsed_response = json.loads(response_text)
            self.logger.info("Successfully parsed JSON response")
            
            # Check if it's already in TTS format
            if "episode_info" not in parsed_response or "script_structure" not in parsed_response:
                # Convert to TTS format
                script_text = parsed_response.get('full_script', response_text)
                parsed_response = self._convert_to_tts_format(script_text, episode_title)
                
        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse JSON response: {e}")
            # If not JSON, treat as plain text script and convert to TTS format
            parsed_response = self._convert_to_tts_format(response_text, episode_title)
          # Add generation metadata
        parsed_response["generation_metadata"] = {
            "source_analysis": original_data[0] if isinstance(original_data, list) and original_data else {},
            "generation_timestamp": datetime.now().isoformat(),
            "episode_title": episode_title,
            "gemini_model": "gemini-2.5-flash-preview-05-20"
        }
        
        return parsed_response
    
    def save_podcast_script(self, script_data: Dict, output_path: str) -> tuple[Path, Path]:
        """
        Save both JSON structure and readable script
        
        Returns:
            Tuple of (json_path, script_path)
        """
        output_path = Path(output_path)
        
        # Save structured data
        json_path = output_path.with_suffix('.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(script_data, f, indent=2, ensure_ascii=False)
          # Save readable script
        script_path = output_path.with_suffix('.txt')
        with open(script_path, 'w', encoding='utf-8') as f:
            # Extract script from TTS format or use full_script
            if 'script_structure' in script_data and 'intro' in script_data['script_structure']:
                script_text = script_data['script_structure']['intro'].get('script', '')
            else:
                script_text = script_data.get('full_script', '')
            f.write(script_text)
        
        self.logger.info(f"Saved podcast script files:")
        self.logger.info(f"  JSON: {json_path}")
        self.logger.info(f"  Script: {script_path}")
        
        return json_path, script_path
    
    def generate_multiple_variations(
        self, 
        analysis_json_path: str, 
        episode_title: str,
        prompt_templates: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Generate multiple script variations using different prompt templates
        
        Returns:
            Dictionary mapping template names to script data
        """
        variations = {}
        
        for template in prompt_templates:
            self.logger.info(f"Generating variation with template: {template}")
            try:
                script_data = self.generate_podcast_script(
                    analysis_json_path, 
                    episode_title, 
                    template
                )
                variations[template] = script_data
            except Exception as e:
                self.logger.error(f"Failed to generate variation with {template}: {e}")
                variations[template] = {"error": str(e)}
        
        return variations
    
    def generate_tts_ready_script(
        self, 
        analysis_json_path: str, 
        episode_title: str,
        episode_number: str = "001",
        initials: str = "TBD",
        prompt_template: str = "tts_podcast_narrative_prompt.txt",
        custom_instructions: str = ""
    ) -> Dict[str, Any]:
        """
        Generate TTS-ready podcast script with structured audio segments
        
        Args:
            analysis_json_path: Path to the analysis JSON file
            episode_title: Title of the episode
            episode_number: Episode number for filename generation
            initials: Guest initials for filename generation
            prompt_template: Name of TTS-specific prompt template
            custom_instructions: Additional instructions
            
        Returns:
            Dictionary containing TTS-ready script structure with audio filenames
        """
        
        self.logger.info(f"Generating TTS-ready script for: {episode_title}")
        
        # First generate the base script using existing method
        base_script = self.generate_podcast_script(
            analysis_json_path, episode_title, prompt_template, custom_instructions
        )
          # Load analysis data for clip information
        analysis_data = self._load_analysis_data(analysis_json_path)
        
        # Transform to TTS-ready format
        tts_script = self._transform_to_tts_format(
            base_script, analysis_data, episode_number, initials
        )
        
        return tts_script
    
    def _transform_to_tts_format(
        self, 
        base_script: Dict, 
        analysis_data: Dict, 
        episode_number: str,
        initials: str
    ) -> Dict[str, Any]:
        """
        Transform base script to TTS-ready format with audio filenames and structure
        """
        
        # Extract episode info
        episode_info = {
            "title": base_script.get("generation_metadata", {}).get("episode_title", "Unknown Episode"),
            "episode_number": episode_number,
            "initials": initials,
            "source_video": f"{base_script.get('generation_metadata', {}).get('episode_title', 'Unknown')}.mp4",
            "estimated_total_duration": base_script.get("script_metadata", {}).get("estimated_duration", "25-30 minutes")
        }
        
        # Voice style mapping based on segment type
        voice_styles = {
            "intro": "enthusiastic",
            "pre_clip": "normal", 
            "post_clip": "sarcastic",  # For fact-checking
            "outro": "normal"
        }
        
        # Parse the full script to extract segments
        full_script = base_script.get("full_script", "")
        clip_segments = []
        
        # Extract selected clips info
        selected_clips = base_script.get("selected_clips", [])
        
        for i, clip in enumerate(selected_clips, 1):
            # Generate safe filename from clip_id
            safe_clip_name = self._make_safe_filename(clip.get("clip_id", f"clip_{i}"))
            
            segment = {
                "segment_index": i,
                "pre_clip": {
                    "script": f"Next, we're analyzing {clip.get('title', f'Clip {i}')}...",
                    "voice_style": voice_styles["pre_clip"],
                    "audio_filename": f"pre_clip_{i:03d}_{episode_number}_{safe_clip_name}_{initials}.wav",
                    "estimated_duration": "1 minute",
                    "video_instruction": "Show setup graphics, prepare for clip"
                },
                "clip_reference": {
                    "clip_id": clip.get("clip_id", f"clip_{i}"),
                    "title": clip.get("title", f"Clip {i}"),
                    "start_time": clip.get("start_time", "0:00:00"),
                    "end_time": clip.get("end_time", "0:00:30"),
                    "video_filename": f"[{clip.get('severity_level', 'UNKNOWN')}]_{i:02d}_{safe_clip_name}.mp4",
                    "estimated_duration": self._calculate_clip_duration(
                        clip.get("start_time", "0:00:00"), 
                        clip.get("end_time", "0:00:30")
                    )
                },
                "post_clip": {
                    "script": f"Let's fact-check what we just heard about {clip.get('title', 'this topic')}...",
                    "voice_style": voice_styles["post_clip"],
                    "audio_filename": f"post_clip_{i:03d}_{episode_number}_{safe_clip_name}_{initials}.wav",
                    "estimated_duration": "2-3 minutes", 
                    "video_instruction": "Show fact-checking graphics, sources"
                }
            }
            clip_segments.append(segment)
        
        # Build structured TTS script
        tts_script = {
            "episode_info": episode_info,
            "script_structure": {
                "intro": {
                    "script": self._extract_intro_from_script(full_script),
                    "voice_style": voice_styles["intro"],
                    "audio_filename": f"intro_{episode_number}_{initials}.wav",
                    "estimated_duration": "3-4 minutes",
                    "video_instruction": "Show intro graphics, host avatar"
                },
                "clip_segments": clip_segments,
                "outro": {
                    "script": self._extract_outro_from_script(full_script),
                    "voice_style": voice_styles["outro"], 
                    "audio_filename": f"conclusion_{episode_number}_{initials}.wav",
                    "estimated_duration": "5-7 minutes",
                    "video_instruction": "Show conclusion graphics, call to action"
                }
            },
            "generation_metadata": {
                "script_generation_timestamp": datetime.now().isoformat(),
                "tts_config_used": "Algenib voice, 24kHz WAV",
                "video_clips_source": "analysis_video_clipper.py output",
                "total_audio_segments": 2 + (len(clip_segments) * 2),  # intro + outro + pre/post for each clip
                "narrative_theme": base_script.get("narrative_theme", "Content Analysis"),
                "base_script_metadata": base_script.get("script_metadata", {})
            }
        }
        
        return tts_script
    
    def _make_safe_filename(self, text: str) -> str:
        """Make a string safe for use in filenames"""
        # Remove special characters and spaces
        safe = re.sub(r'[^\w\s-]', '', text)
        safe = re.sub(r'[-\s]+', '_', safe)
        return safe.lower()[:30]  # Limit length
    
    def _calculate_clip_duration(self, start_time: str, end_time: str) -> str:
        """Calculate duration between two timestamp strings"""
        try:
            # Simple duration calculation for MM:SS or HH:MM:SS format
            def time_to_seconds(time_str):
                parts = time_str.split(':')
                if len(parts) == 2:  # MM:SS
                    return int(parts[0]) * 60 + int(parts[1])
                elif len(parts) == 3:  # HH:MM:SS
                    return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                return 0
            
            start_seconds = time_to_seconds(start_time)
            end_seconds = time_to_seconds(end_time)
            duration_seconds = end_seconds - start_seconds
            
            if duration_seconds < 60:
                return f"{duration_seconds} seconds"
            else:
                minutes = duration_seconds // 60
                seconds = duration_seconds % 60
                return f"{minutes}:{seconds:02d}"
        except:
            return "Unknown duration"
    
    def _extract_intro_from_script(self, full_script: str) -> str:
        """Extract intro section from full script"""
        # Look for intro markers or take first few paragraphs
        lines = full_script.split('\n')
        intro_lines = []
        
        for line in lines[:10]:  # Take first 10 lines as intro
            if line.strip() and not line.startswith('[CLIP_MARKER'):
                intro_lines.append(line.strip())
            if len(intro_lines) >= 5:  # Reasonable intro length
                break
                
        return '\n'.join(intro_lines) if intro_lines else "Welcome to our analysis episode..."
    
    def _extract_outro_from_script(self, full_script: str) -> str:
        """Extract outro section from full script"""
        # Look for conclusion markers or take last few paragraphs
        lines = full_script.split('\n')
        outro_lines = []
        
        # Look for conclusion markers or take last non-empty lines
        for line in reversed(lines[-15:]):  # Check last 15 lines
            if line.strip() and not line.startswith('[CLIP_MARKER'):
                outro_lines.insert(0, line.strip())
            if len(outro_lines) >= 5:  # Reasonable outro length
                break
                
        return '\n'.join(outro_lines) if outro_lines else "That concludes our analysis. Thanks for listening..."

    def save_tts_ready_script(self, tts_script: Dict, output_path: str) -> Path:
        """
        Save TTS-ready script in the ideal format
        
        Returns:
            Path to saved TTS script file
        """
        output_path = Path(output_path)
        
        # Save TTS-ready structured data
        tts_path = output_path.with_suffix('.json')
        with open(tts_path, 'w', encoding='utf-8') as f:
            json.dump(tts_script, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved TTS-ready script: {tts_path}")
        
        return tts_path
    
    def _load_analysis_data(self, analysis_path: str) -> Dict[str, Any]:
        """
        Load analysis data from either JSON or text format files
        
        Args:
            analysis_path: Path to analysis file (JSON or text with embedded JSON)
            
        Returns:
            Dictionary containing the analysis data
        """
        try:
            with open(analysis_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try to parse as direct JSON first
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                self.logger.info("File is not direct JSON, attempting to extract embedded JSON")
            
            # If not direct JSON, look for JSON array in the content
            # Find JSON array patterns
            json_patterns = [
                r'\[\s*\{.*?\}\s*\]',  # Array of objects
                r'\{.*?\}',            # Single object
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, content, re.DOTALL)
                for match in matches:
                    try:
                        parsed = json.loads(match)
                        self.logger.info("Successfully extracted JSON from text format")
                        return parsed if isinstance(parsed, list) else [parsed]
                    except json.JSONDecodeError:
                        continue
              # Fail clearly if no valid JSON is found
            error_msg = f"No valid JSON found in analysis file: {analysis_path}. The file must contain properly formatted JSON data for podcast generation."
            self.logger.error(error_msg)
            raise ValueError(error_msg)
            
        except Exception as e:
            self.logger.error(f"Error loading analysis data: {e}")
            raise
    
    def _convert_to_tts_format(self, response_text: str, episode_title: str) -> Dict[str, Any]:
        """
        Convert plain text script to TTS-compatible format
        """
        # Extract episode number from title (simple approach)
        import re
        episode_match = re.search(r'(\d+)', episode_title)
        episode_number = episode_match.group(1) if episode_match else "001"
        
        # Generate episode initials
        words = episode_title.split()
        initials = ''.join([word[0].upper() for word in words[:2]]) if len(words) >= 2 else "EP"
        
        return {
            "episode_info": {
                "title": episode_title,
                "episode_number": episode_number,
                "initials": initials,
                "source_video": f"{episode_title}.mp4",
                "estimated_total_duration": "20-25 minutes"
            },
            "script_structure": {
                "intro": {
                    "script": response_text,
                    "voice_style": "normal",
                    "audio_filename": f"full_script_{episode_number}_{initials}.wav",
                    "estimated_duration": "20-25 minutes",
                    "video_instruction": "Show podcast graphics"
                }
            }
        }

# Example usage and testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate podcast scripts from analysis data")
    parser.add_argument("--test-basic", action="store_true", help="Test basic script generation")
    parser.add_argument("--test-tts", action="store_true", help="Test TTS-ready script generation")
    parser.add_argument("--analysis-path", help="Path to analysis JSON file")
    parser.add_argument("--episode-title", help="Episode title")
    parser.add_argument("--episode-number", default="001", help="Episode number")
    parser.add_argument("--initials", default="TBD", help="Guest initials")
    
    args = parser.parse_args()
    
    # Default test data
    default_analysis_path = "Transcripts/Joe_Rogan_Experience/Joe Rogan Experience 2325 - Aaron Rodgers/Joe Rogan Experience 2325 - Aaron Rodgers_analysis_analysis.json"
    default_episode_title = "Joe Rogan Experience 2325 - Aaron Rodgers"
    
    analysis_path = args.analysis_path or default_analysis_path
    episode_title = args.episode_title or default_episode_title
    
    generator = PodcastNarrativeGenerator()
    
    if args.test_tts:
        # Test TTS-ready script generation
        print("Testing TTS-ready script generation...")
        
        if Path(analysis_path).exists():
            tts_script = generator.generate_tts_ready_script(
                analysis_json_path=analysis_path,
                episode_title=episode_title,
                episode_number=args.episode_number,
                initials=args.initials,
                prompt_template="tts_podcast_narrative_prompt.txt"
            )
            
            # Save TTS script
            output_path = "test_tts_podcast_script"
            tts_path = generator.save_tts_ready_script(tts_script, output_path)
            
            print(f"✅ TTS script generation completed!")
            print(f"🎵 TTS Script: {tts_path}")
            print(f"📊 Audio segments: {tts_script['generation_metadata']['total_audio_segments']}")
            print(f"🎬 Clip segments: {len(tts_script['script_structure']['clip_segments'])}")
        else:
            print(f"❌ Analysis file not found: {analysis_path}")
    
    elif args.test_basic:
        # Test basic script generation
        print("Testing basic script generation...")
        
        if Path(analysis_path).exists():
            script_data = generator.generate_podcast_script(
                analysis_path,
                episode_title
            )
            
            # Save the script
            output_path = "test_podcast_script"
            json_path, txt_path = generator.save_podcast_script(script_data, output_path)
            
            print(f"✅ Basic script generation completed!")
            print(f"📄 JSON: {json_path}")
            print(f"📝 Script: {txt_path}")
        else:
            print(f"❌ Analysis file not found: {analysis_path}")
    
    else:
        print("Usage: python podcast_narrative_generator.py [--test-basic | --test-tts]")
        print("")
        print("Options:")
        print("  --test-basic     Generate traditional podcast script")
        print("  --test-tts       Generate TTS-ready structured script")
        print("  --analysis-path  Path to analysis JSON file")
        print("  --episode-title  Episode title")
        print("  --episode-number Episode number (default: 001)")
        print("  --initials       Guest initials (default: TBD)")
        print("")
        print("The TTS-ready script includes:")
        print("- Structured audio segments with filenames")
        print("- Voice style specifications")
        print("- Video clip references")
        print("- Integration points for video editor")
