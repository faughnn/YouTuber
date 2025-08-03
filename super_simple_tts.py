#!/usr/bin/env python3
"""
Super Simple Text-to-Speech Script

A minimal script that uses the Chatterbox TTS API to convert text into speech.
No complex dependencies - just requests and built-in Python modules.

Requirements:
- Chatterbox TTS server running on localhost:4123
- Python requests library: pip install requests

Usage:
    python super_simple_tts.py "Your text here"
    
Or run without arguments to use interactive mode.
"""

import sys
import time
import requests
import subprocess
import signal
import atexit
from pathlib import Path

# TTS Configuration - Modify these if needed
API_BASE_URL = "http://localhost:4123"
EXAGGERATION = 0.7     # Emotion intensity (0.25-2.0)
CFG_WEIGHT = 0.3       # Pace control (0.0-1.0) 
TEMPERATURE = 0.7      # Sampling randomness (0.05-5.0)

# Chatterbox Server Configuration
CHATTERBOX_PYTHON_PATH = r"C:/Users/nfaug/AppData/Local/Programs/Python/Python312/python.exe"
CHATTERBOX_SCRIPT_PATH = r"c:/Users/nfaug/chatterbox-tts-api/main.py"
SERVER_STARTUP_WAIT = 10  # seconds to wait for server to start

# Global variable to track server process
_server_process = None

# Global variable to track server process
_server_process = None

def is_server_running() -> bool:
    """
    Check if the Chatterbox TTS server is already running
    
    Returns:
        True if server responds, False otherwise
    """
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def start_chatterbox_server() -> bool:
    """
    Start the Chatterbox TTS server if it's not already running
    
    Returns:
        True if server is running (either started or was already running), False otherwise
    """
    global _server_process
    
    # Check if server is already running
    if is_server_running():
        print("✅ Chatterbox TTS server is already running")
        return True
    
    print("🚀 Starting Chatterbox TTS server...")
    
    try:
        # Start the server process
        _server_process = subprocess.Popen(
            [CHATTERBOX_PYTHON_PATH, CHATTERBOX_SCRIPT_PATH],
            cwd=Path(CHATTERBOX_SCRIPT_PATH).parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
        )
        
        # Wait for server to start up
        print(f"⏳ Waiting {SERVER_STARTUP_WAIT} seconds for server to initialize...")
        
        for i in range(SERVER_STARTUP_WAIT):
            time.sleep(1)
            if is_server_running():
                print("✅ Chatterbox TTS server started successfully!")
                return True
            if i == SERVER_STARTUP_WAIT // 2:
                print("   Still starting up...")
        
        # If we get here, server didn't start in time
        print("❌ Server failed to start within timeout period")
        stop_chatterbox_server()
        return False
        
    except Exception as e:
        print(f"❌ Failed to start Chatterbox server: {e}")
        return False

def stop_chatterbox_server():
    """
    Stop the Chatterbox TTS server if we started it
    """
    global _server_process
    
    if _server_process:
        print("🛑 Stopping Chatterbox TTS server...")
        try:
            if sys.platform == "win32":
                # On Windows, send CTRL_BREAK_EVENT to the process group
                _server_process.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                _server_process.terminate()
            
            # Wait for process to end
            _server_process.wait(timeout=5)
            print("✅ Chatterbox TTS server stopped")
        except subprocess.TimeoutExpired:
            # Force kill if it doesn't stop gracefully
            _server_process.kill()
            print("⚠️ Chatterbox TTS server force stopped")
        except Exception as e:
            print(f"⚠️ Error stopping server: {e}")
        finally:
            _server_process = None

# Register cleanup function to stop server on exit
atexit.register(stop_chatterbox_server)

def text_to_speech(text: str, output_file: str = None) -> bool:
    """
    Convert text to speech using Chatterbox TTS API
    
    Args:
        text: Text to convert
        output_file: Where to save the audio (optional)
    
    Returns:
        True if successful, False otherwise
    """
    if not output_file:
        timestamp = int(time.time())
        output_file = f"speech_{timestamp}.wav"
    
    try:
        print(f"🔄 Converting text to speech...")
        print(f"   Text length: {len(text)} characters")
        print(f"   Output file: {output_file}")
        
        # API payload
        payload = {
            "input": text.strip(),
            "exaggeration": EXAGGERATION,
            "cfg_weight": CFG_WEIGHT,
            "temperature": TEMPERATURE
        }
        
        # Make API call
        response = requests.post(
            f"{API_BASE_URL}/v1/audio/speech",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=300
        )
        
        # Check response
        if response.status_code == 200:
            # Save audio file
            Path(output_file).write_bytes(response.content)
            file_size = Path(output_file).stat().st_size
            
            print(f"✅ Success! Audio saved: {output_file} ({file_size:,} bytes)")
            return True
        else:
            print(f"❌ API Error: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to TTS server at {API_BASE_URL}")
        print("   Make sure Chatterbox TTS is running on localhost:4123")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🎤 Super Simple Text-to-Speech")
    print("=" * 40)
    
    # Start Chatterbox server if needed
    if not start_chatterbox_server():
        print("\n💥 Failed to start Chatterbox TTS server!")
        print("\nTroubleshooting:")
        print("• Check that the Python path is correct:", CHATTERBOX_PYTHON_PATH)
        print("• Check that the script path is correct:", CHATTERBOX_SCRIPT_PATH)
        print("• Make sure Chatterbox TTS dependencies are installed")
        return
    
    try:
        # Get text input
        if len(sys.argv) > 1:
            # Use command line arguments
            text = " ".join(sys.argv[1:])
        else:
            # Interactive mode
            print("Enter the text you want to convert to speech:")
            text = input("> ").strip()
            
            if not text:
                text = "Hello! This is a test of the text to speech system."
                print(f"Using default text: {text}")
        
        # Convert to speech
        print(f"\n📝 Text to convert: {text}")
        success = text_to_speech(text)
        
        if success:
            print("\n🎉 Conversion complete!")
        else:
            print("\n💥 Conversion failed!")
            print("\nTroubleshooting:")
            print("• Server should be running automatically")
            print("• Check server address:", API_BASE_URL)
            print("• Try shorter text if it's very long")
    
    finally:
        # Always stop the server when we're done
        stop_chatterbox_server()

if __name__ == "__main__":
    main()
