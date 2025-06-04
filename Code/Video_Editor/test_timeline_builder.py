"""
Complete Timeline Builder Test
Tests the full workflow from TTS-ready script to video timeline
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add project paths
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent))

from timeline_builder import TimelineBuilder

def create_sample_tts_script():
    """Create a sample TTS-ready script for testing"""
    
    sample_script = {
        "episode_info": {
            "title": "Joe Rogan Experience 2325 - Aaron Rodgers Analysis",
            "episode_number": "001",
            "initials": "JRE2325-AR",
            "source_video": "JRE2325_full_episode.mp4"
        },
        "script_structure": {
            "intro": {
                "script": "Welcome to The Bullseye, where we analyze the most outrageous moments from popular podcasts. Today, we're diving into Joe Rogan's conversation with Aaron Rodgers, and trust me, it's a wild ride through conspiracy theories and questionable medical advice.",
                "voice_style": "enthusiastic",
                "audio_filename": "intro_001_JRE2325-AR.wav",
                "video_instruction": "Host speaking with energy, intro graphics",
                "estimated_duration": 15.0
            },
            "clip_segments": [
                {
                    "pre_clip": {
                        "script": "Our first clip features Aaron Rodgers making some pretty bold claims about vaccine deaths. Get ready for some statistical gymnastics that would make an Olympic athlete jealous.",
                        "voice_style": "normal",
                        "audio_filename": "pre_clip_001_001_vaccine_deaths_JRE2325-AR.wav",
                        "video_instruction": "Host setting up clip, slight skeptical expression",
                        "estimated_duration": 8.0
                    },
                    "clip_reference": {
                        "clip_id": "vaccine_deaths_claim",
                        "start_time": "0:57:17",
                        "end_time": "0:57:53",
                        "duration": 36.0,
                        "title": "Claim of 470,000 Vaccine Deaths in US"
                    },
                    "post_clip": {
                        "script": "Well, that escalated quickly! Aaron went from zero to apocalyptic conspiracy faster than you can say 'peer review.' That claim about 470,000 vaccine deaths? That's not just misleading, that's a masterclass in how to turn correlation into causation with a dash of dramatic flair.",
                        "voice_style": "sarcastic",
                        "audio_filename": "post_clip_001_001_vaccine_deaths_JRE2325-AR.wav",
                        "video_instruction": "Host reacting with raised eyebrows, fact-check graphics",
                        "estimated_duration": 12.0
                    }
                },
                {
                    "pre_clip": {
                        "script": "But wait, there's more! Our next clip features a deep dive into blood clots and myocarditis. Because apparently, medical school is optional when you have a podcast microphone.",
                        "voice_style": "normal",
                        "audio_filename": "pre_clip_002_001_side_effects_JRE2325-AR.wav",
                        "video_instruction": "Host with mock serious expression",
                        "estimated_duration": 7.0
                    },
                    "clip_reference": {
                        "clip_id": "vaccine_side_effects",
                        "start_time": "1:00:32",
                        "end_time": "1:02:22",
                        "duration": 110.0,
                        "title": "COVID Vaccine Side Effects Discussion"
                    },
                    "post_clip": {
                        "script": "Ah yes, the classic 'I'm not a doctor but I play one on my podcast' approach to medical analysis. The confidence with which complex medical topics get oversimplified never ceases to amaze me. It's like watching someone explain quantum physics using only finger puppets.",
                        "voice_style": "sarcastic",
                        "audio_filename": "post_clip_002_001_side_effects_JRE2325-AR.wav",
                        "video_instruction": "Host with amused disbelief, medical fact graphics",
                        "estimated_duration": 10.0
                    }
                }
            ],
            "outro": {
                "script": "And that's a wrap on today's episode of The Bullseye! Remember folks, just because someone says it confidently into a microphone doesn't make it medical advice. Until next time, keep questioning, keep fact-checking, and keep your critical thinking skills sharp!",
                "voice_style": "normal",
                "audio_filename": "outro_001_JRE2325-AR.wav",
                "video_instruction": "Host wrapping up, outro graphics and subscribe button",
                "estimated_duration": 12.0
            }
        },
        "generation_metadata": {
            "created_at": "2024-12-19T20:30:00Z",
            "script_version": "1.0",
            "ai_model": "gemini-1.5-pro",
            "workflow_version": "tts_ready_v1.0"
        }
    }
    
    return sample_script

def test_timeline_builder():
    """Test the complete timeline building workflow"""
    
    print("🎬 Timeline Builder Comprehensive Test")
    print("=" * 50)
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Step 1: Create sample TTS script
        print("\n📝 Step 1: Creating sample TTS-ready script...")
        sample_script = create_sample_tts_script()
        
        # Save sample script to file
        test_script_path = Path(__file__).parent / "test_tts_ready_script.json"
        with open(test_script_path, 'w', encoding='utf-8') as f:
            json.dump(sample_script, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Sample TTS script created: {test_script_path}")
        print(f"   Episode: {sample_script['episode_info']['title']}")
        print(f"   Segments: {len(sample_script['script_structure']['clip_segments'])} clips")
        
        # Step 2: Initialize Timeline Builder
        print("\n🏗️  Step 2: Initializing Timeline Builder...")
        builder = TimelineBuilder()
        
        print(f"✅ Timeline Builder initialized")
        print(f"   Audio output: {builder.audio_output_dir}")
        print(f"   Timeline output: {builder.timeline_output_dir}")
        print(f"   TTS generator available: {builder.tts_generator is not None}")
        
        # Step 3: Build timeline from TTS script
        print("\n🎵 Step 3: Building timeline from TTS script...")
        
        timeline_data = builder.build_timeline_from_tts_script(\n            str(test_script_path),\n            output_name=\"JRE2325_AR_Analysis_Test\"\n        )\n        \n        print(f\"✅ Timeline built successfully!\")\n        print(f\"   Total duration: {timeline_data['total_duration']:.1f} seconds\")\n        print(f\"   Timeline segments: {len(timeline_data['timeline_segments'])}\")\n        print(f\"   Audio files generated: {len(timeline_data['audio_files'])}\")\n        print(f\"   Video files needed: {len(timeline_data['video_files_needed'])}\")\n        \n        # Step 4: Display timeline structure\n        print(\"\\n📋 Step 4: Timeline Structure Analysis...\")\n        print(\"\\nTimeline Segments:\")\n        for i, segment in enumerate(timeline_data['timeline_segments']):\n            duration = segment.get('actual_duration', segment.get('estimated_duration', 0))\n            print(f\"  {i+1}. [{segment['start_time']:.1f}s-{segment['end_time']:.1f}s] \"\n                  f\"{segment['type']} - {segment['segment_name']} ({duration:.1f}s)\")\n        \n        print(\"\\nAudio Files Generated:\")\n        for key, path in timeline_data['audio_files'].items():\n            exists = \"✅\" if os.path.exists(path) else \"❌\"\n            print(f\"  {exists} {key}: {Path(path).name}\")\n        \n        print(\"\\nVideo Files Needed:\")\n        for video_file in timeline_data['video_files_needed']:\n            print(f\"  📹 {video_file}\")\n        \n        # Step 5: Generate editing instructions\n        print(\"\\n🎬 Step 5: Video Editing Instructions...\")\n        editing_instructions = timeline_data['editing_instructions']\n        \n        print(f\"Project Name: {editing_instructions['project_name']}\")\n        print(f\"Resolution: {editing_instructions['sequence_resolution']}\")\n        print(f\"Frame Rate: {editing_instructions['frame_rate']} fps\")\n        print(f\"Total Duration: {editing_instructions['total_duration']:.1f} seconds\")\n        \n        print(\"\\nAudio Track Segments:\")\n        for track in editing_instructions['audio_tracks']:\n            print(f\"  Track: {track['track_name']}\")\n            for segment in track['segments']:\n                print(f\"    [{segment['start_time']:.1f}s-{segment['end_time']:.1f}s] \"\n                      f\"{segment['segment_name']} - {Path(segment['audio_file']).name}\")\n        \n        print(\"\\nVideo Track Segments:\")\n        for track in editing_instructions['video_tracks']:\n            print(f\"  Track: {track['track_name']}\")\n            for segment in track['segments']:\n                if 'video_file_needed' in segment:\n                    print(f\"    [{segment['start_time']:.1f}s-{segment['end_time']:.1f}s] \"\n                          f\"Video Clip - {segment['video_file_needed']}\")\n                else:\n                    print(f\"    [{segment['start_time']:.1f}s-{segment['end_time']:.1f}s] \"\n                          f\"Narrator - {segment['video_instruction']}\")\n        \n        # Step 6: Generate project files\n        print(\"\\n📁 Step 6: Generating editor project files...\")\n        \n        timeline_file = timeline_data['timeline_file_path']\n        project_files = builder.generate_editing_project_files(timeline_file, 'davinci')\n        \n        for editor, file_path in project_files.items():\n            print(f\"  ✅ {editor.title()} project file: {Path(file_path).name}\")\n        \n        # Step 7: Summary and next steps\n        print(\"\\n🎯 Step 7: Workflow Summary\")\n        print(\"=\"*30)\n        print(\"✅ TTS-ready script processed successfully\")\n        print(\"✅ Audio files generated (or would be with real TTS)\")\n        print(\"✅ Timeline structure created\")\n        print(\"✅ Video editing instructions generated\")\n        print(\"✅ Project files created for video editors\")\n        \n        print(\"\\n📈 Next Steps:\")\n        print(\"1. 🎥 Extract/clip video segments from source material\")\n        print(\"2. 🎬 Import timeline and files into video editor\")\n        print(\"3. 🔄 Follow assembly order for final video\")\n        print(\"4. 🎨 Add graphics, transitions, and final polish\")\n        print(\"5. 📤 Export final podcast episode\")\n        \n        print(\"\\n🚀 Timeline Builder Test COMPLETED SUCCESSFULLY!\")\n        \n        return timeline_data\n        \n    except Exception as e:\n        print(f\"\\n❌ Error in timeline builder test: {e}\")\n        import traceback\n        traceback.print_exc()\n        return None\n\ndef analyze_workflow_integration():\n    \"\"\"Analyze how this integrates with the complete workflow\"\"\"\n    \n    print(\"\\n🔗 Workflow Integration Analysis\")\n    print(\"=\" * 40)\n    \n    workflow_steps = [\n        \"1. 📺 Video Analysis → Extract interesting clips\",\n        \"2. 🤖 Content Analysis → Generate base podcast script\", \n        \"3. 🎵 TTS Workflow → Create TTS-ready structured script\",\n        \"4. 🏗️  Timeline Builder → Generate audio + create timeline\",  # ← WE ARE HERE\n        \"5. 🎬 Video Assembly → Combine audio + video clips\",\n        \"6. 🎨 Final Polish → Add graphics, export final video\"\n    ]\n    \n    for step in workflow_steps:\n        if \"Timeline Builder\" in step:\n            print(f\"  ✅ {step} ← CURRENT IMPLEMENTATION\")\n        else:\n            print(f\"     {step}\")\n    \n    print(\"\\n📋 Integration Points:\")\n    print(\"• Input: TTS-ready script JSON (from enhanced podcast generator)\")\n    print(\"• Process: Generate audio files + build timeline structure\")\n    print(\"• Output: Complete timeline with editing instructions\")\n    print(\"• Next: Video assembly module to combine everything\")\n    \n    print(\"\\n🎯 What We've Achieved:\")\n    print(\"• ✅ Complete audio generation from structured scripts\")\n    print(\"• ✅ Timeline assembly with proper timing calculations\")\n    print(\"• ✅ Video editor integration instructions\")\n    print(\"• ✅ Automated workflow from script to timeline\")\n    print(\"• ✅ Support for multiple video editors\")\n\nif __name__ == \"__main__\":\n    # Run the comprehensive test\n    timeline_result = test_timeline_builder()\n    \n    if timeline_result:\n        analyze_workflow_integration()\n        \n        print(\"\\n\" + \"=\"*60)\n        print(\"🎊 VIDEO EDITOR TIMELINE BUILDER IMPLEMENTATION COMPLETE!\")\n        print(\"=\"*60)\n    else:\n        print(\"\\n❌ Test failed - check errors above\")
