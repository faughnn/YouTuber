"""
Simple Gemini TTS Generator for Podcast Scripts
Converts text to speech using Gemini TTS API
"""

import os
import json
import wave
import yaml
import time
from pathlib import Path
from google import genai
from google.genai import types

class SimpleTTSGenerator:
    """Simple TTS generator using Gemini"""
    
    def __init__(self, output_dir: str = None):
        # Load TTS configuration
        self.config = self._load_tts_config()
        
        self.api_key = self._get_api_key()
        self.client = genai.Client(api_key=self.api_key)
        
        # Set output directory - default to Content/Audio/Generated
        if output_dir is None:
            # Navigate from TTS/core/ to Content/Audio/Generated
            base_path = Path(__file__).parent.parent.parent.parent
            self.output_dir = base_path / "Content" / "Audio" / "Generated"
        else:
            self.output_dir = Path(output_dir)
            
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_tts_config(self):
        """Load TTS configuration from config file"""
        try:
            # Try to find the config file from TTS/core/
            script_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(script_dir, "..", "config", "tts_config.json")
            
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return json.load(f)
            else:
                # Return default config if file not found
                print("⚠️ TTS config file not found, using defaults")
                return {
                    "provider": "gemini",
                    "gemini": {
                        "model": "gemini-2.5-flash-preview-tts",
                        "voice_name": "Kore",
                        "audio_format": "wav",
                        "sample_rate": 24000,
                        "channels": 1,
                        "sample_width": 2
                    }
                }
        except Exception as e:
            print(f"Error loading TTS config: {e}")
            # Return default config on error
            return {
                "provider": "gemini",
                "gemini": {
                    "model": "gemini-2.5-flash-preview-tts",
                    "voice_name": "Kore",
                    "audio_format": "wav",
                    "sample_rate": 24000,
                    "channels": 1,
                    "sample_width": 2
                }
            }
    
    def _get_api_key(self):
        """Get Gemini API key from config"""
        try:
            # Try multiple possible config paths from TTS/core/
            script_dir = os.path.dirname(os.path.abspath(__file__))
            possible_paths = [
                os.path.join(script_dir, "..", "..", "Config", "default_config.yaml"),
                os.path.join(script_dir, "..", "..", "..", "Config", "default_config.yaml"),
                "../../Config/default_config.yaml",
                "../../../Config/default_config.yaml"
            ]
            
            config_path = None
            for path in possible_paths:
                abs_path = os.path.abspath(path)
                if os.path.exists(abs_path):
                    config_path = abs_path
                    break
            
            if not config_path:
                raise FileNotFoundError(f"Config file not found in any of: {possible_paths}")
                
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                return config['api']['gemini_api_key']
        except Exception as e:
            print(f"Error loading API key: {e}")
            raise
    
    def generate_audio(self, text, output_filename, voice_style="normal"):
        """Generate audio from text"""
        try:
            # Enhance text based on style
            if voice_style == "enthusiastic":
                enhanced_text = f"Say enthusiastically: {text}"
            elif voice_style == "sarcastic":
                enhanced_text = f"Say with a slightly sarcastic tone: {text}"
            else:
                enhanced_text = text
            
            print(f"🎙️ Generating audio ({len(text)} characters)...")
              # Generate audio
            response = self.client.models.generate_content(
                model=self.config['gemini']['model'],
                contents=enhanced_text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=self.config['gemini']['voice_name'],
                            )
                        )
                    ),
                )
            )
              # Extract and save audio
            audio_data = response.candidates[0].content.parts[0].inline_data.data
            output_path = self.output_dir / output_filename
            
            with wave.open(str(output_path), "wb") as wf:
                wf.setnchannels(self.config['gemini']['channels'])
                wf.setsampwidth(self.config['gemini']['sample_width'])
                wf.setframerate(self.config['gemini']['sample_rate'])
                wf.writeframes(audio_data)
            
            print(f"✅ Audio saved: {output_path}")
            return str(output_path)
            
        except Exception as e:
            print(f"❌ Failed to generate audio: {e}")
            raise
    
    def generate_podcast_from_script(self, script_path, episode_title):
        """Generate podcast audio from script file"""
        print(f"🎬 Generating podcast: {episode_title}")
        
        # Load script
        with open(script_path, 'r', encoding='utf-8') as f:
            script_text = f.read()
        
        # Clean up script (remove JSON if present)
        if script_text.strip().startswith('{'):
            try:
                script_data = json.loads(script_text)
                script_text = script_data.get('script', script_data.get('content', str(script_data)))
            except:
                pass
        
        # Simple segmentation by paragraphs
        paragraphs = [p.strip() for p in script_text.split('\n\n') if p.strip() and len(p.strip()) > 20]
        
        audio_files = []
        total_chars = 0
        
        for i, paragraph in enumerate(paragraphs[:5]):  # Limit to first 5 paragraphs for testing
            if len(paragraph) < 10:
                continue
                
            # Determine voice style
            voice_style = "normal"
            if i == 0:  # Intro
                voice_style = "enthusiastic"
            elif "?" in paragraph or "really" in paragraph.lower():
                voice_style = "sarcastic"
            
            filename = f"{episode_title.replace(' ', '_')}_segment_{i+1}.wav"
            
            try:
                audio_path = self.generate_audio(paragraph, filename, voice_style)
                audio_files.append(audio_path)
                total_chars += len(paragraph)
                
                # Small delay to avoid rate limiting
                time.sleep(1)
                
            except Exception as e:
                print(f"⚠️ Failed to generate segment {i+1}: {e}")
                continue
        
        # Save metadata
        metadata = {
            'title': episode_title,
            'segments': len(audio_files),
            'audio_files': audio_files,
            'total_characters': total_chars,
            'generated_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        metadata_path = self.output_dir / f"{episode_title.replace(' ', '_')}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Generated {len(audio_files)} audio segments!")
        print(f"📁 Files saved to: {self.output_dir}")
        
        return metadata

def main():
    """Command line interface"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python tts_generator.py <script_path> [episode_title]")
        sys.exit(1)
    
    script_path = sys.argv[1]
    episode_title = sys.argv[2] if len(sys.argv) > 2 else "Test Episode"
    
    try:
        generator = SimpleTTSGenerator()
        result = generator.generate_podcast_from_script(script_path, episode_title)
        
        print(f"\n🎉 Success! Generated {result['segments']} audio segments")
        print(f"📊 Total characters processed: {result['total_characters']}")
        
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
