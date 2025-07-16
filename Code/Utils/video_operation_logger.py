"""
Enhanced Video Logger - Specialized logging for video operations

This module provides a specialized logger for video operations that:
- Shows progress for video conversion and compilation
- Groups related video operations
- Provides technical details when needed
- Manages FFmpeg output appropriately
"""

import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, SpinnerColumn, MofNCompleteColumn
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from .enhanced_pipeline_logger import EnhancedPipelineLogger, LogLevel


class VideoOperationLogger:
    """
    Specialized logger for video operations that provides organized output
    """
    
    def __init__(self, enhanced_logger: EnhancedPipelineLogger):
        self.enhanced_logger = enhanced_logger
        self.console = enhanced_logger.console
        self.verbosity = enhanced_logger.verbosity
        self.conversion_count = 0
        self.total_duration = 0.0
        self.current_operation = None
        
    def start_conversion_batch(self, total_files: int, operation_type: str = "conversion"):
        """Start a batch of video conversions"""
        if self.verbosity != LogLevel.QUIET:
            title = "Video Conversion" if operation_type == "conversion" else "Video Processing"
            panel = Panel(
                f"[cyan]Processing {total_files} video files[/cyan]",
                title=f"[bold blue]{title}[/bold blue]",
                border_style="blue"
            )
            self.console.print(panel)
    
    def start_file_conversion(self, input_file: str, output_file: str, duration: Optional[float] = None):
        """Start converting a single file"""
        self.current_operation = Path(input_file).name
        self.conversion_count += 1
        
        if duration:
            self.total_duration += duration
        
        if self.verbosity != LogLevel.QUIET:
            duration_info = f" ({duration:.1f}s)" if duration else ""
            self.console.print(f"[cyan]🎬 Converting: {Path(input_file).name}{duration_info}[/cyan]")
    
    def log_ffmpeg_command(self, command: List[str]):
        """Log FFmpeg command with appropriate verbosity"""
        if self.verbosity == LogLevel.DEBUG:
            # Show full command in debug mode
            cmd_str = " ".join(command)
            if len(cmd_str) > 100:
                cmd_str = cmd_str[:100] + "..."
            self.console.print(f"[dim]  🔧 FFmpeg: {cmd_str}[/dim]")
        elif self.verbosity == LogLevel.VERBOSE:
            # Show simplified command info
            input_files = [arg for i, arg in enumerate(command) if i > 0 and command[i-1] == '-i']
            output_file = command[-1] if command else "unknown"
            self.console.print(f"[dim]  🔧 Processing: {len(input_files)} input(s) → {Path(output_file).name}[/dim]")
    
    def log_conversion_success(self, output_file: str, duration: float, file_size: Optional[int] = None):
        """Log successful conversion"""
        if self.verbosity != LogLevel.QUIET:
            size_info = f" ({file_size // (1024*1024)}MB)" if file_size else ""
            self.console.print(f"[green]  ✅ Created {Path(output_file).name} in {duration:.1f}s{size_info}[/green]")
    
    def log_conversion_failure(self, output_file: str, error: str, duration: Optional[float] = None):
        """Log conversion failure"""
        time_info = f" after {duration:.1f}s" if duration else ""
        # Truncate long FFmpeg error messages
        short_error = error[:100] + "..." if len(error) > 100 else error
        self.console.print(f"[red]  ❌ Failed {Path(output_file).name}{time_info}: {short_error}[/red]")
    
    def log_validation_result(self, file_path: str, is_valid: bool, specs: Optional[Dict] = None):
        """Log video validation results"""
        if self.verbosity in [LogLevel.VERBOSE, LogLevel.DEBUG]:
            if is_valid:
                spec_info = ""
                if specs and self.verbosity == LogLevel.DEBUG:
                    spec_info = f" ({specs.get('width', '?')}x{specs.get('height', '?')} @ {specs.get('fps', '?')}fps)"
                self.console.print(f"[green]  ✅ Validation passed: {Path(file_path).name}{spec_info}[/green]")
            else:
                self.console.print(f"[yellow]  ⚠️  Validation failed: {Path(file_path).name}[/yellow]")
    
    def start_compilation(self, input_files: List[str], output_file: str):
        """Start video compilation process"""
        if self.verbosity != LogLevel.QUIET:
            panel = Panel(
                f"[cyan]Compiling {len(input_files)} video segments[/cyan]\n"
                f"[yellow]Output: {Path(output_file).name}[/yellow]",
                title="[bold magenta]Video Compilation[/bold magenta]",
                border_style="magenta"
            )
            self.console.print(panel)
    
    def log_compilation_progress(self, current_segment: int, total_segments: int, segment_name: str):
        """Log compilation progress"""
        if self.verbosity in [LogLevel.NORMAL, LogLevel.VERBOSE, LogLevel.DEBUG]:
            self.console.print(f"[cyan]  📼 [{current_segment}/{total_segments}] Adding: {segment_name}[/cyan]")
    
    def log_compilation_success(self, output_file: str, duration: float, total_duration: float, file_size: Optional[int] = None):
        """Log successful compilation"""
        if self.verbosity != LogLevel.QUIET:
            size_info = f" ({file_size // (1024*1024)}MB)" if file_size else ""
            self.console.print(f"[green]✅ Compilation complete: {Path(output_file).name}[/green]")
            self.console.print(f"[green]   📊 Video duration: {total_duration:.1f}s, Processing time: {duration:.1f}s{size_info}[/green]")
    
    def display_conversion_summary(self, stats: Dict[str, Any]):
        """Display video processing summary"""
        if self.verbosity == LogLevel.QUIET:
            return
        
        table = Table(title="Video Processing Summary", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green", justify="right")
        
        table.add_row("Files Processed", str(stats.get('total_files', 0)))
        table.add_row("✅ Successful", str(stats.get('successful_conversions', 0)))
        table.add_row("❌ Failed", str(stats.get('failed_conversions', 0)))
        table.add_row("⏭️  Skipped", str(stats.get('skipped_conversions', 0)))
        
        if 'total_video_duration' in stats:
            table.add_row("🎬 Total Video Duration", f"{stats['total_video_duration']:.1f}s")
        
        if 'processing_time' in stats:
            table.add_row("⏱️  Processing Time", f"{stats['processing_time']:.1f}s")
        
        if 'output_file_size' in stats:
            size_mb = stats['output_file_size'] / (1024 * 1024)
            table.add_row("📁 Output Size", f"{size_mb:.1f}MB")
        
        self.console.print(table)
    
    @contextmanager
    def conversion_progress_context(self, total_items: int, description: str = "Converting videos"):
        """Context manager for video conversion progress"""
        if self.verbosity == LogLevel.QUIET:
            class QuietProgress:
                def __init__(self):
                    self.completed = 0
                
                def advance(self, increment=1):
                    self.completed += increment
            
            yield QuietProgress()
            return
        
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
            
            class VideoProgressTracker:
                def __init__(self, progress_obj, task_id):
                    self.progress = progress_obj
                    self.task_id = task_id
                
                def advance(self, increment=1):
                    self.progress.advance(self.task_id, increment)
                
                def update_description(self, description: str):
                    self.progress.update(self.task_id, description=description)
            
            yield VideoProgressTracker(progress, task)
    
    @contextmanager
    def long_operation_context(self, description: str = "Processing video..."):
        """Context manager for long video operations with spinner"""
        if self.verbosity == LogLevel.QUIET:
            yield
            return
        
        from rich.spinner import Spinner
        from rich.live import Live
        
        spinner = Spinner("dots", text=f"[cyan]{description}[/cyan]")
        
        with Live(spinner, console=self.console, refresh_per_second=4):
            yield
    
    def log_background_image_selection(self, segment_type: str, image_path: str):
        """Log background image selection"""
        if self.verbosity == LogLevel.DEBUG:
            self.console.print(f"[dim]  🖼️  {segment_type}: {Path(image_path).name}[/dim]")
    
    def log_technical_specs(self, specs: Dict[str, Any]):
        """Log video technical specifications"""
        if self.verbosity in [LogLevel.VERBOSE, LogLevel.DEBUG]:
            specs_panel = Panel(
                "\n".join([f"[cyan]{key}:[/cyan] {value}" for key, value in specs.items()]),
                title="[bold]Video Specifications[/bold]",
                border_style="blue"
            )
            self.console.print(specs_panel)
    
    def create_error_summary(self, failed_conversions: List[Dict[str, Any]]):
        """Create a summary of failed conversions"""
        if not failed_conversions or self.verbosity == LogLevel.QUIET:
            return
        
        error_table = Table(title="Failed Conversions", box=box.ROUNDED)
        error_table.add_column("File", style="red")
        error_table.add_column("Error", style="yellow")
        
        for failure in failed_conversions[:10]:  # Limit to first 10 failures
            error_table.add_row(
                Path(failure.get('file_path', 'Unknown')).name,
                failure.get('error', 'Unknown error')[:50] + "..." if len(failure.get('error', '')) > 50 else failure.get('error', 'Unknown error')
            )
        
        if len(failed_conversions) > 10:
            error_table.add_row("...", f"({len(failed_conversions) - 10} more failures)")
        
        self.console.print(error_table)


def create_video_logger(enhanced_logger: EnhancedPipelineLogger) -> VideoOperationLogger:
    """Factory function to create a video logger"""
    return VideoOperationLogger(enhanced_logger)
