"""
Enhanced Pipeline Logger - Advanced logging system for YouTube processing pipeline

This module provides a sophisticated logging system that addresses issues with log duplication,
verbosity, and provides enhanced progress visualization for long-running operations.

Features:
- Unified logging without duplication
- Rich progress bars and spinners
- Hierarchical stage logging
- User-friendly output modes
- Configurable verbosity levels
"""

import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum

from rich.console import Console
from rich.progress import (
    Progress, BarColumn, TextColumn, TimeRemainingColumn, 
    TimeElapsedColumn, SpinnerColumn, MofNCompleteColumn
)
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.align import Align
from rich.rule import Rule
from rich import box
from rich.logging import RichHandler


class LogLevel(Enum):
    """Log verbosity levels"""
    QUIET = "quiet"      # Only errors and critical messages
    NORMAL = "normal"    # Standard user-friendly output
    VERBOSE = "verbose"  # Detailed technical information
    DEBUG = "debug"      # All diagnostic information


class StageType(Enum):
    """Pipeline stage types for specialized logging"""
    EXTRACTION = "extraction"
    ANALYSIS = "analysis"
    GENERATION = "generation"
    TTS = "tts"
    VIDEO = "video"
    COMPILATION = "compilation"


@dataclass
class StageConfig:
    """Configuration for a pipeline stage"""
    name: str
    stage_type: StageType
    show_progress: bool = True
    enable_substeps: bool = True
    color: str = "blue"


@dataclass
class LogContext:
    """Context information for coordinated logging"""
    stage_name: str
    stage_type: StageType
    verbosity: LogLevel
    show_technical_details: bool
    track_progress: bool


class EnhancedPipelineLogger:
    """
    Advanced pipeline logger that provides:
    - Coordinated logging without duplication
    - Rich progress visualization
    - Hierarchical stage management
    - Configurable verbosity
    """
    
    def __init__(self, verbosity: LogLevel = LogLevel.NORMAL):
        self.console = Console()
        self.verbosity = verbosity
        self.current_context: Optional[LogContext] = None
        self.stage_loggers: Dict[str, logging.Logger] = {}
        self.active_progress: Optional[Progress] = None
        self.stage_start_times: Dict[str, float] = {}
        
        # Setup root logger to prevent duplication
        self._setup_root_logger()
        
        # Stage configurations
        self.stage_configs = {
            "extraction": StageConfig("Media Extraction", StageType.EXTRACTION, color="green"),
            "transcript": StageConfig("Transcript Generation", StageType.ANALYSIS, color="blue"),
            "analysis": StageConfig("Content Analysis", StageType.ANALYSIS, color="blue"),
            "generation": StageConfig("Narrative Generation", StageType.GENERATION, color="magenta"),
            "tts": StageConfig("Audio Generation", StageType.TTS, color="cyan"),
            "video": StageConfig("Video Clipping", StageType.VIDEO, color="yellow"),
            "compilation": StageConfig("Video Compilation", StageType.COMPILATION, color="red")
        }
    
    def _setup_root_logger(self):
        """Configure root logger to prevent duplication and integrate with Rich"""
        # Clear existing handlers to prevent duplication
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        # Set up Rich handler for clean output
        if self.verbosity == LogLevel.DEBUG:
            log_level = logging.DEBUG
        elif self.verbosity == LogLevel.VERBOSE:
            log_level = logging.INFO
        elif self.verbosity == LogLevel.NORMAL:
            log_level = logging.WARNING
        else:  # QUIET
            log_level = logging.ERROR
        
        rich_handler = RichHandler(
            console=self.console,
            show_path=self.verbosity in [LogLevel.VERBOSE, LogLevel.DEBUG],
            show_time=self.verbosity in [LogLevel.VERBOSE, LogLevel.DEBUG],
            markup=True
        )
        rich_handler.setLevel(log_level)
        
        # Format based on verbosity
        if self.verbosity in [LogLevel.VERBOSE, LogLevel.DEBUG]:
            formatter = logging.Formatter(
                '%(name)s - %(levelname)s - %(message)s'
            )
        else:
            formatter = logging.Formatter('%(message)s')
        
        rich_handler.setFormatter(formatter)
        root_logger.addHandler(rich_handler)
        root_logger.setLevel(log_level)
    
    def set_verbosity(self, verbosity: LogLevel):
        """Change logging verbosity dynamically"""
        self.verbosity = verbosity
        self._setup_root_logger()
    
    @contextmanager
    def stage_context(self, stage_key: str, stage_number: int = None):
        """
        Context manager for pipeline stages that coordinates all logging
        
        Args:
            stage_key: Key identifying the stage (e.g., 'tts', 'video')
            stage_number: Optional stage number for display
        """
        if stage_key not in self.stage_configs:
            raise ValueError(f"Unknown stage: {stage_key}")
        
        config = self.stage_configs[stage_key]
        
        # Create context
        context = LogContext(
            stage_name=config.name,
            stage_type=config.stage_type,
            verbosity=self.verbosity,
            show_technical_details=self.verbosity in [LogLevel.VERBOSE, LogLevel.DEBUG],
            track_progress=config.show_progress
        )
        
        previous_context = self.current_context
        self.current_context = context
        
        # Stage header
        stage_title = f"Stage {stage_number}: {config.name}" if stage_number else config.name
        self._display_stage_header(stage_title, config.color)
        
        # Track timing
        start_time = time.time()
        self.stage_start_times[stage_key] = start_time
        
        try:
            yield self
        finally:
            # Stage footer with timing
            duration = time.time() - start_time
            self._display_stage_footer(stage_title, duration, config.color)
            
            # Restore previous context
            self.current_context = previous_context
    
    def _display_stage_header(self, title: str, color: str):
        """Display rich stage header"""
        if self.verbosity != LogLevel.QUIET:
            panel = Panel(
                Align.center(Text(title, style=f"bold {color}")),
                border_style=color,
                padding=(0, 1)
            )
            self.console.print(panel)
    
    def _display_stage_footer(self, title: str, duration: float, color: str):
        """Display rich stage footer with timing"""
        if self.verbosity != LogLevel.QUIET:
            duration_text = f"Completed in {duration:.1f}s"
            self.console.print(
                f"[{color}]✅ {title} - {duration_text}[/{color}]"
            )
            self.console.print()
    
    def info(self, message: str, **kwargs):
        """Log info message with current context"""
        if self.verbosity in [LogLevel.NORMAL, LogLevel.VERBOSE, LogLevel.DEBUG]:
            if self.current_context and self.current_context.stage_type == StageType.TTS:
                # Special handling for TTS to reduce noise
                if any(noise in message.lower() for noise in ['api call', 'validation', 'retry']):
                    if self.verbosity == LogLevel.DEBUG:
                        self.console.print(f"[dim]{message}[/dim]")
                else:
                    self.console.print(f"[blue]{message}[/blue]")
            else:
                self.console.print(f"[blue]{message}[/blue]")
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        if self.verbosity != LogLevel.QUIET:
            self.console.print(f"[yellow]⚠️  {message}[/yellow]")
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self.console.print(f"[red]❌ {message}[/red]")
    
    def success(self, message: str, **kwargs):
        """Log success message"""
        if self.verbosity != LogLevel.QUIET:
            self.console.print(f"[green]✅ {message}[/green]")
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        if self.verbosity == LogLevel.DEBUG:
            self.console.print(f"[dim]{message}[/dim]")
    
    @contextmanager
    def progress_context(self, total: int, description: str = "Processing"):
        """
        Context manager for progress tracking
        
        Args:
            total: Total number of items to process
            description: Description for the progress bar
        """
        if not self.current_context or not self.current_context.track_progress:
            # No progress tracking, just yield a simple counter
            logger_instance = self  # Capture reference to the logger
            class SimpleProgress:
                def __init__(self):
                    self.current = 0
                    self.total = total
                
                def advance(self, increment=1):
                    self.current += increment
                    if logger_instance.verbosity != LogLevel.QUIET:
                        logger_instance.console.print(f"Progress: {self.current}/{self.total}")
            
            yield SimpleProgress()
            return
        
        # Create rich progress bar
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TextColumn("•"),
            TimeElapsedColumn(),
            TextColumn("•"),
            TimeRemainingColumn(),
            console=self.console
        )
        
        with progress:
            task = progress.add_task(description, total=total)
            
            class ProgressTracker:
                def __init__(self, progress_obj, task_id):
                    self.progress = progress_obj
                    self.task_id = task_id
                
                def advance(self, increment=1):
                    self.progress.advance(self.task_id, increment)
                
                def update_description(self, description: str):
                    self.progress.update(self.task_id, description=description)
            
            yield ProgressTracker(progress, task)
    
    @contextmanager
    def spinner_context(self, description: str = "Processing..."):
        """Context manager for spinner during long operations"""
        if self.verbosity == LogLevel.QUIET:
            yield
            return
        
        from rich.spinner import Spinner
        from rich.live import Live
        
        spinner = Spinner("dots", text=description)
        
        with Live(spinner, console=self.console, refresh_per_second=10):
            yield
    
    def display_summary_table(self, title: str, data: Dict[str, Any]):
        """Display a summary table"""
        if self.verbosity == LogLevel.QUIET:
            return
        
        table = Table(title=title, box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in data.items():
            table.add_row(key, str(value))
        
        self.console.print(table)
    
    def get_stage_logger(self, stage_key: str) -> logging.Logger:
        """
        Get a logger for a specific stage that coordinates with the main logger
        
        This prevents duplication by ensuring stage loggers route through
        the main enhanced logger system.
        """
        if stage_key not in self.stage_loggers:
            logger = logging.getLogger(f"pipeline.{stage_key}")
            
            # Remove existing handlers to prevent duplication
            logger.handlers.clear()
            
            # Create custom handler that routes through enhanced logger
            class EnhancedLogHandler(logging.Handler):
                def __init__(self, enhanced_logger):
                    super().__init__()
                    self.enhanced_logger = enhanced_logger
                
                def emit(self, record):
                    message = self.format(record)
                    
                    if record.levelno >= logging.ERROR:
                        self.enhanced_logger.error(message)
                    elif record.levelno >= logging.WARNING:
                        self.enhanced_logger.warning(message)
                    elif record.levelno >= logging.INFO:
                        self.enhanced_logger.info(message)
                    else:
                        self.enhanced_logger.debug(message)
            
            handler = EnhancedLogHandler(self)
            logger.addHandler(handler)
            logger.setLevel(logging.DEBUG)
            logger.propagate = False  # Prevent duplication
            
            self.stage_loggers[stage_key] = logger
        
        return self.stage_loggers[stage_key]
    
    def section_header(self, title: str, emoji: str = ""):
        """Display a section header with optional emoji"""
        if self.verbosity != LogLevel.QUIET:
            display_title = f"{emoji} {title}" if emoji else title
            panel = Panel(
                Align.center(Text(display_title, style="bold blue")),
                border_style="blue",
                padding=(0, 1)
            )
            self.console.print(panel)
    
    def spinner(self, description: str = "Processing..."):
        """Simple spinner method that returns context manager"""
        return self.spinner_context(description)


# Global logger instance
_global_logger: Optional[EnhancedPipelineLogger] = None


def get_enhanced_logger(verbosity: LogLevel = LogLevel.NORMAL) -> EnhancedPipelineLogger:
    """Get the global enhanced pipeline logger"""
    global _global_logger
    
    if _global_logger is None:
        _global_logger = EnhancedPipelineLogger(verbosity)
    else:
        _global_logger.set_verbosity(verbosity)
    
    return _global_logger


def set_global_verbosity(verbosity: LogLevel):
    """Set verbosity for the global logger"""
    global _global_logger
    if _global_logger is not None:
        _global_logger.set_verbosity(verbosity)
