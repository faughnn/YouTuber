"""
Database Initialization and Migration Scripts
=============================================

Scripts for initializing the SQLite database, creating tables,
and managing database migrations for the YouTube Pipeline UI.

Created: June 20, 2025
Agent: Implementation Agent
Task Reference: Phase 1, Task 1.2 - Database Models & Session Management
"""

import os
import sys
from pathlib import Path
from flask import Flask

# Add the UI directory to Python path for imports
ui_dir = Path(__file__).parent.parent
sys.path.insert(0, str(ui_dir))

from config import Config
from database.models import db, init_db, PipelineSession, PresetConfiguration
from database.utils import PresetManager


def create_database(app=None):
    """
    Create the SQLite database and all tables.
    
    Args:
        app: Flask application instance (optional)
    """
    if app is None:
        app = create_app_for_db_init()
    
    with app.app_context():
        # Ensure database directory exists
        db_path = Path(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create all tables
        db.create_all()
        print(f"✅ Database created successfully at: {db_path}")
        
        # Create default preset configurations
        create_default_presets()
        
        print("✅ Database initialization completed")


def create_app_for_db_init():
    """Create a minimal Flask app for database initialization."""
    app = Flask(__name__)
    
    # Database configuration
    ui_root = Path(__file__).parent.parent
    db_path = ui_root / 'database' / 'pipeline_sessions.db'
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'db-init-key'
    
    # Initialize database
    db.init_app(app)
    
    return app


def create_default_presets():
    """Create default preset configurations."""
    default_presets = [
        {
            'name': 'Full Pipeline - Auto Segments',
            'description': 'Complete 7-stage pipeline with automatic segment selection',
            'category': 'system',
            'configuration': {
                'stage_selection': [1, 2, 3, 4, 5, 6, 7],
                'segment_mode': 'auto',
                'prompt_references': {
                    'content_analysis': 'default_content_analysis.txt',
                    'segment_selection': 'auto_segment_selection.txt'
                },
                'audio_method': 'tts',
                'output_settings': {
                    'format': 'mp4',
                    'quality': 'high',
                    'include_subtitles': True
                }
            }
        },
        {
            'name': 'Full Pipeline - Manual Segments',
            'description': 'Complete 7-stage pipeline with manual segment selection',
            'category': 'system',
            'configuration': {
                'stage_selection': [1, 2, 3, 4, 5, 6, 7],
                'segment_mode': 'manual',
                'prompt_references': {
                    'content_analysis': 'default_content_analysis.txt',
                    'segment_selection': 'manual_segment_selection.txt'
                },
                'audio_method': 'tts',
                'output_settings': {
                    'format': 'mp4',
                    'quality': 'high',
                    'include_subtitles': True
                }
            }
        },
        {
            'name': 'Analysis Only',
            'description': 'Content analysis and segment identification only',
            'category': 'template',
            'configuration': {
                'stage_selection': [1, 2, 3],
                'segment_mode': 'auto',
                'prompt_references': {
                    'content_analysis': 'detailed_analysis.txt'
                },
                'audio_method': 'tts',
                'output_settings': {
                    'format': 'json',
                    'quality': 'standard',
                    'include_subtitles': False
                }
            }
        },
        {
            'name': 'Quick Video Generation',
            'description': 'Fast processing with voice cloning for final output',
            'category': 'template',
            'configuration': {
                'stage_selection': [1, 2, 3, 4, 5, 6, 7],
                'segment_mode': 'auto',
                'prompt_references': {
                    'content_analysis': 'quick_analysis.txt',
                    'segment_selection': 'auto_segment_selection.txt'
                },
                'audio_method': 'voice_clone',
                'output_settings': {
                    'format': 'mp4',
                    'quality': 'standard',
                    'include_subtitles': True
                }
            }
        }
    ]
    
    for preset_data in default_presets:
        # Check if preset already exists
        existing = PresetManager.get_preset_by_name(preset_data['name'])
        if not existing:
            PresetManager.create_preset(
                name=preset_data['name'],
                description=preset_data['description'],
                category=preset_data['category'],
                configuration=preset_data['configuration']
            )
            print(f"✅ Created default preset: {preset_data['name']}")
        else:
            print(f"ℹ️  Preset already exists: {preset_data['name']}")


def reset_database(app=None):
    """
    Reset the database by dropping and recreating all tables.
    USE WITH CAUTION - This will delete all data.
    """
    if app is None:
        app = create_app_for_db_init()
    
    with app.app_context():
        print("⚠️  Resetting database - all data will be lost!")
        response = input("Are you sure? Type 'yes' to continue: ")
        
        if response.lower() == 'yes':
            db.drop_all()
            print("🗑️  All tables dropped")
            
            db.create_all()
            print("✅ Tables recreated")
            
            create_default_presets()
            print("✅ Database reset completed")
        else:
            print("❌ Database reset cancelled")


def validate_database(app=None):
    """Validate database structure and connectivity."""
    if app is None:
        app = create_app_for_db_init()
    
    with app.app_context():
        try:
            # Test basic connectivity
            db.session.execute(db.text('SELECT 1'))
            print("✅ Database connection successful")
            
            # Check table existence
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            expected_tables = ['pipeline_sessions', 'preset_configurations']
            missing_tables = [t for t in expected_tables if t not in existing_tables]
            
            if missing_tables:
                print(f"❌ Missing tables: {missing_tables}")
                return False
            else:
                print("✅ All required tables exist")
            
            # Test basic operations
            session_count = PipelineSession.query.count()
            preset_count = PresetConfiguration.query.count()
            
            print(f"📊 Database stats:")
            print(f"   - Pipeline sessions: {session_count}")
            print(f"   - Preset configurations: {preset_count}")
            
            return True
            
        except Exception as e:
            print(f"❌ Database validation failed: {e}")
            return False


if __name__ == '__main__':
    """Command-line interface for database operations."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Database management for YouTube Pipeline UI')
    parser.add_argument('action', choices=['init', 'reset', 'validate'], 
                       help='Database action to perform')
    
    args = parser.parse_args()
    
    if args.action == 'init':
        print("🚀 Initializing database...")
        create_database()
    elif args.action == 'reset': 
        print("🔄 Resetting database...")
        reset_database()
    elif args.action == 'validate':
        print("🔍 Validating database...")
        success = validate_database()
        sys.exit(0 if success else 1)
