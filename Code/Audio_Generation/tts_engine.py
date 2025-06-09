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
    """Result of a TTS generation operation."""
    success: bool
    output_path: str
    error_message: str = ""
    audio_duration: float = 0.0
    file_size: int = 0
    generation_time: float = 0.0
    text_length: int = 0


class GeminiTTSEngine:
    """
    TTS Engine using Google's Gemini API with advanced tone processing.
    
    Supports natural language tone descriptions and generates high-quality
    audio files suitable for podcast production.
    """
    
    def __init__(self, config):
        """
        Initialize the TTS engine with configuration.
        
        Args:
            config: AudioGenerationConfig instance with Gemini settings
        """
        self.config = config
        self.gemini_config = config.load_gemini_config()
        self.audio_settings = config.get_audio_settings()
        self.logger = logging.getLogger(__name__)
        
        # Initialize Gemini API if available
        if GEMINI_AVAILABLE and self.gemini_config.api_key:
            self._initialize_gemini_api()
        else:
            self.logger.warning("Gemini API not available - using test mode")
        
        # Tone processing templates
        self.tone_templates = {
            'default': "Say this with {tone}:",
            'conversational': "In a {tone} conversational style, say:",
            'analytical': "In an {tone} analytical tone, say:",
            'educational': "Using an {tone} educational approach, say:",        }
        
    def _initialize_gemini_api(self) -> None:
        """Initialize the Gemini API client."""
        try:
            self.client = genai.Client(api_key=self.gemini_config.api_key)
            self.logger.info(f"Gemini API initialized with model: {self.gemini_config.model}")
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini API: {e}")
            raise

    def generate_audio(self, text: str, tone: str, output_path: Union[str, Path]) -> TTSResult:
        """
        Generate audio from text with specified tone.
        
        Args:
            text: Text content to convert to speech
            tone: Natural language tone description
            output_path: Path where audio file should be saved
            
        Returns:
            TTSResult with operation details
        """
        start_time = time.time()
        output_path = Path(output_path)
        
        self.logger.info(f"Generating audio for text length {len(text)} with tone: '{tone}'")
        
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
                text_length=len(text)            )
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Format the prompt with tone instruction
            prompt = self._format_tone_instruction(tone, text)
            
            # Generate audio using Gemini API
            if not GEMINI_AVAILABLE or not self.gemini_config.api_key:
                error_message = "Gemini API not available or API key not configured"
                self.logger.error(error_message)
                return TTSResult(
                    success=False,
                    output_path=str(output_path),
                    error_message=error_message,
                    generation_time=time.time() - start_time,
                    text_length=len(text)
                )
            
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

    def _format_tone_instruction(self, tone: str, text: str) -> str:
        """
        Format the tone instruction for optimal TTS results.
        
        Args:
            tone: Natural language tone description
            text: Text content to be spoken
            
        Returns:
            Formatted prompt for Gemini TTS
        """
        # Clean and process the tone
        tone = tone.strip()
        if not tone:
            tone = self.audio_settings.fallback_tone
        
        # Determine the best template based on tone keywords
        template_key = 'default'
        
        if any(word in tone.lower() for word in ['conversational', 'chat', 'friendly', 'casual']):
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
            else:
                self.logger.error(f"Failed to generate real audio: {e}")
            raise e  # Re-raise the error instead of falling back to test audio

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
            # The audio_data should already be properly formatted audio
            
            # Check if the audio_data is already in WAV format
            if audio_data.startswith(b'RIFF'):
                # Audio is already a complete WAV file, save directly
                with open(output_path, 'wb') as f:
                    f.write(audio_data)
                self.logger.debug(f"Audio saved as complete WAV file: {output_path}")
            else:
                # Audio is raw PCM data, need to create WAV format
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
        Validate that the audio file was created correctly.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            True if valid, False otherwise
        """
        try:
            if not file_path.exists():
                return False
            
            if file_path.stat().st_size == 0:
                self.logger.error(f"Audio file is empty: {file_path}")
                return False
            
            # Try to open as WAV file to validate structure
            try:
                with wave.open(str(file_path), 'rb') as wav_file:
                    frames = wav_file.getnframes()
                    if frames == 0:
                        self.logger.error(f"Audio file has no frames: {file_path}")
                        return False
            except wave.Error as e:
                self.logger.warning(f"Could not validate WAV structure: {e}")
                # File might be in different format, but exists and has content
            
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
            Duration in seconds, or 0.0 if cannot be determined
        """
        try:
            with wave.open(str(file_path), 'rb') as wav_file:
                frames = wav_file.getnframes()
                sample_rate = wav_file.getframerate()
                if sample_rate > 0:
                    return frames / sample_rate
        except Exception as e:
            self.logger.debug(f"Could not determine audio duration: {e}")
        
        return 0.0

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
                time.sleep(self.audio_settings.delay_between_requests)
            
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
        Test the connection to Gemini API.
        
        Returns:
            True if connection is working, False otherwise
        """
        try:
            # Simple test with minimal text
            test_text = "Testing connection."
            test_tone = "neutral"
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = Path(temp_file.name)
            
            result = self.generate_audio(test_text, test_tone, temp_path)
            
            # Clean up test file
            if temp_path.exists():
                temp_path.unlink()
            
            return result.success
            
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False
