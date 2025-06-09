"""
Test script to validate the file organization functionality
without making API calls.
"""

import sys
import os

# Add path for file organizer
current_dir = os.path.dirname(os.path.abspath(__file__))
utils_dir = os.path.join(current_dir, '..', 'Utils')
sys.path.append(utils_dir)

try:
    from file_organizer import FileOrganizer
    print("✅ FileOrganizer import successful")
except ImportError as e:
    print(f"❌ FileOrganizer import failed: {e}")
    sys.exit(1)

def test_file_organization():
    """Test the file organization functionality."""
    
    # Create FileOrganizer
    base_paths = {
        'episode_base': os.path.join(os.path.dirname(__file__), '..', '..', 'Content'),
        'analysis_rules': os.path.join(os.path.dirname(__file__), 'Rules')
    }
    
    # Convert to absolute paths
    for key, path in base_paths.items():
        base_paths[key] = os.path.abspath(path)
    
    print(f"Base paths: {base_paths}")
    
    try:
        file_organizer = FileOrganizer(base_paths)
        print("✅ FileOrganizer created successfully")
    except Exception as e:
        print(f"❌ FileOrganizer creation failed: {e}")
        return False
    
    # Test with the existing Bono transcript
    transcript_path = r"C:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Content\Joe_Rogan_Experience\Joe Rogan Experience #2330 - Bono\Input\original_audio_full_transcript.json"
    
    if not os.path.exists(transcript_path):
        print(f"❌ Test transcript not found: {transcript_path}")
        return False
    
    print(f"📁 Testing with transcript: {transcript_path}")
    
    try:
        # Test the analysis output path generation
        analysis_path = file_organizer.get_analysis_output_path(transcript_path)
        print(f"📄 Analysis output path: {analysis_path}")
        
        # Check if the path is in the Processing folder
        expected_processing_folder = r"C:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Content\Joe_Rogan_Experience\Joe Rogan Experience #2330 - Bono\Processing"
        
        if expected_processing_folder in analysis_path:
            print("✅ Output path correctly targets Processing folder")
        else:
            print(f"❌ Output path not in expected Processing folder")
            print(f"   Expected to contain: {expected_processing_folder}")
            print(f"   Actual path: {analysis_path}")
            return False
        
        # Test that the Processing directory exists or gets created
        processing_dir = os.path.dirname(analysis_path)
        if os.path.exists(processing_dir):
            print(f"✅ Processing directory exists: {processing_dir}")
        else:
            print(f"❌ Processing directory not found: {processing_dir}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing file organization: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing File Organization Integration")
    print("=" * 50)
    
    success = test_file_organization()
    
    if success:
        print("\n🎉 All file organization tests passed!")
        print("✅ The transcript_analyzer.py will now output files to organized Processing folders")
    else:
        print("\n❌ File organization test failed")
        sys.exit(1)
