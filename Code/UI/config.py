"""
Configuration Management for YouTube Pipeline UI
===============================================

This module provides centralized configuration management for the Flask web interface,
integrating with the existing YouTube processing pipeline structure.

Created: June 20, 2025
Agent: Implementation Agent  
Task Reference: Phase 1, Task 1.1 - Core Flask Application Setup
"""

import os
from pathlib import Path

class Config:
    """
    Base configuration class for the Flask application.
    Designed to integrate with existing project structure and Windows file paths.
    """
    
    # Flask Core Settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'youtube-pipeline-ui-dev-key-2025'
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Project Structure Integration
    # Root project directory (YouTuber folder)
    PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
    
    # Content directory for episode management
    CONTENT_DIR = PROJECT_ROOT / 'Content'
    
    # Code directory for master processor integration
    CODE_DIR = PROJECT_ROOT / 'Code'
    
    # UI-specific paths
    UI_ROOT = Path(__file__).parent.resolve()
    STATIC_FOLDER = UI_ROOT / 'static'
    TEMPLATES_FOLDER = UI_ROOT / 'templates'
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_DIR = PROJECT_ROOT / 'logs'
    
    # Pipeline Integration Settings
    MASTER_PROCESSOR_PATH = CODE_DIR / 'master_processor_v2.py'
      # Server Configuration
    HOST = os.environ.get('FLASK_HOST', '127.0.0.1')
    PORT = int(os.environ.get('FLASK_PORT', 5000))
    
    # Database Configuration
    DATABASE_PATH = UI_ROOT / 'database' / 'pipeline_sessions.db'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{DATABASE_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
      # SocketIO Configuration
    SOCKETIO_ASYNC_MODE = 'threading'
    SOCKETIO_CORS_ALLOWED_ORIGINS = "*"
    SOCKETIO_TRANSPORT = ['polling', 'websocket']
    SOCKETIO_ENGINEIO_LOGGER = False  # Reduce verbose logging
    SOCKETIO_SOCKETIO_LOGGER = False  # Reduce verbose logging
    
    # Pipeline Stage Configuration
    PIPELINE_STAGES = {
        1: 'Media Extraction',
        2: 'Transcript Generation', 
        3: 'Content Analysis',
        4: 'Narrative Generation',
        5: 'Audio Generation',
        6: 'Video Clipping',
        7: 'Video Compilation'
    }
    
    # File Extensions for Stage Detection
    STAGE_OUTPUT_PATTERNS = {
        1: ['*.mp4', '*.mp3', '*.wav'],  # Media files
        2: ['*transcript*.txt', '*transcript*.json'],  # Transcript files
        3: ['*analysis*.json', '*content_analysis*'],  # Analysis files
        4: ['*script*.txt', '*narrative*'],  # Script files
        5: ['*generated_audio*', '*tts_audio*'],  # Generated audio
        6: ['*clips*', '*segments*'],  # Video clips
        7: ['*final*', '*compiled*']  # Final video
    }
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration-specific setup."""
        # Ensure log directory exists
        log_dir = Path(Config.LOG_DIR)
        log_dir.mkdir(exist_ok=True)
        
        # Ensure content directory exists
        content_dir = Path(Config.CONTENT_DIR)
        content_dir.mkdir(exist_ok=True)

class DevelopmentConfig(Config):
    """Development-specific configuration."""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production-specific configuration."""
    DEBUG = False
    LOG_LEVEL = 'INFO'
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'CHANGE-THIS-IN-PRODUCTION'

class TestingConfig(Config):
    """Testing-specific configuration."""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# Configuration dictionary for easy selection
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
