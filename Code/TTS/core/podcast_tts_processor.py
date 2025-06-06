#!/usr/bin/env python3
"""
TTS Integration Module
Generates all audio files from structured podcast script using the TTS system.
Integrates with the existing TTS generator to create organized audio segments.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
import os

# Add TTS directory to path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from tts_generator import SimpleTTSGenerator

class PodcastTTSProcessor:
    """Process structured podcast scripts into organized TTS audio files"""
    def __init__(self, output_dir: str = None):
        """
        Initialize with TTS configuration
        
        Args:
            output_dir: Directory for TTS audio output, uses default if None
        """
        self.logger = logging.getLogger(__name__)
        
        # Initialize TTS generator with output directory (not config path)
        # SimpleTTSGenerator loads its own config internally
        self.tts_generator = SimpleTTSGenerator(output_dir)
            
        self.logger.info("TTS Processor initialized")
    
    def generate_podcast_audio(
        self, 
        tts_script_path: str, 
        output_directory: str = None
    ) -> Dict[str, Any]:
        """
        Generate all audio files from TTS-ready script
        
        Args:
            tts_script_path: Path to the structured TTS script JSON
            output_directory: Directory to save audio files (uses default if None)
            
        Returns:
            Dictionary with generation results and file paths
        """
        
        # Load TTS script
        with open(tts_script_path, 'r', encoding='utf-8') as f:
            tts_script = json.load(f)
        
        self.logger.info(f"Processing TTS script: {Path(tts_script_path).name}")        # Setup output directory
        if output_directory is None:
            # Extract episode structure from script path
            script_path = Path(tts_script_path)
            
            # If script is in Output/Scripts/, get the episode folder
            if script_path.parts[-2] == 'Scripts' and script_path.parts[-3] == 'Output':
                episode_dir = script_path.parent.parent.parent  # Go up to episode folder
                output_directory = episode_dir / "Output" / "Audio"
            else:
                # Fallback: create episode structure based on episode info
                script_dir = Path(__file__).parent.parent.parent  # YouTuber root
                episode_name = tts_script["episode_info"].get("title", "Unknown_Episode").replace(" ", "_")
                series_name = tts_script["episode_info"].get("series", "Unknown_Series").replace(" ", "_")
                episode_dir = script_dir / "Content" / series_name / episode_name
                output_directory = episode_dir / "Output" / "Audio"
        
        output_dir = Path(output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)
          # Track generation results
        results = {
            "episode_info": tts_script["episode_info"],
            "output_directory": str(output_dir),
            "generated_files": [],
            "failed_files": [],
            "total_segments": 0,
            "successful_segments": 0
        }
        
        script_structure = tts_script["script_structure"]
        
        # Generate intro audio
        if "intro" in script_structure:
            self._generate_segment_audio(
                script_structure["intro"], output_dir, "intro", results
            )
        
        # Generate clip segment audio (pre-clip and post-clip)
        for segment in script_structure.get("clip_segments", []):
            segment_index = segment["segment_index"]
            
            # Pre-clip audio
            if "pre_clip" in segment:
                self._generate_segment_audio(
                    segment["pre_clip"], output_dir, f"pre_clip_{segment_index}", results
                )
            
            # Post-clip audio  
            if "post_clip" in segment:
                self._generate_segment_audio(
                    segment["post_clip"], output_dir, f"post_clip_{segment_index}", results
                )
        
        # Generate outro audio
        if "outro" in script_structure:
            self._generate_segment_audio(
                script_structure["outro"], output_dir, "outro", results
            )
        
        # Save generation report
        self._save_generation_report(results, output_dir)
        
        success_rate = results["successful_segments"] / results["total_segments"] if results["total_segments"] > 0 else 0
        self.logger.info(f"Audio generation complete: {results['successful_segments']}/{results['total_segments']} segments ({success_rate:.1%} success)")
        
        return results
    
    def _generate_segment_audio(
        self, 
        segment: Dict, 
        output_dir: Path, 
        segment_type: str, 
        results: Dict
    ) -> None:
        """Generate audio for a single script segment"""
        
        results["total_segments"] += 1
        
        try:
            script_text = segment.get("script", "")
            voice_style = segment.get("voice_style", "normal")
            audio_filename = segment.get("audio_filename", f"{segment_type}.wav")
            
            if not script_text.strip():
                self.logger.warning(f"Empty script for {segment_type}, skipping")
                results["failed_files"].append({
                    "filename": audio_filename,
                    "error": "Empty script text",
                    "segment_type": segment_type
                })
                return
            
            # Generate audio using TTS
            output_path = output_dir / audio_filename
            
            self.logger.info(f"Generating {segment_type}: {audio_filename}")
            self.logger.debug(f"Voice style: {voice_style}, Text length: {len(script_text)} chars")
              # Use TTS generator with voice style
            success = self.tts_generator.generate_audio(
                text=script_text,
                output_filename=str(output_path),
                voice_style=voice_style
            )
            
            if success:
                results["successful_segments"] += 1
                results["generated_files"].append({
                    "filename": audio_filename,
                    "path": str(output_path),
                    "segment_type": segment_type,
                    "voice_style": voice_style,
                    "estimated_duration": segment.get("estimated_duration", "unknown"),
                    "text_length": len(script_text)
                })
                self.logger.info(f"✓ Generated: {audio_filename}")
            else:
                results["failed_files"].append({
                    "filename": audio_filename,
                    "error": "TTS generation failed",
                    "segment_type": segment_type
                })
                self.logger.error(f"✗ Failed: {audio_filename}")
                
        except Exception as e:
            self.logger.error(f"Error generating {segment_type}: {e}")
            results["failed_files"].append({
                "filename": segment.get("audio_filename", f"{segment_type}.wav"),
                "error": str(e),
                "segment_type": segment_type
            })
    
    def _save_generation_report(self, results: Dict, output_dir: Path) -> None:
        """Save detailed generation report"""
        
        report_path = output_dir / "tts_generation_report.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Also save a human-readable summary
        summary_path = output_dir / "tts_generation_summary.txt"
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("TTS GENERATION SUMMARY\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"Episode: {results['episode_info']['title']}\n")
            f.write(f"Episode Number: {results['episode_info']['episode_number']}\n")
            f.write(f"Total Segments: {results['total_segments']}\n")
            f.write(f"Successful: {results['successful_segments']}\n")
            f.write(f"Failed: {len(results['failed_files'])}\n")
            f.write(f"Success Rate: {results['successful_segments']/results['total_segments']:.1%}\n\n")
            
            if results["generated_files"]:
                f.write("GENERATED FILES:\n")
                f.write("-" * 20 + "\n")
                for file_info in results["generated_files"]:
                    f.write(f"✓ {file_info['filename']} ({file_info['voice_style']}, {file_info['estimated_duration']})\n")
                f.write("\n")
            
            if results["failed_files"]:
                f.write("FAILED FILES:\n")
                f.write("-" * 20 + "\n")
                for file_info in results["failed_files"]:
                    f.write(f"✗ {file_info['filename']}: {file_info['error']}\n")
        
        self.logger.info(f"Generation report saved: {report_path}")

    def validate_tts_script(self, tts_script_path: str) -> Dict[str, Any]:
        """
        Validate TTS script structure before generation
        
        Returns:
            Validation results with issues found
        """
        validation = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "segment_count": 0,
            "estimated_files": 0
        }
        
        try:
            with open(tts_script_path, 'r', encoding='utf-8') as f:
                tts_script = json.load(f)
        except Exception as e:
            validation["valid"] = False
            validation["errors"].append(f"Failed to load script: {e}")
            return validation
        
        # Check required structure
        if "script_structure" not in tts_script:
            validation["errors"].append("Missing 'script_structure' section")
            validation["valid"] = False
        
        if "episode_info" not in tts_script:
            validation["warnings"].append("Missing 'episode_info' section")
        
        script_structure = tts_script.get("script_structure", {})
        
        # Validate intro
        if "intro" in script_structure:
            validation["estimated_files"] += 1
            if not script_structure["intro"].get("script", "").strip():
                validation["warnings"].append("Intro section has empty script")
        
        # Validate clip segments
        clip_segments = script_structure.get("clip_segments", [])
        validation["segment_count"] = len(clip_segments)
        
        for i, segment in enumerate(clip_segments, 1):
            if "pre_clip" in segment:
                validation["estimated_files"] += 1
                if not segment["pre_clip"].get("script", "").strip():
                    validation["warnings"].append(f"Clip {i} pre-clip has empty script")
            
            if "post_clip" in segment:
                validation["estimated_files"] += 1
                if not segment["post_clip"].get("script", "").strip():
                    validation["warnings"].append(f"Clip {i} post-clip has empty script")
        
        # Validate outro
        if "outro" in script_structure:
            validation["estimated_files"] += 1
            if not script_structure["outro"].get("script", "").strip():
                validation["warnings"].append("Outro section has empty script")
        
        if validation["estimated_files"] == 0:
            validation["errors"].append("No audio segments found to generate")
            validation["valid"] = False
        
        return validation


# Example usage and testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate TTS audio from structured podcast script")
    parser.add_argument("script_path", help="Path to TTS-ready script JSON file")
    parser.add_argument("--output-dir", help="Output directory for audio files")
    parser.add_argument("--validate-only", action="store_true", help="Only validate script without generating audio")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    processor = PodcastTTSProcessor()
    
    if args.validate_only:
        # Validation only
        validation = processor.validate_tts_script(args.script_path)
        print(f"Validation Results:")
        print(f"Valid: {validation['valid']}")
        print(f"Estimated files: {validation['estimated_files']}")
        print(f"Segment count: {validation['segment_count']}")
        
        if validation['warnings']:
            print("\nWarnings:")
            for warning in validation['warnings']:
                print(f"  ⚠️ {warning}")
        
        if validation['errors']:
            print("\nErrors:")
            for error in validation['errors']:
                print(f"  ❌ {error}")
    else:
        # Generate audio
        try:
            results = processor.generate_podcast_audio(args.script_path, args.output_dir)
            print(f"\n✅ Generation complete!")
            print(f"📁 Output directory: {results.get('output_directory', args.output_dir)}")
            print(f"🎵 Generated files: {results['successful_segments']}/{results['total_segments']}")
        except Exception as e:
            print(f"❌ Generation failed: {e}")
            exit(1)
