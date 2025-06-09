"""
Test script for the Batch Processor module.
This script tests the full audio generation pipeline.
"""

import tempfile
from pathlib import Path

from json_parser import AudioSection, EpisodeInfo
from config import AudioGenerationConfig
from batch_processor import AudioBatchProcessor, ProcessingReport
from audio_file_manager import AudioFileManager, EpisodeMetadata

def test_batch_processor():
    """Test the batch processor with a complete pipeline."""
    print("Audio Generation System - Batch Processor Test")
    print("=" * 60)
    
    try:
        # Initialize batch processor
        print("Initializing Batch Processor...")
        processor = AudioBatchProcessor()
        
        # Validate environment
        print("\n1. Validating processing environment...")
        validation = processor.validate_processing_environment()
        print(f"Configuration valid: {'✓' if validation['config_valid'] else '✗'}")
        print(f"TTS connection: {'✓' if validation['tts_connection'] else '✗'}")
        print(f"Content root exists: {'✓' if validation['content_root_exists'] else '✗'}")
        print(f"Write permissions: {'✓' if validation['write_permissions'] else '✗'}")
        
        # Create test data
        print("\n2. Creating test audio sections...")
        test_sections = [
            AudioSection(
                section_id="intro_001",
                section_type="intro",
                script_content="Welcome to Media Literacy Moments! Today we're diving deep into some fascinating claims that need our attention.",
                audio_tone="enthusiastic, welcoming",
                estimated_duration="30 seconds"
            ),
            AudioSection(
                section_id="pre_clip_001",
                section_type="pre_clip",
                script_content="Let's examine this first claim about social media algorithms and their impact on political polarization.",
                audio_tone="conversational, setting up intrigue",
                estimated_duration="45 seconds",
                clip_reference="segment_001"
            ),
            AudioSection(
                section_id="post_clip_001",
                section_type="post_clip",
                script_content="While algorithms do contribute to filter bubbles, the relationship is more nuanced than this claim suggests. Research shows multiple factors at play including user behavior and content diversity.",
                audio_tone="analytical, fact-checking mode",
                estimated_duration="90 seconds",
                clip_reference="segment_001"
            ),
            AudioSection(
                section_id="outro_001",
                section_type="outro",
                script_content="Thanks for joining us on this fact-checking journey. Remember to always question, verify, and think critically about the information you encounter.",
                audio_tone="thoughtful, educational wrap-up",
                estimated_duration="25 seconds"
            )
        ]
        
        print(f"Created {len(test_sections)} test sections")
        
        # Test individual section processing
        print("\n3. Testing audio section processing...")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Process sections
            results = processor.process_audio_sections(test_sections, str(temp_path))
            
            print(f"\nProcessing results:")
            successful = sum(1 for r in results if r.success)
            print(f"• Total sections: {len(results)}")
            print(f"• Successful: {successful}")
            print(f"• Failed: {len(results) - successful}")
            
            # Display individual results
            for result in results:
                status = "✓" if result.success else "✗"
                print(f"  {status} {result.section_id} ({result.section_type})")
                if result.success:
                    print(f"    File: {Path(result.audio_file_path).name}")
                    print(f"    Size: {result.file_size} bytes")
                    print(f"    Duration: {result.audio_duration:.2f}s")
                    print(f"    Generation time: {result.generation_time:.2f}s")
                else:
                    print(f"    Error: {result.error_message}")
            
            # Test file manager functionality
            print("\n4. Testing file management...")
            file_manager = AudioFileManager()
            
            # Create episode metadata
            episode_metadata = EpisodeMetadata(
                episode_name="Test Episode",
                episode_path=str(temp_path),
                script_file="test_script.txt",
                total_sections=len(test_sections),
                audio_sections=len(test_sections),
                video_sections=0,
                generated_timestamp="2024-06-08 12:00:00"
            )
            
            # Save metadata
            metadata_file = file_manager.save_generation_metadata(
                results, episode_metadata, str(temp_path)
            )
            print(f"Metadata saved to: {Path(metadata_file).name}")
            
            # Test report generation
            print("\n5. Testing report generation...")
            report_data = processor.generate_processing_report(results)
            
            print(f"Report summary:")
            summary = report_data["summary"]
            print(f"• Total sections: {summary['total_sections']}")
            print(f"• Success rate: {summary['success_rate']:.1%}")
            print(f"• Average generation time: {summary['average_generation_time']:.2f}s")
            
            if report_data["failed_sections"]:
                print(f"• Failed sections: {len(report_data['failed_sections'])}")
                for failed in report_data["failed_sections"]:
                    print(f"  - {failed['section_id']}: {failed['error']}")
        
        print("\n6. Testing error handling...")
        
        # Test with invalid section
        invalid_section = AudioSection(
            section_id="",  # Invalid empty ID
            section_type="invalid_type",
            script_content="",  # Empty content
            audio_tone="",
            estimated_duration="unknown"
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            error_results = processor.process_audio_sections([invalid_section], str(temp_dir))
            
            if error_results and not error_results[0].success:
                print("✓ Error handling working correctly")
                print(f"  Error captured: {error_results[0].error_message[:50]}...")
            else:
                print("✗ Error handling may need improvement")
        
        print("\n" + "=" * 60)
        print("Batch Processor testing completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"Error during batch processor testing: {e}")
        import traceback
        traceback.print_exc()

def test_file_manager():
    """Test the file manager independently."""
    print("\nTesting Audio File Manager...")
    print("-" * 40)
    
    try:
        # Test directory operations
        file_manager = AudioFileManager()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Test episode structure creation
            print("1. Testing episode structure creation...")
            audio_dir = file_manager.create_episode_structure(str(temp_path))
            print(f"Audio directory created: {Path(audio_dir).name}")
            
            # Test path generation
            print("2. Testing path generation...")
            output_path = file_manager.get_audio_output_path(str(temp_path), "test_section_001")
            print(f"Generated path: {Path(output_path).name}")
            
            # Test validation
            print("3. Testing directory validation...")
            is_valid = file_manager.validate_output_directory(audio_dir)
            print(f"Directory validation: {'✓' if is_valid else '✗'}")
            
            print("File Manager tests completed!")
            
    except Exception as e:
        print(f"Error during file manager testing: {e}")

if __name__ == "__main__":
    test_batch_processor()
    test_file_manager()
