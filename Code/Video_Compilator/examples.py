"""
Video Compilator Usage Examples

This script demonstrates how to use the Video Compilator system
to compile podcast episodes using the proven working method.
"""

import logging
import sys
from pathlib import Path

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from Video_Compilator import SimpleCompiler, AudioToVideoConverter, DirectConcatenator


def example_basic_compilation():
    """Basic example of compiling an episode"""
    print("=== Basic Episode Compilation ===")
    
    # Initialize the compiler
    compiler = SimpleCompiler(
        keep_temp_files=True,    # Keep temp files for debugging
        validate_segments=True   # Validate segments before concatenation
    )
    
    # Path to the episode directory
    episode_path = Path("C:/Users/nfaug/OneDrive - LIR/Desktop/YouTuber/Content/Joe_Rogan_Experience/Joe Rogan Experience #2330 - Bono")
    
    if episode_path.exists():
        print(f"Compiling episode: {episode_path.name}")
        
        # Compile the episode
        result = compiler.compile_episode(episode_path)
        
        if result.success:
            print(f"✓ Compilation successful!")
            print(f"  Output: {result.output_path}")
            print(f"  Duration: {result.duration:.2f}s" if result.duration else "  Duration: Unknown")
            print(f"  File size: {result.file_size/1024/1024:.1f}MB" if result.file_size else "  File size: Unknown")
            print(f"  Segments processed: {result.segments_processed}")
            print(f"  Audio segments converted: {result.audio_segments_converted}")
        else:
            print(f"✗ Compilation failed: {result.error}")
    else:
        print(f"Episode directory not found: {episode_path}")


def example_audio_conversion_only():
    """Example of converting just audio files to video"""
    print("\n=== Audio to Video Conversion Only ===")
    
    # Initialize the audio converter
    converter = AudioToVideoConverter()
    
    # Example audio file (if it exists)
    episode_path = Path("C:/Users/nfaug/OneDrive - LIR/Desktop/YouTuber/Content/Joe_Rogan_Experience/Joe Rogan Experience #2330 - Bono")
    audio_dir = episode_path / "Output" / "Audio"
    
    if not audio_dir.exists():
        audio_dir = episode_path / "Audio"
    
    if audio_dir.exists():
        audio_files = list(audio_dir.glob("*.wav"))
        if audio_files:
            audio_file = audio_files[0]  # Use the first audio file
            output_file = audio_file.with_suffix('.mp4')
            
            print(f"Converting: {audio_file.name}")
            success = converter.convert_audio_segment(audio_file, output_file)
            
            if success:
                print(f"✓ Successfully converted to: {output_file}")
            else:
                print(f"✗ Failed to convert: {audio_file.name}")
        else:
            print("No audio files found to convert")
    else:
        print(f"Audio directory not found: {audio_dir}")


def example_direct_concatenation():
    """Example of directly concatenating video files"""
    print("\n=== Direct Video Concatenation ===")
    
    # Initialize the concatenator
    concatenator = DirectConcatenator()
    
    # Example: Create some test segments (this is just for demonstration)
    episode_path = Path("C:/Users/nfaug/OneDrive - LIR/Desktop/YouTuber/Content/Joe_Rogan_Experience/Joe Rogan Experience #2330 - Bono")
    
    # Look for video files
    video_files = []
    for video_dir in [episode_path / "Output" / "Video", episode_path / "Video"]:
        if video_dir.exists():
            video_files.extend(list(video_dir.glob("*.mp4")))
    
    if len(video_files) >= 2:
        # Take first two video files for demonstration
        segments = video_files[:2]
        output_path = episode_path / "test_concatenated.mp4"
        
        print(f"Concatenating {len(segments)} video segments:")
        for i, segment in enumerate(segments, 1):
            print(f"  {i}: {segment.name}")
        
        # Validate inputs
        if concatenator.validate_concatenation_inputs(segments):
            result = concatenator.concatenate_mixed_segments(segments, output_path)
            
            if result.success:
                print(f"✓ Concatenation successful: {result.output_path}")
                print(f"  Duration: {result.duration:.2f}s" if result.duration else "  Duration: Unknown")
            else:
                print(f"✗ Concatenation failed: {result.error}")
        else:
            print("✗ Input validation failed")
    else:
        print("Need at least 2 video files for concatenation demo")


def example_with_custom_settings():
    """Example with custom compiler settings"""
    print("\n=== Compilation with Custom Settings ===")
    
    # Custom compiler settings
    compiler = SimpleCompiler(
        keep_temp_files=False,    # Don't keep temp files (cleanup after)
        validate_segments=True    # Still validate for safety
    )
    
    episode_path = Path("C:/Users/nfaug/OneDrive - LIR/Desktop/YouTuber/Content/Joe_Rogan_Experience/Joe Rogan Experience #2330 - Bono")
    
    if episode_path.exists():
        # Custom output filename
        custom_output = "Joe_Rogan_2330_Bono_CUSTOM.mp4"
        
        print(f"Compiling with custom output name: {custom_output}")
        result = compiler.compile_episode(episode_path, custom_output)
        
        if result.success:
            print(f"✓ Custom compilation successful: {result.output_path}")
        else:
            print(f"✗ Custom compilation failed: {result.error}")
    else:
        print("Episode directory not found for custom compilation")


def main():
    """Run all examples"""
    print("Video Compilator Usage Examples")
    print("=" * 50)
    
    # Set up logging to see what's happening
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    
    # Run examples
    try:
        example_basic_compilation()
        example_audio_conversion_only()
        example_direct_concatenation()
        example_with_custom_settings()
    except KeyboardInterrupt:
        print("\n✗ Examples interrupted by user")
    except Exception as e:
        print(f"\n✗ Example failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("Examples complete!")
    print("\nFor more advanced usage, see:")
    print("  - README.md for documentation")
    print("  - cli.py for command-line usage")
    print("  - test_video_compilator.py for testing")


if __name__ == "__main__":
    main()
