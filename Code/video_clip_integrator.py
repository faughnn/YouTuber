#!/usr/bin/env python3
"""
Video Clip Integration Helper
Demonstrates how to extract video clips based on TTS script clip references.
This bridges the gap between script generation and video editing.
"""

import json
import logging
from pathlib import Path
import subprocess
from typing import Dict, List, Any

class VideoClipIntegrator:
    """Integrate TTS scripts with video clip extraction"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract_clips_from_tts_script(
        self, 
        tts_script_path: str,
        source_video_path: str,
        output_directory: str = None
    ) -> Dict[str, Any]:
        """
        Extract video clips referenced in TTS script
        
        Args:
            tts_script_path: Path to TTS-ready script JSON
            source_video_path: Path to source video file
            output_directory: Directory for clip output
            
        Returns:
            Results of clip extraction process
        """
        
        # Load TTS script
        with open(tts_script_path, 'r', encoding='utf-8') as f:
            tts_script = json.load(f)
        
        episode_info = tts_script.get("episode_info", {})
        script_structure = tts_script.get("script_structure", {})
        
        self.logger.info(f"Extracting clips for: {episode_info.get('title', 'Unknown Episode')}")
        
        # Setup output directory
        if output_directory is None:
            output_directory = Path(source_video_path).parent / "Clips" / "TTS_Referenced_Clips"
        
        output_dir = Path(output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract clip information from script
        clips_to_extract = []
        clip_segments = script_structure.get("clip_segments", [])
        
        for segment in clip_segments:
            clip_ref = segment.get("clip_reference", {})
            if clip_ref:
                clips_to_extract.append({
                    "clip_id": clip_ref.get("clip_id", "unknown"),
                    "title": clip_ref.get("title", "Untitled Clip"),
                    "start_time": clip_ref.get("start_time", "0:00:00"),
                    "end_time": clip_ref.get("end_time", "0:00:30"),
                    "expected_filename": clip_ref.get("video_filename", "clip.mp4"),
                    "segment_index": segment.get("segment_index", 0)
                })
        
        self.logger.info(f"Found {len(clips_to_extract)} clips to extract")
        
        # Generate extraction manifest for analysis_video_clipper.py
        extraction_manifest = self._create_extraction_manifest(clips_to_extract)
        manifest_path = output_dir / "extraction_manifest.json"
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(extraction_manifest, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Extraction manifest created: {manifest_path}")
        
        # Create instructions for manual clip extraction
        instructions_path = output_dir / "clip_extraction_instructions.txt"
        self._create_extraction_instructions(
            clips_to_extract, source_video_path, output_dir, instructions_path
        )
        
        return {
            "clips_found": len(clips_to_extract),
            "output_directory": str(output_dir),
            "manifest_path": str(manifest_path),
            "instructions_path": str(instructions_path),
            "clips_to_extract": clips_to_extract,
            "source_video": source_video_path
        }
    
    def _create_extraction_manifest(self, clips: List[Dict]) -> Dict[str, Any]:
        """Create manifest for clip extraction tools"""
        
        manifest = {
            "extraction_type": "tts_script_referenced",
            "clips": []
        }
        
        for clip in clips:
            manifest["clips"].append({
                "narrativeSegmentTitle": clip["title"],
                "severityRating": "TTS_REFERENCED",
                "fullerContextTimestamps": {
                    "start": self._timestamp_to_seconds(clip["start_time"]),
                    "end": self._timestamp_to_seconds(clip["end_time"])
                },
                "clipContextDescription": f"Clip referenced in TTS script: {clip['title']}",
                "harmPotential": "Referenced for podcast analysis"
            })
        
        return manifest
    
    def _timestamp_to_seconds(self, timestamp: str) -> float:
        """Convert timestamp string to seconds"""
        try:
            parts = timestamp.split(':')
            if len(parts) == 2:  # MM:SS
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:  # HH:MM:SS
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            return 0.0
        except:
            return 0.0
    
    def _create_extraction_instructions(
        self, 
        clips: List[Dict], 
        source_video: str, 
        output_dir: Path,
        instructions_path: Path
    ) -> None:
        """Create human-readable extraction instructions"""
        
        with open(instructions_path, 'w', encoding='utf-8') as f:
            f.write("VIDEO CLIP EXTRACTION INSTRUCTIONS\n")
            f.write("=" * 50 + "\n\n")
            f.write("This file contains instructions for extracting video clips\n")
            f.write("referenced in the TTS podcast script.\n\n")
            
            f.write(f"Source Video: {source_video}\n")
            f.write(f"Output Directory: {output_dir}\n")
            f.write(f"Total Clips: {len(clips)}\n\n")
            
            f.write("EXTRACTION METHODS:\n")
            f.write("-" * 30 + "\n\n")
            
            f.write("Method 1: Using analysis_video_clipper.py\n")
            f.write(f"python Code/Video_Clipper/analysis_video_clipper.py \\\n")
            f.write(f"  \"{source_video}\" \\\n")
            f.write(f"  \"{output_dir / 'extraction_manifest.json'}\" \\\n")
            f.write(f"  --output-dir TTS_Referenced_Clips\n\n")
            
            f.write("Method 2: Manual FFmpeg Commands\n")
            f.write("-" * 30 + "\n")
            
            for i, clip in enumerate(clips, 1):
                output_filename = f"{i:02d}_{clip['clip_id']}.mp4"
                f.write(f"\n# Clip {i}: {clip['title']}\n")
                f.write(f"ffmpeg -i \"{source_video}\" \\\n")
                f.write(f"  -ss {clip['start_time']} \\\n")
                f.write(f"  -to {clip['end_time']} \\\n")
                f.write(f"  -c copy \\\n")
                f.write(f"  -y \"{output_dir / output_filename}\"\n")
            
            f.write("\n\nCLIP DETAILS:\n")
            f.write("-" * 20 + "\n")
            
            for i, clip in enumerate(clips, 1):
                f.write(f"\nClip {i}:\n")
                f.write(f"  Title: {clip['title']}\n")
                f.write(f"  ID: {clip['clip_id']}\n")
                f.write(f"  Time: {clip['start_time']} - {clip['end_time']}\n")
                f.write(f"  Expected Filename: {clip['expected_filename']}\n")
        
        self.logger.info(f"Extraction instructions saved: {instructions_path}")

    def verify_extracted_clips(
        self, 
        extraction_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Verify that expected clips were extracted"""
        
        output_dir = Path(extraction_results["output_directory"])
        clips_to_extract = extraction_results["clips_to_extract"]
        
        verification = {
            "total_expected": len(clips_to_extract),
            "found_clips": [],
            "missing_clips": [],
            "verification_passed": True
        }
        
        for clip in clips_to_extract:
            # Check for various possible filenames
            possible_names = [
                clip["expected_filename"],
                f"{clip['segment_index']:02d}_{clip['clip_id']}.mp4",
                f"[TTS_REFERENCED]_{clip['segment_index']:02d}_{clip['clip_id']}.mp4"
            ]
            
            found = False
            for name in possible_names:
                clip_path = output_dir / name
                if clip_path.exists():
                    verification["found_clips"].append({
                        "clip_id": clip["clip_id"],
                        "title": clip["title"],
                        "found_path": str(clip_path),
                        "file_size": clip_path.stat().st_size
                    })
                    found = True
                    break
            
            if not found:
                verification["missing_clips"].append(clip)
                verification["verification_passed"] = False
        
        self.logger.info(f"Clip verification: {len(verification['found_clips'])}/{verification['total_expected']} found")
        
        return verification


# Example usage and testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract video clips from TTS script references")
    parser.add_argument("tts_script", help="Path to TTS-ready script JSON file")
    parser.add_argument("source_video", help="Path to source video file")
    parser.add_argument("--output-dir", help="Output directory for clips")
    parser.add_argument("--verify-only", action="store_true", help="Only verify existing clips")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    integrator = VideoClipIntegrator()
    
    if args.verify_only:
        # Verification mode (assumes extraction was already done)
        print("Verification mode not yet implemented")
    else:
        # Extraction mode
        try:
            results = integrator.extract_clips_from_tts_script(
                args.tts_script, args.source_video, args.output_dir
            )
            
            print(f"\n✅ Clip extraction setup complete!")
            print(f"📁 Output directory: {results['output_directory']}")
            print(f"🎬 Clips to extract: {results['clips_found']}")
            print(f"📋 Instructions: {results['instructions_path']}")
            print(f"📄 Manifest: {results['manifest_path']}")
            
        except Exception as e:
            print(f"❌ Extraction setup failed: {e}")
            exit(1)
