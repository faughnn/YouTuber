import json
import google.generativeai as genai
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml
from datetime import datetime
import logging

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
    
    def __init__(self, config_path: str = "Scripts/config/default_config.yaml"):
        # Load existing config
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)        # Initialize Gemini
        genai.configure(api_key=self.config['api']['gemini_api_key'])
        self.model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
        
        # Initialize prompt loader
        self.prompt_loader = PromptLoader("Scripts/Content Analysis/Prompts/")
        
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
        
        # Load analysis data
        with open(analysis_json_path, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)
        
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
        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse JSON response: {e}")
            # If not JSON, treat as plain text script
            parsed_response = {
                "narrative_theme": "Generated Script",
                "selected_clips": [],
                "clip_order": [],
                "full_script": response_text,
                "script_metadata": {
                    "estimated_duration": "unknown",
                    "target_audience": "general",
                    "key_themes": []
                }
            }
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
            f.write(script_data.get('full_script', ''))
        
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

# Example usage and testing
if __name__ == "__main__":
    # Test the generator
    generator = PodcastNarrativeGenerator()
    
    # Test with Joe Rogan 2325 analysis
    analysis_path = "Transcripts/Joe_Rogan_Experience/Joe Rogan Experience 2325 - Aaron Rodgers/Joe Rogan Experience 2325 - Aaron Rodgers_analysis_analysis.json"
    
    if Path(analysis_path).exists():
        script_data = generator.generate_podcast_script(
            analysis_path,
            "Joe Rogan Experience 2325 - Aaron Rodgers"
        )
        
        # Save the script
        output_path = "test_podcast_script"
        json_path, txt_path = generator.save_podcast_script(script_data, output_path)
        
        print(f"✅ Test completed successfully!")
        print(f"📄 JSON: {json_path}")
        print(f"📝 Script: {txt_path}")
    else:
        print(f"❌ Analysis file not found: {analysis_path}")
