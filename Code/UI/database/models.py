"""
Database Models for YouTube Pipeline UI
======================================

SQLAlchemy models for session tracking and workflow preset management.
Supports pipeline execution monitoring and state persistence.

Created: June 20, 2025
Agent: Implementation Agent
Task Reference: Phase 1, Task 1.2 - Database Models & Session Management
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import JSON, Text
from sqlalchemy.sql import func

db = SQLAlchemy()

class PipelineSession(db.Model):
    """
    Model for tracking pipeline execution sessions.
    
    Tracks the 7-stage pipeline progress for each episode:
    1. Audio Extraction
    2. Content Analysis  
    3. Segment Identification
    4. Segment Selection
    5. Audio Generation
    6. Video Compilation
    7. Final Output
    """
    __tablename__ = 'pipeline_sessions'
    
    # Primary Key
    session_id = db.Column(db.String(36), primary_key=True)  # UUID format
    
    # Episode Information
    episode_path = db.Column(db.String(500), nullable=False, index=True)
    episode_title = db.Column(db.String(200))
    show_name = db.Column(db.String(100), index=True)
    
    # Pipeline Stage Tracking (JSON field for 7-stage status)
    # Format: {"stage_1": "completed", "stage_2": "in_progress", "stage_3": "pending", ...}
    stage_status = db.Column(JSON, nullable=False, default={
        "stage_1_audio_extraction": "pending",
        "stage_2_content_analysis": "pending", 
        "stage_3_segment_identification": "pending",
        "stage_4_segment_selection": "pending",
        "stage_5_audio_generation": "pending",
        "stage_6_video_compilation": "pending",
        "stage_7_final_output": "pending"
    })
    
    # Session Metadata
    status = db.Column(db.String(20), default='initialized')  # initialized, running, completed, failed
    progress_percentage = db.Column(db.Integer, default=0)
    current_stage = db.Column(db.Integer, default=1)  # Current stage being processed (1-7)
    
    # Error Tracking
    error_message = db.Column(Text)
    last_error_stage = db.Column(db.Integer)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # Configuration References
    preset_id = db.Column(db.String(36), db.ForeignKey('preset_configurations.preset_id'))
    
    def __repr__(self):
        return f'<PipelineSession {self.session_id}: {self.episode_title}>'
    
    def get_stage_progress(self):
        """Calculate overall progress based on completed stages."""
        completed_stages = sum(1 for status in self.stage_status.values() if status == 'completed')
        return (completed_stages / 7) * 100
    
    def update_stage_status(self, stage_key, status):
        """Update the status of a specific pipeline stage."""
        if stage_key in self.stage_status:
            stage_status_copy = self.stage_status.copy()
            stage_status_copy[stage_key] = status
            self.stage_status = stage_status_copy
            self.progress_percentage = self.get_stage_progress()
            self.updated_at = datetime.utcnow()
    
    def get_current_stage_name(self):
        """Get human-readable name for current stage."""
        stage_names = {
            1: "Audio Extraction",
            2: "Content Analysis", 
            3: "Segment Identification",
            4: "Segment Selection",
            5: "Audio Generation",
            6: "Video Compilation",
            7: "Final Output"
        }
        return stage_names.get(self.current_stage, "Unknown")


class PresetConfiguration(db.Model):
    """
    Model for storing workflow preset configurations.
    
    Stores references to prompts, stage selections, segment modes,
    and audio method preferences for reusable workflow configurations.
    """
    __tablename__ = 'preset_configurations'
    
    # Primary Key
    preset_id = db.Column(db.String(36), primary_key=True)  # UUID format
    
    # Preset Metadata
    preset_name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(Text)
    category = db.Column(db.String(50), default='custom')  # custom, system, template
    
    # Configuration JSON Structure:
    # {
    #   "stage_selection": [1, 2, 3, 4, 5, 6, 7],  # Which stages to execute
    #   "segment_mode": "manual" | "auto",
    #   "prompt_references": {
    #     "content_analysis": "prompt_file_name.txt",
    #     "segment_selection": "segment_prompt.txt"
    #   },
    #   "audio_method": "tts" | "voice_clone",
    #   "output_settings": {
    #     "format": "mp4",
    #     "quality": "high",
    #     "include_subtitles": true
    #   }
    # }
    configuration_json = db.Column(JSON, nullable=False)
    
    # Usage Tracking
    usage_count = db.Column(db.Integer, default=0)
    last_used_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    sessions = db.relationship('PipelineSession', backref='preset', lazy='dynamic')
    
    def __repr__(self):
        return f'<PresetConfiguration {self.preset_name}>'
    
    def increment_usage(self):
        """Increment usage count and update last used timestamp."""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def get_stage_names(self):
        """Get human-readable names for enabled stages."""
        stage_names = {
            1: "Audio Extraction",
            2: "Content Analysis", 
            3: "Segment Identification",
            4: "Segment Selection",
            5: "Audio Generation",
            6: "Video Compilation",
            7: "Final Output"
        }
        enabled_stages = self.configuration_json.get('stage_selection', [])
        return [stage_names.get(stage, f"Stage {stage}") for stage in enabled_stages]


# Database utility functions for common operations
def init_db(app):
    """Initialize database with Flask application."""
    db.init_app(app)
    with app.app_context():
        db.create_all()
        app.logger.info("Database tables created successfully")


def create_tables():
    """Create all database tables."""
    db.create_all()


def drop_tables():
    """Drop all database tables (use with caution)."""
    db.drop_all()
