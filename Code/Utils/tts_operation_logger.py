"""
Enhanced TTS Logger - Specialized logging for TTS operations

This module provides a specialized logger for TTS operations that:
- Reduces verbosity and noise
- Shows meaningful progress for long operations
- Groups related operations
- Provides clean user-friendly output
"""

import logging
import time
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, SpinnerColumn, MofNCompleteColumn
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from .enhanced_pipeline_logger import EnhancedPipelineLogger, LogLevel


class TTSOperationLogger:
    """
    Specialized logger for TTS operations that provides clean, organized output
    """
    
    def __init__(self, enhanced_logger: EnhancedPipelineLogger):
        self.enhanced_logger = enhanced_logger
        self.console = enhanced_logger.console
        self.verbosity = enhanced_logger.verbosity
        self.api_call_count = 0
        self.validation_attempts = 0
        self.current_section = None
        
    def start_episode_processing(self, total_sections: int, existing_count: int):
        """Start processing an episode with summary info"""
        if self.verbosity != LogLevel.QUIET:
            summary_panel = Panel(
                f"[cyan]Processing {total_sections} audio sections[/cyan]\n"
                f"[green]✅ {existing_count} existing files (will skip)[/green]\n"
                f"[yellow]🔄 {total_sections - existing_count} files to generate[/yellow]",
                title="[bold blue]TTS Audio Generation[/bold blue]",
                border_style="blue"
            )
            self.console.print(summary_panel)
    
    def start_section_processing(self, section_id: str, section_num: int, total_sections: int, is_existing: bool = False):
        """Start processing a single section"""
        self.current_section = section_id
        
        if is_existing:
            if self.verbosity in [LogLevel.NORMAL, LogLevel.VERBOSE, LogLevel.DEBUG]:
                self.console.print(f"[green]✅ [{section_num}/{total_sections}] Skipping existing: {section_id}[/green]")
        else:
            if self.verbosity != LogLevel.QUIET:
                self.console.print(f"[cyan]🔄 [{section_num}/{total_sections}] Generating: {section_id}[/cyan]")
    
    def log_api_call(self, section_id: str, attempt: int = 1):
        """Log API call with reduced verbosity"""
        self.api_call_count += 1
        
        if self.verbosity == LogLevel.DEBUG:
            self.console.print(f"[dim]  📡 API call #{self.api_call_count} for {section_id} (attempt {attempt})[/dim]")
        elif self.verbosity == LogLevel.VERBOSE and attempt > 1:
            self.console.print(f"[yellow]  🔄 Retry {attempt} for {section_id}[/yellow]")
    
    def log_audio_validation(self, section_id: str, is_valid: bool, details: str = ""):
        """Log audio validation with appropriate verbosity"""
        self.validation_attempts += 1
        
        if is_valid:
            if self.verbosity in [LogLevel.VERBOSE, LogLevel.DEBUG]:
                self.console.print(f"[green]  ✅ Audio validation passed for {section_id}[/green]")
        else:
            if self.verbosity != LogLevel.QUIET:
                reason = f" ({details})" if details else ""
                self.console.print(f"[yellow]  ⚠️  Audio validation failed for {section_id}{reason}[/yellow]")
    
    def log_section_success(self, section_id: str, duration: float, file_size: Optional[int] = None):
        """Log successful section completion"""
        if self.verbosity != LogLevel.QUIET:
            size_info = f" ({file_size // 1024}KB)" if file_size else ""
            self.console.print(f"[green]  ✅ Generated {section_id} in {duration:.1f}s{size_info}[/green]")
    
    def log_section_failure(self, section_id: str, error: str, duration: Optional[float] = None):
        """Log section failure"""
        time_info = f" after {duration:.1f}s" if duration else ""
        self.console.print(f"[red]  ❌ Failed {section_id}{time_info}: {error}[/red]")
    
    def display_processing_summary(self, stats: Dict[str, Any]):
        """Display final processing summary"""
        if self.verbosity == LogLevel.QUIET:
            return
        
        # Create summary table
        table = Table(title="TTS Processing Summary", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green", justify="right")
        
        table.add_row("Total Sections", str(stats.get('total_sections', 0)))
        table.add_row("✅ Successful", str(stats.get('successful_sections', 0)))
        table.add_row("❌ Failed", str(stats.get('failed_sections', 0)))
        table.add_row("⏭️  Skipped (existing)", str(stats.get('skipped_sections', 0)))
        table.add_row("📡 API Calls", str(self.api_call_count))
        table.add_row("🔍 Validations", str(self.validation_attempts))
        
        if 'processing_time' in stats:
            table.add_row("⏱️  Total Time", f"{stats['processing_time']:.1f}s")
        
        self.console.print(table)
    
    @contextmanager
    def batch_progress_context(self, total_items: int, description: str = "Generating audio"):
        """Context manager for batch TTS processing with progress"""
        if self.verbosity == LogLevel.QUIET:
            # Simple counter for quiet mode
            class QuietProgress:
                def __init__(self):
                    self.completed = 0
                
                def advance(self, increment=1):
                    self.completed += increment
            
            yield QuietProgress()
            return
        
        # Rich progress bar for visual feedback
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TextColumn("•"),
            TimeRemainingColumn(),
            console=self.console
        )
        
        with progress:
            task = progress.add_task(description, total=total_items)
            
            class TTSProgressTracker:
                def __init__(self, progress_obj, task_id):
                    self.progress = progress_obj
                    self.task_id = task_id
                
                def advance(self, increment=1):
                    self.progress.advance(self.task_id, increment)
                
                def update_description(self, description: str):
                    self.progress.update(self.task_id, description=description)
            
            yield TTSProgressTracker(progress, task)
    
    def log_configuration_info(self, config_info: Dict[str, Any]):
        """Log TTS configuration information"""
        if self.verbosity in [LogLevel.VERBOSE, LogLevel.DEBUG]:
            config_panel = Panel(
                "\n".join([f"[cyan]{key}:[/cyan] {value}" for key, value in config_info.items()]),
                title="[bold]TTS Configuration[/bold]",
                border_style="blue"
            )
            self.console.print(config_panel)
    
    def log_file_organization(self, source_path: str, organized_path: str):
        """Log file organization step"""
        if self.verbosity == LogLevel.DEBUG:
            self.console.print(f"[dim]  📁 Organized: {Path(source_path).name} → {Path(organized_path).name}[/dim]")
    
    def create_error_summary(self, failed_sections: List[Dict[str, Any]]):
        """Create a summary of failed sections"""
        if not failed_sections or self.verbosity == LogLevel.QUIET:
            return
        
        error_table = Table(title="Failed Sections", box=box.ROUNDED)
        error_table.add_column("Section ID", style="red")
        error_table.add_column("Error", style="yellow")
        
        for failure in failed_sections[:10]:  # Limit to first 10 failures
            error_table.add_row(
                failure.get('section_id', 'Unknown'),
                failure.get('error', 'Unknown error')[:50] + "..." if len(failure.get('error', '')) > 50 else failure.get('error', 'Unknown error')
            )
        
        if len(failed_sections) > 10:
            error_table.add_row("...", f"({len(failed_sections) - 10} more failures)")
        
        self.console.print(error_table)


def create_tts_logger(enhanced_logger: EnhancedPipelineLogger) -> TTSOperationLogger:
    """Factory function to create a TTS logger"""
    return TTSOperationLogger(enhanced_logger)
