#!/usr/bin/env python3
"""
Test TTS Integration Workflow
Demonstrates the complete pipeline from analysis to TTS-ready script to audio generation.
"""

import json
import logging
from pathlib import Path
import sys

# Add necessary paths
sys.path.append(str(Path(__file__).parent / "Content_Analysis"))
sys.path.append(str(Path(__file__).parent / "TTS"))

from Content_Analysis.podcast_narrative_generator import PodcastNarrativeGenerator
from TTS.podcast_tts_processor import PodcastTTSProcessor

def test_complete_tts_workflow():
    """Test the complete workflow from analysis to TTS audio"""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    logger.info("Starting TTS workflow test...")
    
    # Test data paths
    analysis_path = "Transcripts/Joe_Rogan_Experience/Joe Rogan Experience 2325 - Aaron Rodgers/Joe Rogan Experience 2325 - Aaron Rodgers_analysis_analysis.json"
    episode_title = "Joe Rogan Experience 2325 - Aaron Rodgers"
    
    if not Path(analysis_path).exists():
        logger.error(f"Analysis file not found: {analysis_path}")
        logger.info("Please ensure you have an analysis file to test with")
        return False
    
    try:
        # Step 1: Generate TTS-ready script
        logger.info("=== STEP 1: Generating TTS-ready script ===")
        generator = PodcastNarrativeGenerator()
        
        tts_script = generator.generate_tts_ready_script(
            analysis_json_path=analysis_path,
            episode_title=episode_title,
            episode_number="001",
            initials="AR",
            prompt_template="tts_podcast_narrative_prompt.txt"
        )
          # Save TTS script - create test episode structure
        test_episode_dir = Path("Content/Test_Series/Test_Episode_001")
        test_episode_dir.mkdir(parents=True, exist_ok=True)
        
        # Create the Output/Scripts folder structure
        scripts_output_dir = test_episode_dir / "Output" / "Scripts" 
        scripts_output_dir.mkdir(parents=True, exist_ok=True)
        
        script_output_path = scripts_output_dir / "test_tts_ready_script.json"
        
        saved_script_path = generator.save_tts_ready_script(tts_script, str(script_output_path))
        logger.info(f"✓ TTS script saved: {saved_script_path}")
        
        # Step 2: Validate TTS script
        logger.info("=== STEP 2: Validating TTS script ===")
        processor = PodcastTTSProcessor()
        
        validation = processor.validate_tts_script(str(saved_script_path))
        logger.info(f"Script validation: {'✓ VALID' if validation['valid'] else '✗ INVALID'}")
        logger.info(f"Estimated audio files: {validation['estimated_files']}")
        logger.info(f"Clip segments: {validation['segment_count']}")
        
        if validation['warnings']:
            logger.warning("Validation warnings:")
            for warning in validation['warnings']:
                logger.warning(f"  ⚠️ {warning}")
        
        if validation['errors']:
            logger.error("Validation errors:")
            for error in validation['errors']:
                logger.error(f"  ❌ {error}")
            return False
        
        # Step 3: Generate TTS audio files  
        logger.info("=== STEP 3: Generating TTS audio files ===")
          # Setup audio output directory - use new structure
        audio_output_dir = test_episode_dir / "Output" / "Audio"
        audio_output_dir.mkdir(parents=True, exist_ok=True)
        
        results = processor.generate_podcast_audio(
            tts_script_path=str(saved_script_path),
            output_directory=str(audio_output_dir)
        )
        
        # Report results
        logger.info("=== GENERATION RESULTS ===")
        logger.info(f"Episode: {results['episode_info']['title']}")
        logger.info(f"Total segments: {results['total_segments']}")
        logger.info(f"Successful: {results['successful_segments']}")
        logger.info(f"Failed: {len(results['failed_files'])}")
        logger.info(f"Success rate: {results['successful_segments']/results['total_segments']:.1%}")
        
        if results["generated_files"]:
            logger.info("\nGenerated audio files:")
            for file_info in results["generated_files"]:
                logger.info(f"  ✓ {file_info['filename']} ({file_info['voice_style']}, ~{file_info['estimated_duration']})")
        
        if results["failed_files"]:
            logger.warning("\nFailed audio files:")
            for file_info in results["failed_files"]:
                logger.warning(f"  ✗ {file_info['filename']}: {file_info['error']}")
        
        # Step 4: Display next steps
        logger.info("=== NEXT STEPS ===")
        logger.info("1. Review generated audio files for quality")
        logger.info("2. Use analysis_video_clipper.py to extract video clips")
        logger.info("3. Use Video_Editor system to combine audio + video")
        
        logger.info(f"\n🎵 Audio files location: {audio_output_dir}")
        logger.info(f"📄 TTS script location: {saved_script_path}")
        logger.info(f"📊 Generation report: {audio_output_dir}/tts_generation_report.json")
        
        return results['successful_segments'] == results['total_segments']
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def demo_ideal_format():
    """Demonstrate the ideal TTS format structure"""
    
    logger = logging.getLogger(__name__)
    
    # Load and display the ideal format example
    example_path = Path("Code/TTS/examples/ideal_podcast_format.json")
    
    if example_path.exists():
        logger.info("=== IDEAL TTS FORMAT STRUCTURE ===")
        with open(example_path, 'r', encoding='utf-8') as f:
            ideal_format = json.load(f)
        
        print(json.dumps(ideal_format, indent=2))
        
        logger.info(f"\n📋 Ideal format example: {example_path}")
        logger.info("This shows the target structure for TTS-ready scripts")
    else:
        logger.warning(f"Ideal format example not found: {example_path}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test TTS integration workflow")
    parser.add_argument("--demo-format", action="store_true", help="Show ideal format structure")
    parser.add_argument("--full-test", action="store_true", help="Run complete workflow test")
    
    args = parser.parse_args()
    
    if args.demo_format:
        demo_ideal_format()
    elif args.full_test:
        success = test_complete_tts_workflow()
        exit(0 if success else 1)
    else:
        print("Usage: python test_tts_workflow.py [--demo-format | --full-test]")
        print("")
        print("Options:")
        print("  --demo-format    Show the ideal TTS script format structure")
        print("  --full-test      Run complete workflow test (requires analysis file)")
        print("")
        print("The full test demonstrates:")
        print("1. Generating TTS-ready script from analysis data")
        print("2. Validating script structure")
        print("3. Generating organized audio files")
        print("4. Reporting results and next steps")
