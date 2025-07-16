"""
File Monitor Service
===================

Real-time file monitoring service for detecting pipeline stage completion
and tracking output file creation. Provides file system watching capabilities
for stage completion detection and progress updates.

Created: June 20, 2025
Agent: Agent_Pipeline_Integration
Task Reference: Phase 2, Task 2.1 - Master Processor Integration
"""

import os
import time
import json
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Set
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class PipelineFileMonitor:
    """
    File monitoring service for pipeline stage completion detection.
    
    Monitors expected output files for each stage:
    - Stage 1: Audio/video files in Input directory
    - Stage 2: original_audio_transcript.json in Processing
    - Stage 3: original_audio_analysis_results.json in Processing
    - Stage 4: unified_podcast_script.json in Output/Scripts
    - Stage 5: Audio files in Output/Audio
    - Stage 6: Video clips in Output/Clips
    - Stage 7: Final video in Output
    """
    
    def __init__(self, episode_directory: str, callback: Optional[Callable] = None):
        """
        Initialize file monitor for specific episode directory.
        
        Args:
            episode_directory: Path to episode directory to monitor
            callback: Optional callback function for file events
        """
        self.episode_directory = Path(episode_directory)
        self.callback = callback
        self.logger = self._setup_logging()
        
        # File monitoring state
        self.observer = None
        self.is_monitoring = False
        self.monitored_files = set()
        self.stage_completion_status = {}
        
        # Expected files for each stage
        self.stage_file_patterns = {
            1: {
                'patterns': ['Input/*.mp3', 'Input/*.wav', 'Input/*.mp4'],
                'description': 'Media extraction files'
            },
            2: {
                'patterns': ['Processing/original_audio_transcript.json'],
                'description': 'Transcript generation'
            },
            3: {
                'patterns': ['Processing/original_audio_analysis_results.json'],
                'description': 'Content analysis results'
            },
            4: {
                'patterns': ['Output/Scripts/unified_podcast_script.json'],
                'description': 'Narrative generation script'
            },
            5: {
                'patterns': ['Output/Audio/*.wav', 'Output/Audio/*.mp3'],
                'description': 'Generated audio files'
            },
            6: {
                'patterns': ['Output/Clips/*.mp4'],
                'description': 'Video clips'
            },
            7: {
                'patterns': ['*_final.mp4'],
                'description': 'Final compiled video'
            }
        }
        
        # Minimum file sizes for validation (in bytes)
        self.min_file_sizes = {
            1: 1024 * 1024,  # 1MB for media files
            2: 1024,  # 1KB for JSON files
            3: 1024,  # 1KB for JSON files
            4: 1024,  # 1KB for JSON files
            5: 1024 * 100,  # 100KB for audio files
            6: 1024 * 1024,  # 1MB for video clips
            7: 1024 * 1024 * 10  # 10MB for final video
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for file monitor."""
        logger = logging.getLogger('file_monitor')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def start_monitoring(self, stages_to_monitor: List[int] = None):
        """
        Start file monitoring for specified stages.
        
        Args:
            stages_to_monitor: List of stage numbers to monitor (default: all)
        """
        try:
            if self.is_monitoring:
                self.logger.warning("File monitoring already active")
                return
            
            stages_to_monitor = stages_to_monitor or list(range(1, 8))
            
            self.logger.info(f"Starting file monitoring for episode: {self.episode_directory}")
            self.logger.info(f"Monitoring stages: {stages_to_monitor}")
            
            # Ensure episode directory exists
            if not self.episode_directory.exists():
                self.logger.warning(f"Episode directory does not exist: {self.episode_directory}")
                return
            
            # Initialize stage completion status
            for stage in stages_to_monitor:
                self.stage_completion_status[stage] = {
                    'completed': False,
                    'files_found': [],
                    'last_check': None
                }
            
            # Set up file system watcher
            event_handler = PipelineFileEventHandler(self)
            self.observer = Observer()
            self.observer.schedule(event_handler, str(self.episode_directory), recursive=True)
            self.observer.start()
            
            self.is_monitoring = True
            self.logger.info("File monitoring started successfully")
            
            # Perform initial scan
            self._perform_initial_scan(stages_to_monitor)
            
        except Exception as e:
            self.logger.error(f"Failed to start file monitoring: {e}")
            raise
    
    def stop_monitoring(self):
        """Stop file monitoring."""
        try:
            if not self.is_monitoring:
                return
            
            if self.observer:
                self.observer.stop()
                self.observer.join()
                self.observer = None
            
            self.is_monitoring = False
            self.logger.info("File monitoring stopped")
            
        except Exception as e:
            self.logger.error(f"Failed to stop file monitoring: {e}")
    
    def _perform_initial_scan(self, stages_to_monitor: List[int]):
        """
        Perform initial scan of episode directory for existing files.
        
        Args:
            stages_to_monitor: List of stage numbers to scan
        """
        try:
            self.logger.info("Performing initial file scan")
            
            for stage in stages_to_monitor:
                self._check_stage_completion(stage)
            
            self.logger.info("Initial file scan completed")
            
        except Exception as e:
            self.logger.error(f"Initial scan failed: {e}")
    
    def _check_stage_completion(self, stage: int) -> bool:
        """
        Check if files for a specific stage are complete.
        
        Args:
            stage: Stage number to check
            
        Returns:
            bool: True if stage files are complete
        """
        try:
            if stage not in self.stage_file_patterns:
                return False
            
            patterns = self.stage_file_patterns[stage]['patterns']
            min_size = self.min_file_sizes.get(stage, 0)
            
            found_files = []
            
            # Check each pattern
            for pattern in patterns:
                # Convert pattern to glob pattern
                pattern_path = self.episode_directory / pattern
                
                # Handle glob patterns
                if '*' in pattern:
                    parent_dir = pattern_path.parent
                    filename_pattern = pattern_path.name
                    
                    if parent_dir.exists():
                        for file_path in parent_dir.glob(filename_pattern):
                            if file_path.is_file() and file_path.stat().st_size >= min_size:
                                found_files.append(str(file_path))
                else:
                    # Direct file path
                    if pattern_path.exists() and pattern_path.stat().st_size >= min_size:
                        found_files.append(str(pattern_path))
            
            # Update stage status
            stage_complete = len(found_files) > 0
            
            if stage in self.stage_completion_status:
                previous_status = self.stage_completion_status[stage]['completed']
                self.stage_completion_status[stage].update({
                    'completed': stage_complete,
                    'files_found': found_files,
                    'last_check': datetime.now()
                })
                
                # Trigger callback if status changed
                if stage_complete and not previous_status:
                    self.logger.info(f"Stage {stage} completed - Files found: {found_files}")
                    if self.callback:
                        self.callback(stage, 'completed', found_files)
            
            return stage_complete
            
        except Exception as e:
            self.logger.error(f"Failed to check stage {stage} completion: {e}")
            return False
    
    def get_stage_file_info(self, stage: int) -> Dict:
        """
        Get detailed file information for a specific stage.
        
        Args:
            stage: Stage number
            
        Returns:
            Dict: File information including paths, sizes, timestamps
        """
        try:
            if stage not in self.stage_completion_status:
                return {'error': f'Stage {stage} not monitored'}
            
            status = self.stage_completion_status[stage]
            file_details = []
            
            for file_path in status['files_found']:
                path_obj = Path(file_path)
                if path_obj.exists():
                    stat = path_obj.stat()
                    file_details.append({
                        'path': str(file_path),
                        'size': stat.st_size,
                        'size_mb': round(stat.st_size / (1024 * 1024), 2),
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'created': datetime.fromtimestamp(stat.st_ctime).isoformat()
                    })
            
            return {
                'stage': stage,
                'completed': status['completed'],
                'files_count': len(status['files_found']),
                'files': file_details,
                'last_check': status['last_check'].isoformat() if status['last_check'] else None,
                'description': self.stage_file_patterns[stage]['description']
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get stage {stage} file info: {e}")
            return {'error': str(e)}
    
    def get_all_stages_status(self) -> Dict:
        """
        Get status of all monitored stages.
        
        Returns:
            Dict: Complete status of all stages
        """
        try:
            status = {
                'episode_directory': str(self.episode_directory),
                'monitoring_active': self.is_monitoring,
                'stages': {}
            }
            
            for stage in self.stage_completion_status:
                status['stages'][stage] = self.get_stage_file_info(stage)
            
            return status
            
        except Exception as e:
            self.logger.error(f"Failed to get all stages status: {e}")
            return {'error': str(e)}
    
    def wait_for_stage_completion(self, stage: int, timeout: int = 300) -> bool:
        """
        Wait for a specific stage to complete with timeout.
        
        Args:
            stage: Stage number to wait for
            timeout: Timeout in seconds
            
        Returns:
            bool: True if stage completed within timeout
        """
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                if self._check_stage_completion(stage):
                    return True
                time.sleep(5)  # Check every 5 seconds
            
            self.logger.warning(f"Timeout waiting for stage {stage} completion")
            return False
            
        except Exception as e:
            self.logger.error(f"Error waiting for stage {stage}: {e}")
            return False
    
    def validate_file_integrity(self, file_path: str) -> Dict:
        """
        Validate file integrity and readability.
        
        Args:
            file_path: Path to file to validate
            
        Returns:
            Dict: Validation results
        """
        try:
            path_obj = Path(file_path)
            
            if not path_obj.exists():
                return {'valid': False, 'error': 'File does not exist'}
            
            if not path_obj.is_file():
                return {'valid': False, 'error': 'Path is not a file'}
            
            stat = path_obj.stat()
            
            # Check file size
            if stat.st_size == 0:
                return {'valid': False, 'error': 'File is empty'}
            
            # Check if file is still being written (size changing)
            time.sleep(1)
            new_stat = path_obj.stat()
            if new_stat.st_size != stat.st_size:
                return {'valid': False, 'error': 'File is still being written'}
            
            # Validate JSON files
            if file_path.endswith('.json'):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        json.load(f)
                except json.JSONDecodeError:
                    return {'valid': False, 'error': 'Invalid JSON format'}
            
            return {
                'valid': True,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}


class PipelineFileEventHandler(FileSystemEventHandler):
    """
    File system event handler for pipeline file monitoring.
    """
    
    def __init__(self, monitor: PipelineFileMonitor):
        """
        Initialize event handler.
        
        Args:
            monitor: PipelineFileMonitor instance
        """
        self.monitor = monitor
        self.logger = monitor.logger
    
    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return
        
        self.logger.debug(f"File created: {event.src_path}")
        self._handle_file_event(event.src_path)
    
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
        
        self.logger.debug(f"File modified: {event.src_path}")
        self._handle_file_event(event.src_path)
    
    def _handle_file_event(self, file_path: str):
        """
        Handle file system events and check for stage completion.
        
        Args:
            file_path: Path to the file that changed
        """
        try:
            # Check all stages for completion
            for stage in self.monitor.stage_completion_status:
                self.monitor._check_stage_completion(stage)
                
        except Exception as e:
            self.logger.error(f"Error handling file event for {file_path}: {e}")


class MultiEpisodeFileMonitor:
    """
    Manager for monitoring multiple episode directories simultaneously.
    """
    
    def __init__(self, callback: Optional[Callable] = None):
        """
        Initialize multi-episode file monitor.
        
        Args:
            callback: Optional callback function for file events
        """
        self.callback = callback
        self.monitors: Dict[str, PipelineFileMonitor] = {}
        self.logger = logging.getLogger('multi_episode_monitor')
    
    def add_episode_monitor(self, episode_directory: str, stages_to_monitor: List[int] = None) -> str:
        """
        Add monitoring for a new episode directory.
        
        Args:
            episode_directory: Path to episode directory
            stages_to_monitor: List of stages to monitor
            
        Returns:
            str: Monitor ID for the episode
        """
        try:
            monitor_id = f"episode_{hash(episode_directory)}"
            
            # Create callback wrapper
            def episode_callback(stage, status, files):
                if self.callback:
                    self.callback(monitor_id, episode_directory, stage, status, files)
            
            # Create and start monitor
            monitor = PipelineFileMonitor(episode_directory, episode_callback)
            monitor.start_monitoring(stages_to_monitor)
            
            self.monitors[monitor_id] = monitor
            
            self.logger.info(f"Added episode monitor: {monitor_id} for {episode_directory}")
            
            return monitor_id
            
        except Exception as e:
            self.logger.error(f"Failed to add episode monitor: {e}")
            raise
    
    def remove_episode_monitor(self, monitor_id: str):
        """
        Remove monitoring for an episode.
        
        Args:
            monitor_id: Monitor ID to remove
        """
        try:
            if monitor_id in self.monitors:
                self.monitors[monitor_id].stop_monitoring()
                del self.monitors[monitor_id]
                self.logger.info(f"Removed episode monitor: {monitor_id}")
                
        except Exception as e:
            self.logger.error(f"Failed to remove episode monitor: {e}")
    
    def get_all_monitors_status(self) -> Dict:
        """
        Get status of all active monitors.
        
        Returns:
            Dict: Status of all monitors
        """
        try:
            status = {
                'active_monitors': len(self.monitors),
                'monitors': {}
            }
            
            for monitor_id, monitor in self.monitors.items():
                status['monitors'][monitor_id] = monitor.get_all_stages_status()
            
            return status
            
        except Exception as e:
            self.logger.error(f"Failed to get all monitors status: {e}")
            return {'error': str(e)}
    
    def stop_all_monitoring(self):
        """Stop all active monitors."""
        try:
            for monitor_id in list(self.monitors.keys()):
                self.remove_episode_monitor(monitor_id)
            
            self.logger.info("All episode monitoring stopped")
            
        except Exception as e:
            self.logger.error(f"Failed to stop all monitoring: {e}")


# Utility functions
def create_file_monitor(episode_directory: str, callback: Optional[Callable] = None) -> PipelineFileMonitor:
    """
    Factory function for creating file monitor instance.
    
    Args:
        episode_directory: Path to episode directory
        callback: Optional callback function
        
    Returns:
        PipelineFileMonitor: Configured file monitor
    """
    return PipelineFileMonitor(episode_directory, callback)


def create_multi_episode_monitor(callback: Optional[Callable] = None) -> MultiEpisodeFileMonitor:
    """
    Factory function for creating multi-episode monitor instance.
    
    Args:
        callback: Optional callback function
        
    Returns:
        MultiEpisodeFileMonitor: Configured multi-episode monitor
    """
    return MultiEpisodeFileMonitor(callback)
