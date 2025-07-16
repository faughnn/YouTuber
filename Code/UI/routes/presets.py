"""
Presets Management Routes
YouTube Pipeline UI - Workflow Presets and Configuration

This module handles workflow presets, configuration templates,
and reusable pipeline settings for efficient content processing.

Created: June 20, 2025
Agent: Agent_Preset_Audio
Task Reference: Phase 5, Task 5.1 - Workflow Preset System
"""

from flask import Blueprint, render_template, request, jsonify, current_app
from flask_socketio import emit
import json
from pathlib import Path
from datetime import datetime

from services.preset_manager import PresetManager

bp = Blueprint('presets', __name__)

# Initialize preset manager
preset_manager = PresetManager()

@bp.route('/')
def presets_dashboard():
    """
    Presets management dashboard.
    
    Main interface for creating, editing, and managing workflow presets.
    """
    try:
        return render_template('presets.html')
    
    except Exception as e:
        current_app.logger.error(f"Presets dashboard error: {e}")
        return render_template('presets.html', error=str(e))

@bp.route('/api/presets')
def get_presets_api():
    """
    API endpoint to get all available presets.
    
    Returns:
        JSON response with presets list and success status
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
        current_app.logger.error(f"Get presets API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/presets/<preset_id>')
def get_preset_api(preset_id):
    """
    API endpoint to get a specific preset by ID.
    
    Args:
        preset_id: UUID of the preset
        
    Returns:
        JSON response with preset data
    """
    try:
        success, result = preset_manager.load_preset(preset_id=preset_id)
        
        if success:
            return jsonify({
                'success': True,
                'preset': result
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 404
    
    except Exception as e:
        current_app.logger.error(f"Get preset API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/presets', methods=['POST'])
def create_preset_api():
    """
    API endpoint to create a new preset.
    
    Expects JSON data with preset configuration.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Extract preset data
        name = data.get('name')
        description = data.get('description')
        category = data.get('category', 'custom')
        configuration = data.get('configuration')
        
        if not name or not configuration:
            return jsonify({
                'success': False,
                'error': 'Name and configuration are required'
            }), 400
        
        # Create preset
        success, result = preset_manager.create_preset(
            name=name,
            configuration=configuration,
            description=description,
            category=category
        )
        
        if success:
            # Emit SocketIO event for real-time updates
            if hasattr(current_app, 'socketio'):
                current_app.socketio.emit('preset_created', {
                    'preset_id': result['preset_id'],
                    'name': result['name'],
                    'category': result['category']
                })
            
            return jsonify({
                'success': True,
                'preset_id': result['preset_id'],
                'message': 'Preset created successfully',
                'warnings': result.get('validation_warnings', [])
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error'],
                'validation_errors': result.get('validation_errors', [])
            }), 400
    
    except Exception as e:
        current_app.logger.error(f"Create preset API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/presets/<preset_id>', methods=['PUT'])
def update_preset_api(preset_id):
    """
    API endpoint to update an existing preset.
    
    Args:
        preset_id: UUID of the preset to update
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Update preset
        success, result = preset_manager.update_preset(
            preset_id=preset_id,
            configuration=data.get('configuration'),
            description=data.get('description')
        )
        
        if success:
            # Emit SocketIO event for real-time updates
            if hasattr(current_app, 'socketio'):
                current_app.socketio.emit('preset_updated', {
                    'preset_id': preset_id
                })
            
            return jsonify({
                'success': True,
                'message': 'Preset updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
    
    except Exception as e:
        current_app.logger.error(f"Update preset API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/presets/<preset_id>', methods=['DELETE'])
def delete_preset_api(preset_id):
    """
    API endpoint to delete a preset.
    
    Args:
        preset_id: UUID of the preset to delete
    """
    try:
        success, result = preset_manager.delete_preset(preset_id)
        
        if success:
            # Emit SocketIO event for real-time updates
            if hasattr(current_app, 'socketio'):
                current_app.socketio.emit('preset_deleted', {
                    'preset_id': preset_id
                })
            
            return jsonify({
                'success': True,
                'message': result['message']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
    
    except Exception as e:
        current_app.logger.error(f"Delete preset API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/presets/<preset_id>/load', methods=['POST'])
def load_preset_api(preset_id):
    """
    API endpoint to load a preset for pipeline execution.
    
    Args:
        preset_id: UUID of the preset to load
    """
    try:
        success, result = preset_manager.use_preset(preset_id)
        
        if success:
            # Emit SocketIO event for real-time updates
            if hasattr(current_app, 'socketio'):
                current_app.socketio.emit('preset_loaded', {
                    'preset_id': preset_id,
                    'preset_name': result['name'],
                    'configuration': result['configuration']
                })
            
            return jsonify({
                'success': True,
                'preset_id': preset_id,
                'preset_name': result['name'],
                'configuration': result['configuration'],
                'usage_count': result['usage_count']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
    
    except Exception as e:
        current_app.logger.error(f"Load preset API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/presets/<preset_id>/export')
def export_preset_api(preset_id):
    """
    API endpoint to export a preset.
    
    Args:
        preset_id: UUID of the preset to export
    """
    try:
        success, result = preset_manager.load_preset(preset_id=preset_id)
        
        if success:
            return jsonify({
                'success': True,
                'preset_data': result
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 404
    
    except Exception as e:
        current_app.logger.error(f"Export preset API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/presets/import', methods=['POST'])
def import_preset_api():
    """
    API endpoint to import a preset from JSON data.
    """
    try:
        data = request.get_json()
        
        if not data or 'preset_data' not in data:
            return jsonify({
                'success': False,
                'error': 'Invalid import data format'
            }), 400
        
        preset_data = data['preset_data']
        overwrite = data.get('overwrite', False)
        
        # Create preset from imported data
        success, result = preset_manager.create_preset(
            name=preset_data['name'],
            configuration=preset_data['configuration'],
            description=preset_data.get('description'),
            category=preset_data.get('category', 'custom')
        )
        
        if success:
            # Emit SocketIO event for real-time updates
            if hasattr(current_app, 'socketio'):
                current_app.socketio.emit('preset_imported', {
                    'preset_id': result['preset_id'],
                    'name': result['name']
                })
            
            return jsonify({
                'success': True,
                'preset_id': result['preset_id'],
                'message': 'Preset imported successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
    
    except Exception as e:
        current_app.logger.error(f"Import preset API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/api/statistics')
def get_statistics_api():
    """
    API endpoint to get preset usage statistics.
    """
    try:
        statistics = preset_manager.get_preset_statistics()
        
        return jsonify({
            'success': True,
            'statistics': statistics
        })
    
    except Exception as e:
        current_app.logger.error(f"Get statistics API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Legacy placeholder functions (will be removed)
@bp.route('/api/legacy_presets')
def get_legacy_presets():
    """
    Legacy preset endpoint for backward compatibility.
    Returns placeholder preset data.
    """
    try:
        # TODO: In Phase 5, this will return actual preset data from storage
        presets = {
            'presets': [
                {
                    'id': 'default_full',
                    'name': 'Full Pipeline Default',
                    'description': 'Complete 7-stage processing pipeline',
                    'stages': list(range(1, 8)),
                    'category': 'Full Pipeline',
                    'created_at': datetime.now().isoformat(),
                    'enabled': True
                },
                {
                    'id': 'audio_only',
                    'name': 'Audio-Only Processing',
                    'description': 'Process through audio generation (stages 1-5)',
                    'stages': list(range(1, 6)),
                    'category': 'Audio Only',
                    'created_at': datetime.now().isoformat(),
                    'enabled': True
                },
                {
                    'id': 'script_only',
                    'name': 'Script Generation Only',
                    'description': 'Generate narrative script (stages 1-4)',
                    'stages': list(range(1, 5)),
                    'category': 'Script Generation',
                    'created_at': datetime.now().isoformat(),
                    'enabled': True
                }
            ],
            'note': 'These are placeholder presets. Full implementation in Phase 5.'
        }
        
        return jsonify(presets)
    
    except Exception as e:
        current_app.logger.error(f"Presets API error: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/presets', methods=['POST'])
def create_preset():
    """
    Create a new workflow preset.
    
    Returns:
        JSON response confirming preset creation
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No preset data provided'}), 400
        
        required_fields = ['name', 'description', 'stages']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({'error': f'Missing required fields: {missing_fields}'}), 400
        
        # TODO: In Phase 5, this will save the preset to persistent storage
        preset = {
            'id': f"preset_{hash(data['name'])}",
            'name': data['name'],
            'description': data['description'],
            'stages': data['stages'],
            'category': data.get('category', 'Custom Workflow'),
            'configuration': data.get('configuration', {}),
            'created_at': datetime.now().isoformat(),
            'enabled': True
        }
        
        current_app.logger.info(f"Preset creation requested: {preset['name']}")
        
        response = {
            'status': 'created',
            'preset': preset,
            'note': 'Preset storage will be implemented in Phase 5'
        }
        
        return jsonify(response), 201
    
    except Exception as e:
        current_app.logger.error(f"Preset creation error: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/presets/<preset_id>', methods=['GET'])
def get_preset(preset_id):
    """
    Get a specific preset by ID.
    
    Args:
        preset_id (str): Unique preset identifier
        
    Returns:
        JSON response with preset details
    """
    try:
        # TODO: In Phase 5, this will load the actual preset from storage
        preset = {
            'id': preset_id,
            'name': 'Example Preset',
            'description': 'Placeholder preset data',
            'stages': [1, 2, 3, 4],
            'category': 'Custom Workflow',
            'configuration': {},
            'created_at': datetime.now().isoformat(),
            'enabled': True,
            'note': 'Preset loading will be implemented in Phase 5'
        }
        
        return jsonify(preset)
    
    except Exception as e:
        current_app.logger.error(f"Preset retrieval error: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/presets/<preset_id>', methods=['PUT'])
def update_preset(preset_id):
    """
    Update an existing preset.
    
    Args:
        preset_id (str): Unique preset identifier
        
    Returns:
        JSON response confirming preset update
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No update data provided'}), 400
        
        # TODO: In Phase 5, this will update the actual preset in storage
        updated_preset = {
            'id': preset_id,
            'name': data.get('name', 'Updated Preset'),
            'description': data.get('description', 'Updated description'),
            'stages': data.get('stages', []),
            'category': data.get('category', 'Custom Workflow'),
            'configuration': data.get('configuration', {}),
            'updated_at': datetime.now().isoformat(),
            'enabled': data.get('enabled', True)
        }
        
        current_app.logger.info(f"Preset update requested: {preset_id}")
        
        response = {
            'status': 'updated',
            'preset': updated_preset,
            'note': 'Preset updates will be implemented in Phase 5'
        }
        
        return jsonify(response)
    
    except Exception as e:
        current_app.logger.error(f"Preset update error: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/presets/<preset_id>', methods=['DELETE'])
def delete_preset(preset_id):
    """
    Delete a preset.
    
    Args:
        preset_id (str): Unique preset identifier
        
    Returns:
        JSON response confirming preset deletion
    """
    try:
        # TODO: In Phase 5, this will delete the actual preset from storage
        response = {
            'status': 'deleted',
            'preset_id': preset_id,
            'note': 'Preset deletion will be implemented in Phase 5'
        }
        
        current_app.logger.info(f"Preset deletion requested: {preset_id}")
        
        return jsonify(response)
    
    except Exception as e:
        current_app.logger.error(f"Preset deletion error: {e}")
        return jsonify({'error': str(e)}), 500
