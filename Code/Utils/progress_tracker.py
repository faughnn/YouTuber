"""
Progress Tracking Utilities for Master Processor

Provides progress tracking, time estimation, and user feedback functionality.
"""

import time
from typing import Optional, Dict, List
from dataclasses import dataclass
from enum import Enum


class ProcessingStage(Enum):
    """Processing stages for the master processor pipeline."""
    INPUT_VALIDATION = "input_validation"
    AUDIO_ACQUISITION = "audio_acquisition"
    TRANSCRIPT_GENERATION = "transcript_generation"
    CONTENT_ANALYSIS = "content_analysis"
    FILE_ORGANIZATION = "file_organization"
    PODCAST_GENERATION = "podcast_generation"


@dataclass
class StageProgress:
    """Progress information for a single processing stage."""
    stage: ProcessingStage
    status: str  # "pending", "running", "completed", "failed"
    progress_percent: float = 0.0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    estimated_duration: Optional[float] = None
    current_step: str = ""


class ProgressTracker:
    """Tracks progress across multiple processing stages."""
    
    def __init__(self):
        self.stages: Dict[ProcessingStage, StageProgress] = {}
        self.session_start_time = time.time()
        self.current_stage: Optional[ProcessingStage] = None
        
        # Initialize all stages
        for stage in ProcessingStage:
            self.stages[stage] = StageProgress(
                stage=stage,
                status="pending"
            )
    
    def start_stage(self, stage: ProcessingStage, estimated_duration: Optional[float] = None):
        """Start a processing stage."""
        self.current_stage = stage
        stage_progress = self.stages[stage]
        stage_progress.status = "running"
        stage_progress.start_time = time.time()
        stage_progress.estimated_duration = estimated_duration
        stage_progress.progress_percent = 0.0
    
    def update_stage_progress(self, progress_percent: float, current_step: str = ""):
        """Update progress for the current stage."""
        if self.current_stage:
            stage_progress = self.stages[self.current_stage]
            stage_progress.progress_percent = min(100.0, max(0.0, progress_percent))
            stage_progress.current_step = current_step
    
    def complete_stage(self, stage: ProcessingStage):
        """Mark a stage as completed."""
        stage_progress = self.stages[stage]
        stage_progress.status = "completed"
        stage_progress.end_time = time.time()
        stage_progress.progress_percent = 100.0
        
        if self.current_stage == stage:
            self.current_stage = None
    
    def fail_stage(self, stage: ProcessingStage, error_message: str = ""):
        """Mark a stage as failed."""
        stage_progress = self.stages[stage]
        stage_progress.status = "failed"
        stage_progress.end_time = time.time()
        stage_progress.current_step = f"Error: {error_message}"
        
        if self.current_stage == stage:
            self.current_stage = None
    
    def get_overall_progress(self) -> float:
        """Calculate overall progress percentage."""
        total_stages = len(self.stages)
        completed_stages = sum(1 for s in self.stages.values() if s.status == "completed")
        
        if self.current_stage:
            current_progress = self.stages[self.current_stage].progress_percent / 100.0
            return ((completed_stages + current_progress) / total_stages) * 100.0
        
        return (completed_stages / total_stages) * 100.0
    
    def get_estimated_time_remaining(self) -> Optional[float]:
        """Estimate time remaining based on completed stages."""
        completed_stages = [s for s in self.stages.values() if s.status == "completed"]
        
        if not completed_stages:
            return None
        
        # Calculate average time per completed stage
        total_completed_time = sum(
            s.end_time - s.start_time for s in completed_stages
            if s.start_time and s.end_time
        )
        
        if not total_completed_time:
            return None
        
        avg_time_per_stage = total_completed_time / len(completed_stages)
        remaining_stages = sum(1 for s in self.stages.values() if s.status == "pending")
        
        # Add time for current stage if running
        current_stage_remaining = 0
        if self.current_stage:
            current_stage_progress = self.stages[self.current_stage]
            if current_stage_progress.estimated_duration:
                current_stage_remaining = current_stage_progress.estimated_duration * (
                    1 - current_stage_progress.progress_percent / 100.0
                )
            else:
                current_stage_remaining = avg_time_per_stage * (
                    1 - current_stage_progress.progress_percent / 100.0
                )
        
        return (remaining_stages * avg_time_per_stage) + current_stage_remaining
    
    def format_time(self, seconds: float) -> str:
        """Format time in a human-readable format."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    def get_progress_display(self, input_description: str = "") -> str:
        """Generate a formatted progress display."""
        lines = []
        
        # Header
        if input_description:
            lines.append(f"🚀 Processing: {input_description}")
        else:
            lines.append("🚀 Processing...")
          # Stage progress
        stage_icons = {
            ProcessingStage.INPUT_VALIDATION: "📋",
            ProcessingStage.AUDIO_ACQUISITION: "🎵",
            ProcessingStage.TRANSCRIPT_GENERATION: "📝",
            ProcessingStage.CONTENT_ANALYSIS: "🤖",
            ProcessingStage.FILE_ORGANIZATION: "📁",
            ProcessingStage.PODCAST_GENERATION: "🎙️"
        }
        
        stage_names = {
            ProcessingStage.INPUT_VALIDATION: "Input validation",
            ProcessingStage.AUDIO_ACQUISITION: "Audio acquisition",
            ProcessingStage.TRANSCRIPT_GENERATION: "Transcript generation",
            ProcessingStage.CONTENT_ANALYSIS: "Content analysis",
            ProcessingStage.FILE_ORGANIZATION: "File organization",
            ProcessingStage.PODCAST_GENERATION: "Podcast generation"
        }
        
        for stage in ProcessingStage:
            stage_progress = self.stages[stage]
            icon = stage_icons[stage]
            name = stage_names[stage]
            
            if stage_progress.status == "completed":
                duration = ""
                if stage_progress.start_time and stage_progress.end_time:
                    elapsed = stage_progress.end_time - stage_progress.start_time
                    duration = f" ({self.format_time(elapsed)})"
                lines.append(f"├── ✅ {name}{duration}")
            
            elif stage_progress.status == "running":
                progress_bar = self._create_progress_bar(stage_progress.progress_percent)
                step_info = f" - {stage_progress.current_step}" if stage_progress.current_step else ""
                lines.append(f"├── {icon} {name} {progress_bar} {stage_progress.progress_percent:.0f}%{step_info}")
            
            elif stage_progress.status == "failed":
                error_info = f" - {stage_progress.current_step}" if stage_progress.current_step else ""
                lines.append(f"├── ❌ {name}{error_info}")
            
            else:  # pending
                lines.append(f"├── ⏳ {name} (pending)")
        
        # Overall progress
        overall_progress = self.get_overall_progress()
        lines.append("")
        lines.append(f"Overall Progress: {overall_progress:.1f}% complete")
        
        # Time estimation
        eta = self.get_estimated_time_remaining()
        if eta:
            lines.append(f"Estimated Time Remaining: {self.format_time(eta)}")
        
        elapsed = time.time() - self.session_start_time
        lines.append(f"Elapsed Time: {self.format_time(elapsed)}")
        
        return "\n".join(lines)
    
    def _create_progress_bar(self, percent: float, width: int = 10) -> str:
        """Create a visual progress bar."""
        filled = int((percent / 100.0) * width)
        empty = width - filled
        return f"[{'█' * filled}{'░' * empty}]"
