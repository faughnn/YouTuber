#!/usr/bin/env python3
"""
Autonomous Pipeline Runner
===========================

Runs the full 7-stage YouTube processing pipeline without manual input.
Uses ElevenLabs for TTS and "without_hook" narrative format.

Usage:
    python run_autonomous.py <youtube_url>

Example:
    python run_autonomous.py "https://www.youtube.com/watch?v=abc123"

Author: Claude Code
Created: 2024-12-28
"""

import sys
import os

# Apply torch.load patch BEFORE any other imports to fix PyTorch 2.6+ compatibility
# This must be done early so pyannote/whisperx models can load correctly
try:
    import torch
    print(f"[DEBUG] PyTorch version: {torch.__version__}")

    # Method 1: Add required classes to safe globals
    try:
        import typing
        from omegaconf import ListConfig, DictConfig
        from omegaconf.base import ContainerMetadata
        safe_globals = [ListConfig, DictConfig, ContainerMetadata, typing.Any]
        torch.serialization.add_safe_globals(safe_globals)
        print(f"[DEBUG] Added {len(safe_globals)} classes to safe globals")
    except Exception as e:
        print(f"[DEBUG] Could not add safe globals: {e}")

    # Method 2: Patch torch.load to use weights_only=False by default
    _original_torch_load = torch.load
    def _patched_torch_load(*args, **kwargs):
        if 'weights_only' not in kwargs:
            kwargs['weights_only'] = False
        return _original_torch_load(*args, **kwargs)
    torch.load = _patched_torch_load
    print("[DEBUG] torch.load patched successfully")
except ImportError:
    print("[DEBUG] torch not found")
    pass  # torch not installed yet

import logging
import traceback
from datetime import datetime

# Fix Windows console encoding for Unicode/emoji support
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

    # Load API keys from Windows User environment variables
    # This ensures they're available before module imports
    import subprocess
    def get_user_env(name):
        try:
            result = subprocess.run(
                ['powershell', '-Command', f"[Environment]::GetEnvironmentVariable('{name}', 'User')"],
                capture_output=True, text=True, timeout=5
            )
            value = result.stdout.strip()
            return value if value else None
        except:
            return None

    # Set API keys if not already in environment
    if not os.environ.get('GEMINI_API_KEY'):
        key = get_user_env('GEMINI_API_KEY')
        if key:
            os.environ['GEMINI_API_KEY'] = key
            print(f"[DEBUG] Gemini API key loaded: {key[:10]}...{key[-4:]}")
        else:
            print("[DEBUG] WARNING: No GEMINI_API_KEY found in Windows env vars!")
    else:
        print(f"[DEBUG] Gemini API key already in env: {os.environ['GEMINI_API_KEY'][:10]}...")

    if not os.environ.get('ELEVENLABS_API_KEY'):
        key = get_user_env('ELEVENLABS_API_KEY')
        if key:
            os.environ['ELEVENLABS_API_KEY'] = key
            print(f"[DEBUG] ElevenLabs API key loaded: {key[:10]}...{key[-4:]}")
        else:
            print("[DEBUG] WARNING: No ELEVENLABS_API_KEY found in Windows env vars!")

    if not os.environ.get('HUGGINGFACE_TOKEN'):
        key = get_user_env('HUGGINGFACE_TOKEN')
        if key:
            os.environ['HUGGINGFACE_TOKEN'] = key
            os.environ['HuggingFaceToken'] = key  # Also set the variant used by diarizer
            print(f"[DEBUG] HuggingFace token loaded: {key[:10]}...{key[-4:]}")
        else:
            print("[DEBUG] WARNING: No HUGGINGFACE_TOKEN found in Windows env vars!")
    else:
        print(f"[DEBUG] HuggingFace token already in env: {os.environ['HUGGINGFACE_TOKEN'][:10]}...")

# Add Code directory to path
code_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, code_dir)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            os.path.join(code_dir, '..', 'logs', f'autonomous_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
            mode='w'
        ) if os.path.exists(os.path.join(code_dir, '..', 'logs')) else logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run_pipeline(youtube_url: str) -> dict:
    """
    Run the full pipeline on a YouTube URL.

    Args:
        youtube_url: YouTube video URL

    Returns:
        dict with results or error info
    """
    from master_processor_v2 import MasterProcessorV2

    logger.info("=" * 60)
    logger.info("AUTONOMOUS PIPELINE RUNNER")
    logger.info("=" * 60)
    logger.info(f"YouTube URL: {youtube_url}")
    logger.info(f"TTS Provider: ElevenLabs")
    logger.info(f"Narrative Format: without_hook")
    logger.info("=" * 60)

    result = {
        'success': False,
        'url': youtube_url,
        'start_time': datetime.now().isoformat(),
        'end_time': None,
        'final_output': None,
        'episode_dir': None,
        'error': None,
        'stage_failed': None
    }

    try:
        # Initialize processor in autonomous mode (skips user prompts)
        logger.info("Initializing MasterProcessorV2 in autonomous mode...")
        processor = MasterProcessorV2(autonomous=True)

        logger.info(f"Session ID: {processor.session_id}")

        # Run full pipeline with ElevenLabs and without_hook format
        logger.info("Starting full pipeline...")
        final_output = processor.process_full_pipeline(
            url=youtube_url,
            tts_provider="elevenlabs",
            narrative_format="without_hook"
        )

        result['success'] = True
        result['final_output'] = final_output
        result['episode_dir'] = processor.episode_dir

        logger.info("=" * 60)
        logger.info("PIPELINE COMPLETED SUCCESSFULLY")
        logger.info(f"Final output: {final_output}")
        logger.info(f"Episode directory: {processor.episode_dir}")
        logger.info("=" * 60)

    except Exception as e:
        result['error'] = str(e)
        result['traceback'] = traceback.format_exc()

        logger.error("=" * 60)
        logger.error("PIPELINE FAILED")
        logger.error(f"Error: {e}")
        logger.error("Traceback:")
        logger.error(traceback.format_exc())
        logger.error("=" * 60)

    result['end_time'] = datetime.now().isoformat()
    return result


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python run_autonomous.py <youtube_url>")
        print()
        print("Example:")
        print('  python run_autonomous.py "https://www.youtube.com/watch?v=abc123"')
        sys.exit(1)

    youtube_url = sys.argv[1]

    # Validate URL
    if 'youtube.com' not in youtube_url and 'youtu.be' not in youtube_url:
        print(f"Error: Invalid YouTube URL: {youtube_url}")
        print("URL must contain 'youtube.com' or 'youtu.be'")
        sys.exit(1)

    # Ensure logs directory exists
    logs_dir = os.path.join(code_dir, '..', 'logs')
    os.makedirs(logs_dir, exist_ok=True)

    # Run pipeline
    result = run_pipeline(youtube_url)

    # Exit with appropriate code
    if result['success']:
        print(f"\nSuccess! Final output: {result['final_output']}")
        sys.exit(0)
    else:
        print(f"\nFailed: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
