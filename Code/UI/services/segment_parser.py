"""
Segment Parser Service for YouTube Pipeline UI
Handles parsing, validation, sorting, and filtering of analysis JSON files
"""

import json
import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class HarmCategory:
    """Data model for harm category information"""
    primary_type: str
    misinformation_subtype: Optional[List[str]] = None
    conspiracy_theme: Optional[List[str]] = None

@dataclass
class QuoteClip:
    """Data model for individual quote clips"""
    timestamp: float
    speaker: str
    quote: str

@dataclass
class TimestampRange:
    """Data model for fuller context timestamps"""
    start: float
    end: float

@dataclass
class AnalysisSegment:
    """Data model for analysis segment with all metadata"""
    segment_id: str
    narrativeSegmentTitle: str
    guest_name: str
    primary_speaker_of_quote: str
    severityRating: str
    harm_category: HarmCategory
    identified_rhetorical_strategies: List[str]
    potential_societal_impacts: List[str]
    confidence_in_classification: str
    brief_reasoning_for_classification: str
    clipContextDescription: str
    suggestedClip: List[QuoteClip]
    fullerContextTimestamps: TimestampRange
    segmentDurationInSeconds: float
    
    @property
    def sort_timestamp(self) -> float:
        """Get the primary timestamp for sorting (start of fuller context)"""
        return self.fullerContextTimestamps.start

class SegmentParser:
    """
    Comprehensive JSON parser for analysis segments with sorting, filtering, and validation
    """
    
    # Severity rating order for sorting (most severe first)
    SEVERITY_ORDER = {
        "CRITICAL": 0,
        "HIGH": 1,
        "MEDIUM": 2,
        "LOW": 3
    }
    
    def __init__(self):
        self.segments: List[AnalysisSegment] = []
        self.parsing_errors: List[str] = []
        self.validation_warnings: List[str] = []
    
    def parse_json_file(self, file_path: str) -> bool:
        """
        Parse analysis JSON file and load segments
        
        Args:
            file_path: Path to the original_audio_analysis_results.json file
            
        Returns:
            bool: True if parsing successful, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                error_msg = f"Analysis file not found: {file_path}"
                logger.error(error_msg)
                self.parsing_errors.append(error_msg)
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            
            if not isinstance(raw_data, list):
                error_msg = "Expected JSON array format for segments"
                logger.error(error_msg)
                self.parsing_errors.append(error_msg)
                return False
            
            self.segments = []
            self.parsing_errors = []
            self.validation_warnings = []
            
            for i, segment_data in enumerate(raw_data):
                try:
                    segment = self._parse_segment(segment_data, i)
                    if segment:
                        self.segments.append(segment)
                except Exception as e:
                    error_msg = f"Error parsing segment {i}: {str(e)}"
                    logger.error(error_msg)
                    self.parsing_errors.append(error_msg)
            
            # Sort by default order (timestamp)
            self.sort_segments('timestamp')
            
            success_msg = f"Successfully parsed {len(self.segments)} segments from {file_path}"
            logger.info(success_msg)
            
            if self.parsing_errors:
                logger.warning(f"Parsing completed with {len(self.parsing_errors)} errors")
            
            if self.validation_warnings:
                logger.warning(f"Parsing completed with {len(self.validation_warnings)} warnings")
            
            return True
            
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON format: {str(e)}"
            logger.error(error_msg)
            self.parsing_errors.append(error_msg)
            return False
        except Exception as e:
            error_msg = f"Unexpected error parsing file: {str(e)}"
            logger.error(error_msg)
            self.parsing_errors.append(error_msg)
            return False
    
    def _parse_segment(self, data: Dict[str, Any], index: int) -> Optional[AnalysisSegment]:
        """
        Parse individual segment data with validation
        
        Args:
            data: Raw segment data dictionary
            index: Segment index for error reporting
            
        Returns:
            AnalysisSegment object or None if parsing fails
        """
        try:
            # Validate required fields
            required_fields = [
                'segment_id', 'narrativeSegmentTitle', 'severityRating',
                'harm_category', 'confidence_in_classification',
                'brief_reasoning_for_classification', 'clipContextDescription',
                'fullerContextTimestamps', 'segmentDurationInSeconds'
            ]
            
            for field in required_fields:
                if field not in data:
                    warning_msg = f"Segment {index}: Missing required field '{field}'"
                    logger.warning(warning_msg)
                    self.validation_warnings.append(warning_msg)
            
            # Parse harm category
            harm_category_data = data.get('harm_category', {})
            harm_category = HarmCategory(
                primary_type=harm_category_data.get('primary_type', 'Unknown'),
                misinformation_subtype=harm_category_data.get('misinformation_subtype'),
                conspiracy_theme=harm_category_data.get('conspiracy_theme')
            )
            
            # Parse suggested clips
            suggested_clips = []
            for clip_data in data.get('suggestedClip', []):
                try:
                    clip = QuoteClip(
                        timestamp=float(clip_data.get('timestamp', 0)),
                        speaker=clip_data.get('speaker', 'Unknown'),
                        quote=clip_data.get('quote', '')
                    )
                    suggested_clips.append(clip)
                except (ValueError, TypeError) as e:
                    warning_msg = f"Segment {index}: Invalid clip data: {str(e)}"
                    logger.warning(warning_msg)
                    self.validation_warnings.append(warning_msg)
            
            # Parse fuller context timestamps
            timestamps_data = data.get('fullerContextTimestamps', {})
            fuller_timestamps = TimestampRange(
                start=float(timestamps_data.get('start', 0)),
                end=float(timestamps_data.get('end', 0))
            )
            
            # Validate timestamp consistency
            if fuller_timestamps.end <= fuller_timestamps.start:
                warning_msg = f"Segment {index}: Invalid timestamp range"
                logger.warning(warning_msg)
                self.validation_warnings.append(warning_msg)
            
            # Create segment object
            segment = AnalysisSegment(
                segment_id=data.get('segment_id', f'segment_{index}'),
                narrativeSegmentTitle=data.get('narrativeSegmentTitle', 'Untitled Segment'),
                guest_name=data.get('guest_name', 'Unknown'),
                primary_speaker_of_quote=data.get('primary_speaker_of_quote', 'Unknown'),
                severityRating=data.get('severityRating', 'MEDIUM'),
                harm_category=harm_category,
                identified_rhetorical_strategies=data.get('identified_rhetorical_strategies', []),
                potential_societal_impacts=data.get('potential_societal_impacts', []),
                confidence_in_classification=data.get('confidence_in_classification', 'Unknown'),
                brief_reasoning_for_classification=data.get('brief_reasoning_for_classification', ''),
                clipContextDescription=data.get('clipContextDescription', ''),
                suggestedClip=suggested_clips,
                fullerContextTimestamps=fuller_timestamps,
                segmentDurationInSeconds=float(data.get('segmentDurationInSeconds', 0))
            )
            
            return segment
            
        except Exception as e:
            error_msg = f"Failed to parse segment {index}: {str(e)}"
            logger.error(error_msg)
            self.parsing_errors.append(error_msg)
            return None
    
    def sort_segments(self, sort_by: str, reverse: bool = False) -> None:
        """
        Sort segments by specified criteria
        
        Args:
            sort_by: Sort criteria ('severity', 'duration', 'speaker', 'category', 'confidence', 'timestamp')
            reverse: Sort in reverse order
        """
        try:
            if sort_by == 'severity':
                self.segments.sort(
                    key=lambda s: self.SEVERITY_ORDER.get(s.severityRating, 999),
                    reverse=reverse
                )
            elif sort_by == 'duration':
                self.segments.sort(
                    key=lambda s: s.segmentDurationInSeconds,
                    reverse=reverse
                )
            elif sort_by == 'speaker':
                self.segments.sort(
                    key=lambda s: s.primary_speaker_of_quote.lower(),
                    reverse=reverse
                )
            elif sort_by == 'category':
                self.segments.sort(
                    key=lambda s: s.harm_category.primary_type.lower(),
                    reverse=reverse
                )
            elif sort_by == 'confidence':
                # Sort by confidence level (High, Medium, Low, Unknown)
                confidence_order = {"High": 0, "Medium": 1, "Low": 2, "Unknown": 3}
                self.segments.sort(
                    key=lambda s: confidence_order.get(s.confidence_in_classification, 999),
                    reverse=reverse
                )
            elif sort_by == 'timestamp':
                self.segments.sort(
                    key=lambda s: s.sort_timestamp,
                    reverse=reverse
                )
            else:
                logger.warning(f"Unknown sort criteria: {sort_by}")
                
            logger.info(f"Segments sorted by {sort_by} (reverse={reverse})")
            
        except Exception as e:
            error_msg = f"Error sorting segments: {str(e)}"
            logger.error(error_msg)
            self.parsing_errors.append(error_msg)
    
    def filter_segments(self, 
                       severity_filter: Optional[List[str]] = None,
                       category_filter: Optional[List[str]] = None,
                       speaker_filter: Optional[List[str]] = None,
                       confidence_filter: Optional[List[str]] = None,
                       min_duration: Optional[float] = None,
                       max_duration: Optional[float] = None) -> List[AnalysisSegment]:
        """
        Filter segments based on various criteria
        
        Args:
            severity_filter: List of severity levels to include
            category_filter: List of harm categories to include
            speaker_filter: List of speakers to include
            confidence_filter: List of confidence levels to include
            min_duration: Minimum segment duration in seconds
            max_duration: Maximum segment duration in seconds
            
        Returns:
            List of filtered segments
        """
        filtered_segments = self.segments.copy()
        
        try:
            if severity_filter:
                filtered_segments = [s for s in filtered_segments if s.severityRating in severity_filter]
            
            if category_filter:
                filtered_segments = [s for s in filtered_segments if s.harm_category.primary_type in category_filter]
            
            if speaker_filter:
                filtered_segments = [s for s in filtered_segments if s.primary_speaker_of_quote in speaker_filter]
            
            if confidence_filter:
                filtered_segments = [s for s in filtered_segments if s.confidence_in_classification in confidence_filter]
            
            if min_duration is not None:
                filtered_segments = [s for s in filtered_segments if s.segmentDurationInSeconds >= min_duration]
            
            if max_duration is not None:
                filtered_segments = [s for s in filtered_segments if s.segmentDurationInSeconds <= max_duration]
            
            logger.info(f"Filtered segments: {len(filtered_segments)} of {len(self.segments)} segments match criteria")
            return filtered_segments
            
        except Exception as e:
            error_msg = f"Error filtering segments: {str(e)}"
            logger.error(error_msg)
            self.parsing_errors.append(error_msg)
            return self.segments
    
    def get_segment_statistics(self) -> Dict[str, Any]:
        """
        Calculate segment statistics and overview
        
        Returns:
            Dictionary containing segment statistics
        """
        if not self.segments:
            return {
                'total_segments': 0,
                'total_duration': 0,
                'severity_breakdown': {},
                'category_breakdown': {},
                'speaker_breakdown': {},
                'confidence_breakdown': {},
                'duration_stats': {}
            }
        
        try:
            total_duration = sum(s.segmentDurationInSeconds for s in self.segments)
            
            # Count by severity
            severity_counts = {}
            for segment in self.segments:
                severity = segment.severityRating
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Count by category
            category_counts = {}
            for segment in self.segments:
                category = segment.harm_category.primary_type
                category_counts[category] = category_counts.get(category, 0) + 1
            
            # Count by speaker
            speaker_counts = {}
            for segment in self.segments:
                speaker = segment.primary_speaker_of_quote
                speaker_counts[speaker] = speaker_counts.get(speaker, 0) + 1
            
            # Count by confidence
            confidence_counts = {}
            for segment in self.segments:
                confidence = segment.confidence_in_classification
                confidence_counts[confidence] = confidence_counts.get(confidence, 0) + 1
            
            # Duration statistics
            durations = [s.segmentDurationInSeconds for s in self.segments]
            duration_stats = {
                'min': min(durations),
                'max': max(durations),
                'average': sum(durations) / len(durations),
                'median': sorted(durations)[len(durations) // 2]
            }
            
            stats = {
                'total_segments': len(self.segments),
                'total_duration': round(total_duration, 2),
                'severity_breakdown': severity_counts,
                'category_breakdown': category_counts,
                'speaker_breakdown': speaker_counts,
                'confidence_breakdown': confidence_counts,
                'duration_stats': {k: round(v, 2) for k, v in duration_stats.items()}
            }
            
            logger.info(f"Generated statistics for {len(self.segments)} segments")
            return stats
            
        except Exception as e:
            error_msg = f"Error calculating statistics: {str(e)}"
            logger.error(error_msg)
            self.parsing_errors.append(error_msg)
            return {}
    
    def save_selected_segments(self, selected_segment_ids: List[str], output_path: str) -> bool:
        """
        Save selected segments to JSON file in pipeline-compatible format
        
        Args:
            selected_segment_ids: List of segment IDs to include in output
            output_path: Path to save the selected_segments.json file
            
        Returns:
            bool: True if save successful, False otherwise
        """
        try:
            # Filter segments by selected IDs
            selected_segments = [s for s in self.segments if s.segment_id in selected_segment_ids]
            
            if not selected_segments:
                warning_msg = "No segments selected for output"
                logger.warning(warning_msg)
                self.validation_warnings.append(warning_msg)
                return False
            
            # Convert segments back to original JSON format
            output_data = []
            for segment in selected_segments:
                # Convert harm category back to dict
                harm_category_dict = {
                    'primary_type': segment.harm_category.primary_type
                }
                if segment.harm_category.misinformation_subtype:
                    harm_category_dict['misinformation_subtype'] = segment.harm_category.misinformation_subtype
                if segment.harm_category.conspiracy_theme:
                    harm_category_dict['conspiracy_theme'] = segment.harm_category.conspiracy_theme
                
                # Convert quote clips back to dict format
                suggested_clips = []
                for clip in segment.suggestedClip:
                    suggested_clips.append({
                        'timestamp': clip.timestamp,
                        'speaker': clip.speaker,
                        'quote': clip.quote
                    })
                
                # Build segment data in original format
                segment_data = {
                    'segment_id': segment.segment_id,
                    'narrativeSegmentTitle': segment.narrativeSegmentTitle,
                    'guest_name': segment.guest_name,
                    'primary_speaker_of_quote': segment.primary_speaker_of_quote,
                    'severityRating': segment.severityRating,
                    'harm_category': harm_category_dict,
                    'identified_rhetorical_strategies': segment.identified_rhetorical_strategies,
                    'potential_societal_impacts': segment.potential_societal_impacts,
                    'confidence_in_classification': segment.confidence_in_classification,
                    'brief_reasoning_for_classification': segment.brief_reasoning_for_classification,
                    'clipContextDescription': segment.clipContextDescription,
                    'suggestedClip': suggested_clips,
                    'fullerContextTimestamps': {
                        'start': segment.fullerContextTimestamps.start,
                        'end': segment.fullerContextTimestamps.end
                    },
                    'segmentDurationInSeconds': segment.segmentDurationInSeconds
                }
                
                output_data.append(segment_data)
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save to file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            success_msg = f"Successfully saved {len(selected_segments)} selected segments to {output_path}"
            logger.info(success_msg)
            return True
            
        except Exception as e:
            error_msg = f"Error saving selected segments: {str(e)}"
            logger.error(error_msg)
            self.parsing_errors.append(error_msg)
            return False
    
    def get_segments(self) -> List[AnalysisSegment]:
        """Get all loaded segments"""
        return self.segments.copy()
    
    def get_segment_by_id(self, segment_id: str) -> Optional[AnalysisSegment]:
        """Get specific segment by ID"""
        for segment in self.segments:
            if segment.segment_id == segment_id:
                return segment
        return None
    
    def get_parsing_errors(self) -> List[str]:
        """Get list of parsing errors"""
        return self.parsing_errors.copy()
    
    def get_validation_warnings(self) -> List[str]:
        """Get list of validation warnings"""
        return self.validation_warnings.copy()
    
    def validate_selection(self, segment_ids: List[str]) -> Tuple[List[str], List[str]]:
        """
        Validate segment selection for completeness and integrity
        
        Args:
            segment_ids: List of segment IDs to validate
            
        Returns:
            Tuple of (valid_ids, invalid_ids)
        """
        valid_ids = []
        invalid_ids = []
        
        available_ids = {s.segment_id for s in self.segments}
        
        for segment_id in segment_ids:
            if segment_id in available_ids:
                valid_ids.append(segment_id)
            else:
                invalid_ids.append(segment_id)
        
        if invalid_ids:
            logger.warning(f"Invalid segment IDs: {invalid_ids}")
        
        logger.info(f"Selection validation: {len(valid_ids)} valid, {len(invalid_ids)} invalid")
        return valid_ids, invalid_ids

# Integration interface for UI components
class SegmentParserInterface:
    """
    High-level interface for UI integration
    Provides simplified methods for common operations
    """
    
    def __init__(self):
        self.parser = SegmentParser()
        self.current_episode_path = None
    
    def load_episode_analysis(self, episode_path: str) -> bool:
        """
        Load analysis for specific episode
        
        Args:
            episode_path: Path to episode folder (e.g., Content/Joe_Rogan_Experience/Episode_Name/)
            
        Returns:
            bool: Success status
        """
        analysis_file = os.path.join(episode_path, 'Processing', 'original_audio_analysis_results.json')
        
        if self.parser.parse_json_file(analysis_file):
            self.current_episode_path = episode_path
            return True
        return False
    
    def get_sorted_segments(self, sort_by: str = 'timestamp', reverse: bool = False) -> List[Dict[str, Any]]:
        """
        Get segments sorted by criteria, formatted for UI consumption
        
        Args:
            sort_by: Sort criteria
            reverse: Reverse sort order
            
        Returns:
            List of segment dictionaries
        """
        self.parser.sort_segments(sort_by, reverse)
        segments = self.parser.get_segments()
        
        # Convert to UI-friendly format
        ui_segments = []
        for segment in segments:
            ui_segment = {
                'id': segment.segment_id,
                'title': segment.narrativeSegmentTitle,
                'severity': segment.severityRating,
                'duration': segment.segmentDurationInSeconds,
                'speaker': segment.primary_speaker_of_quote,
                'category': segment.harm_category.primary_type,
                'confidence': segment.confidence_in_classification,
                'start_time': segment.fullerContextTimestamps.start,
                'end_time': segment.fullerContextTimestamps.end,
                'description': segment.clipContextDescription,
                'reasoning': segment.brief_reasoning_for_classification,
                'quote_count': len(segment.suggestedClip)
            }
            ui_segments.append(ui_segment)
        
        return ui_segments
    
    def save_segment_selection(self, segment_ids: List[str]) -> bool:
        """
        Save selected segments for pipeline processing
        
        Args:
            segment_ids: List of selected segment IDs
            
        Returns:
            bool: Success status
        """
        if not self.current_episode_path:
            logger.error("No episode loaded")
            return False
        
        output_path = os.path.join(self.current_episode_path, 'Processing', 'selected_segments.json')
        return self.parser.save_selected_segments(segment_ids, output_path)
    
    def get_overview_stats(self) -> Dict[str, Any]:
        """Get overview statistics for UI dashboard"""
        return self.parser.get_segment_statistics()
    
    def get_status(self) -> Dict[str, Any]:
        """Get parser status and error information"""
        return {
            'segments_loaded': len(self.parser.segments),
            'errors': self.parser.get_parsing_errors(),
            'warnings': self.parser.get_validation_warnings(),
            'current_episode': self.current_episode_path
        }
    
    def _format_segment_for_ui(self, segment: AnalysisSegment) -> Dict[str, Any]:
        """Format segment data for UI consumption"""
        return {
            'segment_id': segment.segment_id,
            'narrativeSegmentTitle': segment.narrativeSegmentTitle,
            'guest_name': segment.guest_name,
            'primary_speaker_of_quote': segment.primary_speaker_of_quote,
            'severityRating': segment.severityRating,
            'harm_category': {
                'primary_type': segment.harm_category.primary_type,
                'misinformation_subtype': segment.harm_category.misinformation_subtype,
                'conspiracy_theme': segment.harm_category.conspiracy_theme
            },
            'identified_rhetorical_strategies': segment.identified_rhetorical_strategies,
            'potential_societal_impacts': segment.potential_societal_impacts,
            'confidence_in_classification': segment.confidence_in_classification,
            'brief_reasoning_for_classification': segment.brief_reasoning_for_classification,
            'clipContextDescription': segment.clipContextDescription,
            'suggestedClip': [
                {
                    'timestamp': clip.timestamp,
                    'speaker': clip.speaker,
                    'quote': clip.quote
                } for clip in segment.suggestedClip
            ],
            'fullerContextTimestamps': {
                'start': segment.fullerContextTimestamps.start,
                'end': segment.fullerContextTimestamps.end
            },
            'segmentDurationInSeconds': segment.segmentDurationInSeconds,
            'formatted_duration': self._format_duration(segment.segmentDurationInSeconds),
            'formatted_timestamp': self._format_timestamp(segment.fullerContextTimestamps.start)
        }
    
    def get_selected_segments(self) -> List[AnalysisSegment]:
        """Get currently selected segments"""
        # This would need to be implemented with selection state management
        # For now, return empty list as placeholder
        return []
    
    def get_output_path(self) -> str:
        """Get the output path for selected segments"""
        if self.current_episode_path:
            return os.path.join(self.current_episode_path, 'Processing', 'selected_segments.json')
        return ""
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds to human-readable format"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            remaining_seconds = seconds % 60
            return f"{minutes}m {remaining_seconds:.1f}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            remaining_seconds = seconds % 60
            return f"{hours}h {minutes}m {remaining_seconds:.1f}s"
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format timestamp to MM:SS or HH:MM:SS format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"

# Example usage and testing function
if __name__ == "__main__":
    # Test with real data
    test_episode_path = r"C:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Content\Joe_Rogan_Experience\Joe Rogan Experience #2339 - Luis J. Gomez & Big Jay Oakerson"
    
    # Test using the interface
    interface = SegmentParserInterface()
    
    print("Testing Segment Parser with real episode data...")
    
    # Load episode analysis
    if interface.load_episode_analysis(test_episode_path):
        print("✓ Successfully loaded episode analysis")
        
        # Get overview statistics
        stats = interface.get_overview_stats()
        print(f"✓ Episode contains {stats['total_segments']} segments")
        print(f"✓ Total duration: {stats['total_duration']} seconds")
        print(f"✓ Severity breakdown: {stats['severity_breakdown']}")
        
        # Test sorting
        segments = interface.get_sorted_segments('severity')
        print(f"✓ Sorted by severity: {len(segments)} segments")
        
        # Test filtering (using direct parser)
        critical_segments = interface.parser.filter_segments(severity_filter=['CRITICAL'])
        print(f"✓ Critical segments: {len(critical_segments)}")
        
        # Test selection validation
        test_ids = [s.segment_id for s in interface.parser.segments[:3]]  # First 3 segments
        valid_ids, invalid_ids = interface.parser.validate_selection(test_ids)
        print(f"✓ Selection validation: {len(valid_ids)} valid, {len(invalid_ids)} invalid")
        
        # Test saving selected segments
        if interface.save_segment_selection(test_ids):
            print("✓ Successfully saved selected segments")
        
        # Display status
        status = interface.get_status()
        print(f"✓ Parser Status: {status['segments_loaded']} segments loaded")
        if status['errors']:
            print(f"⚠ Parsing errors: {len(status['errors'])}")
        if status['warnings']:
            print(f"⚠ Validation warnings: {len(status['warnings'])}")
            
    else:
        print("✗ Failed to load episode analysis")
        status = interface.get_status()
        for error in status['errors']:
            print(f"Error: {error}")
