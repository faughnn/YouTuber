"""
Unit Tests for ChatterboxResponseParser

Tests JSON parsing functionality with real pipeline data, validation,
and audio section extraction for TTS processing.
"""

import unittest
import json
import tempfile
import os
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from json_parser import (
    ChatterboxResponseParser,
    AudioSection,
    EpisodeInfo,
    ValidationResult
)


class TestChatterboxResponseParser(unittest.TestCase):
    """Test suite for ChatterboxResponseParser functionality."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.parser = ChatterboxResponseParser()
        self.temp_dir = tempfile.mkdtemp()
        
        # Create sample test data
        self.sample_episode_data = {
            "episode_info": {
                "narrative_theme": "Technology and Innovation Discussion",
                "total_estimated_duration": "42 minutes",
                "target_audience": "Technology enthusiasts and entrepreneurs",
                "key_themes": ["AI development", "Future technology", "Innovation"],
                "total_clips_analyzed": 8,
                "source_file": "test_episode.json"
            },
            "podcast_sections": [
                {
                    "section_id": "intro_001",
                    "section_type": "intro",
                    "script_content": "Welcome to today's podcast discussing the future of artificial intelligence.",
                    "estimated_duration": "30 seconds"
                },
                {
                    "section_id": "pre_clip_001", 
                    "section_type": "pre_clip",
                    "script_content": "Before we dive into this fascinating clip about AI development, let me set the context.",
                    "estimated_duration": "45 seconds",
                    "clip_reference": "clip_001"
                },
                {
                    "section_id": "video_clip_001",
                    "section_type": "video_clip",
                    "clip_id": "clip_001",
                    "start_time": "00:05:30",
                    "end_time": "00:08:15",
                    "title": "AI Development Discussion",
                    "estimated_duration": "2 minutes 45 seconds",
                    "selection_reason": "Key insights about AI development",
                    "severity_level": "medium",
                    "key_claims": ["AI will transform industries", "Current limitations exist"]
                },
                {
                    "section_id": "post_clip_001",
                    "section_type": "post_clip", 
                    "script_content": "That was an incredible insight into how AI development is progressing.",
                    "estimated_duration": "35 seconds",
                    "clip_reference": "clip_001"
                },
                {
                    "section_id": "outro_001",
                    "section_type": "outro",
                    "script_content": "Thank you for listening to today's episode. Join us next time for more technology discussions.",
                    "estimated_duration": "40 seconds"
                }
            ]
        }
        
    def tearDown(self):
        """Clean up after each test method."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_parser_initialization(self):
        """Test parser initialization and section type definitions."""
        parser = ChatterboxResponseParser()
        
        # Check section types are properly defined
        self.assertIn('intro', parser.audio_section_types)
        self.assertIn('pre_clip', parser.audio_section_types)
        self.assertIn('post_clip', parser.audio_section_types)
        self.assertIn('outro', parser.audio_section_types)
        self.assertIn('video_clip', parser.video_section_types)
        
        # Check required fields
        self.assertIn('script_content', parser.audio_required_fields)
        self.assertIn('section_type', parser.audio_required_fields)
        self.assertIn('section_id', parser.audio_required_fields)
        
        print("✓ Parser initialization successful with proper section definitions")
    
    def test_json_data_validation(self):
        """Test JSON data structure validation."""
        # Test valid data
        validation_result = self.parser.validate_podcast_sections(self.sample_episode_data)
        
        self.assertIsInstance(validation_result, ValidationResult)
        self.assertTrue(validation_result.is_valid)
        self.assertEqual(len(validation_result.errors), 0)
        self.assertEqual(validation_result.audio_section_count, 4)  # intro, pre_clip, post_clip, outro
        self.assertEqual(validation_result.video_section_count, 1)  # video_clip
        
        print(f"✓ Validation successful: {validation_result.audio_section_count} audio sections, {validation_result.video_section_count} video sections")
    
    def test_episode_info_extraction(self):
        """Test episode information extraction."""
        validation_result = self.parser.validate_podcast_sections(self.sample_episode_data)
        
        self.assertIsNotNone(validation_result.episode_info)
        episode_info = validation_result.episode_info
        
        self.assertEqual(episode_info.narrative_theme, "Technology and Innovation Discussion")
        self.assertEqual(episode_info.total_estimated_duration, "42 minutes")
        self.assertEqual(episode_info.total_clips_analyzed, 8)
        self.assertIn("AI development", episode_info.key_themes)
        
        print(f"✓ Episode info extracted: {episode_info.narrative_theme}")
        print(f"  Duration: {episode_info.total_estimated_duration}")
        print(f"  Clips: {episode_info.total_clips_analyzed}")
    
    def test_audio_section_extraction(self):
        """Test audio section extraction for TTS processing."""
        audio_sections = self.parser.extract_audio_sections(self.sample_episode_data)
        
        self.assertEqual(len(audio_sections), 4)
        
        # Test specific audio sections
        intro_section = next((s for s in audio_sections if s.section_type == 'intro'), None)
        self.assertIsNotNone(intro_section)
        self.assertEqual(intro_section.section_id, 'intro_001')
        self.assertIn('Welcome to today\'s podcast', intro_section.script_content)
        
        # Test pre_clip section with clip reference
        pre_clip_section = next((s for s in audio_sections if s.section_type == 'pre_clip'), None)
        self.assertIsNotNone(pre_clip_section)
        self.assertEqual(pre_clip_section.clip_reference, 'clip_001')
        
        print("✓ Audio section extraction successful")
        for section in audio_sections:
            print(f"  {section.section_type}: {section.section_id} ({section.estimated_duration})")
    
    def test_file_parsing(self):
        """Test parsing from actual JSON files."""
        # Create test file
        test_file_path = os.path.join(self.temp_dir, "test_script.json")
        with open(test_file_path, 'w', encoding='utf-8') as f:
            json.dump(self.sample_episode_data, f, indent=2)
        
        # Test file parsing
        parsed_data = self.parser.parse_response_file(test_file_path)
        self.assertIsInstance(parsed_data, dict)
        self.assertIn('podcast_sections', parsed_data)
        self.assertIn('episode_info', parsed_data)
        
        print(f"✓ File parsing successful: {test_file_path}")
    
    def test_real_pipeline_data(self):
        """Test with real pipeline data from Content directory."""
        # Look for real unified_podcast_script.json files
        content_dir = Path(__file__).parent.parent.parent / "Content"
        
        real_script_files = []
        if content_dir.exists():
            # Search for unified_podcast_script.json files
            for episode_dir in content_dir.rglob("*/Output/Scripts/unified_podcast_script.json"):
                if episode_dir.exists():
                    real_script_files.append(episode_dir)
        
        if real_script_files:
            print(f"✓ Found {len(real_script_files)} real script files to test")
            
            for script_file in real_script_files[:2]:  # Test first 2 files
                try:
                    print(f"  Testing: {script_file}")
                    
                    # Parse real file
                    parsed_data = self.parser.parse_response_file(script_file)
                    validation_result = self.parser.validate_podcast_sections(parsed_data)
                    
                    print(f"    Valid: {validation_result.is_valid}")
                    print(f"    Audio sections: {validation_result.audio_section_count}")
                    print(f"    Video sections: {validation_result.video_section_count}")
                    print(f"    Errors: {len(validation_result.errors)}")
                    
                    if validation_result.errors:
                        for error in validation_result.errors[:3]:  # Show first 3 errors
                            print(f"      ERROR: {error}")
                    
                    # Test audio section extraction
                    if validation_result.is_valid:
                        audio_sections = self.parser.extract_audio_sections(parsed_data)
                        print(f"    Extracted {len(audio_sections)} audio sections for TTS")
                    
                except Exception as e:
                    print(f"    ERROR parsing {script_file}: {type(e).__name__}: {e}")
        else:
            print("! No real script files found for testing")
    
    def test_malformed_json_handling(self):
        """Test handling of malformed JSON data."""
        # Test missing required fields
        malformed_data = {
            "episode_info": {
                "narrative_theme": "Test Theme"
                # Missing other required fields
            },
            "podcast_sections": [
                {
                    "section_id": "test_001",
                    "section_type": "intro"
                    # Missing script_content and estimated_duration
                }
            ]
        }
        
        validation_result = self.parser.validate_podcast_sections(malformed_data)
        
        self.assertFalse(validation_result.is_valid)
        self.assertGreater(len(validation_result.errors), 0)
        
        print(f"✓ Malformed JSON handling: {len(validation_result.errors)} errors detected")
        for error in validation_result.errors[:3]:
            print(f"  ERROR: {error}")
    
    def test_empty_data_handling(self):
        """Test handling of empty or missing data."""
        # Test empty sections
        empty_data = {
            "episode_info": {
                "narrative_theme": "Empty Test",
                "total_estimated_duration": "0 minutes",
                "target_audience": "Test",
                "key_themes": [],
                "total_clips_analyzed": 0,
                "source_file": "empty_test.json"
            },
            "podcast_sections": []
        }
        
        validation_result = self.parser.validate_podcast_sections(empty_data)
        
        # Should be valid but have zero sections
        self.assertTrue(validation_result.is_valid)
        self.assertEqual(validation_result.audio_section_count, 0)
        self.assertEqual(validation_result.video_section_count, 0)
        
        print("✓ Empty data handling: validation passed with 0 sections")
    
    def test_audio_section_dataclass(self):
        """Test AudioSection dataclass functionality."""
        # Test AudioSection creation
        section = AudioSection(
            section_id="test_section_001",
            section_type="intro",
            script_content="This is a test introduction.",
            estimated_duration="30 seconds"
        )
        
        self.assertEqual(section.section_id, "test_section_001")
        self.assertEqual(section.section_type, "intro")
        self.assertEqual(section.script_content, "This is a test introduction.")
        self.assertEqual(section.estimated_duration, "30 seconds")
        self.assertIsNone(section.clip_reference)  # Default value
        
        # Test with clip reference
        clip_section = AudioSection(
            section_id="pre_clip_001",
            section_type="pre_clip",
            script_content="Before the clip...",
            estimated_duration="45 seconds",
            clip_reference="clip_001"
        )
        
        self.assertEqual(clip_section.clip_reference, "clip_001")
        
        print("✓ AudioSection dataclass functionality verified")
    
    def test_section_type_validation(self):
        """Test section type validation."""
        # Test valid audio section types
        for section_type in ['intro', 'pre_clip', 'post_clip', 'outro']:
            test_data = {
                "episode_info": self.sample_episode_data["episode_info"],
                "podcast_sections": [
                    {
                        "section_id": f"test_{section_type}",
                        "section_type": section_type,
                        "script_content": f"Test {section_type} content",
                        "estimated_duration": "30 seconds"
                    }
                ]
            }
            
            validation_result = self.parser.validate_podcast_sections(test_data)
            self.assertTrue(validation_result.is_valid)
        
        # Test invalid section type
        invalid_data = {
            "episode_info": self.sample_episode_data["episode_info"],
            "podcast_sections": [
                {
                    "section_id": "invalid_001",
                    "section_type": "invalid_type",
                    "script_content": "Invalid section",
                    "estimated_duration": "30 seconds"
                }
            ]
        }
        
        validation_result = self.parser.validate_podcast_sections(invalid_data)
        self.assertFalse(validation_result.is_valid)
        
        print("✓ Section type validation working correctly")


class TestParserIntegration(unittest.TestCase):
    """Integration tests for parser with other components."""
    
    def test_simplified_structure_compatibility(self):
        """Test that simplified AudioSection structure is compatible with pipeline."""
        parser = ChatterboxResponseParser()
        
        # Create sample data
        sample_data = {
            "episode_info": {
                "narrative_theme": "Integration Test",
                "total_estimated_duration": "10 minutes",
                "target_audience": "Developers",
                "key_themes": ["Testing", "Integration"],
                "total_clips_analyzed": 1,
                "source_file": "integration_test.json"
            },
            "podcast_sections": [
                {
                    "section_id": "intro_001",
                    "section_type": "intro",
                    "script_content": "Welcome to the integration test episode.",
                    "estimated_duration": "20 seconds"
                }
            ]
        }
        
        # Parse and extract audio sections
        validation_result = parser.validate_podcast_sections(sample_data)
        self.assertTrue(validation_result.is_valid)
        
        audio_sections = parser.extract_audio_sections(sample_data)
        self.assertEqual(len(audio_sections), 1)
        
        # Verify simplified structure (no audio_tone field)
        section = audio_sections[0]
        self.assertFalse(hasattr(section, 'audio_tone'))
        
        print("✓ Simplified AudioSection structure confirmed (no audio_tone field)")
        print("✓ Compatible with Chatterbox fixed-parameter approach")


if __name__ == '__main__':
    print("=" * 60)
    print("CHATTERBOX JSON PARSER UNIT TESTS")
    print("=" * 60)
    
    # Run tests with detailed output
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "=" * 60)
    print("JSON PARSER UNIT TESTS COMPLETED")
    print("=" * 60)
