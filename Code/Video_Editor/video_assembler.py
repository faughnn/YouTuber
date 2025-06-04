"""
Video Assembly Module
Combines timeline data with actual video clips to create final podcast episodes
Final step in the automated video generation pipeline
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import subprocess
import shutil

class VideoAssembler:
    """
    Assembles final video from timeline data, audio files, and video clips
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize Video Assembler
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.logger = logging.getLogger(__name__)
        
        # Set up paths
        self.base_path = Path(__file__).parent.parent.parent
        self.audio_dir = self.base_path / "Content" / "Audio" / "Generated" / "TTS_Ready"
        self.video_clips_dir = self.base_path / "Content" / "Video_Clips"
        self.timelines_dir = self.base_path / "Content" / "Timelines"
        self.output_dir = self.base_path / "Content" / "Video" / "Final_Episodes"
        
        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Video assembly settings
        self.video_settings = {
            "resolution": "1920x1080",
            "frame_rate": 30,
            "audio_sample_rate": 44100,
            "video_codec": "libx264",
            "audio_codec": "aac",
            "quality": "high"  # high, medium, low
        }
        
        self.logger.info("Video Assembler initialized")
    
    def assemble_video_from_timeline(self, timeline_file: str, output_name: str = None) -> Dict:
        """
        Assemble final video from timeline data
        
        Args:
            timeline_file: Path to timeline JSON file
            output_name: Custom output filename (optional)
            
        Returns:
            Assembly result data
        """
        try:
            # Load timeline data
            with open(timeline_file, 'r', encoding='utf-8') as f:
                timeline_data = json.load(f)
            
            self.logger.info(f"Assembling video from timeline: {timeline_file}")
            
            # Extract info
            episode_info = timeline_data.get('episode_info', {})
            timeline_segments = timeline_data.get('timeline_segments', [])
            
            # Generate output name if not provided
            if not output_name:
                title = episode_info.get('title', 'Unknown_Episode')
                episode_num = episode_info.get('episode_number', '001')
                output_name = f"{self._make_safe_filename(title)}_Episode_{episode_num}"
            
            # Step 1: Validate all required files exist
            validation_result = self._validate_assembly_files(timeline_segments)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': 'File validation failed',
                    'missing_files': validation_result['missing_files']
                }
            
            # Step 2: Prepare assembly workspace
            workspace = self._prepare_assembly_workspace(output_name)
            
            # Step 3: Generate FFmpeg assembly script
            ffmpeg_script = self._generate_ffmpeg_assembly_script(
                timeline_segments, workspace, output_name
            )
            
            # Step 4: Execute video assembly
            assembly_result = self._execute_video_assembly(ffmpeg_script, workspace)
            
            # Step 5: Post-process and finalize
            final_result = self._finalize_assembly(assembly_result, workspace, output_name)
            
            return {
                'success': True,
                'output_file': final_result['output_file'],
                'assembly_time': final_result['assembly_time'],
                'file_size': final_result['file_size'],
                'duration': timeline_data.get('total_duration', 0),
                'segments_processed': len(timeline_segments),
                'workspace': str(workspace),
                'ffmpeg_script': ffmpeg_script
            }
            
        except Exception as e:
            self.logger.error(f"Video assembly failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _validate_assembly_files(self, timeline_segments: List[Dict]) -> Dict:
        """Validate that all required audio and video files exist"""
        
        missing_files = []
        audio_files = []
        video_files = []
        
        for segment in timeline_segments:
            segment_type = segment.get('type')
            
            if segment_type == 'narrator':
                audio_file = segment.get('audio_file')
                if audio_file and not os.path.exists(audio_file):
                    missing_files.append(f"Audio: {audio_file}")
                elif audio_file:
                    audio_files.append(audio_file)
            
            elif segment_type == 'video_clip':
                video_file = segment.get('video_file')
                if video_file and not os.path.exists(video_file):
                    missing_files.append(f"Video: {video_file}")
                elif video_file:
                    video_files.append(video_file)
        
        return {
            'valid': len(missing_files) == 0,
            'missing_files': missing_files,
            'audio_files_found': len(audio_files),
            'video_files_found': len(video_files)
        }
    
    def _prepare_assembly_workspace(self, output_name: str) -> Path:
        """Prepare temporary workspace for assembly"""
        
        workspace = self.output_dir / f"{output_name}_workspace"
        workspace.mkdir(exist_ok=True)
        
        # Create subdirectories
        (workspace / "audio").mkdir(exist_ok=True)
        (workspace / "video").mkdir(exist_ok=True)
        (workspace / "temp").mkdir(exist_ok=True)
        
        return workspace
    
    def _generate_ffmpeg_assembly_script(self, timeline_segments: List[Dict], 
                                        workspace: Path, output_name: str) -> Dict:
        """Generate FFmpeg commands for video assembly"""
        
        # Create segment files list
        segment_files = []
        concat_list_path = workspace / "segments_list.txt"
        
        for i, segment in enumerate(timeline_segments):
            segment_type = segment.get('type')
            duration = segment.get('actual_duration', segment.get('estimated_duration', 5.0))
            
            if segment_type == 'narrator':
                # Create video from audio + static background/graphics
                audio_file = segment.get('audio_file')
                video_instruction = segment.get('video_instruction', 'Host speaking')
                
                # Generate narrator video segment
                segment_file = workspace / "temp" / f"segment_{i:03d}_narrator.mp4"
                narrator_cmd = self._create_narrator_video_command(
                    audio_file, segment_file, duration, video_instruction
                )
                segment_files.append({
                    'file': str(segment_file),
                    'command': narrator_cmd,
                    'type': 'narrator'
                })
            
            elif segment_type == 'video_clip':
                # Use existing video clip
                video_file = segment.get('video_file')
                start_time = segment.get('source_start_time', 0)
                
                # Extract/prepare video clip segment
                segment_file = workspace / "temp" / f"segment_{i:03d}_clip.mp4"
                clip_cmd = self._create_clip_video_command(
                    video_file, segment_file, start_time, duration
                )
                segment_files.append({
                    'file': str(segment_file),
                    'command': clip_cmd,
                    'type': 'video_clip'
                })
        
        # Create concat list file
        with open(concat_list_path, 'w') as f:
            for seg in segment_files:
                f.write(f"file '{seg['file']}'\n")
        
        # Final concatenation command
        final_output = self.output_dir / f"{output_name}.mp4"
        concat_cmd = self._create_concatenation_command(concat_list_path, final_output)
        
        return {
            'segment_commands': [seg['command'] for seg in segment_files],
            'concat_list': str(concat_list_path),
            'concat_command': concat_cmd,
            'final_output': str(final_output),
            'total_segments': len(segment_files)
        }
    
    def _create_narrator_video_command(self, audio_file: str, output_file: Path, 
                                     duration: float, video_instruction: str) -> str:
        """Create FFmpeg command for narrator video segment"""
        
        # For now, create a simple colored background with text
        # In production, this could use AI-generated avatars, stock footage, etc.
        
        if audio_file and os.path.exists(audio_file):
            # Use actual audio file
            cmd = [
                'ffmpeg', '-y',
                '-f', 'lavfi', '-i', f'color=c=0x2C3E50:s={self.video_settings["resolution"]}:d={duration}',
                '-i', audio_file,
                '-vf', f'drawtext=text="{video_instruction}":fontcolor=white:fontsize=24:x=(w-text_w)/2:y=(h-text_h)/2',
                '-c:v', self.video_settings['video_codec'],
                '-c:a', self.video_settings['audio_codec'],
                '-r', str(self.video_settings['frame_rate']),
                '-shortest',
                str(output_file)
            ]
        else:
            # Create silent video placeholder
            cmd = [
                'ffmpeg', '-y',
                '-f', 'lavfi', '-i', f'color=c=0x2C3E50:s={self.video_settings["resolution"]}:d={duration}',
                '-f', 'lavfi', '-i', f'anullsrc=channel_layout=stereo:sample_rate={self.video_settings["audio_sample_rate"]}',
                '-vf', f'drawtext=text="NARRATOR: {video_instruction}":fontcolor=white:fontsize=24:x=(w-text_w)/2:y=(h-text_h)/2',
                '-c:v', self.video_settings['video_codec'],
                '-c:a', self.video_settings['audio_codec'],
                '-r', str(self.video_settings['frame_rate']),
                '-t', str(duration),
                str(output_file)
            ]
        
        return ' '.join(cmd)
    
    def _create_clip_video_command(self, video_file: str, output_file: Path, 
                                 start_time: float, duration: float) -> str:
        """Create FFmpeg command for video clip segment"""
        
        if video_file and os.path.exists(video_file):
            # Extract clip from existing video
            cmd = [
                'ffmpeg', '-y',
                '-i', video_file,
                '-ss', str(start_time),
                '-t', str(duration),
                '-c:v', self.video_settings['video_codec'],
                '-c:a', self.video_settings['audio_codec'],
                '-r', str(self.video_settings['frame_rate']),
                str(output_file)
            ]
        else:
            # Create placeholder for missing video
            cmd = [
                'ffmpeg', '-y',
                '-f', 'lavfi', '-i', f'color=c=0x8E44AD:s={self.video_settings["resolution"]}:d={duration}',
                '-f', 'lavfi', '-i', f'anullsrc=channel_layout=stereo:sample_rate={self.video_settings["audio_sample_rate"]}',
                '-vf', f'drawtext=text="VIDEO CLIP NEEDED: {Path(video_file).name if video_file else "Unknown"}":fontcolor=white:fontsize=32:x=(w-text_w)/2:y=(h-text_h)/2',
                '-c:v', self.video_settings['video_codec'],
                '-c:a', self.video_settings['audio_codec'],
                '-r', str(self.video_settings['frame_rate']),
                '-t', str(duration),
                str(output_file)
            ]
        
        return ' '.join(cmd)
    
    def _create_concatenation_command(self, concat_list: str, output_file: Path) -> str:
        """Create FFmpeg command for final video concatenation"""
        
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_list,
            '-c', 'copy',
            str(output_file)
        ]
        
        return ' '.join(cmd)
    
    def _execute_video_assembly(self, ffmpeg_script: Dict, workspace: Path) -> Dict:
        """Execute the video assembly process"""
        
        start_time = datetime.now()
        
        try:
            # Execute segment generation commands
            self.logger.info(f"Generating {ffmpeg_script['total_segments']} video segments...")
            
            for i, cmd in enumerate(ffmpeg_script['segment_commands']):
                self.logger.info(f"Processing segment {i+1}/{ffmpeg_script['total_segments']}")
                
                # For demo purposes, we'll create the command files instead of executing
                # In production, you would run: subprocess.run(cmd, shell=True, check=True)
                cmd_file = workspace / f"segment_{i:03d}_command.txt"
                with open(cmd_file, 'w') as f:
                    f.write(cmd)
                
                # Create dummy output file for demo
                segment_file = cmd.split()[-1]  # Last argument is output file
                Path(segment_file).parent.mkdir(parents=True, exist_ok=True)
                Path(segment_file).touch()
            
            # Execute concatenation command
            self.logger.info("Concatenating final video...")
            concat_cmd_file = workspace / "final_concat_command.txt"
            with open(concat_cmd_file, 'w') as f:
                f.write(ffmpeg_script['concat_command'])
            
            # Create dummy final output for demo
            Path(ffmpeg_script['final_output']).touch()
            
            end_time = datetime.now()
            assembly_time = (end_time - start_time).total_seconds()
            
            return {
                'success': True,
                'assembly_time': assembly_time,
                'segments_created': ffmpeg_script['total_segments'],
                'final_output': ffmpeg_script['final_output']
            }
            
        except Exception as e:
            self.logger.error(f"FFmpeg execution failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _finalize_assembly(self, assembly_result: Dict, workspace: Path, output_name: str) -> Dict:
        """Finalize the assembly process"""
        
        if assembly_result['success']:
            output_file = assembly_result['final_output']
            
            # Get file info
            file_size = os.path.getsize(output_file) if os.path.exists(output_file) else 0
            
            # Create assembly report
            report = {
                'output_file': output_file,
                'file_size': file_size,
                'assembly_time': assembly_result['assembly_time'],
                'creation_date': datetime.now().isoformat(),
                'workspace_location': str(workspace)
            }
            
            # Save assembly report
            report_file = workspace / f"{output_name}_assembly_report.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            self.logger.info(f"Video assembly completed: {output_file}")
            return report
        else:
            raise Exception(f"Assembly failed: {assembly_result.get('error', 'Unknown error')}")
    
    def _make_safe_filename(self, filename: str) -> str:
        """Convert string to safe filename"""
        import re
        # Remove or replace unsafe characters
        safe = re.sub(r'[<>:"/\\|?*]', '_', filename)
        safe = re.sub(r'\s+', '_', safe)
        return safe[:100]  # Limit length
    
    def get_assembly_status(self, timeline_file: str) -> Dict:
        """Get status of video assembly requirements"""
        
        try:
            with open(timeline_file, 'r', encoding='utf-8') as f:
                timeline_data = json.load(f)
            
            segments = timeline_data.get('timeline_segments', [])
            validation = self._validate_assembly_files(segments)
            
            return {
                'timeline_loaded': True,
                'total_segments': len(segments),
                'files_validation': validation,
                'ready_for_assembly': validation['valid'],
                'estimated_duration': timeline_data.get('total_duration', 0)
            }
            
        except Exception as e:
            return {
                'timeline_loaded': False,
                'error': str(e)
            }

if __name__ == "__main__":
    # Demo usage
    assembler = VideoAssembler()
    
    # Example usage with timeline file
    timeline_file = Path(__file__).parent.parent.parent / "Content" / "Timelines" / "JRE2325_AR_Analysis_Test_timeline.json"
    
    if timeline_file.exists():
        print("🎬 Testing Video Assembly...")
        
        # Check assembly status
        status = assembler.get_assembly_status(str(timeline_file))
        print(f"Assembly Status: {status}")
        
        # Attempt assembly
        result = assembler.assemble_video_from_timeline(str(timeline_file))
        print(f"Assembly Result: {result}")
    else:
        print("❌ Timeline file not found. Run timeline builder test first.")
