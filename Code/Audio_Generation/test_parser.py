"""
Test script for the JSON parser module.
This script tests parsing functionality with sample data.
"""

import json
import sys
from pathlib import Path

# Import from current directory
from json_parser import GeminiResponseParser, AudioSection
from config import AudioGenerationConfig

def test_sample_json():
    """Test with a sample JSON structure."""
    
    # Sample JSON matching the expected format
    sample_data = {
        "narrative_theme": "Fact-checking celebrity health claims",
        "podcast_sections": [
            {
                "section_type": "intro",
                "section_id": "intro_001",
                "script_content": "Welcome to Media Literacy Moments, where we fact-check the most interesting claims from popular podcasts. Today we're examining some health and wellness statements from Joe Rogan's conversation with Bono.",
                "estimated_duration": "30 seconds",
                "audio_tone": "enthusiastic, welcoming"
            },
            {
                "section_type": "pre_clip",
                "section_id": "pre_clip_001",
                "clip_reference": "segment_001",
                "script_content": "Let's start with an interesting claim about vitamin D and immune system benefits. Bono mentioned some specific health benefits that deserve closer examination.",
                "estimated_duration": "45 seconds",
                "audio_tone": "conversational, setting up intrigue"
            },
            {
                "section_type": "video_clip",
                "section_id": "video_clip_001",
                "clip_id": "segment_001",
                "start_time": "00:05:30",
                "end_time": "00:06:45",
                "title": "Bono discusses vitamin D benefits",
                "selection_reason": "Contains specific health claims about vitamin D supplementation",
                "severity_level": "MEDIUM",
                "key_claims": ["Vitamin D prevents all infections", "Everyone should take 5000 IU daily"],
                "estimated_duration": "75 seconds"
            },
            {
                "section_type": "post_clip",
                "section_id": "post_clip_001",
                "clip_reference": "segment_001",
                "script_content": "While vitamin D is indeed important for immune function, let's unpack these claims with actual research. The idea that vitamin D prevents 'all infections' is an oversimplification...",
                "estimated_duration": "2 minutes",
                "audio_tone": "analytical, fact-checking mode"
            },
            {
                "section_type": "outro",
                "section_id": "outro_001",
                "script_content": "Remember, celebrity endorsements don't equal medical advice. Always consult healthcare professionals for personalized recommendations. Thanks for joining Media Literacy Moments!",
                "estimated_duration": "30 seconds",
                "audio_tone": "thoughtful, educational wrap-up"
            }
        ],
        "script_metadata": {
            "total_estimated_duration": "6 minutes",
            "target_audience": "Health-conscious podcast listeners",
            "key_themes": ["vitamin supplementation", "celebrity health claims", "evidence-based medicine"],
            "total_clips_analyzed": 3
        }
    }
    
    print("Testing JSON Parser with sample data...")
    
    # Initialize parser
    parser = GeminiResponseParser()
    
    # Test validation
    print("\n1. Testing validation...")
    validation_result = parser.validate_podcast_sections(sample_data)
    
    print(f"Validation result: {'PASSED' if validation_result.is_valid else 'FAILED'}")
    print(f"Audio sections: {validation_result.audio_section_count}")
    print(f"Video sections: {validation_result.video_section_count}")
    
    if validation_result.errors:
        print("Errors:")
        for error in validation_result.errors:
            print(f"  - {error}")
    
    if validation_result.warnings:
        print("Warnings:")
        for warning in validation_result.warnings:
            print(f"  - {warning}")
    
    # Test audio section extraction
    print("\n2. Testing audio section extraction...")
    sections = sample_data['podcast_sections']
    audio_sections = parser.extract_audio_sections(sections)
    
    print(f"Extracted {len(audio_sections)} audio sections:")
    for section in audio_sections:
        print(f"  - {section.section_id} ({section.section_type}): '{section.script_content[:50]}...'")
        print(f"    Tone: {section.audio_tone}")
        print(f"    Duration: {section.estimated_duration}")
        if section.clip_reference:
            print(f"    Clip Reference: {section.clip_reference}")
        print()
    
    # Test episode metadata extraction
    print("3. Testing episode metadata extraction...")
    episode_info = parser.extract_episode_metadata(sample_data)
    print(f"Theme: {episode_info.narrative_theme}")
    print(f"Duration: {episode_info.total_estimated_duration}")
    print(f"Audience: {episode_info.target_audience}")
    print(f"Key themes: {episode_info.key_themes}")
    print(f"Clips analyzed: {episode_info.total_clips_analyzed}")

def test_config():
    """Test configuration loading."""
    print("\n" + "="*50)
    print("Testing Configuration Manager...")
    
    try:
        config = AudioGenerationConfig()
        
        print("\nConfiguration Summary:")
        summary = config.get_config_summary()
        
        for section, settings in summary.items():
            print(f"\n{section.upper()}:")
            if isinstance(settings, dict):
                for key, value in settings.items():
                    print(f"  {key}: {value}")
            else:
                print(f"  {settings}")
        
        # Test validation
        print("\nValidation:")
        validation = config.validate_configuration()
        print(f"Valid: {validation.is_valid}")
        
        if validation.errors:
            print("Errors:")
            for error in validation.errors:
                print(f"  - {error}")
        
        if validation.warnings:
            print("Warnings:")
            for warning in validation.warnings:
                print(f"  - {warning}")
                
    except Exception as e:
        print(f"Configuration test failed: {e}")

def test_invalid_json():
    """Test parser with invalid JSON structures."""
    print("\n" + "="*50)
    print("Testing Invalid JSON Handling...")
    
    parser = GeminiResponseParser()
    
    # Test cases
    test_cases = [
        {
            "name": "Missing podcast_sections",
            "data": {"narrative_theme": "test"}
        },
        {
            "name": "Empty podcast_sections",
            "data": {"podcast_sections": []}
        },
        {
            "name": "Invalid section_type",
            "data": {
                "podcast_sections": [{
                    "section_type": "invalid_type",
                    "section_id": "test_001"
                }]
            }
        },
        {
            "name": "Missing required fields",
            "data": {
                "podcast_sections": [{
                    "section_type": "intro",
                    "section_id": "intro_001"
                    # Missing script_content, audio_tone, estimated_duration
                }]
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")
        result = parser.validate_podcast_sections(test_case['data'])
        print(f"Valid: {result.is_valid}")
        if result.errors:
            print("Errors:")
            for error in result.errors[:3]:  # Show first 3 errors
                print(f"  - {error}")

if __name__ == "__main__":
    print("Audio Generation System - JSON Parser Test")
    print("=" * 50)
    
    try:
        test_sample_json()
        test_config()
        test_invalid_json()
        
        print("\n" + "="*50)
        print("All tests completed successfully!")
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
