"""
Prompt Management Routes
YouTube Pipeline UI - Stage 3/4 Prompt Selection and Management

This module handles prompt management for Stage 3 analysis and Stage 4 narrative
generation, supporting both predefined and custom prompt workflows.

Created: June 20, 2025
Agent: Agent_Audio_Integration
Task Reference: Phase 5, Task 5.2 - Audio Integration System (Prompt Management)
"""

from flask import Blueprint, request, jsonify, current_app
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

bp = Blueprint('prompts', __name__, url_prefix='/api/prompts')
logger = logging.getLogger(__name__)

# Default prompt directories (relative to project root)
DEFAULT_PROMPT_DIRS = {
    'stage3': Path('Code/Content_Analysis/Generation_Templates'),
    'stage4': Path('Code/Video_Compilator/prompts')
}

def scan_prompt_files(prompt_dir: Path, stage: str) -> List[Dict[str, Any]]:
    """
    Scan directory for prompt files and extract metadata
    
    Args:
        prompt_dir: Directory containing prompt files
        stage: Stage identifier ('stage3' or 'stage4')
    
    Returns:
        List of prompt information dictionaries
    """
    prompts = []
    
    if not prompt_dir.exists():
        logger.warning(f"Prompt directory not found: {prompt_dir}")
        return prompts
    
    # Look for common prompt file patterns
    prompt_patterns = ['*.txt', '*.md', '*.json']
    
    for pattern in prompt_patterns:
        for prompt_file in prompt_dir.glob(pattern):
            try:
                # Extract basic metadata
                prompt_info = {
                    'id': prompt_file.stem,
                    'name': prompt_file.stem.replace('_', ' ').title(),
                    'filename': prompt_file.name,
                    'path': str(prompt_file),
                    'stage': stage,
                    'type': 'file',
                    'format': prompt_file.suffix.lower(),
                    'size': prompt_file.stat().st_size,
                    'modified': prompt_file.stat().st_mtime
                }
                
                # Try to extract additional metadata from file content
                if prompt_file.suffix.lower() == '.json':
                    try:
                        with open(prompt_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        if isinstance(data, dict):
                            prompt_info['name'] = data.get('name', prompt_info['name'])
                            prompt_info['description'] = data.get('description', '')
                            prompt_info['version'] = data.get('version', '1.0')
                            prompt_info['author'] = data.get('author', '')
                            
                    except Exception as e:
                        logger.debug(f"Could not parse JSON metadata from {prompt_file}: {e}")
                
                elif prompt_file.suffix.lower() in ['.txt', '.md']:
                    try:
                        with open(prompt_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Look for metadata in first few lines
                        lines = content.split('\n')[:10]
                        for line in lines:
                            if line.startswith('# ') or line.startswith('Title:'):
                                title = line.replace('#', '').replace('Title:', '').strip()
                                if title:
                                    prompt_info['name'] = title
                                break
                        
                        # Set content preview
                        prompt_info['preview'] = content[:200] + '...' if len(content) > 200 else content
                        
                    except Exception as e:
                        logger.debug(f"Could not read content from {prompt_file}: {e}")
                
                prompts.append(prompt_info)
                
            except Exception as e:
                logger.error(f"Error processing prompt file {prompt_file}: {e}")
    
    return sorted(prompts, key=lambda x: x['name'])

@bp.route('/list', methods=['GET'])
def list_prompts():
    """
    List available prompts for both Stage 3 and Stage 4
    
    Query parameters:
    - stage: Filter by stage ('stage3' or 'stage4')
    - format: Filter by file format
    """
    try:
        stage_filter = request.args.get('stage', '')
        format_filter = request.args.get('format', '')
        
        prompt_data = {
            'stage3': [],
            'stage4': []
        }
        
        # Scan default prompt directories
        for stage, default_dir in DEFAULT_PROMPT_DIRS.items():
            if stage_filter and stage_filter != stage:
                continue
                
            prompts = scan_prompt_files(default_dir, stage)
            
            # Apply format filter
            if format_filter:
                prompts = [p for p in prompts if p['format'] == format_filter]
            
            prompt_data[stage] = prompts
        
        # Add some default/built-in prompts if directories are empty
        if not prompt_data['stage3']:
            prompt_data['stage3'] = [
                {
                    'id': 'default_analysis',
                    'name': 'Default Content Analysis',
                    'type': 'builtin',
                    'stage': 'stage3',
                    'description': 'Standard content analysis prompt for segment identification'
                },
                {
                    'id': 'detailed_analysis',
                    'name': 'Detailed Analysis',
                    'type': 'builtin', 
                    'stage': 'stage3',
                    'description': 'In-depth analysis with additional context extraction'
                }
            ]
        
        if not prompt_data['stage4']:
            prompt_data['stage4'] = [
                {
                    'id': 'default_narrative',
                    'name': 'Default Narrative Generation',
                    'type': 'builtin',
                    'stage': 'stage4',
                    'description': 'Standard narrative prompt for podcast-style commentary'
                },
                {
                    'id': 'engaging_narrative',
                    'name': 'Engaging Commentary',
                    'type': 'builtin',
                    'stage': 'stage4', 
                    'description': 'More engaging and conversational narrative style'
                }
            ]
        
        total_prompts = len(prompt_data['stage3']) + len(prompt_data['stage4'])
        
        return jsonify({
            'success': True,
            'prompts': prompt_data,
            'total_count': total_prompts,
            'stage3_count': len(prompt_data['stage3']),
            'stage4_count': len(prompt_data['stage4'])
        })
        
    except Exception as e:
        logger.error(f"Error listing prompts: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to list prompts: {str(e)}'
        }), 500

@bp.route('/get/<stage>/<prompt_id>', methods=['GET'])
def get_prompt(stage: str, prompt_id: str):
    """
    Get detailed prompt information including content
    
    Args:
        stage: Stage identifier ('stage3' or 'stage4')
        prompt_id: Prompt identifier
    """
    try:
        if stage not in ['stage3', 'stage4']:
            return jsonify({
                'success': False,
                'error': 'Invalid stage. Must be stage3 or stage4'
            }), 400
        
        # First check if it's a built-in prompt
        builtin_prompts = {
            'stage3': {
                'default_analysis': {
                    'content': 'Analyze the provided content and identify key segments for extraction...',
                    'instructions': 'Focus on controversial, educational, or highly engaging moments.'
                },
                'detailed_analysis': {
                    'content': 'Perform detailed content analysis with context extraction...',
                    'instructions': 'Include speaker identification, topic categorization, and sentiment analysis.'
                }
            },
            'stage4': {
                'default_narrative': {
                    'content': 'Generate engaging podcast-style commentary for the selected segments...',
                    'instructions': 'Maintain conversational tone and provide context.'
                },
                'engaging_narrative': {
                    'content': 'Create highly engaging commentary with personality and flair...',
                    'instructions': 'Use dynamic language and strong hooks to maintain audience interest.'
                }
            }
        }
        
        if prompt_id in builtin_prompts.get(stage, {}):
            prompt_data = builtin_prompts[stage][prompt_id]
            return jsonify({
                'success': True,
                'prompt': {
                    'id': prompt_id,
                    'stage': stage,
                    'type': 'builtin',
                    'content': prompt_data['content'],
                    'instructions': prompt_data['instructions']
                }
            })
        
        # Check file-based prompts
        prompt_dir = DEFAULT_PROMPT_DIRS.get(stage)
        if not prompt_dir or not prompt_dir.exists():
            return jsonify({
                'success': False,
                'error': f'Prompt directory not found for {stage}'
            }), 404
        
        # Look for prompt file
        prompt_file = None
        for ext in ['.txt', '.md', '.json']:
            candidate = prompt_dir / f"{prompt_id}{ext}"
            if candidate.exists():
                prompt_file = candidate
                break
        
        if not prompt_file:
            return jsonify({
                'success': False,
                'error': f'Prompt not found: {prompt_id}'
            }), 404
        
        # Read prompt content
        with open(prompt_file, 'r', encoding='utf-8') as f:
            if prompt_file.suffix == '.json':
                data = json.load(f)
                if isinstance(data, dict):
                    content = data.get('content', '')
                    instructions = data.get('instructions', '')
                else:
                    content = str(data)
                    instructions = ''
            else:
                content = f.read()
                instructions = ''
        
        return jsonify({
            'success': True,
            'prompt': {
                'id': prompt_id,
                'stage': stage,
                'type': 'file',
                'filename': prompt_file.name,
                'content': content,
                'instructions': instructions,
                'path': str(prompt_file)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting prompt {stage}/{prompt_id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get prompt: {str(e)}'
        }), 500

@bp.route('/create', methods=['POST'])
def create_custom_prompt():
    """
    Create a new custom prompt
    
    Expected JSON data:
    - stage: Target stage ('stage3' or 'stage4')
    - name: Prompt name
    - content: Prompt content
    - instructions: Optional instructions
    - description: Optional description
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        stage = data.get('stage', '')
        name = data.get('name', '').strip()
        content = data.get('content', '').strip()
        instructions = data.get('instructions', '').strip()
        description = data.get('description', '').strip()
        
        if stage not in ['stage3', 'stage4']:
            return jsonify({
                'success': False,
                'error': 'Invalid stage. Must be stage3 or stage4'
            }), 400
        
        if not name or not content:
            return jsonify({
                'success': False,
                'error': 'Name and content are required'
            }), 400
        
        # Create custom prompts directory
        custom_prompts_dir = Path('Code/UI/custom_prompts') / stage
        custom_prompts_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename from name
        filename = name.lower().replace(' ', '_').replace('/', '_').replace('\\', '_')
        filename = ''.join(c for c in filename if c.isalnum() or c in ['_', '-'])
        prompt_file = custom_prompts_dir / f"{filename}.json"
        
        # Ensure unique filename
        counter = 1
        while prompt_file.exists():
            prompt_file = custom_prompts_dir / f"{filename}_{counter}.json"
            counter += 1
        
        # Create prompt data
        prompt_data = {
            'id': prompt_file.stem,
            'name': name,
            'description': description,
            'stage': stage,
            'type': 'custom',
            'content': content,
            'instructions': instructions,
            'created_at': os.path.getmtime(prompt_file) if prompt_file.exists() else None,
            'author': 'Custom',
            'version': '1.0'
        }
        
        # Save prompt file
        with open(prompt_file, 'w', encoding='utf-8') as f:
            json.dump(prompt_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Created custom prompt: {stage}/{prompt_file.stem}")
        
        return jsonify({
            'success': True,
            'prompt': prompt_data,
            'path': str(prompt_file),
            'message': f'Custom prompt "{name}" created successfully'
        })
        
    except Exception as e:
        logger.error(f"Error creating custom prompt: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to create prompt: {str(e)}'
        }), 500

@bp.route('/delete/<stage>/<prompt_id>', methods=['DELETE'])
def delete_prompt(stage: str, prompt_id: str):
    """
    Delete a custom prompt (built-in prompts cannot be deleted)
    
    Args:
        stage: Stage identifier ('stage3' or 'stage4')
        prompt_id: Prompt identifier
    """
    try:
        if stage not in ['stage3', 'stage4']:
            return jsonify({
                'success': False,
                'error': 'Invalid stage. Must be stage3 or stage4'
            }), 400
        
        # Check if it's a built-in prompt (cannot delete)
        builtin_prompts = ['default_analysis', 'detailed_analysis', 'default_narrative', 'engaging_narrative']
        if prompt_id in builtin_prompts:
            return jsonify({
                'success': False,
                'error': 'Cannot delete built-in prompts'
            }), 400
        
        # Look for custom prompt file
        custom_prompts_dir = Path('Code/UI/custom_prompts') / stage
        
        prompt_file = None
        for ext in ['.json', '.txt', '.md']:
            candidate = custom_prompts_dir / f"{prompt_id}{ext}"
            if candidate.exists():
                prompt_file = candidate
                break
        
        if not prompt_file:
            return jsonify({
                'success': False,
                'error': f'Custom prompt not found: {prompt_id}'
            }), 404
        
        # Delete the file
        prompt_file.unlink()
        
        logger.info(f"Deleted custom prompt: {stage}/{prompt_id}")
        
        return jsonify({
            'success': True,
            'message': f'Custom prompt "{prompt_id}" deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting prompt {stage}/{prompt_id}: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to delete prompt: {str(e)}'
        }), 500

@bp.route('/validate', methods=['POST'])
def validate_prompt():
    """
    Validate prompt content and structure
    
    Expected JSON data:
    - stage: Target stage
    - content: Prompt content to validate
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        stage = data.get('stage', '')
        content = data.get('content', '').strip()
        
        if stage not in ['stage3', 'stage4']:
            return jsonify({
                'success': False,
                'error': 'Invalid stage. Must be stage3 or stage4'
            }), 400
        
        if not content:
            return jsonify({
                'success': False,
                'error': 'Content is required for validation'
            }), 400
        
        # Basic validation rules
        validation_results = {
            'valid': True,
            'warnings': [],
            'suggestions': [],
            'stats': {
                'length': len(content),
                'words': len(content.split()),
                'lines': len(content.split('\n'))
            }
        }
        
        # Length checks
        if len(content) < 50:
            validation_results['warnings'].append('Prompt is very short - consider adding more detail')
        elif len(content) > 5000:
            validation_results['warnings'].append('Prompt is very long - consider condensing for better performance')
        
        # Stage-specific validation
        if stage == 'stage3':
            required_keywords = ['analyze', 'content', 'segment', 'identify']
            missing_keywords = [kw for kw in required_keywords if kw.lower() not in content.lower()]
            if missing_keywords:
                validation_results['suggestions'].append(f'Consider including keywords: {", ".join(missing_keywords)}')
        
        elif stage == 'stage4':
            required_keywords = ['narrative', 'commentary', 'generate', 'podcast']
            missing_keywords = [kw for kw in required_keywords if kw.lower() not in content.lower()]
            if missing_keywords:
                validation_results['suggestions'].append(f'Consider including keywords: {", ".join(missing_keywords)}')
        
        return jsonify({
            'success': True,
            'validation': validation_results
        })
        
    except Exception as e:
        logger.error(f"Error validating prompt: {e}")
        return jsonify({
            'success': False,
            'error': f'Validation failed: {str(e)}'
        }), 500
