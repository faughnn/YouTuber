"""
Test script for the TTS Engine module.
This script tests TTS functionality with sample audio generation.
"""

import tempfile
from pathlib import Path

from .json_parser import AudioSection
from .config import AudioGenerationConfig
from .tts_engine import GeminiTTSEngine, TTSResult

def test_tts_engine():
    """Test the TTS engine with sample audio sections."""
    print("Testing TTS Engine...")
    
    try:
        # Initialize configuration
        config = AudioGenerationConfig()
        
        # Check if configuration is valid
        validation = config.validate_configuration()
        if not validation.is_valid:
            print("Configuration validation failed:")
            for error in validation.errors:
                print(f"  - {error}")
            return
        
        # Initialize TTS engine
        tts_engine = GeminiTTSEngine(config)
        
        print(f"TTS Engine initialized with voice: {tts_engine.gemini_config.voice_name}")
        
        # Test connection
        print("\n1. Testing API connection...")
        connection_ok = tts_engine.test_connection()
        print(f"Connection test: {'PASSED' if connection_ok else 'FAILED'}")
        
        if not connection_ok:
            print("Note: Using test audio generation mode")
        
        # Sample audio sections for testing
        test_sections = [
            AudioSection(
                section_id="intro_001",
                section_type="intro",
                script_content="Welcome to Media Literacy Moments! Today we're fact-checking some interesting health claims.",
                audio_tone="enthusiastic, welcoming",
                estimated_duration="30 seconds"
            ),
            AudioSection(
                section_id="pre_clip_001",
                section_type="pre_clip",
                script_content="Let's examine this claim about vitamin supplements and immune system benefits.",
                audio_tone="conversational, setting up intrigue",
                estimated_duration="45 seconds",
                clip_reference="segment_001"
            ),
            AudioSection(
                section_id="post_clip_001",
                section_type="post_clip",
                script_content="While vitamin D is important for immune function, the claim that it prevents all infections is an oversimplification. Research shows mixed results for supplementation benefits.",
                audio_tone="analytical, fact-checking mode",
                estimated_duration="2 minutes",
                clip_reference="segment_001"
            )
        ]
        
        print(f"\n2. Testing audio generation with {len(test_sections)} sections...")
        
        # Create temporary directory for test files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            for i, section in enumerate(test_sections):
                print(f"\nGenerating audio for section {i+1}: {section.section_id}")
                print(f"  Type: {section.section_type}")
                print(f"  Tone: {section.audio_tone}")
                print(f"  Text length: {len(section.script_content)} characters")
                
                # Generate output path
                output_path = temp_path / f"{section.section_id}.wav"
                
                # Generate audio
                result = tts_engine.generate_audio_with_retry(
                    text=section.script_content,
                    tone=section.audio_tone,
                    output_path=output_path
                )
                
                # Display results
                print(f"  Result: {'SUCCESS' if result.success else 'FAILED'}")
                
                if result.success:
                    print(f"  File: {result.output_path}")
                    print(f"  Size: {result.file_size} bytes")
                    print(f"  Duration: {result.audio_duration:.2f} seconds")
                    print(f"  Generation time: {result.generation_time:.2f} seconds")
                else:
                    print(f"  Error: {result.error_message}")
                
                print(f"  Text processed: {result.text_length} characters")
        
        print("\n3. Testing tone instruction formatting...")
        
        test_tones = [
            "enthusiastic, welcoming",
            "conversational, setting up intrigue", 
            "analytical, fact-checking mode",
            "thoughtful, educational wrap-up",
            "dramatic and intense",
            "casual friendly chat"
        ]
        
        test_text = "This is a test of tone formatting."
        
        for tone in test_tones:
            formatted = tts_engine._format_tone_instruction(tone, test_text)
            print(f"  Tone: '{tone}'")
            print(f"  Formatted: '{formatted.split()[0:8]}...'")  # Show first few words
            print()
        
        print("4. Testing error handling...")
        
        # Test with empty text
        result = tts_engine.generate_audio("", "neutral", temp_path / "empty_test.wav")
        print(f"Empty text test: {'PASSED' if not result.success else 'FAILED'}")
        
        # Test with very long text
        long_text = "This is a test. " * 500  # Exceeds max length
        result = tts_engine.generate_audio(long_text, "neutral", temp_path / "long_test.wav")
        print(f"Long text test: {'PASSED' if not result.success else 'FAILED'}")
        
        print("\nTTS Engine testing completed!")
        
    except Exception as e:
        print(f"TTS Engine test failed: {e}")
        import traceback
        traceback.print_exc()

def test_tone_templates():
    """Test tone template selection and formatting."""
    print("\n" + "="*50)
    print("Testing Tone Template Selection...")
    
    config = AudioGenerationConfig()
    tts_engine = GeminiTTSEngine(config)
    
    test_cases = [
        ("enthusiastic, welcoming", "conversational"),
        ("analytical, fact-checking mode", "analytical"),
        ("dramatic and intense", "dramatic"),
        ("educational approach", "educational"),
        ("neutral tone", "default"),
        ("friendly chat style", "conversational"),
        ("examining the evidence", "analytical"),
        ("teaching moment", "educational")
    ]
    
    test_text = "This is a sample text for tone testing."
    
    for tone, expected_category in test_cases:
        formatted = tts_engine._format_tone_instruction(tone, test_text)
        
        # Check if the expected template type was used
        template_used = "unknown"
        if "conversational" in formatted.lower():
            template_used = "conversational"
        elif "analytical" in formatted.lower():
            template_used = "analytical"
        elif "dramatic" in formatted.lower():
            template_used = "dramatic"
        elif "educational" in formatted.lower():
            template_used = "educational"
        else:
            template_used = "default"
        
        match = "✓" if template_used == expected_category else "✗"
        
        print(f"{match} Tone: '{tone}' -> {template_used} (expected: {expected_category})")

if __name__ == "__main__":
    print("Audio Generation System - TTS Engine Test")
    print("=" * 50)
    
    test_tts_engine()
    test_tone_templates()
    
    print("\n" + "="*50)
    print("All TTS tests completed!")
