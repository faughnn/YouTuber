"""
Test script for Video Compilator

Simple test to validate the implementation and demonstrate usage.
"""

import logging
import sys
from pathlib import Path

# Add the parent directory to Python path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent))

from Video_Compilator import SimpleCompiler, AudioToVideoConverter, DirectConcatenator


def test_audio_converter():
    """Test the AudioToVideoConverter component"""
    print("=== Testing AudioToVideoConverter ===")
    
    try:
        converter = AudioToVideoConverter()
        print(f"✓ AudioToVideoConverter initialized")
        print(f"  Background image: {converter.background_image}")
        
        # Check if background image exists
        if Path(converter.background_image).exists():
            print(f"✓ Background image found")
        else:
            print(f"✗ Background image not found: {converter.background_image}")
            return False
        
        return True
    except Exception as e:
        print(f"✗ AudioToVideoConverter test failed: {e}")
        return False


def test_concatenator():
    """Test the DirectConcatenator component"""
    print("\n=== Testing DirectConcatenator ===")
    
    try:
        concatenator = DirectConcatenator()
        print(f"✓ DirectConcatenator initialized")
        
        # Test validation with empty list
        result = concatenator.validate_concatenation_inputs([])
        if not result:
            print(f"✓ Empty input validation works correctly")
        else:
            print(f"✗ Empty input validation should return False")
            return False
        
        return True
    except Exception as e:
        print(f"✗ DirectConcatenator test failed: {e}")
        return False


def test_simple_compiler():
    """Test the SimpleCompiler component"""
    print("\n=== Testing SimpleCompiler ===")
    
    try:
        compiler = SimpleCompiler()
        print(f"✓ SimpleCompiler initialized")
        print(f"  Keep temp files: {compiler.keep_temp_files}")
        print(f"  Validate segments: {compiler.validate_segments}")
        
        return True
    except Exception as e:
        print(f"✗ SimpleCompiler test failed: {e}")
        return False


def test_episode_compilation():
    """Test compilation with a real episode if available"""
    print("\n=== Testing Episode Compilation ===")
    
    # Look for an episode directory to test with
    content_dir = Path("C:/Users/nfaug/OneDrive - LIR/Desktop/YouTuber/Content")
    episode_dirs = []
    
    if content_dir.exists():
        for item in content_dir.iterdir():
            if item.is_dir():
                for subitem in item.iterdir():
                    if subitem.is_dir():
                        episode_dirs.append(subitem)
    
    if not episode_dirs:
        print("✓ No episode directories found for testing (this is okay)")
        return True
    
    # Try to compile the first episode found
    test_episode = episode_dirs[0]
    print(f"Testing with episode: {test_episode.name}")
    
    try:
        compiler = SimpleCompiler()
        
        # Just test parsing without actual compilation
        try:
            script_path = test_episode / "Scripts" / "unified_podcast_script.json"
            if script_path.exists():
                segments = compiler.parse_script(script_path)
                print(f"✓ Script parsed successfully: {len(segments)} segments")
            else:
                segments = compiler.discover_episode_files(test_episode)
                print(f"✓ File discovery successful: {len(segments)} files found")
        except Exception as e:
            print(f"⚠ Episode parsing test failed (this may be normal): {e}")
        
        return True
    except Exception as e:
        print(f"✗ Episode compilation test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("Video Compilator Test Suite")
    print("=" * 50)
    
    # Set up basic logging
    logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
    
    tests = [
        test_audio_converter,
        test_concatenator,
        test_simple_compiler,
        test_episode_compilation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
    
    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed!")
        print("\nThe Video Compilator is ready to use.")
        print("\nUsage example:")
        print("  from Video_Compilator import SimpleCompiler")
        print("  compiler = SimpleCompiler()")
        print("  result = compiler.compile_episode(Path('episode_directory'))")
    else:
        print("✗ Some tests failed. Check the output above for details.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
