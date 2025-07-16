"""
Flask Application Entry Point
YouTube Pipeline UI - Flask Web Interface

This module initializes the Flask application with proper configuration,
blueprint registration, and integration with the existing YouTube processing pipeline.

Created: June 20, 2025
Agent: Implementation Agent
Task Reference: Phase 1, Task 1.1 - Core Flask Application Setup
"""

import os
import sys
import logging
from datetime import datetime
from flask import Flask, render_template
from flask_socketio import SocketIO

# Add the parent Code directory to the Python path for importing existing modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from database.models import db, init_db

def create_app(config_class=Config):
    """
    Application factory pattern for Flask app creation.
    
    Args:
        config_class: Configuration class to use for the app
        
    Returns:
        Flask application instance    """
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Ensure CONTENT_DIR is available as a string in app config
    app.config['CONTENT_DIR'] = str(config_class.CONTENT_DIR)
    
    # Initialize Database
    init_db(app)
      # Initialize SocketIO for real-time updates
    socketio = SocketIO(
        app, 
        cors_allowed_origins=config_class.SOCKETIO_CORS_ALLOWED_ORIGINS,
        async_mode=config_class.SOCKETIO_ASYNC_MODE,
        transport=config_class.SOCKETIO_TRANSPORT,
        engineio_logger=config_class.SOCKETIO_ENGINEIO_LOGGER,
        socketio_logger=config_class.SOCKETIO_SOCKETIO_LOGGER
    )
      # Configure logging to integrate with existing master_processor_v2.py logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = logging.FileHandler('logs/ui_flask.log')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('YouTube Pipeline UI startup')
      # Register Blueprints
    from routes.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from routes.pipeline import bp as pipeline_bp, init_pipeline_routes
    app.register_blueprint(pipeline_bp, url_prefix='/pipeline')
    
    # Initialize pipeline routes with app and socketio context
    with app.app_context():
        init_pipeline_routes(app, socketio)
    
    from routes.episodes import episodes_bp
    app.register_blueprint(episodes_bp, url_prefix='/episodes')
    
    from routes.segments import bp as segments_bp
    app.register_blueprint(segments_bp, url_prefix='/segments')
    
    from routes.presets import bp as presets_bp
    app.register_blueprint(presets_bp, url_prefix='/presets')
    
    # Initialize WebSocket event handlers
    from routes.websocket_handlers import init_socketio_events
    init_socketio_events(socketio)
    
    # Template context processors
    @app.context_processor
    def inject_datetime():
        """Make datetime and current time available in all templates"""
        return {
            'datetime': datetime,
            'now': datetime.now()
        }
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500
    
    # Store socketio instance for access in routes
    app.socketio = socketio
    
    return app, socketio

if __name__ == '__main__':
    app, socketio = create_app()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
