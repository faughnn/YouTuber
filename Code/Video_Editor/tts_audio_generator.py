"""
TTS Audio Generator for Video Editor
Generates narrator audio files using existing Gemini TTS system
"""

import os
import sys
from pathlib import Path
from typing import Dict, List
import logging

# Add the TTS module to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from TTS import SimpleTTSGenerator
except ImportError as e:
    logging.error(f"Could not import TTS generator: {e}")
    SimpleTTSGenerator = None

class TTSAudioGenerator:
    def __init__(self, output_dir: str = None):
        """
        Initialize TTS Audio Generator
        
        Args:
            output_dir: Directory to save generated audio files
        """
        self.logger = logging.getLogger(__name__)
        
        if output_dir is None:
            # Default to Content/Audio/Generated/Narrator
            base_path = Path(__file__).parent.parent.parent
            output_dir = base_path / "Content" / "Audio" / "Generated" / "Narrator"
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize TTS generator
        if SimpleTTSGenerator:
            try:
                self.tts_generator = SimpleTTSGenerator()
                self.logger.info("TTS generator initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize TTS generator: {e}")
                self.tts_generator = None
        else:
            self.tts_generator = None
            self.logger.warning("TTS generator not available")
    
    def generate_all_audio_files(self, timeline_data: Dict, expected_filenames: Dict) -> Dict[str, str]:
        """
        Generate all audio files for the timeline
        
        Args:
            timeline_data: Parsed timeline data from script parser
            expected_filenames: Expected filenames from script parser
            
        Returns:
            Dictionary mapping segment types to generated file paths
        """
        if not self.tts_generator:
            self.logger.error("TTS generator not available")
            return {}
        
        generated_files = {}
        
        try:
            # Generate intro audio
            if timeline_data['script_segments']['intro']:
                intro_path = self._generate_audio_file(
                    text=timeline_data['script_segments']['intro'],
                    filename=expected_filenames['intro'],
                    segment_type='intro'
                )
                if intro_path:
                    generated_files['intro'] = intro_path
            
            # Generate conclusion audio
            if timeline_data['script_segments']['conclusion']:
                conclusion_path = self._generate_audio_file(
                    text=timeline_data['script_segments']['conclusion'],
                    filename=expected_filenames['conclusion'],
                    segment_type='conclusion'
                )
                if conclusion_path:
                    generated_files['conclusion'] = conclusion_path
            
            # Generate pre-clip setup audio files
            generated_files['pre_clips'] = []
            pre_setups = timeline_data['script_segments']['pre_clip_setups']
            
            for i, pre_setup_text in enumerate(pre_setups):
                if i < len(expected_filenames['pre_clips']) and pre_setup_text.strip():
                    pre_clip_path = self._generate_audio_file(
                        text=pre_setup_text,
                        filename=expected_filenames['pre_clips'][i],
                        segment_type=f'pre_clip_{i+1}'
                    )
                    if pre_clip_path:
                        generated_files['pre_clips'].append(pre_clip_path)
            
            # Generate post-clip analysis audio files
            generated_files['post_clips'] = []
            post_analyses = timeline_data['script_segments']['post_clip_analyses']
            
            for i, post_analysis_text in enumerate(post_analyses):
                if i < len(expected_filenames['post_clips']) and post_analysis_text.strip():
                    post_clip_path = self._generate_audio_file(
                        text=post_analysis_text,
                        filename=expected_filenames['post_clips'][i],
                        segment_type=f'post_clip_{i+1}'
                    )
                    if post_clip_path:
                        generated_files['post_clips'].append(post_clip_path)
            
            self.logger.info(f"Generated {len([f for f in generated_files.values() if f])} audio files")
            return generated_files
            
        except Exception as e:
            self.logger.error(f"Error generating audio files: {e}")
            return {}
    
    def _generate_audio_file(self, text: str, filename: str, segment_type: str) -> str:
        """
        Generate a single audio file
        
        Args:
            text: Text to convert to speech
            filename: Output filename
            segment_type: Type of segment for logging
            
        Returns:
            Path to generated audio file or None if failed
        """
        try:
            # Clean up the text
            cleaned_text = self._clean_text_for_tts(text)
            
            if not cleaned_text.strip():
                self.logger.warning(f"Empty text for {segment_type}, skipping")
                return None
            
            # Generate audio file path
            output_path = self.output_dir / filename
            
            # Check if file already exists
            if output_path.exists():
                self.logger.info(f"Audio file already exists: {filename}")
                return str(output_path)
            
            self.logger.info(f"Generating audio for {segment_type}: {filename}")
            
            # Generate the audio using TTS
            success = self.tts_generator.generate_audio(
                text=cleaned_text,
                output_path=str(output_path)
            )
            
            if success and output_path.exists():
                self.logger.info(f"Successfully generated: {filename}")
                return str(output_path)
            else:
                self.logger.error(f"Failed to generate audio for {segment_type}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating audio for {segment_type}: {e}")
            return None
    
    def _clean_text_for_tts(self, text: str) -> str:
        """
        Clean text for TTS processing
        
        Args:
            text: Raw text from script
            
        Returns:
            Cleaned text suitable for TTS
        """
        # Remove markdown formatting
        cleaned = text.replace('**', '')
        cleaned = cleaned.replace('*', '')
        
        # Remove stage directions and formatting
        import re
        
        # Remove lines that start with ** (stage directions)
        lines = cleaned.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
                
            # Skip obvious stage directions
            if line.startswith('**(') and line.endswith(')**'):
                continue
                
            # Skip lines that are just formatting markers
            if line in ['**Host:**', '**PRE-CLIP SETUP:**', '**POST-CLIP ANALYSIS:**']:
                continue
                
            # Remove Host: prefixes
            if line.startswith('**Host:**'):
                line = line.replace('**Host:**', '').strip()
            
            # Add the line if it has content
            if line:
                cleaned_lines.append(line)
        
        # Join lines back together
        cleaned = ' '.join(cleaned_lines)
        
        # Fix common TTS issues
        cleaned = cleaned.replace('\\"', '"')  # Fix escaped quotes
        cleaned = cleaned.replace('\\n', ' ')  # Fix escaped newlines
        cleaned = re.sub(r'\s+', ' ', cleaned)  # Multiple spaces to single space
        
        return cleaned.strip()
    
    def check_existing_audio_files(self, expected_filenames: Dict) -> Dict[str, bool]:
        """
        Check which audio files already exist
        
        Args:
            expected_filenames: Expected filenames from script parser
            
        Returns:
            Dictionary mapping filenames to existence status
        """
        existing_files = {}
        
        # Check intro and conclusion
        for key in ['intro', 'conclusion']:
            if key in expected_filenames:
                filepath = self.output_dir / expected_filenames[key]
                existing_files[expected_filenames[key]] = filepath.exists()
        
        # Check pre-clip and post-clip files
        for key in ['pre_clips', 'post_clips']:
            if key in expected_filenames:
                for filename in expected_filenames[key]:
                    filepath = self.output_dir / filename
                    existing_files[filename] = filepath.exists()
        
        return existing_files
    
    def get_audio_duration(self, audio_file_path: str) -> float:
        """
        Get duration of an audio file in seconds
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            Duration in seconds, or 0.0 if unable to determine
        """
        try:
            # Try to use librosa if available
            try:
                import librosa
                y, sr = librosa.load(audio_file_path)
                return len(y) / sr
            except ImportError:
                pass
            
            # Try to use wave for WAV files
            try:
                import wave
                with wave.open(audio_file_path, 'r') as wav_file:
                    frames = wav_file.getnframes()
                    sample_rate = wav_file.getframerate()
                    return frames / sample_rate
            except:
                pass
            
            # Default fallback - estimate based on file size (very rough)
            file_size = os.path.getsize(audio_file_path)
            # Rough estimate: 1MB = ~60 seconds for compressed audio
            estimated_duration = file_size / (1024 * 1024) * 60
            self.logger.warning(f"Using rough duration estimate for {audio_file_path}: {estimated_duration:.1f}s")
            return estimated_duration
            
        except Exception as e:
            self.logger.error(f"Could not determine duration for {audio_file_path}: {e}")
            return 0.0

if __name__ == "__main__":
    # Test with the simple script
    import sys
    sys.path.append('.')
    from script_parser import ScriptParser
    
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Parse the script
        parser = ScriptParser()
        timeline_data = parser.parse_script_file('test_simple_script.json')
        expected_filenames = parser.generate_audio_filenames(timeline_data)
        
        print("Timeline data parsed successfully")
        print(f"Episode: {timeline_data['episode_info']['title']}")
        print(f"Clips: {len(timeline_data['clips'])}")
        
        # Initialize TTS generator
        tts_gen = TTSAudioGenerator()
        
        # Check existing files
        existing = tts_gen.check_existing_audio_files(expected_filenames)
        print(f"\nExisting audio files:")
        for filename, exists in existing.items():
            status = "EXISTS" if exists else "MISSING"
            print(f"  {filename}: {status}")
        
        # Generate missing audio files
        print(f"\nGenerating audio files...")
        generated_files = tts_gen.generate_all_audio_files(timeline_data, expected_filenames)
        
        print(f"\nGeneration complete!")
        print(f"Generated files: {len([f for f in generated_files.values() if f])}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
