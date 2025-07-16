"""
Episode Management Routes
=========================

Flask routes for episode discovery, selection, and management functionality.
Provides web interface endpoints for browsing episodes, checking status,
and initiating pipeline processing on selected episodes.

Created: June 20, 2025
Agent: Implementation Agent
Task Reference: Phase 2, Task 2.2 - Episode Management System
"""

import json
import logging
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from datetime import datetime

# Import services and models
from services.episode_manager import EpisodeManager
from services.pipeline_controller import PipelineController
from database.utils import SessionManager
from config import Config

# Create Blueprint for episode routes
episodes_bp = Blueprint('episodes', __name__, url_prefix='/episodes')

# Initialize services
episode_manager = EpisodeManager(str(Config.CONTENT_DIR))
session_manager = SessionManager()
logger = logging.getLogger(__name__)


@episodes_bp.route('/')
def episodes_dashboard():
    """Main episodes dashboard showing all available episodes."""
    try:
        # Get all episodes
        episodes = episode_manager.discover_episodes()
        
        # Get statistics
        stats = episode_manager.get_episode_statistics()
        
        # Get filter parameters
        show_filter = request.args.get('show', '')
        status_filter = request.args.get('status', '')
        search_query = request.args.get('search', '')
        
        # Apply filters
        filtered_episodes = episodes
        
        if show_filter:
            filtered_episodes = [ep for ep in filtered_episodes if ep.show_name == show_filter]
        
        if status_filter:
            filtered_episodes = [ep for ep in filtered_episodes if ep.processing_status == status_filter]
        
        if search_query:
            filtered_episodes = episode_manager.search_episodes(search_query)
            if show_filter:
                filtered_episodes = [ep for ep in filtered_episodes if ep.show_name == show_filter]
            if status_filter:
                filtered_episodes = [ep for ep in filtered_episodes if ep.processing_status == status_filter]
        
        # Sort episodes by show and then by episode number/title
        filtered_episodes.sort(key=lambda x: (x.show_name, x.episode_number or x.episode_title))
        
        return render_template('episodes.html',
                             episodes=filtered_episodes,
                             stats=stats,
                             show_filter=show_filter,
                             status_filter=status_filter,
                             search_query=search_query,
                             shows=list(stats['shows'].keys()))
    
    except Exception as e:
        logger.error(f"Error loading episodes dashboard: {e}")
        flash(f"Error loading episodes: {str(e)}", 'error')
        return render_template('episodes.html', episodes=[], stats={}, shows=[])


@episodes_bp.route('/api/episodes')
def api_get_episodes():
    """API endpoint to get episodes data as JSON."""
    try:
        episodes = episode_manager.discover_episodes()
        
        # Convert to serializable format
        episodes_data = []
        for episode in episodes:
            episode_dict = {
                'episode_id': episode.episode_id,
                'show_name': episode.show_name,
                'episode_title': episode.episode_title,
                'episode_number': episode.episode_number,
                'full_path': episode.full_path,
                'processing_status': episode.processing_status,
                'stages_completed': episode.stages_completed,
                'stages_total': episode.stages_total,
                'last_processed': episode.last_processed,
                'duration': episode.duration,
                'has_audio_analysis': episode.has_audio_analysis,
                'has_transcript': episode.has_transcript,
                'has_final_output': episode.has_final_output,
                'active_sessions': episode.active_sessions
            }
            episodes_data.append(episode_dict)
        
        return jsonify({
            'success': True,
            'episodes': episodes_data,
            'count': len(episodes_data)
        })
    
    except Exception as e:
        logger.error(f"Error in API get episodes: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@episodes_bp.route('/api/episodes/<episode_id>')
def api_get_episode(episode_id):
    """API endpoint to get specific episode data."""
    try:
        episode = episode_manager.get_episode_by_id(episode_id)
        
        if not episode:
            return jsonify({
                'success': False,
                'error': 'Episode not found'
            }), 404
        
        episode_data = {
            'episode_id': episode.episode_id,
            'show_name': episode.show_name,
            'episode_title': episode.episode_title,
            'episode_number': episode.episode_number,
            'full_path': episode.full_path,
            'processing_path': episode.processing_path,
            'input_path': episode.input_path,
            'output_path': episode.output_path,
            'processing_status': episode.processing_status,
            'stages_completed': episode.stages_completed,
            'stages_total': episode.stages_total,
            'last_processed': episode.last_processed,
            'duration': episode.duration,
            'has_audio_analysis': episode.has_audio_analysis,
            'has_transcript': episode.has_transcript,
            'has_final_output': episode.has_final_output,
            'active_sessions': episode.active_sessions,
            'last_session_id': episode.last_session_id
        }
        
        return jsonify({
            'success': True,
            'episode': episode_data
        })
    
    except Exception as e:
        logger.error(f"Error getting episode {episode_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@episodes_bp.route('/api/episodes/<episode_id>/validate')
def api_validate_episode(episode_id):
    """API endpoint to validate an episode for pipeline processing."""
    try:
        episode = episode_manager.get_episode_by_id(episode_id)
        
        if not episode:
            return jsonify({
                'success': False,
                'error': 'Episode not found'
            }), 404
        
        is_valid, message = episode_manager.validate_episode_path(episode.full_path)
        
        return jsonify({
            'success': True,
            'valid': is_valid,
            'message': message,
            'episode_id': episode_id
        })
    
    except Exception as e:
        logger.error(f"Error validating episode {episode_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@episodes_bp.route('/api/episodes/<episode_id>/process', methods=['POST'])
def api_process_episode(episode_id):
    """API endpoint to start pipeline processing for an episode."""
    try:
        # Get episode data
        episode = episode_manager.get_episode_by_id(episode_id)
        
        if not episode:
            return jsonify({
                'success': False,
                'error': 'Episode not found'
            }), 404
        
        # Validate episode path
        is_valid, validation_message = episode_manager.validate_episode_path(episode.full_path)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': f'Episode validation failed: {validation_message}'
            }), 400
        
        # Get processing parameters from request
        data = request.get_json() or {}
        stages = data.get('stages', [1, 2, 3, 4, 5, 6, 7])  # Default to all stages
        preset_id = data.get('preset_id')
          # Initialize pipeline controller
        from app import app, socketio  # Import from main app
        pipeline_controller = PipelineController(app, socketio)
        
        # Start pipeline processing for the episode
        result = pipeline_controller.start_pipeline_for_episode(
            episode_path=episode.full_path,
            selected_stages=stages,
            preset_id=preset_id
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'session_id': result['session_id'],
                'message': f'Pipeline processing started for episode: {episode.episode_title}'
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
    
    except Exception as e:
        logger.error(f"Error processing episode {episode_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@episodes_bp.route('/api/episodes/<episode_id>/sessions')
def api_get_episode_sessions(episode_id):
    """Get all pipeline sessions for an episode."""
    try:
        episode = episode_manager.get_episode_by_id(episode_id)
        
        if not episode:
            return jsonify({
                'success': False,
                'error': 'Episode not found'
            }), 404
        
        sessions = session_manager.get_sessions_by_episode(episode.full_path)
        
        sessions_data = []
        for session in sessions:
            session_data = {
                'session_id': session.session_id,
                'status': session.status,
                'progress_percentage': session.progress_percentage,
                'current_stage': session.current_stage,
                'stage_status': session.stage_status,
                'created_at': session.created_at.isoformat() if session.created_at else None,
                'updated_at': session.updated_at.isoformat() if session.updated_at else None,
                'started_at': session.started_at.isoformat() if session.started_at else None,
                'completed_at': session.completed_at.isoformat() if session.completed_at else None,
                'error_message': session.error_message
            }
            sessions_data.append(session_data)
        
        return jsonify({
            'success': True,
            'sessions': sessions_data,
            'count': len(sessions_data)
        })
    
    except Exception as e:
        logger.error(f"Error getting sessions for episode {episode_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@episodes_bp.route('/api/search')
def api_search_episodes():
    """API endpoint for episode search."""
    try:
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query is required'
            }), 400
        
        episodes = episode_manager.search_episodes(query)
        
        # Convert to serializable format
        episodes_data = []
        for episode in episodes:
            episode_dict = {
                'episode_id': episode.episode_id,
                'show_name': episode.show_name,
                'episode_title': episode.episode_title,
                'episode_number': episode.episode_number,
                'processing_status': episode.processing_status,
                'stages_completed': episode.stages_completed,
                'duration': episode.duration
            }
            episodes_data.append(episode_dict)
        
        return jsonify({
            'success': True,
            'episodes': episodes_data,
            'count': len(episodes_data),
            'query': query
        })
    
    except Exception as e:
        logger.error(f"Error searching episodes: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@episodes_bp.route('/api/statistics')
def api_get_statistics():
    """API endpoint to get episode statistics."""
    try:
        stats = episode_manager.get_episode_statistics()
        
        return jsonify({
            'success': True,
            'statistics': stats
        })
    
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@episodes_bp.route('/api/episodes/<episode_id>/cleanup', methods=['POST'])
def api_cleanup_episode(episode_id):
    """API endpoint to clean up episode processing data."""
    try:
        episode = episode_manager.get_episode_by_id(episode_id)
        
        if not episode:
            return jsonify({
                'success': False,
                'error': 'Episode not found'
            }), 404
        
        # Get stages to clean from request
        data = request.get_json() or {}
        stages_to_clean = data.get('stages')  # None means all stages
        
        success = episode_manager.cleanup_episode_data(episode.full_path, stages_to_clean)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Cleanup completed for episode: {episode.episode_title}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Cleanup failed'
            }), 500
    
    except Exception as e:
        logger.error(f"Error cleaning up episode {episode_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Register error handlers for the blueprint
@episodes_bp.errorhandler(404)
def episode_not_found(error):
    return jsonify({
        'success': False,
        'error': 'Episode not found'
    }), 404


@episodes_bp.errorhandler(500)
def episode_server_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500
