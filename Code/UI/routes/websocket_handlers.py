"""
WebSocket Event Handlers
YouTube Pipeline UI - Real-time Communication

This module handles WebSocket connections and events for real-time
communication between the Flask backend and frontend components.

Created: June 21, 2025
Agent: Implementation Agent
Task Reference: Fix WebSocket transport errors
"""

from flask import request
from flask_socketio import emit, disconnect
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def init_socketio_events(socketio):
    """
    Initialize WebSocket event handlers.
    
    Args:
        socketio: SocketIO instance
    """
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection."""
        try:
            logger.info(f"Client connected: {request.sid}")
            emit('status', {'msg': 'Connected to YouTube Pipeline UI'})
        except Exception as e:
            logger.error(f"Error in connect handler: {e}")
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection."""
        try:
            logger.info(f"Client disconnected: {request.sid}")
        except Exception as e:
            logger.error(f"Error in disconnect handler: {e}")
    
    @socketio.on('ping')
    def handle_ping(data=None):
        """Handle ping for keepalive."""
        try:
            emit('pong', {'timestamp': str(datetime.now())})
        except Exception as e:
            logger.error(f"Error in ping handler: {e}")
    
    @socketio.on('join_room')
    def handle_join_room(data):
        """Handle joining a specific room."""
        try:
            room = data.get('room', 'general')
            logger.info(f"Client {request.sid} joined room: {room}")
            emit('joined', {'room': room})
        except Exception as e:
            logger.error(f"Error in join_room handler: {e}")
    
    @socketio.on('error')
    def handle_error(error):
        """Handle WebSocket errors."""
        logger.error(f"WebSocket error: {error}")
    
    logger.info("SocketIO event handlers initialized")
