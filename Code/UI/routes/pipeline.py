"""
Pipeline Control Routes
YouTube Pipeline UI - Pipeline Execution and Monitoring

This module handles pipeline execution control, stage selection,
and real-time monitoring of the YouTube processing pipeline.

Updated to integrate with PipelineController service for full master_processor_v2 integration.

Created: June 20, 2025
Agent: Implementation Agent
Task Reference: Phase 2, Task 2.1 - Master Processor Integration
"""

from flask import Blueprint, render_template, request, jsonify, current_app
from flask_socketio import emit
import os
import sys
import uuid
import threading
from pathlib import Path
from datetime import datetime

# Import database models and services
from database.models import db, PipelineSession
from database.utils import SessionManager
from services.pipeline_controller import PipelineController
from services.file_monitor import create_file_monitor

bp = Blueprint('pipeline', __name__)

# Initialize pipeline controller (will be configured with app context)
pipeline_controller = None

def init_pipeline_routes(app, socketio):
    """
    Initialize pipeline routes with app and socketio context.
    
    Args:
        app: Flask application instance
        socketio: SocketIO instance
    """
    global pipeline_controller
    pipeline_controller = PipelineController(app, socketio)

@bp.route('/')
def pipeline_dashboard():
    """
    Pipeline control dashboard.
    
    Main interface for pipeline execution control, stage selection,
    and monitoring pipeline progress.
    """
    try:
        pipeline_config = {
            'stages': current_app.config['PIPELINE_STAGES'],
            'master_processor_available': Path(current_app.config['MASTER_PROCESSOR_PATH']).exists()
        }
        
        return render_template('pipeline/dashboard.html', config=pipeline_config)
    
    except Exception as e:
        current_app.logger.error(f"Pipeline dashboard error: {e}")
        return render_template('pipeline/dashboard.html', config={'error': str(e)})

@bp.route('/execute', methods=['POST'])
def execute_pipeline():
    """
    Execute pipeline with selected stages using integrated master_processor_v2.
    
    Handles pipeline execution requests with flexible stage selection,
    database session tracking, and real-time monitoring.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        youtube_url = data.get('youtube_url')
        selected_stages = data.get('selected_stages', [])
        execution_mode = data.get('execution_mode', 'custom')
        episode_directory = data.get('episode_directory', None)  # For smart resume
        
        # Extract audio method configuration
        audio_method = data.get('audio_method', 'tts')
        manual_audio_files = data.get('manual_audio_files', {})
        selected_prompt = data.get('selected_prompt', None)
        
        if not youtube_url:
            return jsonify({'error': 'YouTube URL is required'}), 400
        
        if not selected_stages:
            return jsonify({'error': 'At least one stage must be selected'}), 400
        
        # Validate and sort stages for sequential execution
        try:
            selected_stages = sorted([int(stage) for stage in selected_stages])
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid stage numbers provided'}), 400
          # Validate stage dependencies using pipeline controller with smart resume
        if pipeline_controller:
            if episode_directory:
                # Use smart validation that checks for existing files
                validation_result = pipeline_controller.validate_stage_dependencies_smart(
                    selected_stages, episode_directory
                )
            else:
                # Use basic validation
                validation_result = pipeline_controller.validate_stage_dependencies(selected_stages)
                
            if not validation_result['valid']:
                return jsonify({
                    'error': validation_result['message'],
                    'validation_details': validation_result
                }), 400
        
        # Create database session for tracking
        session_id = str(uuid.uuid4())
        
        # Extract show name and episode title from URL (basic implementation)
        show_name = "Unknown Show"
        episode_title = f"Episode_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Create pipeline session in database
            with current_app.app_context():
                pipeline_session = PipelineSession(
                    session_id=session_id,
                    episode_path="",  # Will be updated when episode directory is created
                    episode_title=episode_title,
                    show_name=show_name,
                    status='initialized',
                    current_stage=selected_stages[0] if selected_stages else 1
                )
                
                db.session.add(pipeline_session)
                db.session.commit()
                
                current_app.logger.info(f"Created pipeline session: {session_id}")
        
        except Exception as db_error:
            current_app.logger.error(f"Database session creation failed: {db_error}")
            return jsonify({'error': 'Failed to create tracking session'}), 500
        
        # Define progress callback for real-time updates
        def progress_callback(session_id, status, progress, stage):
            try:
                if hasattr(current_app, 'socketio'):
                    current_app.socketio.emit('pipeline_progress', {
                        'session_id': session_id,
                        'status': status,
                        'progress': progress,
                        'stage': stage,                        'timestamp': datetime.now().isoformat()
                    })
            except Exception as e:
                current_app.logger.error(f"Failed to emit progress update: {e}")
        
        # Execute pipeline asynchronously with enhanced monitoring
        if pipeline_controller:
            try:
                # Start pipeline execution in background thread
                execution_thread = threading.Thread(
                    target=pipeline_controller.execute_pipeline_stages,
                    args=(youtube_url, selected_stages, session_id),                    kwargs={
                        'config_path': None,
                        'episode_directory': episode_directory,
                        'audio_method': audio_method,
                        'manual_audio_files': manual_audio_files,
                        'selected_prompt': selected_prompt
                    }
                )
                execution_thread.daemon = True
                execution_thread.start()
                
                current_app.logger.info(f"Pipeline execution started in background: {session_id}")
                
                return jsonify({
                    'status': 'started',
                    'session_id': session_id,
                    'execution_mode': execution_mode,
                    'selected_stages': selected_stages,
                    'message': 'Pipeline execution started successfully',
                    'monitoring_enabled': True
                })
                
            except Exception as exec_error:
                current_app.logger.error(f"Failed to start pipeline execution: {exec_error}")
                return jsonify({'error': f'Failed to start execution: {str(exec_error)}'}), 500
        else:
            return jsonify({'error': 'Pipeline controller not initialized'}), 500
    
    except Exception as e:
        current_app.logger.error(f"Pipeline execution error: {e}")
        return jsonify({'error': f'Pipeline execution failed: {str(e)}'}), 500

@bp.route('/status/<session_id>')
def pipeline_status(session_id):
    """
    Get pipeline execution status using integrated database tracking.
    
    Args:
        session_id (str): Database session identifier
        
    Returns:
        JSON response with current pipeline status
    """
    try:
        if pipeline_controller:
            status = pipeline_controller.get_execution_status(session_id)
            return jsonify(status)
        else:
            # Fallback to database-only status
            with current_app.app_context():
                session = PipelineSession.query.get(session_id)
                if session:
                    return jsonify({
                        'session_id': session_id,
                        'status': session.status,
                        'progress': session.progress_percentage,
                        'current_stage': session.current_stage,
                        'stage_status': session.stage_status,
                        'error_message': session.error_message,
                        'started_at': session.started_at.isoformat() if session.started_at else None,
                        'completed_at': session.completed_at.isoformat() if session.completed_at else None,
                        'episode_title': session.episode_title
                    })
                else:
                    return jsonify({'error': f'Session {session_id} not found'}), 404
    
    except Exception as e:
        current_app.logger.error(f"Pipeline status error: {e}")
        return jsonify({'error': f'Status check failed: {str(e)}'}), 500

@bp.route('/stop/<session_id>', methods=['POST'])
def stop_pipeline(session_id):
    """
    Stop pipeline execution using integrated pipeline controller.
    
    Args:
        session_id (str): Database session identifier
        
    Returns:
        JSON response confirming pipeline stop request
    """
    try:
        if pipeline_controller:
            result = pipeline_controller.stop_pipeline_execution(session_id)
            return jsonify(result)
        else:
            # Fallback to database-only stop
            with current_app.app_context():
                session = PipelineSession.query.get(session_id)
                if session:
                    session.status = 'stopped'
                    session.error_message = 'Stopped by user request'
                    db.session.commit()
                    
                    return jsonify({
                        'status': 'success',
                        'message': f'Pipeline execution {session_id} marked as stopped'
                    })
                else:
                    return jsonify({'error': f'Session {session_id} not found'}), 404
    
    except Exception as e:
        current_app.logger.error(f"Pipeline stop error: {e}")
        return jsonify({'error': f'Stop request failed: {str(e)}'}), 500

@bp.route('/sessions')
def list_pipeline_sessions():
    """
    List all pipeline execution sessions.
    
    Returns:
        JSON response with list of pipeline sessions
    """
    try:
        with current_app.app_context():
            sessions = PipelineSession.query.order_by(PipelineSession.created_at.desc()).limit(50).all()
            
            sessions_data = []
            for session in sessions:
                sessions_data.append({
                    'session_id': session.session_id,
                    'episode_title': session.episode_title,
                    'show_name': session.show_name,
                    'status': session.status,
                    'progress': session.progress_percentage,
                    'current_stage': session.current_stage,
                    'created_at': session.created_at.isoformat(),
                    'started_at': session.started_at.isoformat() if session.started_at else None,
                    'completed_at': session.completed_at.isoformat() if session.completed_at else None,
                    'error_message': session.error_message
                })
            
            return jsonify({
                'sessions': sessions_data,
                'total': len(sessions_data)
            })
    
    except Exception as e:
        current_app.logger.error(f"Failed to list sessions: {e}")
        return jsonify({'error': f'Failed to retrieve sessions: {str(e)}'}), 500

@bp.route('/validate-stages', methods=['POST'])
def validate_stages():
    """
    Validate stage dependencies for selected stages.
    
    Returns:
        JSON response with validation results
    """
    try:
        data = request.get_json()
        selected_stages = data.get('selected_stages', [])
        
        if not selected_stages:
            return jsonify({'error': 'No stages provided'}), 400
        
        # Convert to integers
        try:
            selected_stages = [int(stage) for stage in selected_stages]
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid stage numbers'}), 400
        
        if pipeline_controller:
            validation_result = pipeline_controller.validate_stage_dependencies(selected_stages)
            return jsonify(validation_result)
        else:
            # Fallback validation
            return jsonify(_validate_stage_dependencies(selected_stages))
    
    except Exception as e:
        current_app.logger.error(f"Stage validation error: {e}")
        return jsonify({'error': f'Validation failed: {str(e)}'}), 500

def _validate_stage_dependencies(selected_stages):
    """
    Fallback stage dependency validation.
    
    Args:
        selected_stages (list): List of selected stage numbers
        
    Returns:
        dict: Validation result with 'valid' boolean and 'message' string
    """
    # Basic validation - stages must be in valid range
    valid_stages = set(range(1, 8))
    invalid_stages = set(selected_stages) - valid_stages
    
    if invalid_stages:
        return {
            'valid': False,
            'message': f'Invalid stages selected: {sorted(invalid_stages)}'
        }
    
    # Basic dependency checking
    dependencies = {
        2: [1],
        3: [1, 2],
        4: [1, 2, 3],
        5: [1, 2, 3, 4],
        6: [1, 2, 3, 4],
        7: [1, 2, 3, 4, 5, 6]
    }
    
    selected_set = set(selected_stages)
    
    for stage in selected_stages:
        if stage in dependencies:
            required_stages = set(dependencies[stage])
            missing_stages = required_stages - selected_set
            
            if missing_stages:
                return {
                    'valid': False,
                    'message': f'Stage {stage} requires stages {sorted(missing_stages)} to be selected'
                }
    
    return {
        'valid': True,
        'message': 'Stage selection validated successfully'
    }

@bp.route('/interrupt/<session_id>', methods=['POST'])
def interrupt_pipeline(session_id):
    """
    Interrupt running pipeline execution.
    
    Args:
        session_id (str): Database session identifier
        
    Returns:
        JSON response with interruption status
    """
    try:
        if pipeline_controller:
            result = pipeline_controller.interrupt_execution(session_id)
            
            if result['success']:
                return jsonify({
                    'status': 'interrupted',
                    'session_id': session_id,
                    'message': 'Pipeline execution interrupted successfully'
                })
            else:
                return jsonify({
                    'error': result.get('message', 'Failed to interrupt pipeline'),
                    'session_id': session_id
                }), 400
        else:
            return jsonify({'error': 'Pipeline controller not initialized'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Pipeline interruption error: {e}")
        return jsonify({'error': f'Failed to interrupt pipeline: {str(e)}'}), 500

@bp.route('/logs/<session_id>')
def get_pipeline_logs(session_id):
    """
    Get pipeline logs for a specific session.
    
    Args:
        session_id (str): Database session identifier
        
    Returns:
        JSON response with log entries
    """
    try:
        if pipeline_controller:
            logs = pipeline_controller.get_session_logs(session_id)
            return jsonify({
                'session_id': session_id,
                'logs': logs,
                'count': len(logs)
            })
        else:
            return jsonify({'error': 'Pipeline controller not initialized'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Failed to retrieve logs: {e}")
        return jsonify({'error': f'Failed to retrieve logs: {str(e)}'}), 500
