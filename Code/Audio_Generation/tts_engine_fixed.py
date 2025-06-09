"""
TTS Engine using Gemini API

This module provides the core TTS functionality using Google's Gemini API
with support for natural language tone descriptions.
"""

import logging
import time
import wave
import tempfile
import io
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

# Optional import for Gemini API
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    types = None
    GEMINI_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class TTSResult:
    """Result of TTS generation operation."""
    success: bool
    output_path: str
    audio_duration: Optional[float] = None
    file_size: Optional[int] = None
    generation_time: Optional[float] = None
    text_length: Optional[int] = None
    error_message: Optional[str] = None


class GeminiTTSEngine:
    """
    TTS Engine using Google's Gemini API.
    
    Features:
    - Natural language tone descriptions
    - Rate limiting and retry logic
    - Comprehensive error handling
    - Audio file management
    """
    
    def __init__(self, config):
        """
        Initialize the TTS engine.
        
        Args:
            config: AudioGenerationConfig instance
        """
        self.config = config
        self.gemini_config = config.gemini_config
        self.audio_settings = config.audio_settings
        self.logger = logging.getLogger(__name__)
        
        # Initialize Gemini client
        if GEMINI_AVAILABLE and self.gemini_config.api_key:
            try:
                genai.configure(api_key=self.gemini_config.api_key)
                self.client = genai
                self.logger.info("Gemini TTS client initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize Gemini client: {e}")
                raise
        else:
            raise Exception("Gemini API not available or API key not configured")
        
        # Define tone templates for better prompt engineering
        self.tone_templates = {
            'enthusiastic': "Generate audio with an enthusiastic and energetic tone: {tone}. ",
            'conversational': "Generate audio with a natural conversational tone: {tone}. ",
            'analytical': "Generate audio with a thoughtful analytical tone: {tone}. ",
            'educational': "Generate audio with a clear educational tone: {tone}. ",
            'default': "Generate audio with this tone: {tone}. "
        }
    
    def _format_tone_instruction(self, tone: str, text: str) -> str:
        """
        Format tone instruction for optimal TTS results.
        
        Args:
            tone: Natural language tone description
            text: Text content to convert
            
        Returns:
            Formatted prompt with tone instruction
        """
        # Select appropriate template based on tone keywords
        template_key = 'default'
        if any(word in tone.lower() for word in ['enthusiastic', 'energetic', 'excited', 'welcoming']):
            template_key = 'enthusiastic'
        elif any(word in tone.lower() for word in ['conversational', 'casual', 'friendly', 'chat']):
            template_key = 'conversational'
        elif any(word in tone.lower() for word in ['analytical', 'fact-check', 'critical', 'examining']):
            template_key = 'analytical'
        elif any(word in tone.lower() for word in ['educational', 'teaching', 'informative', 'explaining']):
            template_key = 'educational'
        
        template = self.tone_templates.get(template_key, self.tone_templates['default'])
        
        # Format the prompt
        instruction = template.format(tone=tone)
        
        # Combine instruction with text
        full_prompt = f"{instruction}\n\n{text}"
        
        self.logger.debug(f"Formatted prompt: {full_prompt[:100]}...")
        return full_prompt
    
    def _generate_real_audio(self, prompt: str) -> bytes:
        """
        Generate audio using the Gemini TTS API.
        
        Args:
            prompt: Formatted prompt with tone instruction and text
            
        Returns:
            Audio data as bytes
        """
        try:
            self.logger.info(f"Generating real audio with Gemini TTS: {prompt[:50]}...")
            
            # Apply rate limiting to respect API limits
            if self.audio_settings.delay_between_requests > 0:
                self.logger.debug(f"Applying rate limiting delay: {self.audio_settings.delay_between_requests}s")
                time.sleep(self.audio_settings.delay_between_requests)
            
            # Generate audio using Gemini API
            response = self.client.models.generate_content(
                model=self.gemini_config.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=self.gemini_config.voice_name,
                            )
                        )
                    ),
                )
            )
            
            # Extract audio data from response
            if response.candidates and len(response.candidates) > 0:
                audio_data = response.candidates[0].content.parts[0].inline_data.data
                self.logger.info(f"Successfully generated {len(audio_data)} bytes of audio")
                return audio_data
            else:
                raise Exception("No audio data in Gemini response")
                
        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "quota" in error_str or "rate limit" in error_str:
                self.logger.error(f"API rate limit exceeded: {e}")
                self.logger.error("Please wait longer between requests or reduce concurrent processing")
                self.logger.error("Current delay setting: {}s".format(self.audio_settings.delay_between_requests))
            else:
                self.logger.error(f"Failed to generate real audio: {e}")
            raise e
    
    def _create_audio_file(self, audio_data: bytes, output_path: Path) -> bool:
        """
        Save audio data to file in proper WAV format.
        
        Args:
            audio_data: Raw audio data from Gemini TTS
            output_path: Path to save the audio file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # For real audio data from Gemini API, we need to handle it properly
            if isinstance(audio_data, bytes):
                # Direct save of audio data from Gemini
                with open(output_path, 'wb') as f:
                    f.write(audio_data)
                self.logger.debug(f"Audio saved as raw file: {output_path}")
            else:
                # Format as WAV if needed
                with wave.open(str(output_path), 'wb') as wav_file:
                    wav_file.setnchannels(self.gemini_config.channels)
                    wav_file.setsampwidth(self.gemini_config.sample_width)
                    wav_file.setframerate(self.gemini_config.sample_rate)
                    wav_file.writeframes(audio_data)
                self.logger.debug(f"Audio saved as formatted WAV file: {output_path}")
            
            # Validate the created file
            return self._validate_audio_output(output_path)
            
        except Exception as e:
            self.logger.error(f"Failed to save audio file {output_path}: {e}")
            return False
    
    def _validate_audio_output(self, file_path: Path) -> bool:
        """
        Validate that the audio file was created successfully.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            True if file is valid, False otherwise
        """
        try:
            if not file_path.exists():
                self.logger.error(f"Audio file was not created: {file_path}")
                return False
            
            file_size = file_path.stat().st_size
            if file_size == 0:
                self.logger.error(f"Audio file is empty: {file_path}")
                return False
            
            self.logger.debug(f"Audio file validation passed: {file_path} ({file_size} bytes)")
            return True
            
        except Exception as e:
            self.logger.error(f"Audio validation failed for {file_path}: {e}")
            return False
    
    def _get_audio_duration(self, file_path: Path) -> float:
        """
        Get the duration of an audio file in seconds.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Duration in seconds, or 0.0 if unable to determine
        """
        try:
            with wave.open(str(file_path), 'rb') as wav_file:
                frames = wav_file.getnframes()
                sample_rate = wav_file.getframerate()
                duration = frames / float(sample_rate)
                return duration
        except Exception as e:
            self.logger.warning(f"Could not determine audio duration for {file_path}: {e}")
            # Estimate based on file size (rough approximation)
            file_size = file_path.stat().st_size
            estimated_duration = file_size / (self.gemini_config.sample_rate * 2)  # Rough estimate
            return max(1.0, estimated_duration)
    
    def generate_audio(self, text: str, tone: str, output_path: Union[str, Path]) -> TTSResult:
        """
        Generate audio file from text with specified tone.
        
        Args:
            text: Text content to convert to speech
            tone: Natural language tone description
            output_path: Path where audio file should be saved
            
        Returns:
            TTSResult with operation details
        """
        start_time = time.time()
        output_path = Path(output_path)
        
        # Validate inputs
        if not text.strip():
            return TTSResult(
                success=False,
                output_path=str(output_path),
                error_message="Text content cannot be empty",
                generation_time=time.time() - start_time,
                text_length=len(text)
            )
        
        if len(text) > self.audio_settings.max_text_length:
            return TTSResult(
                success=False,
                output_path=str(output_path),
                error_message=f"Text too long ({len(text)} chars, max {self.audio_settings.max_text_length})",
                generation_time=time.time() - start_time,
                text_length=len(text)
            )
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Format the prompt with tone instruction
            prompt = self._format_tone_instruction(tone, text)
            
            # Generate audio using Gemini API
            audio_data = self._generate_real_audio(prompt)
            
            # Save audio file
            success = self._create_audio_file(audio_data, output_path)
            
            if success:
                # Get file info
                file_size = output_path.stat().st_size
                duration = self._get_audio_duration(output_path)
                
                generation_time = time.time() - start_time
                
                self.logger.info(f"Audio generated successfully: {output_path} ({file_size} bytes, {duration:.2f}s)")
                
                return TTSResult(
                    success=True,
                    output_path=str(output_path),
                    audio_duration=duration,
                    file_size=file_size,
                    generation_time=generation_time,
                    text_length=len(text)
                )
            else:
                return TTSResult(
                    success=False,
                    output_path=str(output_path),
                    error_message="Failed to save audio file",
                    generation_time=time.time() - start_time,
                    text_length=len(text)
                )
                
        except Exception as e:
            error_message = f"TTS generation failed: {str(e)}"
            self.logger.error(error_message)
            
            return TTSResult(
                success=False,
                output_path=str(output_path),
                error_message=error_message,
                generation_time=time.time() - start_time,
                text_length=len(text)
            )
    
    def generate_audio_with_retry(self, text: str, tone: str, output_path: Union[str, Path]) -> TTSResult:
        """
        Generate audio with automatic retry on failure.
        
        Args:
            text: Text content to convert to speech
            tone: Natural language tone description
            output_path: Path where audio file should be saved
            
        Returns:
            TTSResult with operation details
        """
        last_result = None
        
        for attempt in range(self.audio_settings.retry_attempts + 1):
            if attempt > 0:
                self.logger.info(f"Retry attempt {attempt}/{self.audio_settings.retry_attempts}")
                # Extra delay for retries, especially for rate limiting
                retry_delay = self.audio_settings.delay_between_requests * (attempt + 1)
                self.logger.info(f"Waiting {retry_delay}s before retry...")
                time.sleep(retry_delay)
            
            result = self.generate_audio(text, tone, output_path)
            
            if result.success:
                return result
            
            last_result = result
            self.logger.warning(f"Attempt {attempt + 1} failed: {result.error_message}")
        
        # All attempts failed
        self.logger.error(f"All {self.audio_settings.retry_attempts + 1} attempts failed")
        return last_result
    
    def test_connection(self) -> bool:
        """
        Test connection to Gemini TTS API.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Simple test with minimal text
            test_text = "Test"
            prompt = self._format_tone_instruction("neutral", test_text)
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=True) as temp_file:
                temp_path = Path(temp_file.name)
                
                # Try to generate a short audio clip
                audio_data = self._generate_real_audio(prompt)
                success = self._create_audio_file(audio_data, temp_path)
                
                if success and temp_path.exists():
                    self.logger.info("TTS connection test successful")
                    return True
                else:
                    self.logger.warning("TTS connection test failed - file not created")
                    return False
                    
        except Exception as e:
            self.logger.warning(f"TTS connection test failed: {e}")
            return False
