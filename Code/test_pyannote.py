#!/usr/bin/env python3
"""Test pyannote pipeline loading with HuggingFace token."""

import os
import sys
import subprocess

# Fix for PyTorch 2.6+ weights_only default change
# Must be applied before importing pyannote
import torch
_original_torch_load = torch.load
def _patched_torch_load(*args, **kwargs):
    # Handle both missing key AND explicit None (Lightning passes weights_only=None)
    if kwargs.get('weights_only') is None:
        kwargs['weights_only'] = False
    return _original_torch_load(*args, **kwargs)
torch.load = _patched_torch_load

# Load token from Windows User env vars
if sys.platform == 'win32':
    try:
        result = subprocess.run(
            ['powershell', '-Command', "[Environment]::GetEnvironmentVariable('HUGGINGFACE_TOKEN', 'User')"],
            capture_output=True, text=True, timeout=5
        )
        token = result.stdout.strip()
        if token:
            os.environ['HUGGINGFACE_TOKEN'] = token
            print(f"Token loaded: {token[:15]}...")
        else:
            print("ERROR: No HUGGINGFACE_TOKEN found in Windows env vars")
            sys.exit(1)
    except Exception as e:
        print(f"ERROR loading token: {e}")
        sys.exit(1)

# Now test pyannote
from pyannote.audio import Pipeline

token = os.environ.get('HUGGINGFACE_TOKEN')
print(f"Using token: {token[:15]}...")

try:
    print("Loading pyannote speaker-diarization-3.1 pipeline...")
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=token
    )

    if pipeline is not None:
        print(f"SUCCESS! Pipeline type: {type(pipeline)}")
        print("Pipeline is ready to use.")
    else:
        print("FAILED: Pipeline.from_pretrained returned None")
        print("This usually means the token is invalid or you haven't accepted the model license.")
        print("Visit: https://huggingface.co/pyannote/speaker-diarization-3.1")
        print("And accept the terms to use this model.")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
