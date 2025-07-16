"""
Progress Logger - Enhanced progress tracking for long operations
===============================================================

Provides beautiful progress bars, spinners, and status displays for long-running
operations in the YouTube processing pipeline.

Features:
- Download progress tracking with spinners
- Processing step tables with status updates
- Real-time progress bars for file operations
- Multi-step process visualization

Created: June 26, 2025
Based on: Enhanced Logging System specification
"""

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from datetime import datetime
import time

class ProgressLogger:
    """
    Logger for tracking progress of long-running operations.
    
    Provides progress bars, spinners, and status tables for operations
    like downloads, file processing, and multi-step workflows.
    """
    
    def __init__(self):
        """Initialize the progress logger."""
        self.console = Console()
        
    def show_download_progress(self, url, description="Downloading"):
        """
        Show a spinner for download operations.
        
        Args:
            url (str): URL being downloaded
            description (str): Description of the download operation
            
        Returns:
            Progress: Progress context manager for updating status
        """
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        )
        
        # Extract filename from URL for display
        filename = url.split('/')[-1] if '/' in url else url[:50] + "..."
        
        return progress, progress.add_task(f"{description}: {filename}", total=None)
        
    def show_file_progress(self, description="Processing", total_steps=100):
        """
        Show a progress bar for file operations with known total.
        
        Args:
            description (str): Description of the operation
            total_steps (int): Total number of steps/items to process
            
        Returns:
            tuple: (Progress object, task_id) for updating progress
        """
        progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        )
        
        task_id = progress.add_task(description, total=total_steps)
        return progress, task_id
        
    def show_processing_steps(self, steps):
        """
        Display a table of processing steps with their current status.
        
        Args:
            steps (list): List of step dictionaries with 'name', 'status', 'details'
        """
        table = Table(title="Processing Steps")
        table.add_column("Step", style="cyan", no_wrap=True)
        table.add_column("Status", style="magenta")
        table.add_column("Details", style="green")
        
        for step in steps:
            status_icon = self._get_status_icon(step.get('status', 'pending'))
            table.add_row(
                step['name'], 
                f"{status_icon} {step.get('status', 'pending')}", 
                step.get('details', '')
            )
            
        self.console.print(table)
        
    def show_live_processing_steps(self, steps):
        """
        Display a live-updating table of processing steps.
        
        Args:
            steps (list): List of step dictionaries that will be updated in place
            
        Returns:
            Live: Live context manager for real-time updates
        """
        def make_table():
            table = Table(title="Processing Steps")
            table.add_column("Step", style="cyan", no_wrap=True)
            table.add_column("Status", style="magenta")
            table.add_column("Details", style="green")
            
            for step in steps:
                status_icon = self._get_status_icon(step.get('status', 'pending'))
                table.add_row(
                    step['name'], 
                    f"{status_icon} {step.get('status', 'pending')}", 
                    step.get('details', '')
                )
            return table
        
        return Live(make_table(), console=self.console, refresh_per_second=2)
        
    def show_multi_progress(self, tasks):
        """
        Display multiple progress bars for concurrent operations.
        
        Args:
            tasks (list): List of task dictionaries with 'name' and 'total'
            
        Returns:
            tuple: (Progress object, list of task_ids)
        """
        progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        )
        
        task_ids = []
        for task in tasks:
            task_id = progress.add_task(
                task['name'], 
                total=task.get('total', 100)
            )
            task_ids.append(task_id)
            
        return progress, task_ids
        
    def show_stage_progress(self, stage_name, substeps):
        """
        Display progress for a pipeline stage with substeps.
        
        Args:
            stage_name (str): Name of the current stage
            substeps (list): List of substep names
            
        Returns:
            tuple: (Progress object, task_id, substep_task_ids)
        """
        progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        )
        
        # Main stage progress
        main_task = progress.add_task(f"🎬 {stage_name}", total=len(substeps))
        
        # Individual substep progress bars
        substep_tasks = []
        for substep in substeps:
            substep_task = progress.add_task(f"  → {substep}", total=100)
            substep_tasks.append(substep_task)
            
        return progress, main_task, substep_tasks
        
    def _get_status_icon(self, status):
        """
        Get appropriate icon for status.
        
        Args:
            status (str): Status string
            
        Returns:
            str: Unicode icon for the status
        """
        status_icons = {
            'pending': '⏳',
            'running': '🔄',
            'success': '✅',
            'complete': '✅',
            'completed': '✅',
            'failed': '❌',
            'error': '❌',
            'warning': '⚠️',
            'skipped': '⏭️',
            'cancelled': '🚫'
        }
        
        return status_icons.get(status.lower(), '❔')
        
    def show_completion_stats(self, stats):
        """
        Display completion statistics in a nice panel.
        
        Args:
            stats (dict): Dictionary with statistics like files_processed, time_taken, etc.
        """
        stats_text = []
        
        if 'files_processed' in stats:
            stats_text.append(f"[white]📁 Files Processed:[/] [cyan]{stats['files_processed']}[/]")
            
        if 'time_taken' in stats:
            stats_text.append(f"[white]⏱️  Time Taken:[/] [yellow]{stats['time_taken']}[/]")
            
        if 'output_size' in stats:
            stats_text.append(f"[white]📊 Output Size:[/] [green]{stats['output_size']}[/]")
            
        if 'success_rate' in stats:
            stats_text.append(f"[white]✅ Success Rate:[/] [green]{stats['success_rate']}%[/]")
            
        # Add any custom stats
        for key, value in stats.items():
            if key not in ['files_processed', 'time_taken', 'output_size', 'success_rate']:
                formatted_key = key.replace('_', ' ').title()
                stats_text.append(f"[white]{formatted_key}:[/] [cyan]{value}[/]")
        
        if stats_text:
            panel = Panel(
                "\n".join(stats_text),
                title="[bold cyan]📊 Processing Statistics[/]",
                border_style="cyan"
            )
            self.console.print(panel)
