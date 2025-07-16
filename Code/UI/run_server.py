"""
Development Server Startup Script
YouTube Pipeline UI - Local Development Server

This script provides a convenient way to start the Flask development server
with proper configuration for the YouTube Pipeline UI.

Created: June 20, 2025
Agent: Implementation Agent
Task Reference: Phase 1, Task 1.1 - Core Flask Application Setup

USAGE:
    python run_server.py [--config development|production|testing]
"""

import os
import sys
import argparse
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def main():
    """Main entry point for the development server."""
    parser = argparse.ArgumentParser(description='Start YouTube Pipeline UI Development Server')
    parser.add_argument('--config', 
                       choices=['development', 'production', 'testing'],
                       default='development',
                       help='Configuration environment to use')
    parser.add_argument('--host',
                       default='127.0.0.1',
                       help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--port',
                       type=int,
                       default=5000,
                       help='Port to bind to (default: 5000)')
    parser.add_argument('--debug',
                       action='store_true',
                       help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Set configuration environment
    os.environ['FLASK_ENV'] = args.config
    if args.debug:
        os.environ['FLASK_DEBUG'] = 'True'
    
    try:
        from app import create_app
        from config import config
        
        # Create app with specified configuration
        config_class = config.get(args.config, config['default'])
        app, socketio = create_app(config_class)
        
        print(f"🚀 Starting YouTube Pipeline UI Server...")
        print(f"📋 Configuration: {args.config}")
        print(f"🌐 Server URL: http://{args.host}:{args.port}")
        print(f"🔧 Debug Mode: {'Enabled' if app.debug else 'Disabled'}")
        print(f"📁 Project Root: {config_class.PROJECT_ROOT}")
        print(f"📂 Content Directory: {config_class.CONTENT_DIR}")
        print(f"⚙️  Master Processor: {config_class.MASTER_PROCESSOR_PATH}")
        print("=" * 60)
        print("Press Ctrl+C to stop the server")
        
        # Start the server with SocketIO support
        socketio.run(
            app,
            host=args.host,
            port=args.port,
            debug=app.debug,
            use_reloader=app.debug
        )
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Make sure all required dependencies are installed:")
        print("pip install flask flask-socketio")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Server Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
