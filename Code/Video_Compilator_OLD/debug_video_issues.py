"""
Debug script to analyze video compilation issues
"""
import subprocess
import json
from pathlib import Path

def analyze_video_file(video_path):
    """Analyze a video file using ffprobe"""
    print(f"\n=== Analyzing: {video_path.name} ===")
    
    if not video_path.exists():
        print(f"❌ File does not exist: {video_path}")
        return None
    
    try:
        # Get detailed info
        command = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(video_path)
        ]
        
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        
        # Extract key info
        format_info = data.get('format', {})
        streams = data.get('streams', [])
        
        print(f"Duration: {float(format_info.get('duration', 0)):.2f} seconds")
        print(f"Size: {int(format_info.get('size', 0)) / (1024*1024):.2f} MB")
        
        for stream in streams:
            codec_type = stream.get('codec_type')
            if codec_type == 'video':
                print(f"Video: {stream.get('codec_name')} {stream.get('width')}x{stream.get('height')} @ {stream.get('r_frame_rate')} fps")
                print(f"Video Bitrate: {stream.get('bit_rate', 'unknown')}")
            elif codec_type == 'audio':
                print(f"Audio: {stream.get('codec_name')} {stream.get('sample_rate')}Hz {stream.get('channels')}ch")
                print(f"Audio Bitrate: {stream.get('bit_rate', 'unknown')}")
        
        return data
        
    except Exception as e:
        print(f"❌ Error analyzing {video_path}: {e}")
        return None

def check_frame_rate_issues(video_path):
    """Check if video has frame rate or timing issues"""
    print(f"\n=== Frame Rate Analysis: {video_path.name} ===")
    
    try:
        # Check for variable frame rate or timing issues
        command = [
            "ffprobe",
            "-v", "quiet",
            "-select_streams", "v:0",
            "-show_entries", "packet=pts_time,duration_time",
            "-of", "csv=p=0",
            str(video_path)
        ]
        
        result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=10)
        lines = result.stdout.strip().split('\n')[:10]  # First 10 frames
        
        if len(lines) > 1:
            times = []
            for line in lines:
                if ',' in line:
                    pts_time, duration_time = line.split(',')
                    try:
                        times.append(float(pts_time))
                    except ValueError:
                        continue
            
            if len(times) > 1:
                intervals = [times[i+1] - times[i] for i in range(len(times)-1)]
                avg_interval = sum(intervals) / len(intervals)
                expected_fps = 1.0 / avg_interval if avg_interval > 0 else 0
                print(f"Detected FPS: {expected_fps:.2f}")
                
                # Check for irregular intervals
                irregular = [abs(interval - avg_interval) > avg_interval * 0.1 for interval in intervals]
                if any(irregular):
                    print("⚠️ WARNING: Irregular frame timing detected")
                else:
                    print("✅ Frame timing appears regular")
        
    except Exception as e:
        print(f"❌ Error checking frame rate: {e}")

def analyze_audio_characteristics(video_path):
    """Analyze audio for warping or speed issues"""
    print(f"\n=== Audio Analysis: {video_path.name} ===")
    
    try:
        # Extract audio characteristics
        command = [
            "ffprobe",
            "-v", "quiet",
            "-select_streams", "a:0",
            "-show_entries", "stream=sample_rate,channels,duration,bit_rate",
            "-of", "csv=p=0",
            str(video_path)
        ]
        
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        if result.stdout.strip():
            print(f"Audio stream info: {result.stdout.strip()}")
        
        # Check for silence at the end
        command = [
            "ffmpeg",
            "-i", str(video_path),
            "-af", "silencedetect=noise=-50dB:duration=2",
            "-f", "null",
            "-"
        ]
        
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        if "silence_end" in result.stderr:
            print("⚠️ WARNING: Extended silence periods detected")
            # Extract silence info
            for line in result.stderr.split('\n'):
                if 'silence_start' in line or 'silence_end' in line:
                    print(f"  {line.strip()}")
        else:
            print("✅ No extended silence periods detected")
            
    except Exception as e:
        print(f"❌ Error analyzing audio: {e}")

def main():
    """Main debug function"""
    base_path = Path(r"C:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Content\Joe_Rogan_Experience\Joe Rogan Experience #2330 - Bono\Output\Video")
    
    print("🔍 VIDEO COMPILATION BUG INVESTIGATION")
    print("=" * 50)
    
    # Check a few sample files
    files_to_check = [
        base_path / "temp" / "temp_intro_001.mp4",  # Narration file
        base_path / "video_clip_001.mp4",  # Video clip
        base_path / "temp" / "temp_pre_clip_001.mp4",  # Another narration
        base_path / "Final" / "Joe Rogan Experience #2330 - Bono_compiled.mp4"  # Final output
    ]
    
    for video_file in files_to_check:
        if video_file.exists():
            analyze_video_file(video_file)
            check_frame_rate_issues(video_file)
            analyze_audio_characteristics(video_file)
            print("-" * 50)
        else:
            print(f"❌ File not found: {video_file}")
    
    # Check the background image processing command
    print("\n🖼️ BACKGROUND IMAGE ANALYSIS")
    print("=" * 50)
    bg_image = Path(r"C:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Assets\Chris_Morris_Images\bloody_hell.jpg")
    if bg_image.exists():
        print(f"✅ Background image exists: {bg_image}")
        try:
            # Check image properties
            command = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_streams",
                str(bg_image)
            ]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            stream = data.get('streams', [{}])[0]
            print(f"Image: {stream.get('width')}x{stream.get('height')}")
        except Exception as e:
            print(f"❌ Error checking background image: {e}")
    else:
        print(f"❌ Background image not found: {bg_image}")

if __name__ == "__main__":
    main()
