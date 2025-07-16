"""
Main Routes - Dashboard and Episode Management
YouTube Pipeline UI - Primary Navigation and Episode Selection

This module handles the main dashboard, episode selection, and general
navigation routes for the YouTube Pipeline UI.

Created: June 20, 2025
Agent: Implementation Agent
Updated: June 20, 2025 - Task 2.2 Episode Management Integration
Task Reference: Phase 1, Task 1.1 - Core Flask Application Setup
                Phase 2, Task 2.2 - Episode Management System
"""

from flask import Blueprint, render_template, request, jsonify, current_app, send_from_directory
import os
from datetime import datetime
from pathlib import Path
from services.episode_manager import EpisodeManager
from services.preset_manager import PresetManager

bp = Blueprint('main', __name__)

# Initialize managers
preset_manager = PresetManager()

@bp.route('/')
def index():
    """
    Main dashboard route.
    
    Displays the primary interface for the YouTube Pipeline UI with
    navigation to all major features, system status overview, and
    episode statistics from the Episode Management System.
    """
    try:
        # Initialize episode manager
        episode_manager = EpisodeManager(current_app.config['CONTENT_DIR'])
        
        # Get episode statistics
        episode_stats = episode_manager.get_episode_statistics()
        
        # Get basic system status for dashboard
        content_dir = Path(current_app.config['CONTENT_DIR'])
        
        dashboard_stats = {
            'shows_count': episode_stats.get('total_shows', 0),
            'episodes_count': episode_stats.get('total_episodes', 0),
            'pipeline_stages': current_app.config.get('PIPELINE_STAGES', {}),
            'system_status': 'Ready',
            'episode_stats': episode_stats
        }
        
        return render_template('index.html', stats=dashboard_stats)
    
    except Exception as e:
        current_app.logger.error(f"Dashboard error: {e}")
        # Fallback stats in case of error
        content_dir = Path(current_app.config.get('CONTENT_DIR', ''))
        shows_count = len([d for d in content_dir.iterdir() if d.is_dir()]) if content_dir.exists() else 0
        
        dashboard_stats = {
            'shows_count': shows_count,
            'episodes_count': 0,
            'pipeline_stages': current_app.config.get('PIPELINE_STAGES', {}),
            'system_status': 'Error',
            'episode_stats': {}
        }
        return render_template('index.html', stats=dashboard_stats)

@bp.route('/api/system-status')
def system_status():
    """
    API endpoint for system status information.
    
    Returns JSON with current system status, configuration, and health checks.
    """
    try:
        status = {
            'status': 'healthy',
            'project_root': str(current_app.config['PROJECT_ROOT']),
            'content_dir': str(current_app.config['CONTENT_DIR']),
            'content_dir_exists': Path(current_app.config['CONTENT_DIR']).exists(),
            'master_processor_exists': Path(current_app.config['MASTER_PROCESSOR_PATH']).exists(),
            'pipeline_stages': current_app.config['PIPELINE_STAGES'],
            'debug_mode': current_app.debug
        }
        
        return jsonify(status)
    
    except Exception as e:
        current_app.logger.error(f"System status error: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@bp.route('/api/status')
def api_status():
    """
    Alternative API endpoint for system status (compatibility).
    """
    return system_status()

@bp.route('/api/stats')
def api_stats():
    """
    API endpoint for dashboard statistics.
    
    Returns episode counts, show information, and system metrics.
    """
    try:
        # Initialize episode manager
        episode_manager = EpisodeManager(current_app.config['CONTENT_DIR'])
        
        # Get episode statistics
        episode_stats = episode_manager.get_episode_statistics()
        
        # Get system stats
        content_dir = Path(current_app.config['CONTENT_DIR'])
        
        stats = {
            'shows_count': episode_stats.get('total_shows', 0),
            'episodes_count': episode_stats.get('total_episodes', 0),
            'system_status': 'healthy',
            'content_dir_exists': content_dir.exists(),
            'episode_stats': episode_stats,
            'pipeline_stages': current_app.config.get('PIPELINE_STAGES', {}),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(stats)
    
    except Exception as e:
        current_app.logger.error(f"API stats error: {e}")
        return jsonify({
            'shows_count': 0,
            'episodes_count': 0,
            'system_status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@bp.route('/api/episodes')
def api_episodes():
    """
    API endpoint for episodes data (main route).
    
    Provides episode listing for frontend components.
    """
    try:
        # Initialize episode manager
        episode_manager = EpisodeManager(current_app.config['CONTENT_DIR'])
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
        current_app.logger.error(f"API episodes error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'episodes': [],
            'count': 0
        }), 500

@bp.route('/api/presets')
def api_presets():
    """
    API endpoint for presets data (main route).
    
    Provides preset listing for frontend components.
    """
    try:
        category = request.args.get('category')
        presets = preset_manager.list_presets(category)
        
        return jsonify({
            'success': True,
            'presets': presets,
            'count': len(presets)
        })
    
    except Exception as e:
        current_app.logger.error(f"API presets error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'presets': [],
            'count': 0
        }), 500

@bp.route('/favicon.ico')
def favicon():
    """
    Handle favicon requests to prevent 404 errors.
    
    Returns a simple response or serves a favicon if one exists in the static folder.
    """
    try:
        # Try to serve favicon from static folder if it exists
        return send_from_directory(
            os.path.join(current_app.root_path, 'static'),
            'favicon.ico',
            mimetype='image/vnd.microsoft.icon'
        )
    except:        # Return empty response with 204 No Content if no favicon exists
        return '', 204
