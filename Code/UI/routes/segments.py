"""
Segment Selection Routes
YouTube Pipeline UI - Manual Segment Selection Interface

This module handles the manual segment selection interface for fine-tuned
control over video content selection and narrative customization.

Created: June 20, 2025
Agent: Implementation Agent
Task Reference: Phase 1, Task 1.1 - Core Flask Application Setup
"""

from flask import Blueprint, render_template, request, jsonify, current_app
import json
from pathlib import Path
from services.segment_parser import SegmentParserInterface

bp = Blueprint('segments', __name__)

@bp.route('/')
def segments_dashboard():
    """
    Segment selection dashboard.
    
    Main interface for manual segment selection, timeline visualization,
    and segment-based narrative control.
    """
    try:
        return render_template('segments/dashboard.html')
    
    except Exception as e:
        current_app.logger.error(f"Segments dashboard error: {e}")
        return render_template('segments/dashboard.html', error=str(e))

@bp.route('/episode/<path:episode_path>')
def episode_segments(episode_path):
    """
    Display segments for a specific episode.
    
    Args:
        episode_path (str): Path to the episode directory
        
    Returns:
        Rendered template with episode segment data
    """
    try:
        episode_dir = Path(episode_path)
        processing_dir = episode_dir / 'Processing'
        
        # Check if episode exists and has processing data
        if not episode_dir.exists():
            return render_template('segments/episode.html', 
                                 error='Episode not found', 
                                 episode_path=episode_path)
        
        # Initialize segment parser interface
        parser_interface = SegmentParserInterface()
        
        # Load episode analysis if available
        segment_data = {
            'episode_path': episode_path,
            'episode_name': episode_dir.name,
            'show_name': episode_dir.parent.name,
            'has_transcript': _check_file_exists(processing_dir, '*transcript*'),
            'has_analysis': _check_file_exists(processing_dir, '*analysis*'),
            'segments': [],
            'statistics': {},
            'timeline_ready': False,
            'parser_loaded': False,
            'error': None
        }
        
        # Try to load segment analysis
        if parser_interface.load_episode_analysis(episode_path):
            segment_data['parser_loaded'] = True
            segment_data['timeline_ready'] = True
            
            # Get segments and statistics
            segments = parser_interface.get_sorted_segments('timestamp')
            segment_data['segments'] = [parser_interface._format_segment_for_ui(s) for s in segments]
            segment_data['statistics'] = parser_interface.get_overview_stats()
            
            current_app.logger.info(f"Loaded {len(segments)} segments for {episode_path}")
        else:
            # Get error status from parser
            status = parser_interface.get_status()
            if status['errors']:
                segment_data['error'] = status['errors'][-1]  # Show latest error
            else:
                segment_data['error'] = 'No analysis data available for this episode'
        
        return render_template('segments/episode.html', data=segment_data)
    
    except Exception as e:
        current_app.logger.error(f"Episode segments error: {e}")
        return render_template('segments/episode.html', 
                             error=str(e), 
                             episode_path=episode_path)

@bp.route('/api/segments/<path:episode_path>')
def get_segments_api(episode_path):
    """
    API endpoint to get segment data for an episode.
    
    Args:
        episode_path (str): Path to the episode directory
        
    Returns:
        JSON response with segment information
    """
    try:
        episode_dir = Path(episode_path)
        
        if not episode_dir.exists():
            return jsonify({'error': 'Episode not found'}), 404
        
        # Initialize segment parser interface
        parser_interface = SegmentParserInterface()
        
        if parser_interface.load_episode_analysis(episode_path):
            # Get sorted segments based on query parameters
            sort_by = request.args.get('sort_by', 'timestamp')
            reverse_sort = request.args.get('reverse', 'false').lower() == 'true'
            
            segments = parser_interface.get_sorted_segments(sort_by, reverse_sort)
            statistics = parser_interface.get_overview_stats()
            
            response = {
                'success': True,
                'episode_path': episode_path,
                'segments': [parser_interface._format_segment_for_ui(s) for s in segments],
                'statistics': statistics,
                'sort_by': sort_by,
                'reverse': reverse_sort
            }
        else:
            status = parser_interface.get_status()
            response = {
                'success': False,
                'error': 'Failed to load segment analysis',
                'details': status.get('errors', [])
            }
        
        return jsonify(response)
    
    except Exception as e:
        current_app.logger.error(f"Segments API error: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/segments/<path:episode_path>/select', methods=['POST'])
def select_segments(episode_path):
    """
    Save segment selection for an episode.
    
    Args:
        episode_path (str): Path to the episode directory
        
    Returns:
        JSON response confirming segment selection
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No selection data provided'}), 400
        
        selected_segment_ids = data.get('selected_segments', [])
        
        if not selected_segment_ids:
            return jsonify({'error': 'No segments selected'}), 400
        
        # Initialize segment parser interface
        parser_interface = SegmentParserInterface()
        
        if not parser_interface.load_episode_analysis(episode_path):
            return jsonify({'error': 'Failed to load episode analysis'}), 404
        
        # Save selection using parser interface
        success = parser_interface.save_segment_selection(selected_segment_ids)
        
        if success:
            # Get selection summary
            selected_segments = parser_interface.get_selected_segments()
            total_duration = sum(s.segmentDurationInSeconds for s in selected_segments)
            
            response = {
                'success': True,
                'episode_path': episode_path,
                'selected_count': len(selected_segments),
                'total_duration': round(total_duration, 2),
                'output_path': parser_interface.get_output_path(),
                'message': f'Successfully saved {len(selected_segments)} segments'
            }
            
            current_app.logger.info(f"Saved segment selection: {episode_path}, {len(selected_segments)} segments, {total_duration:.2f}s")
        else:
            status = parser_interface.get_status()
            response = {
                'success': False,
                'error': 'Failed to save segment selection',
                'details': status.get('errors', [])
            }
        
        return jsonify(response)
    
    except Exception as e:
        current_app.logger.error(f"Segment selection error: {e}")
        return jsonify({'error': str(e)}), 500

def _check_file_exists(directory, pattern):
    """
    Helper function to check if files matching a pattern exist.
    
    Args:
        directory (Path): Directory to search in
        pattern (str): Glob pattern to match
        
    Returns:
        bool: True if matching files exist
    """
    try:
        if not directory or not directory.exists():
            return False
        
        return len(list(directory.glob(pattern))) > 0
    
    except Exception:
        return False
