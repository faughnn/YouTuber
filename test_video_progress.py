"""
Test script to verify the progress bar functionality in video downloads
"""
import sys
import os

# Add the parent directory to sys.path so we can import from Code
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from Extraction.youtube_video_downloader import download_video

def test_progress_bar():
    """Test the progress bar with a short video"""
    
    # Use a short test video (YouTube's test video)
    test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # "Me at the zoo" - first YouTube video, very short
    
    print("Testing video download with progress bar...")
    print(f"URL: {test_url}")
    print("="*50)
    
    try:
        result = download_video(test_url)
        print("="*50)
        print(f"Download result: {result}")
        
        if isinstance(result, str) and result.startswith("An error occurred"):
            print("❌ Test failed with error")
            return False
        else:
            print("✅ Test completed successfully")
            return True
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    print("Video Download Progress Bar Test")
    print("=" * 40)
    success = test_progress_bar()
    
    if success:
        print("\n🎉 Progress bar test completed!")
    else:
        print("\n💥 Progress bar test failed!")
        sys.exit(1)
