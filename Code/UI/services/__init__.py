"""
Services Module for YouTube Pipeline UI
======================================

This module provides service classes for integrating the Flask web UI
with the existing master_processor_v2.py pipeline orchestrator.

Services:
- PipelineController: Primary interface for pipeline execution and control
- PipelineFileMonitor: File monitoring for stage completion detection
- MultiEpisodeFileMonitor: Multi-episode monitoring management

Created: June 20, 2025
Agent: Agent_Pipeline_Integration
Task Reference: Phase 2, Task 2.1 - Master Processor Integration
"""

from .pipeline_controller import PipelineController
from .file_monitor import (
    PipelineFileMonitor, 
    MultiEpisodeFileMonitor,
    create_file_monitor,
    create_multi_episode_monitor
)

__all__ = [
    'PipelineController',
    'PipelineFileMonitor', 
    'MultiEpisodeFileMonitor',
    'create_file_monitor',
    'create_multi_episode_monitor'
]
