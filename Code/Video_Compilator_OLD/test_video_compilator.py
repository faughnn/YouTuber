"""
Test script for Video Compilator

Quick test to verify the Video Compilator implementation.
"""
import sys
from pathlib import Path

# Add the Code directory to the path so we can import Video_Compilator
sys.path.append(str(Path(__file__).parent.parent))

from Video_Compilator import VideoCompilator, compile_episode

def test_video_compilator():
    """Test the Video Compilator with the existing episode"""
    
    # Path to the test episode
    episode_path = r"C:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Content\Joe_Rogan_Experience\Joe Rogan Experience #2330 - Bono"
    
    print("=== Video Compilator Test ===")
    print(f"Episode: {Path(episode_path).name}")
    print()
    
    # Test using the convenience function
    print("Starting compilation...")
    result = compile_episode(episode_path)
    
    print(f"\nCompilation Result:")
    print(f"Success: {result.success}")
    print(f"Execution Time: {result.execution_time:.2f}s")
    
    if result.success:
        print(f"Output Path: {result.output_path}")
        print(f"File Size: {result.stats['compilation']['output_size_mb']:.1f} MB")
        print(f"Total Segments: {result.stats['episode_info']['total_segments']}")
        print(f"Narration Videos Created: {result.stats['assets']['narration_videos_created']}")
    else:
        print(f"Error: {result.error_message}")
    
    return result.success

def test_components_individually():
    """Test individual components"""
    
    print("\n=== Component Tests ===")
    
    # Test script parser
    from Video_Compilator.script_parser import ScriptParser
    
    script_path = Path(r"C:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Content\Joe_Rogan_Experience\Joe Rogan Experience #2330 - Bono\Output\Scripts\unified_podcast_script.json")
    
    parser = ScriptParser()
    try:
        script_data = parser.parse_script(script_path)
        sections = parser.get_section_sequence()
        print(f"✓ Script Parser: Found {len(sections)} sections")
    except Exception as e:
        print(f"✗ Script Parser: {e}")
        return False
    
    # Test asset validator
    from Video_Compilator.asset_validator import AssetValidator
    
    validator = AssetValidator()
    audio_dir = script_path.parent.parent / "Audio"
    video_dir = script_path.parent.parent / "Video"
    
    paths = {
        'script_path': script_path,
        'audio_dir': audio_dir,
        'video_dir': video_dir
    }
    
    validation_result = validator.validate_all_assets(script_data, paths)
    if validation_result.is_valid:
        print("✓ Asset Validator: All assets valid")
    else:
        print(f"⚠ Asset Validator: {validation_result.error_message}")
    
    # Test background processor setup
    from Video_Compilator.background_processor import BackgroundProcessor
    
    processor = BackgroundProcessor()
    if processor.validate_background_setup():
        print("✓ Background Processor: Setup valid")
    else:
        print("✗ Background Processor: Setup failed")
        
    # Test FFmpeg orchestrator
    from Video_Compilator.ffmpeg_orchestrator import FFmpegOrchestrator
    
    orchestrator = FFmpegOrchestrator()
    if orchestrator.test_ffmpeg_availability():
        print("✓ FFmpeg Orchestrator: FFmpeg available")
    else:
        print("✗ FFmpeg Orchestrator: FFmpeg not available")
        
    return True

if __name__ == "__main__":
    print("Testing Video Compilator Implementation...")
    
    # Test components first
    if test_components_individually():
        print("\n" + "="*50)
        # Run full compilation test
        success = test_video_compilator()
        
        if success:
            print("\n🎉 All tests passed! Video Compilator is working correctly.")
        else:
            print("\n❌ Compilation test failed. Check the error messages above.")
    else:
        print("\n❌ Component tests failed. Fix issues before running compilation.")
