"""
Database Utilities for YouTube Pipeline UI
==========================================

Utility functions for database operations, session management,
and preset configuration handling.

Created: June 20, 2025
Agent: Implementation Agent
Task Reference: Phase 1, Task 1.2 - Database Models & Session Management
"""

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

from .models import db, PipelineSession, PresetConfiguration


class SessionManager:
    """Manages pipeline session operations."""
    
    @staticmethod
    def create_session(episode_path: str, episode_title: str = None, 
                      show_name: str = None, preset_id: str = None) -> PipelineSession:
        """
        Create a new pipeline session for an episode.
        
        Args:
            episode_path: Full path to the episode directory
            episode_title: Human-readable episode title
            show_name: Name of the show/series
            preset_id: Optional preset configuration ID
            
        Returns:
            Created PipelineSession instance
        """
        session_id = str(uuid.uuid4())
        
        # Extract show name and episode title from path if not provided
        path_obj = Path(episode_path)
        if not show_name and len(path_obj.parts) >= 2:
            show_name = path_obj.parts[-2]  # Parent directory
        if not episode_title:
            episode_title = path_obj.name  # Episode directory name
        
        session = PipelineSession(
            session_id=session_id,
            episode_path=str(episode_path),
            episode_title=episode_title,
            show_name=show_name,
            preset_id=preset_id,
            status='initialized',
            started_at=datetime.utcnow()
        )
        
        db.session.add(session)
        db.session.commit()
        
        return session
    
    @staticmethod
    def get_session(session_id: str) -> Optional[PipelineSession]:
        """Get session by ID."""
        return PipelineSession.query.filter_by(session_id=session_id).first()
    
    @staticmethod
    def get_sessions_by_episode(episode_path: str) -> List[PipelineSession]:
        """Get all sessions for a specific episode."""
        return PipelineSession.query.filter_by(episode_path=str(episode_path)).all()
    
    @staticmethod
    def get_active_sessions() -> List[PipelineSession]:
        """Get all currently active (running) sessions."""
        return PipelineSession.query.filter_by(status='running').all()
    
    @staticmethod
    def update_session_stage(session_id: str, stage_key: str, status: str) -> bool:
        """
        Update the status of a specific pipeline stage.
        
        Args:
            session_id: Session identifier
            stage_key: Stage key (e.g., 'stage_1_audio_extraction')
            status: New status ('pending', 'in_progress', 'completed', 'failed')
            
        Returns:
            True if update successful, False otherwise
        """
        session = SessionManager.get_session(session_id)
        if not session:
            return False
        
        session.update_stage_status(stage_key, status)
        
        # Update current stage if this stage is completed
        if status == 'completed':
            stage_num = int(stage_key.split('_')[1])
            if stage_num >= session.current_stage:
                session.current_stage = min(stage_num + 1, 7)
        
        # Update overall session status
        if status == 'failed':
            session.status = 'failed'
            session.last_error_stage = int(stage_key.split('_')[1])
        elif all(s == 'completed' for s in session.stage_status.values()):
            session.status = 'completed'
            session.completed_at = datetime.utcnow()
        elif any(s == 'in_progress' for s in session.stage_status.values()):
            session.status = 'running'
        
        db.session.commit()
        return True
    
    @staticmethod
    def delete_session(session_id: str) -> bool:
        """Delete a session."""
        session = SessionManager.get_session(session_id)
        if session:
            db.session.delete(session)
            db.session.commit()
            return True
        return False


class PresetManager:
    """Manages preset configuration operations."""
    
    @staticmethod
    def create_preset(name: str, configuration: Dict[str, Any], 
                     description: str = None, category: str = 'custom') -> PresetConfiguration:
        """
        Create a new preset configuration.
        
        Args:
            name: Unique preset name
            configuration: Configuration dictionary
            description: Optional description
            category: Preset category ('custom', 'system', 'template')
            
        Returns:
            Created PresetConfiguration instance
        """
        preset_id = str(uuid.uuid4())
        
        preset = PresetConfiguration(
            preset_id=preset_id,
            preset_name=name,
            description=description,
            category=category,
            configuration_json=configuration
        )
        
        db.session.add(preset)
        db.session.commit()
        
        return preset
    
    @staticmethod
    def get_preset(preset_id: str) -> Optional[PresetConfiguration]:
        """Get preset by ID."""
        return PresetConfiguration.query.filter_by(preset_id=preset_id).first()
    
    @staticmethod
    def get_preset_by_name(name: str) -> Optional[PresetConfiguration]:
        """Get preset by name."""
        return PresetConfiguration.query.filter_by(preset_name=name).first()
    
    @staticmethod
    def get_all_presets(category: str = None) -> List[PresetConfiguration]:
        """Get all presets, optionally filtered by category."""
        query = PresetConfiguration.query
        if category:
            query = query.filter_by(category=category)
        return query.order_by(PresetConfiguration.preset_name).all()
    
    @staticmethod
    def update_preset(preset_id: str, **updates) -> bool:
        """Update preset configuration."""
        preset = PresetManager.get_preset(preset_id)
        if not preset:
            return False
        
        for key, value in updates.items():
            if hasattr(preset, key):
                setattr(preset, key, value)
        
        preset.updated_at = datetime.utcnow()
        db.session.commit()
        return True
    
    @staticmethod
    def delete_preset(preset_id: str) -> bool:
        """Delete a preset configuration."""
        preset = PresetManager.get_preset(preset_id)
        if preset:
            db.session.delete(preset)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def use_preset(preset_id: str) -> bool:
        """Mark preset as used (increment usage counter)."""
        preset = PresetManager.get_preset(preset_id)
        if preset:
            preset.increment_usage()
            db.session.commit()
            return True
        return False


class EpisodeDiscovery:
    """Utilities for discovering and managing episode directories."""
    
    @staticmethod
    def discover_episodes(content_dir: Path) -> List[Dict[str, str]]:
        """
        Discover all episode directories in the content structure.
        
        Expected structure: Content/{Show}/{Episode}/
        
        Args:
            content_dir: Path to the Content directory
            
        Returns:
            List of episode information dictionaries
        """
        episodes = []
        
        if not content_dir.exists():
            return episodes
        
        for show_dir in content_dir.iterdir():
            if not show_dir.is_dir():
                continue
                
            for episode_dir in show_dir.iterdir():
                if not episode_dir.is_dir():
                    continue
                
                episode_info = {
                    'show_name': show_dir.name,
                    'episode_name': episode_dir.name,
                    'episode_path': str(episode_dir),
                    'processing_dir': str(episode_dir / 'Processing'),
                    'has_processing_dir': (episode_dir / 'Processing').exists(),
                    'session_exists': len(SessionManager.get_sessions_by_episode(str(episode_dir))) > 0
                }
                episodes.append(episode_info)
        
        return episodes
    
    @staticmethod
    def get_episode_status(episode_path: str) -> Dict[str, Any]:
        """
        Get processing status for an episode.
        
        Args:
            episode_path: Path to episode directory
            
        Returns:
            Status information dictionary
        """
        sessions = SessionManager.get_sessions_by_episode(episode_path)
        
        if not sessions:
            return {
                'status': 'not_started',
                'progress': 0,
                'current_stage': 1,
                'last_session': None
            }
        
        latest_session = max(sessions, key=lambda s: s.updated_at)
        
        return {
            'status': latest_session.status,
            'progress': latest_session.progress_percentage,
            'current_stage': latest_session.current_stage,
            'current_stage_name': latest_session.get_current_stage_name(),
            'last_session': latest_session.session_id,
            'session_count': len(sessions)
        }


def validate_database_connection() -> bool:
    """Validate that database connection is working."""
    try:
        # Simple query to test connection
        db.session.execute(db.text('SELECT 1'))
        return True
    except Exception:
        return False


def get_database_stats() -> Dict[str, Any]:
    """Get database statistics."""
    try:
        session_count = PipelineSession.query.count()
        preset_count = PresetConfiguration.query.count()
        active_sessions = PipelineSession.query.filter_by(status='running').count()
        completed_sessions = PipelineSession.query.filter_by(status='completed').count()
        
        return {
            'total_sessions': session_count,
            'total_presets': preset_count,
            'active_sessions': active_sessions,
            'completed_sessions': completed_sessions,
            'database_connected': True
        }
    except Exception as e:
        return {
            'database_connected': False,
            'error': str(e)
        }
