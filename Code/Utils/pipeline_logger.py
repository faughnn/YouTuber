"""
Pipeline Logger - Enhanced logging for YouTube processing pipeline
================================================================

Provides beautiful, consistent logging output for pipeline operations using Rich library.
Designed for YouTube video processing pipeline with stage-based progress tracking.

Features:
- Colorful console output with panels and formatting
- Pipeline start/completion celebrations  
- Stage-by-stage progress tracking
- Error handling with detailed output
- Duration tracking and statistics

Created: June 26, 2025
Based on: Enhanced Logging System specification
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
import logging
from datetime import datetime

class PipelineLogger:
    """
    Main logger for YouTube processing pipeline operations.
    
    Provides rich console output for pipeline stages, completion messages,
    and error handling with beautiful formatting and colors.
    """
    
    def __init__(self, name="Pipeline"):
        """
        Initialize the pipeline logger.
        
        Args:
            name (str): Name of the pipeline for logging context
        """
        self.console = Console()
        self.name = name
        self.start_time = None
        self.stages_completed = []
        
    def pipeline_start(self, url, pipeline_type="FULL"):
        """
        Display pipeline start message with URL and timestamp.
        
        Args:
            url (str): YouTube URL being processed
            pipeline_type (str): Type of pipeline (FULL, AUDIO, SCRIPT, etc.)
        """
        self.start_time = datetime.now()
        self.stages_completed = []
        
        panel = Panel(
            f"[bold cyan]🚀 {pipeline_type} PIPELINE STARTING[/]\n"
            f"[white]URL:[/] {url}\n"
            f"[white]Started:[/] {self.start_time.strftime('%H:%M:%S')}",
            title="[bold green]YouTube Processing Pipeline[/]",
            border_style="green"
        )
        self.console.print(panel)
        
    def stage_start(self, stage_num, stage_name):
        """
        Display stage start message.
        
        Args:
            stage_num (int): Stage number (1-7)
            stage_name (str): Name of the stage
        """
        self.console.print(f"\n[bold yellow]📋 Stage {stage_num}: {stage_name}[/]", style="yellow")
        stage_start_time = datetime.now()
        
        # Track stage start for summary
        self.stages_completed.append({
            'number': stage_num,
            'name': stage_name,
            'start_time': stage_start_time,
            'success': None,
            'output': None,
            'error': None
        })
        
    def stage_success(self, stage_num, stage_name, result_path=None):
        """
        Display stage success message with optional result path.
        
        Args:
            stage_num (int): Stage number (1-7)
            stage_name (str): Name of the stage
            result_path (str, optional): Path to stage output file
        """
        end_time = datetime.now()
        
        # Update stage tracking
        for stage in self.stages_completed:
            if stage['number'] == stage_num:
                stage['success'] = True
                stage['end_time'] = end_time
                stage['duration'] = str(end_time - stage['start_time']).split('.')[0]
                stage['output'] = result_path
                break
        
        if result_path:
            self.console.print(f"[bold green]✅ Stage {stage_num} Complete:[/] {stage_name}")
            self.console.print(f"[dim]   → Output: {result_path}[/]")
        else:
            self.console.print(f"[bold green]✅ Stage {stage_num} Complete:[/] {stage_name}")
            
    def stage_error(self, stage_num, stage_name, error):
        """
        Display stage error message with error details.
        
        Args:
            stage_num (int): Stage number (1-7)
            stage_name (str): Name of the stage
            error (Exception or str): Error that occurred
        """
        end_time = datetime.now()
        
        # Update stage tracking
        for stage in self.stages_completed:
            if stage['number'] == stage_num:
                stage['success'] = False
                stage['end_time'] = end_time
                stage['duration'] = str(end_time - stage['start_time']).split('.')[0]
                stage['error'] = str(error)
                break
        
        self.console.print(f"[bold red]❌ Stage {stage_num} Failed:[/] {stage_name}")
        self.console.print(f"[red]   Error: {str(error)}[/]")
        
    def pipeline_complete(self, final_output=None):
        """
        Display beautiful pipeline completion celebration.
        
        Args:
            final_output (str, optional): Path to final output file
        """
        elapsed = datetime.now() - self.start_time if self.start_time else None
        
        # Create celebration message
        celebration = """
🎉🎬🎉🎬🎉🎬🎉🎬🎉🎬🎉

     PIPELINE COMPLETE!
     
🎉🎬🎉🎬🎉🎬🎉🎬🎉🎬🎉
        """
        
        if final_output:
            panel = Panel(
                f"[bold green]{celebration}[/]\n"
                f"[white]✨ Final Output Ready:[/] [cyan]{final_output}[/]\n"
                f"[white]⏱️  Total Duration:[/] [yellow]{elapsed}[/]\n"
                f"[white]🚀 Ready for Upload![/]",
                title="[bold green]🏆 SUCCESS! 🏆[/]",
                border_style="green",
                padding=(1, 2)
            )
        else:
            panel = Panel(
                f"[bold green]{celebration}[/]\n"
                f"[white]⏱️  Total Duration:[/] [yellow]{elapsed}[/]\n"
                f"[white]🎉 Pipeline Completed Successfully![/]",
                title="[bold green]🏆 SUCCESS! 🏆[/]",
                border_style="green",
                padding=(1, 2)
            )
        
        self.console.print("\n")
        self.console.print(Align.center(panel))
        
        # Show pipeline summary
        self.show_pipeline_summary()
        
    def pipeline_failed(self, error):
        """
        Display pipeline failure message with error details.
        
        Args:
            error (Exception or str): Error that caused pipeline failure
        """
        elapsed = datetime.now() - self.start_time if self.start_time else None
        panel = Panel(
            f"[bold red]💥 PIPELINE FAILED[/]\n"
            f"[red]Error:[/] {str(error)}\n"
            f"[white]Duration:[/] {elapsed}",
            title="[bold red]Failure[/]",
            border_style="red"
        )
        self.console.print("\n")
        self.console.print(panel)
        
        # Show summary of completed stages
        if self.stages_completed:
            self.show_pipeline_summary()
        
    def show_pipeline_summary(self):
        """Display a summary table of all pipeline stages and their status."""
        if not self.stages_completed:
            return
            
        summary_table = Table(title="Pipeline Summary")
        summary_table.add_column("Stage", style="cyan")
        summary_table.add_column("Status", justify="center")
        summary_table.add_column("Duration", style="yellow")
        summary_table.add_column("Output", style="green")
        
        for stage in self.stages_completed:
            if stage['success'] is True:
                status_icon = "✅"
                duration = stage.get('duration', 'N/A')
                output = stage.get('output', 'N/A')
            elif stage['success'] is False:
                status_icon = "❌"
                duration = stage.get('duration', 'N/A')
                output = f"Error: {stage.get('error', 'Unknown')}"
            else:
                status_icon = "⏸️"
                duration = "Not completed"
                output = "N/A"
            
            summary_table.add_row(
                f"{stage['number']}. {stage['name']}",
                status_icon,
                duration,
                output
            )
        
        self.console.print("\n")
        self.console.print(summary_table)
        
    def info(self, message):
        """Display an info message."""
        self.console.print(f"[cyan]ℹ️  {message}[/]")
        
    def success(self, message):
        """Display a success message."""
        self.console.print(f"[green]✅ {message}[/]")
        
    def warning(self, message):
        """Display a warning message."""
        self.console.print(f"[yellow]⚠️  {message}[/]")
        
    def error(self, message):
        """Display an error message."""
        self.console.print(f"[red]❌ {message}[/]")
