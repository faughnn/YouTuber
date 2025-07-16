"""
Audio Integration Routes
YouTube Pipeline UI - Audio File Upload and Management

This module handles manual audio file upload functionality as an alternative
to TTS generation, providing users with flexibility in their audio workflow.

Created: June 20, 2025
Agent: Agent_Audio_Integration  
Task Reference: Phase 5, Task 5.2 - Audio Integration System
"""

from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

# Audio file validation
ALLOWED_EXTENSIONS = {'.mp3', '.wav', '.aac', '.m4a'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

bp = Blueprint('audio', __name__, url_prefix='/api/audio')
logger = logging.getLogger(__name__)

def allowed_file(filename: str) -> bool:
    """Check if file has allowed extension"""
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS

def validate_audio_file(file) -> Dict[str, Any]:
    """
    Validate uploaded audio file
    
    Returns:
        Dict with validation result and details
    """
    if not file:
        return {'valid': False, 'error': 'No file provided'}
    
    if file.filename == '':
        return {'valid': False, 'error': 'No file selected'}
    
    if not allowed_file(file.filename):
        return {
            'valid': False, 
            'error': f'Unsupported file format. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
        }
    
    # Check file size (if possible)
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning
    
    if file_size > MAX_FILE_SIZE:
        return {
            'valid': False,
            'error': f'File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB'
        }
    
    return {
        'valid': True,
        'filename': secure_filename(file.filename),
        'size': file_size,
        'format': Path(file.filename).suffix.lower()
    }

@bp.route('/upload', methods=['POST'])
def upload_audio_file():
    """
    Upload audio file for manual audio workflow
    
    Expected form data:
    - audio_file: The uploaded file
    - file_id: Unique identifier for tracking
    - episode_path (optional): Target episode directory
    """
    try:
        if 'audio_file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No audio file in request'
            }), 400
        
        file = request.files['audio_file']
        file_id = request.form.get('file_id', '')
        episode_path = request.form.get('episode_path', '')
        
        # Validate file
        validation = validate_audio_file(file)
        if not validation['valid']:
            return jsonify({
                'success': False,
                'error': validation['error']
            }), 400
        
        # Create temporary upload directory
        temp_upload_dir = Path(current_app.config.get('UPLOAD_FOLDER', 'temp_uploads'))
        temp_upload_dir.mkdir(exist_ok=True)
        
        # Save file temporarily with unique name
        temp_filename = f"{file_id}_{validation['filename']}"
        temp_filepath = temp_upload_dir / temp_filename
        
        file.save(str(temp_filepath))
        
        logger.info(f"Audio file uploaded: {temp_filename} ({validation['size']} bytes)")
        
        return jsonify({
            'success': True,
            'file_id': file_id,
            'filename': validation['filename'],
            'temp_path': str(temp_filepath),
            'size': validation['size'],
            'format': validation['format'],
            'message': 'File uploaded successfully'
        })
        
    except Exception as e:
        logger.error(f"Audio upload error: {e}")
        return jsonify({
            'success': False,
            'error': f'Upload failed: {str(e)}'
        }), 500

@bp.route('/integrate', methods=['POST'])
def integrate_audio_files():
    """
    Integrate uploaded audio files into episode directory with proper naming
    
    Expected JSON data:
    - episode_path: Path to episode directory
    - file_mappings: Dict mapping section_ids to uploaded file_ids
    - script_path: Path to unified_podcast_script.json for validation
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        episode_path = data.get('episode_path', '')
        file_mappings = data.get('file_mappings', {})
        script_path = data.get('script_path', '')
        
        if not episode_path or not file_mappings:
            return jsonify({
                'success': False,
                'error': 'Missing episode_path or file_mappings'
            }), 400
        
        # Validate episode path exists
        episode_dir = Path(episode_path)
        if not episode_dir.exists():
            return jsonify({
                'success': False,
                'error': f'Episode directory not found: {episode_path}'
            }), 404
        
        # Validate script file if provided
        valid_section_ids = set()
        if script_path and Path(script_path).exists():
            try:
                with open(script_path, 'r', encoding='utf-8') as f:
                    script_data = json.load(f)
                
                # Extract section_ids from script
                for section in script_data.get('podcast_sections', []):
                    section_id = section.get('section_id')
                    if section_id:
                        valid_section_ids.add(section_id)
                        
                logger.info(f"Found {len(valid_section_ids)} section IDs in script")
                        
            except Exception as e:
                logger.warning(f"Could not parse script file {script_path}: {e}")
        
        # Create Output/Audio directory
        audio_output_dir = episode_dir / 'Output' / 'Audio'
        audio_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Process file mappings
        temp_upload_dir = Path(current_app.config.get('UPLOAD_FOLDER', 'temp_uploads'))
        integrated_files = []
        errors = []
        
        for section_id, file_id in file_mappings.items():
            try:
                # Validate section_id if we have script data
                if valid_section_ids and section_id not in valid_section_ids:
                    errors.append(f"Section ID '{section_id}' not found in script")
                    continue
                
                # Find temporary file
                temp_files = list(temp_upload_dir.glob(f"{file_id}_*"))
                if not temp_files:
                    errors.append(f"Temporary file not found for file_id: {file_id}")
                    continue
                
                temp_file = temp_files[0]
                
                # Create target filename with section_id
                target_filename = f"{section_id}.wav"
                target_path = audio_output_dir / target_filename
                
                # Copy and convert file to target location
                shutil.copy2(temp_file, target_path)
                
                # Clean up temporary file
                temp_file.unlink()
                
                integrated_files.append({
                    'section_id': section_id,
                    'filename': target_filename,
                    'path': str(target_path),
                    'size': target_path.stat().st_size
                })
                
                logger.info(f"Integrated audio file: {section_id} -> {target_filename}")
                
            except Exception as e:
                error_msg = f"Failed to integrate {section_id}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        # Create integration report
        result = {
            'success': len(integrated_files) > 0,
            'integrated_count': len(integrated_files),
            'error_count': len(errors),
            'integrated_files': integrated_files,
            'errors': errors,
            'output_directory': str(audio_output_dir)
        }
        
        if errors:
            result['message'] = f"Integrated {len(integrated_files)} files with {len(errors)} errors"
        else:
            result['message'] = f"Successfully integrated {len(integrated_files)} audio files"
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Audio integration error: {e}")
        return jsonify({
            'success': False,
            'error': f'Integration failed: {str(e)}'
        }), 500

@bp.route('/validate', methods=['POST'])
def validate_audio_integration():
    """
    Validate audio files exist for all required sections
    
    Expected JSON data:
    - episode_path: Path to episode directory
    - script_path: Path to unified_podcast_script.json
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        episode_path = data.get('episode_path', '')
        script_path = data.get('script_path', '')
        
        if not episode_path or not script_path:
            return jsonify({
                'success': False,
                'error': 'Missing episode_path or script_path'
            }), 400
        
        # Validate paths exist
        episode_dir = Path(episode_path)
        script_file = Path(script_path)
        
        if not episode_dir.exists():
            return jsonify({
                'success': False,
                'error': f'Episode directory not found: {episode_path}'
            }), 404
        
        if not script_file.exists():
            return jsonify({
                'success': False,
                'error': f'Script file not found: {script_path}'
            }), 404
        
        # Parse script file
        with open(script_file, 'r', encoding='utf-8') as f:
            script_data = json.load(f)
        
        # Extract required section_ids
        required_sections = []
        for section in script_data.get('podcast_sections', []):
            section_id = section.get('section_id')
            section_type = section.get('section_type', '')
            if section_id:
                required_sections.append({
                    'section_id': section_id,
                    'section_type': section_type
                })
        
        # Check for existing audio files
        audio_dir = episode_dir / 'Output' / 'Audio'
        existing_files = []
        missing_files = []
        
        for section in required_sections:
            section_id = section['section_id']
            audio_file = audio_dir / f"{section_id}.wav"
            
            if audio_file.exists():
                existing_files.append({
                    'section_id': section_id,
                    'section_type': section['section_type'],
                    'filename': f"{section_id}.wav",
                    'path': str(audio_file),
                    'size': audio_file.stat().st_size
                })
            else:
                missing_files.append({
                    'section_id': section_id,
                    'section_type': section['section_type'],
                    'expected_filename': f"{section_id}.wav"
                })
        
        validation_result = {
            'success': True,
            'total_sections': len(required_sections),
            'existing_count': len(existing_files),
            'missing_count': len(missing_files),
            'coverage_percentage': round((len(existing_files) / len(required_sections)) * 100, 2) if required_sections else 0,
            'existing_files': existing_files,
            'missing_files': missing_files,
            'audio_directory': str(audio_dir),
            'ready_for_pipeline': len(missing_files) == 0
        }
        
        return jsonify(validation_result)
        
    except Exception as e:
        logger.error(f"Audio validation error: {e}")
        return jsonify({
            'success': False,
            'error': f'Validation failed: {str(e)}'
        }), 500

@bp.route('/cleanup', methods=['POST'])
def cleanup_temp_files():
    """
    Clean up temporary uploaded files
    
    Expected JSON data:
    - file_ids: List of file IDs to clean up (optional, cleans all if not provided)
    """
    try:
        data = request.get_json() or {}
        file_ids = data.get('file_ids', [])
        
        temp_upload_dir = Path(current_app.config.get('UPLOAD_FOLDER', 'temp_uploads'))
        
        if not temp_upload_dir.exists():
            return jsonify({
                'success': True,
                'message': 'No temporary files to clean up'
            })
        
        cleaned_files = []
        
        if file_ids:
            # Clean up specific files
            for file_id in file_ids:
                temp_files = list(temp_upload_dir.glob(f"{file_id}_*"))
                for temp_file in temp_files:
                    temp_file.unlink()
                    cleaned_files.append(temp_file.name)
        else:
            # Clean up all temporary files
            for temp_file in temp_upload_dir.glob("*"):
                if temp_file.is_file():
                    temp_file.unlink()
                    cleaned_files.append(temp_file.name)
        
        logger.info(f"Cleaned up {len(cleaned_files)} temporary audio files")
        
        return jsonify({
            'success': True,
            'cleaned_count': len(cleaned_files),
            'cleaned_files': cleaned_files,
            'message': f'Cleaned up {len(cleaned_files)} temporary files'
        })
        
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        return jsonify({
            'success': False,
            'error': f'Cleanup failed: {str(e)}'
        }), 500