"""
Script Parser for Video Editor
Parses script JSON files and extracts timeline information for video editing
"""

import json
import re
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import logging

class ScriptParser:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def parse_script_file(self, script_path: str) -> Dict:
        """
        Parse a script JSON file and extract timeline information
        
        Args:
            script_path: Path to the script JSON file
            
        Returns:
            Dictionary containing parsed timeline data
        """
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                script_data = json.load(f)
                
            return self._extract_timeline_data(script_data)
            
        except Exception as e:
            self.logger.error(f"Error parsing script file {script_path}: {e}")
            raise
    
    def _extract_timeline_data(self, script_data: Dict) -> Dict:
        """
        Extract timeline information from parsed script data
        
        Args:
            script_data: Parsed JSON script data
            
        Returns:
            Structured timeline data
        """
        timeline = {
            'episode_info': self._extract_episode_info(script_data),
            'clips': self._extract_clip_info(script_data),
            'script_segments': self._extract_script_segments(script_data),
            'timeline_order': []
        }
        
        # Build timeline order
        timeline['timeline_order'] = self._build_timeline_order(timeline)
        
        return timeline
    
    def _extract_episode_info(self, script_data: Dict) -> Dict:
        """Extract episode information for file naming"""
        # Get episode info from metadata or generate from script
        episode_info = {
            'title': script_data.get('episode_title', 'Unknown Episode'),
            'episode_number': '001',  # Default, could be extracted from title
            'initials': 'UNK',  # Default, could be extracted from title
            'theme': script_data.get('narrative_theme', 'General')
        }
        
        # Try to extract episode info from title if available
        if 'generation_metadata' in script_data:
            title = script_data['generation_metadata'].get('episode_title', '')
            if title:
                episode_info.update(self._parse_episode_title(title))
        
        return episode_info
    
    def _parse_episode_title(self, title: str) -> Dict:
        """
        Parse episode title to extract number and initials
        Example: "Joe Rogan Experience 2325 - Aaron Rodgers" -> JRE2325-AR
        """
        info = {}
        
        # Try to extract episode number
        number_match = re.search(r'(\d+)', title)
        if number_match:
            info['episode_number'] = number_match.group(1)
        
        # Try to extract initials based on common patterns
        if 'Joe Rogan Experience' in title:
            # Extract guest initials from "Joe Rogan Experience XXXX - Guest Name"
            guest_match = re.search(r'Joe Rogan Experience \d+ - (.+)', title)
            if guest_match:
                guest_name = guest_match.group(1).strip()
                guest_initials = ''.join([word[0].upper() for word in guest_name.split() if word])
                info['initials'] = f"JRE{info.get('episode_number', '000')}-{guest_initials}"
            else:
                info['initials'] = f"JRE{info.get('episode_number', '000')}"
        else:
            # Generic pattern for other shows
            words = title.split()
            initials = ''.join([word[0].upper() for word in words[:3] if word])
            info['initials'] = f"{initials}{info.get('episode_number', '000')}"
        
        return info
    
    def _extract_clip_info(self, script_data: Dict) -> List[Dict]:
        """Extract video clip information"""
        clips = []
        
        if 'selected_clips' in script_data:
            for i, clip in enumerate(script_data['selected_clips']):
                clip_info = {
                    'index': i + 1,
                    'clip_id': clip.get('clip_id', f'clip_{i+1}'),
                    'title': clip.get('title', f'Clip {i+1}'),
                    'start_time': clip.get('start_time', '0:00:00'),
                    'end_time': clip.get('end_time', '0:00:30'),
                    'duration': self._calculate_duration(
                        clip.get('start_time', '0:00:00'),
                        clip.get('end_time', '0:00:30')
                    ),
                    'safe_filename': self._make_safe_filename(clip.get('clip_id', f'clip_{i+1}'))
                }
                clips.append(clip_info)
        
        return clips
    
    def _extract_script_segments(self, script_data: Dict) -> Dict:
        """Extract narrator script segments"""
        full_script = script_data.get('full_script', '')
        
        segments = {
            'intro': '',
            'pre_clip_setups': [],
            'post_clip_analyses': [],
            'conclusion': ''
        }
        
        # Parse the full script to extract segments
        if full_script:
            segments = self._parse_full_script(full_script)
        
        return segments
    
    def _parse_full_script(self, full_script: str) -> Dict:
        """Parse the full script text to extract individual segments"""
        segments = {
            'intro': '',
            'pre_clip_setups': [],
            'post_clip_analyses': [],
            'conclusion': ''
        }
        
        # Split script by major sections
        lines = full_script.split('\n')
        current_section = None
        current_text = []
        clip_counter = 0
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('### INTRO'):
                current_section = 'intro'
                current_text = []
            elif line.startswith('**PRE-CLIP SETUP:**'):
                # Save intro if we were building it
                if current_section == 'intro':
                    segments['intro'] = '\n'.join(current_text).strip()
                current_section = 'pre_clip'
                current_text = []
            elif line.startswith('**[CLIP_MARKER:'):
                # Save pre-clip setup
                if current_section == 'pre_clip':
                    segments['pre_clip_setups'].append('\n'.join(current_text).strip())
                current_section = 'clip_marker'
                current_text = []
            elif line.startswith('**POST-CLIP ANALYSIS:**'):
                current_section = 'post_clip'
                current_text = []
            elif line.startswith('### CONCLUSION'):
                # Save the last post-clip analysis
                if current_section == 'post_clip':
                    segments['post_clip_analyses'].append('\n'.join(current_text).strip())
                current_section = 'conclusion'
                current_text = []
            elif line.startswith('### CLIP') and 'CLIP_MARKER' not in line:
                # Skip clip headers
                continue
            else:
                # Add content to current section
                if current_section and line:
                    current_text.append(line)
        
        # Save the final section
        if current_section == 'conclusion':
            segments['conclusion'] = '\n'.join(current_text).strip()
        elif current_section == 'post_clip':
            segments['post_clip_analyses'].append('\n'.join(current_text).strip())
        elif current_section == 'intro':
            segments['intro'] = '\n'.join(current_text).strip()
        
        return segments
    
    def _build_timeline_order(self, timeline_data: Dict) -> List[Dict]:
        """Build the sequential timeline order"""
        timeline_order = []
        
        # Add intro
        timeline_order.append({
            'type': 'narrator',
            'segment': 'intro',
            'text': timeline_data['script_segments']['intro']
        })
        
        # Add clips with pre/post commentary
        clips = timeline_data['clips']
        pre_setups = timeline_data['script_segments']['pre_clip_setups']
        post_analyses = timeline_data['script_segments']['post_clip_analyses']
        
        for i, clip in enumerate(clips):
            # Add pre-clip setup
            if i < len(pre_setups):
                timeline_order.append({
                    'type': 'narrator',
                    'segment': 'pre_clip',
                    'clip_index': i + 1,
                    'clip_name': clip['safe_filename'],
                    'text': pre_setups[i]
                })
            
            # Add video clip
            timeline_order.append({
                'type': 'video_clip',
                'clip_index': i + 1,
                'clip_data': clip
            })
            
            # Add post-clip analysis
            if i < len(post_analyses):
                timeline_order.append({
                    'type': 'narrator',
                    'segment': 'post_clip',
                    'clip_index': i + 1,
                    'clip_name': clip['safe_filename'],
                    'text': post_analyses[i]
                })
        
        # Add conclusion
        timeline_order.append({
            'type': 'narrator',
            'segment': 'conclusion',
            'text': timeline_data['script_segments']['conclusion']
        })
        
        return timeline_order
    
    def _calculate_duration(self, start_time: str, end_time: str) -> float:
        """Calculate duration in seconds from start and end times"""
        try:
            start_seconds = self._time_to_seconds(start_time)
            end_seconds = self._time_to_seconds(end_time)
            return max(0, end_seconds - start_seconds)
        except:
            return 30.0  # Default duration
    
    def _time_to_seconds(self, time_str: str) -> float:
        """Convert time string (H:MM:SS or MM:SS) to seconds"""
        parts = time_str.split(':')
        if len(parts) == 3:  # H:MM:SS
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2:  # MM:SS
            return int(parts[0]) * 60 + int(parts[1])
        else:
            return 0.0
    
    def _make_safe_filename(self, text: str) -> str:
        """Convert text to safe filename"""
        # Remove special characters and replace spaces with underscores
        safe = re.sub(r'[^\w\s-]', '', text)
        safe = re.sub(r'[-\s]+', '_', safe)
        return safe.strip('_')
    
    def generate_audio_filenames(self, timeline_data: Dict) -> Dict[str, str]:
        """
        Generate the expected audio filenames for each segment
        
        Returns:
            Dictionary mapping segment types to expected filenames
        """
        episode_info = timeline_data['episode_info']
        episode_num = episode_info['episode_number']
        initials = episode_info['initials']
        
        filenames = {}
        
        # Intro filename
        filenames['intro'] = f"intro_{episode_num}_{initials}.wav"
        
        # Conclusion filename
        filenames['conclusion'] = f"conclusion_{episode_num}_{initials}.wav"
        
        # Pre-clip and post-clip filenames
        filenames['pre_clips'] = []
        filenames['post_clips'] = []
        
        for clip in timeline_data['clips']:
            clip_index = str(clip['index']).zfill(3)
            clip_name = clip['safe_filename']
            
            pre_filename = f"pre_clip_{clip_index}_{episode_num}_{clip_name}_{initials}.wav"
            post_filename = f"post_clip_{clip_index}_{episode_num}_{clip_name}_{initials}.wav"
            
            filenames['pre_clips'].append(pre_filename)
            filenames['post_clips'].append(post_filename)
        
        return filenames

if __name__ == "__main__":
    # Test with the existing script file
    parser = ScriptParser()
    script_path = r"C:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Content\Scripts\Joe_Rogan_Experience\test_podcast_script.json"
    
    try:
        timeline_data = parser.parse_script_file(script_path)
        filenames = parser.generate_audio_filenames(timeline_data)
        
        print("Episode Info:", timeline_data['episode_info'])
        print("\nClips:", len(timeline_data['clips']))
        print("\nTimeline Order:", len(timeline_data['timeline_order']))
        print("\nExpected Audio Filenames:")
        for key, value in filenames.items():
            print(f"  {key}: {value}")
            
    except Exception as e:
        print(f"Error: {e}")
