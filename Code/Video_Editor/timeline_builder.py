"""
Timeline Builder for Video Editor
Creates video editing timelines from TTS-ready podcast scripts
Integrates with the new TTS workflow and generates final video assembly instructions
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
import logging
from datetime import datetime

# Add TTS module to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from TTS.core.tts_generator import SimpleTTSGenerator
except ImportError as e:
    logging.warning(f"Could not import SimpleTTSGenerator: {e}")
    SimpleTTSGenerator = None

class TimelineBuilder:
    """
    Builds video editing timelines from TTS-ready podcast scripts
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize Timeline Builder
        
        Args:
            config_path: Path to TTS config file
        """
        self.logger = logging.getLogger(__name__)
        
        # Set up paths
        self.base_path = Path(__file__).parent.parent.parent
        self.audio_output_dir = self.base_path / "Content" / "Audio" / "Generated" / "TTS_Ready"
        self.timeline_output_dir = self.base_path / "Content" / "Timelines"
        self.video_clips_dir = self.base_path / "Content" / "Video_Clips"
        
        # Create directories
        self.audio_output_dir.mkdir(parents=True, exist_ok=True)
        self.timeline_output_dir.mkdir(parents=True, exist_ok=True)
          # Initialize TTS generator
        self.tts_generator = None
        if SimpleTTSGenerator:
            try:
                if config_path:
                    self.tts_generator = SimpleTTSGenerator(config_path)
                else:
                    # Use default config path
                    default_config = self.base_path / "Code" / "TTS" / "config" / "tts_config.json"
                    if default_config.exists():
                        self.tts_generator = SimpleTTSGenerator(str(default_config))
                    else:
                        self.tts_generator = SimpleTTSGenerator()
                        
                self.logger.info("TTS generator initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize TTS generator: {e}")
                self.tts_generator = None
        else:
            self.logger.warning("TTS generator not available")
    
    def build_timeline_from_tts_script(self, tts_script_path: str, output_name: str = None) -> Dict:
        """
        Build complete video timeline from TTS-ready script
        
        Args:
            tts_script_path: Path to TTS-ready script JSON file
            output_name: Custom name for output files (optional)
            
        Returns:
            Timeline data dictionary
        """
        try:
            # Load TTS script
            with open(tts_script_path, 'r', encoding='utf-8') as f:
                tts_script = json.load(f)
            
            self.logger.info(f"Building timeline from TTS script: {tts_script_path}")
            
            # Extract episode info
            episode_info = tts_script.get('episode_info', {})
            script_structure = tts_script.get('script_structure', {})
            
            # Generate output name if not provided
            if not output_name:
                title = episode_info.get('title', 'Unknown_Episode')
                episode_num = episode_info.get('episode_number', '001')
                output_name = f"{self._make_safe_filename(title)}_{episode_num}"
            
            # Step 1: Generate all audio files
            audio_files = self._generate_audio_from_tts_script(tts_script, output_name)
            
            # Step 2: Build timeline structure
            timeline_data = self._build_timeline_structure(tts_script, audio_files, output_name)
            
            # Step 3: Calculate timing and duration
            timeline_data = self._calculate_timeline_timing(timeline_data)
            
            # Step 4: Generate video editing instructions
            timeline_data['editing_instructions'] = self._generate_editing_instructions(timeline_data)
            
            # Step 5: Save timeline data
            timeline_path = self._save_timeline_data(timeline_data, output_name)
            timeline_data['timeline_file_path'] = timeline_path
            
            self.logger.info(f"Timeline built successfully: {timeline_path}")
            return timeline_data
            
        except Exception as e:
            self.logger.error(f"Error building timeline: {e}")
            raise
    
    def _generate_audio_from_tts_script(self, tts_script: Dict, output_name: str) -> Dict[str, str]:
        """
        Generate all audio files from TTS script structure
        
        Args:
            tts_script: TTS-ready script data
            output_name: Base name for output files
            
        Returns:
            Dictionary mapping segment IDs to audio file paths
        """
        if not self.tts_generator:
            self.logger.error("TTS generator not available")
            return {}
        
        audio_files = {}
        script_structure = tts_script.get('script_structure', {})
        
        try:
            # Generate intro audio
            intro = script_structure.get('intro', {})
            if intro.get('script'):
                intro_path = self._generate_single_audio(
                    text=intro['script'],
                    filename=intro.get('audio_filename', f'intro_{output_name}.wav'),
                    voice_style=intro.get('voice_style', 'enthusiastic'),
                    segment_id='intro'
                )
                if intro_path:
                    audio_files['intro'] = intro_path
            
            # Generate clip segment audio
            clip_segments = script_structure.get('clip_segments', [])
            for i, clip_segment in enumerate(clip_segments):
                segment_id = f'clip_segment_{i+1}'
                
                # Pre-clip audio
                pre_clip = clip_segment.get('pre_clip', {})
                if pre_clip.get('script'):
                    pre_clip_path = self._generate_single_audio(
                        text=pre_clip['script'],
                        filename=pre_clip.get('audio_filename', f'pre_clip_{i+1}_{output_name}.wav'),
                        voice_style=pre_clip.get('voice_style', 'normal'),
                        segment_id=f'{segment_id}_pre'
                    )
                    if pre_clip_path:
                        audio_files[f'{segment_id}_pre'] = pre_clip_path
                
                # Post-clip audio
                post_clip = clip_segment.get('post_clip', {})
                if post_clip.get('script'):
                    post_clip_path = self._generate_single_audio(
                        text=post_clip['script'],
                        filename=post_clip.get('audio_filename', f'post_clip_{i+1}_{output_name}.wav'),
                        voice_style=post_clip.get('voice_style', 'sarcastic'),
                        segment_id=f'{segment_id}_post'
                    )
                    if post_clip_path:
                        audio_files[f'{segment_id}_post'] = post_clip_path
            
            # Generate outro audio
            outro = script_structure.get('outro', {})
            if outro.get('script'):
                outro_path = self._generate_single_audio(
                    text=outro['script'],
                    filename=outro.get('audio_filename', f'outro_{output_name}.wav'),
                    voice_style=outro.get('voice_style', 'normal'),
                    segment_id='outro'
                )
                if outro_path:
                    audio_files['outro'] = outro_path
            
            self.logger.info(f"Generated {len(audio_files)} audio files")
            return audio_files
            
        except Exception as e:
            self.logger.error(f"Error generating audio files: {e}")
            return {}
    
    def _generate_single_audio(self, text: str, filename: str, voice_style: str, segment_id: str) -> Optional[str]:
        """
        Generate a single audio file
        
        Args:
            text: Script text to convert to speech
            filename: Output filename
            voice_style: Voice style (normal, enthusiastic, sarcastic)
            segment_id: Segment identifier for logging
            
        Returns:
            Path to generated audio file or None if failed
        """
        try:
            output_path = self.audio_output_dir / filename
            
            # Check if file already exists
            if output_path.exists():
                self.logger.info(f"Audio file already exists: {filename}")
                return str(output_path)
            
            self.logger.info(f"Generating audio for {segment_id}: {filename}")
            
            # Generate the audio
            success = self.tts_generator.generate_audio(
                text=text,
                output_path=str(output_path),
                voice_style=voice_style
            )
            
            if success and output_path.exists():
                self.logger.info(f"Successfully generated: {filename}")
                return str(output_path)
            else:
                self.logger.error(f"Failed to generate audio for {segment_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating audio for {segment_id}: {e}")
            return None
    
    def _build_timeline_structure(self, tts_script: Dict, audio_files: Dict[str, str], output_name: str) -> Dict:
        """
        Build the timeline structure
        
        Args:
            tts_script: TTS-ready script data
            audio_files: Generated audio file paths
            output_name: Base output name
            
        Returns:
            Timeline structure data
        """
        episode_info = tts_script.get('episode_info', {})
        script_structure = tts_script.get('script_structure', {})
        
        timeline_data = {
            'episode_info': episode_info,
            'output_name': output_name,
            'creation_timestamp': datetime.now().isoformat(),
            'timeline_segments': [],
            'total_duration': 0.0,
            'audio_files': audio_files,
            'video_files_needed': [],
            'assembly_order': []
        }
        
        segment_index = 0
        
        # Add intro segment
        intro = script_structure.get('intro', {})
        if intro:
            intro_segment = {
                'index': segment_index,
                'type': 'narrator',
                'segment_name': 'intro',
                'audio_file': audio_files.get('intro'),
                'script': intro.get('script', ''),
                'voice_style': intro.get('voice_style', 'enthusiastic'),
                'video_instruction': intro.get('video_instruction', 'Host speaking'),
                'estimated_duration': intro.get('estimated_duration', 0.0),
                'start_time': 0.0,
                'end_time': 0.0  # Will be calculated later
            }
            timeline_data['timeline_segments'].append(intro_segment)
            timeline_data['assembly_order'].append({
                'type': 'audio',
                'segment_index': segment_index,
                'file_path': audio_files.get('intro')
            })
            segment_index += 1
        
        # Add clip segments
        clip_segments = script_structure.get('clip_segments', [])
        for i, clip_segment in enumerate(clip_segments):
            
            # Pre-clip segment
            pre_clip = clip_segment.get('pre_clip', {})
            if pre_clip:
                pre_segment = {
                    'index': segment_index,
                    'type': 'narrator',
                    'segment_name': f'pre_clip_{i+1}',
                    'audio_file': audio_files.get(f'clip_segment_{i+1}_pre'),
                    'script': pre_clip.get('script', ''),
                    'voice_style': pre_clip.get('voice_style', 'normal'),
                    'video_instruction': pre_clip.get('video_instruction', 'Host speaking'),
                    'estimated_duration': pre_clip.get('estimated_duration', 0.0),
                    'start_time': 0.0,
                    'end_time': 0.0
                }
                timeline_data['timeline_segments'].append(pre_segment)
                timeline_data['assembly_order'].append({
                    'type': 'audio',
                    'segment_index': segment_index,
                    'file_path': audio_files.get(f'clip_segment_{i+1}_pre')
                })
                segment_index += 1
            
            # Video clip segment
            clip_reference = clip_segment.get('clip_reference', {})
            if clip_reference:
                video_segment = {
                    'index': segment_index,
                    'type': 'video_clip',
                    'segment_name': f'video_clip_{i+1}',
                    'clip_id': clip_reference.get('clip_id', f'clip_{i+1}'),
                    'start_time_in_source': clip_reference.get('start_time', '0:00:00'),
                    'end_time_in_source': clip_reference.get('end_time', '0:00:30'),
                    'clip_duration': clip_reference.get('duration', 30.0),
                    'video_file_needed': f"{clip_reference.get('clip_id', f'clip_{i+1}')}.mp4",
                    'start_time': 0.0,
                    'end_time': 0.0
                }
                timeline_data['timeline_segments'].append(video_segment)
                timeline_data['video_files_needed'].append(video_segment['video_file_needed'])
                timeline_data['assembly_order'].append({
                    'type': 'video',
                    'segment_index': segment_index,
                    'clip_id': clip_reference.get('clip_id'),
                    'file_path': f"{self.video_clips_dir}/{video_segment['video_file_needed']}"
                })
                segment_index += 1
            
            # Post-clip segment
            post_clip = clip_segment.get('post_clip', {})
            if post_clip:
                post_segment = {
                    'index': segment_index,
                    'type': 'narrator',
                    'segment_name': f'post_clip_{i+1}',
                    'audio_file': audio_files.get(f'clip_segment_{i+1}_post'),
                    'script': post_clip.get('script', ''),
                    'voice_style': post_clip.get('voice_style', 'sarcastic'),
                    'video_instruction': post_clip.get('video_instruction', 'Host reacting'),
                    'estimated_duration': post_clip.get('estimated_duration', 0.0),
                    'start_time': 0.0,
                    'end_time': 0.0
                }
                timeline_data['timeline_segments'].append(post_segment)
                timeline_data['assembly_order'].append({
                    'type': 'audio',
                    'segment_index': segment_index,
                    'file_path': audio_files.get(f'clip_segment_{i+1}_post')
                })
                segment_index += 1
        
        # Add outro segment
        outro = script_structure.get('outro', {})
        if outro:
            outro_segment = {
                'index': segment_index,
                'type': 'narrator',
                'segment_name': 'outro',
                'audio_file': audio_files.get('outro'),
                'script': outro.get('script', ''),
                'voice_style': outro.get('voice_style', 'normal'),
                'video_instruction': outro.get('video_instruction', 'Host closing'),
                'estimated_duration': outro.get('estimated_duration', 0.0),
                'start_time': 0.0,
                'end_time': 0.0
            }
            timeline_data['timeline_segments'].append(outro_segment)
            timeline_data['assembly_order'].append({
                'type': 'audio',
                'segment_index': segment_index,
                'file_path': audio_files.get('outro')
            })
        
        return timeline_data
    
    def _calculate_timeline_timing(self, timeline_data: Dict) -> Dict:
        """
        Calculate timing for all timeline segments
        
        Args:
            timeline_data: Timeline structure data
            
        Returns:
            Timeline data with calculated timing
        """
        current_time = 0.0
        
        for segment in timeline_data['timeline_segments']:
            segment['start_time'] = current_time
            
            # Get actual duration
            if segment['type'] == 'narrator' and segment.get('audio_file'):
                actual_duration = self._get_audio_duration(segment['audio_file'])
                if actual_duration > 0:
                    segment['actual_duration'] = actual_duration
                    duration = actual_duration
                else:
                    duration = segment.get('estimated_duration', 10.0)  # Fallback
            elif segment['type'] == 'video_clip':
                duration = segment.get('clip_duration', 30.0)
                segment['actual_duration'] = duration
            else:
                duration = segment.get('estimated_duration', 10.0)
                segment['actual_duration'] = duration
            
            segment['end_time'] = current_time + duration
            current_time += duration
        
        timeline_data['total_duration'] = current_time
        return timeline_data
    
    def _get_audio_duration(self, audio_file_path: str) -> float:
        """
        Get duration of an audio file
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            Duration in seconds
        """
        try:
            if not audio_file_path or not os.path.exists(audio_file_path):
                return 0.0
                
            # Try wave module for WAV files
            import wave
            with wave.open(audio_file_path, 'r') as wav_file:
                frames = wav_file.getnframes()
                sample_rate = wav_file.getframerate()
                return frames / sample_rate
                
        except Exception as e:
            self.logger.warning(f"Could not get duration for {audio_file_path}: {e}")
            return 0.0
    
    def _generate_editing_instructions(self, timeline_data: Dict) -> Dict:
        """
        Generate video editing instructions
        
        Args:
            timeline_data: Complete timeline data
            
        Returns:
            Editing instructions dictionary
        """
        instructions = {
            'project_name': timeline_data['output_name'],
            'total_duration': timeline_data['total_duration'],
            'sequence_resolution': '1920x1080',
            'frame_rate': 30,
            'audio_tracks': [],
            'video_tracks': [],
            'assembly_sequence': timeline_data['assembly_order'],
            'export_settings': {
                'format': 'MP4',
                'codec': 'H.264',
                'quality': 'High',
                'audio_codec': 'AAC'
            }
        }
        
        # Build audio track instructions
        audio_track = {
            'track_name': 'Narrator Audio',
            'track_number': 1,
            'segments': []
        }
        
        for segment in timeline_data['timeline_segments']:
            if segment['type'] == 'narrator' and segment.get('audio_file'):
                audio_track['segments'].append({
                    'start_time': segment['start_time'],
                    'end_time': segment['end_time'],
                    'duration': segment.get('actual_duration', 0.0),
                    'audio_file': segment['audio_file'],
                    'segment_name': segment['segment_name']
                })
        
        instructions['audio_tracks'].append(audio_track)
        
        # Build video track instructions
        video_track = {
            'track_name': 'Main Video',
            'track_number': 1,
            'segments': []
        }
        
        for segment in timeline_data['timeline_segments']:
            if segment['type'] == 'video_clip':
                video_track['segments'].append({
                    'start_time': segment['start_time'],
                    'end_time': segment['end_time'],
                    'duration': segment.get('actual_duration', 0.0),
                    'video_file_needed': segment['video_file_needed'],
                    'clip_id': segment['clip_id'],
                    'source_start': segment['start_time_in_source'],
                    'source_end': segment['end_time_in_source']
                })
            else:
                # For narrator segments, use static video or B-roll
                video_track['segments'].append({
                    'start_time': segment['start_time'],
                    'end_time': segment['end_time'],
                    'duration': segment.get('actual_duration', 0.0),
                    'video_instruction': segment.get('video_instruction', 'Host speaking'),
                    'segment_type': 'narrator_video'
                })
        
        instructions['video_tracks'].append(video_track)
        
        return instructions
    
    def _save_timeline_data(self, timeline_data: Dict, output_name: str) -> str:
        """
        Save timeline data to JSON file
        
        Args:
            timeline_data: Complete timeline data
            output_name: Base output name
            
        Returns:
            Path to saved timeline file
        """
        timeline_filename = f"{output_name}_timeline.json"
        timeline_path = self.timeline_output_dir / timeline_filename
        
        try:
            with open(timeline_path, 'w', encoding='utf-8') as f:
                json.dump(timeline_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Timeline saved to: {timeline_path}")
            return str(timeline_path)
            
        except Exception as e:
            self.logger.error(f"Error saving timeline data: {e}")
            raise
    
    def _make_safe_filename(self, text: str) -> str:
        """Convert text to safe filename"""
        import re
        safe = re.sub(r'[^\w\s-]', '', text)
        safe = re.sub(r'[-\s]+', '_', safe)
        return safe.strip('_')
    
    def generate_editing_project_files(self, timeline_path: str, target_editor: str = 'davinci') -> Dict[str, str]:
        """
        Generate project files for specific video editors
        
        Args:
            timeline_path: Path to timeline JSON file
            target_editor: Target video editor ('davinci', 'premiere', 'generic')
            
        Returns:
            Dictionary of generated project file paths
        """
        try:
            with open(timeline_path, 'r', encoding='utf-8') as f:
                timeline_data = json.load(f)
            
            project_files = {}
            
            if target_editor.lower() == 'davinci':
                project_files['davinci'] = self._generate_davinci_project(timeline_data)
            elif target_editor.lower() == 'premiere':
                project_files['premiere'] = self._generate_premiere_project(timeline_data)
            else:
                # Generic XML format
                project_files['generic'] = self._generate_generic_xml(timeline_data)
            
            return project_files
            
        except Exception as e:
            self.logger.error(f"Error generating project files: {e}")
            return {}
    
    def _generate_davinci_project(self, timeline_data: Dict) -> str:
        """Generate DaVinci Resolve project data"""
        # This would generate DaVinci Resolve XML format
        # For now, return a simplified instruction file
        
        output_name = timeline_data['output_name']
        instructions_path = self.timeline_output_dir / f"{output_name}_davinci_instructions.txt"
        
        instructions = []
        instructions.append("DaVinci Resolve Project Instructions")
        instructions.append("=" * 40)
        instructions.append(f"Project: {timeline_data['episode_info'].get('title', 'Unknown')}")
        instructions.append(f"Total Duration: {timeline_data['total_duration']:.1f} seconds")
        instructions.append("")
        
        instructions.append("Timeline Assembly Order:")
        for i, order_item in enumerate(timeline_data['assembly_order']):
            instructions.append(f"{i+1}. {order_item['type'].upper()}: {order_item.get('file_path', 'N/A')}")
        
        instructions.append("")
        instructions.append("Audio Files to Import:")
        for key, path in timeline_data['audio_files'].items():
            instructions.append(f"  {key}: {path}")
        
        instructions.append("")
        instructions.append("Video Files Needed:")
        for video_file in timeline_data['video_files_needed']:
            instructions.append(f"  {video_file}")
        
        with open(instructions_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(instructions))
        
        return str(instructions_path)
    
    def _generate_premiere_project(self, timeline_data: Dict) -> str:
        """Generate Adobe Premiere project data"""
        # Similar to DaVinci but for Premiere Pro
        output_name = timeline_data['output_name']
        instructions_path = self.timeline_output_dir / f"{output_name}_premiere_instructions.txt"
        
        # Implementation similar to DaVinci but with Premiere-specific instructions
        instructions = ["Adobe Premiere Pro Project Instructions", "=" * 40]
        # ... similar implementation
        
        with open(instructions_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(instructions))
        
        return str(instructions_path)
    
    def _generate_generic_xml(self, timeline_data: Dict) -> str:
        """Generate generic XML timeline format"""
        output_name = timeline_data['output_name']
        xml_path = self.timeline_output_dir / f"{output_name}_timeline.xml"
        
        # Generate a simple XML representation
        xml_content = []
        xml_content.append('<?xml version="1.0" encoding="UTF-8"?>')
        xml_content.append('<timeline>')
        xml_content.append(f'  <project_name>{output_name}</project_name>')
        xml_content.append(f'  <total_duration>{timeline_data["total_duration"]}</total_duration>')
        
        xml_content.append('  <segments>')
        for segment in timeline_data['timeline_segments']:
            xml_content.append(f'    <segment index="{segment["index"]}" type="{segment["type"]}">')
            xml_content.append(f'      <start_time>{segment["start_time"]}</start_time>')
            xml_content.append(f'      <end_time>{segment["end_time"]}</end_time>')
            if segment.get('audio_file'):
                xml_content.append(f'      <audio_file>{segment["audio_file"]}</audio_file>')
            if segment.get('video_file_needed'):
                xml_content.append(f'      <video_file>{segment["video_file_needed"]}</video_file>')
            xml_content.append('    </segment>')
        xml_content.append('  </segments>')
        xml_content.append('</timeline>')
        
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(xml_content))
        
        return str(xml_path)

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Test the timeline builder
    print("Timeline Builder Test")
    print("=" * 40)
    
    try:
        builder = TimelineBuilder()
        
        # Test with a TTS-ready script (we'll need to create or use an existing one)
        tts_script_path = "path/to/tts_ready_script.json"  # This would be from your TTS workflow
        
        print(f"Builder initialized successfully")
        print(f"Audio output directory: {builder.audio_output_dir}")
        print(f"Timeline output directory: {builder.timeline_output_dir}")
        
        # Additional test implementation would go here
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
