"""
Menu Logger - Enhanced menu display for YouTube processing pipeline
===================================================================

Provides beautiful, consistent menu interfaces using Rich library formatting.
Replaces basic print statements with colorful, professional menu displays.

Features:
- Main pipeline menu with current URL display
- Stage selection menus with clear formatting
- Status indicators and visual hierarchy
- Consistent styling across all menus

Created: June 26, 2025
Based on: Enhanced Logging System specification
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align

class MenuLogger:
    """
    Logger for displaying beautiful menu interfaces.
    
    Provides consistent, colorful menu displays for the YouTube processing
    pipeline with proper formatting and status indicators.
    """
    
    def __init__(self):
        """Initialize the menu logger."""
        # Force UTF-8 encoding for Windows console compatibility
        import sys
        if sys.platform == "win32":
            self.console = Console(force_terminal=True, legacy_windows=False)
        else:
            self.console = Console()
        
    def show_main_menu(self, youtube_url=None):
        """
        Display the main pipeline menu with current URL status.
        
        Args:
            youtube_url (str, optional): Current YouTube URL if set
        """
        # URL status with color coding
        url_status = f"[green]{youtube_url}[/]" if youtube_url else "[red]not set[/]"
        
        # Create menu content as formatted text
        menu_content = (
            "[cyan bold]1[/]  Run FULL pipeline (all 7 stages)\n"
            "[cyan bold]2[/]  Run pipeline (END at selected stage)\n" 
            "[cyan bold]3[/]  Start pipeline from specific stage\n"
            "[cyan bold]4[/]  Run ONE STAGE ONLY\n"
            "\n"
            "[cyan bold]0[/]  [bold red]Exit[/]\n"
            "\n"
            f"[white]Current YouTube URL:[/] {url_status}"
        )
        
        panel = Panel(
            menu_content,
            title="[bold cyan]🎬 YouTube Processing Pipeline[/]",
            border_style="cyan",
            padding=(1, 2)
        )
        
        self.console.print("\n")
        self.console.print(panel)
        
    def show_stage_menu(self, title, stages, back_option="Back to main menu"):
        """
        Display a stage selection menu.
        
        Args:
            title (str): Title for the menu
            stages (list): List of stage names
            back_option (str): Text for the back option (default: "Back to main menu")
        """
        # Create menu content as formatted text
        menu_lines = []
        
        # Add all stages
        for i, stage in enumerate(stages, 1):
            menu_lines.append(f"[yellow bold]{i}[/]  {stage}")
            
        # Add separator and back option
        menu_lines.append("")  # Spacer
        menu_lines.append(f"[yellow bold]0[/]  [dim]{back_option}[/]")
        
        menu_content = "\n".join(menu_lines)
        
        panel = Panel(
            menu_content,
            title=f"[bold yellow]{title}[/]",
            border_style="yellow",
            padding=(1, 2)
        )
        
        self.console.print("\n")
        self.console.print(panel)
        
    def show_end_at_menu(self, stages):
        """
        Display menu for selecting end stage.
        
        Args:
            stages (list): List of stage names
        """
        self.show_stage_menu("🏁 Select END Stage", stages, "Back to main menu")
        
    def show_start_from_menu(self, stages):
        """
        Display menu for selecting start stage.
        
        Args:
            stages (list): List of stage names
        """
        self.show_stage_menu("🚀 Select START Stage", stages, "Back to main menu")
        
    def show_single_stage_menu(self, stages):
        """
        Display menu for selecting a single stage to run.
        
        Args:
            stages (list): List of stage names
        """
        self.show_stage_menu("🎯 Select Single Stage", stages, "Back to main menu")
        
    def show_url_prompt(self):
        """Display prompt for YouTube URL entry."""
        panel = Panel(
            "[white]Please enter the YouTube URL you want to process:[/]\n\n"
            "[dim]Example: https://www.youtube.com/watch?v=dQw4w9WgXcQ[/]",
            title="[bold cyan]🔗 YouTube URL Required[/]",
            border_style="cyan"
        )
        
        self.console.print("\n")
        self.console.print(panel)
        
    def show_invalid_choice(self, choice, max_option):
        """
        Display error message for invalid menu choice.
        
        Args:
            choice (str): The invalid choice entered
            max_option (int): Maximum valid option number
        """
        self.console.print(
            f"\n[bold red]❌ Invalid choice: '{choice}'[/]\n"
            f"[yellow]Please enter a number from 0 to {max_option}[/]"
        )
        
    def show_url_set_confirmation(self, url):
        """
        Display confirmation that URL has been set.
        
        Args:
            url (str): The YouTube URL that was set
        """
        self.console.print(f"\n[green]✅ YouTube URL set:[/] [cyan]{url}[/]")
        
    def show_processing_start(self, operation_type, stage_info=""):
        """
        Display message when processing starts.
        
        Args:
            operation_type (str): Type of operation (e.g., "FULL pipeline", "Single stage")
            stage_info (str, optional): Additional stage information
        """
        message = f"[bold green]🚀 Starting {operation_type}[/]"
        if stage_info:
            message += f"\n[white]{stage_info}[/]"
            
        panel = Panel(
            message,
            title="[bold green]Processing Started[/]",
            border_style="green"
        )
        
        self.console.print("\n")
        self.console.print(panel)
        
    def show_goodbye(self):
        """Display goodbye message when exiting."""
        goodbye_panel = Panel(
            "[bold cyan]Thank you for using the YouTube Processing Pipeline![/]\n\n"
            "[white]🎬 Happy video processing! 🎬[/]",
            title="[bold green]Goodbye! 👋[/]",
            border_style="green",
            padding=(1, 2)
        )
        
        self.console.print("\n")
        self.console.print(Align.center(goodbye_panel))
        self.console.print()
        
    def show_narrative_format_menu(self):
        """Display menu for selecting narrative format."""
        menu_content = (
            "[cyan bold]1[/]  Narrative with normal format (tts_podcast_narrative_prompt_WITHOUT_HOOK.txt)\n"
            "[cyan bold]2[/]  Narrative with Opening Hook (tts_podcast_narrative_prompt.txt)\n"
            "\n"
            "[cyan bold]0[/]  [bold red]Cancel[/]"
        )
        
        panel = Panel(
            menu_content,
            title="[bold blue]📝 Select Narrative Format[/]",
            border_style="blue",
            padding=(1, 2)
        )
        
        self.console.print("\n")
        self.console.print(panel)

    def show_error(self, error_message):
        """
        Display an error message in a formatted panel.
        
        Args:
            error_message (str): Error message to display
        """
        panel = Panel(
            f"[bold red]❌ Error:[/]\n[red]{error_message}[/]",
            title="[bold red]Error[/]",
            border_style="red"
        )
        
        self.console.print("\n")
        self.console.print(panel)
        
    def show_warning(self, warning_message):
        """
        Display a warning message in a formatted panel.
        
        Args:
            warning_message (str): Warning message to display
        """
        panel = Panel(
            f"[bold yellow]⚠️  Warning:[/]\n[yellow]{warning_message}[/]",
            title="[bold yellow]Warning[/]",
            border_style="yellow"
        )
        
        self.console.print("\n")
        self.console.print(panel)
        
    def show_info(self, info_message, title="Information"):
        """
        Display an informational message in a formatted panel.
        
        Args:
            info_message (str): Information message to display
            title (str): Title for the panel
        """
        panel = Panel(
            f"[cyan]ℹ️  {info_message}[/]",
            title=f"[bold cyan]{title}[/]",
            border_style="cyan"
        )
        
        self.console.print("\n")
        self.console.print(panel)
    
    def show_episode_selection(self, episodes):
        """
        Display episode selection menu with enhanced formatting.
        
        Args:
            episodes (list): List of episode names/paths
        """
        if not episodes:
            self.show_error("No episodes found in Content directory.")
            return
            
        # Create episodes table
        episode_table = Table(show_header=False, box=None, padding=(0, 2))
        episode_table.add_column("Number", style="cyan bold", width=3)
        episode_table.add_column("Episode", style="white")
        
        # Add episodes with shortened display names
        for idx, episode in enumerate(episodes, 1):
            # Clean up episode name for display
            display_name = episode.replace("\\", " - ").replace("/", " - ")
            if len(display_name) > 80:
                display_name = display_name[:77] + "..."
            episode_table.add_row(str(idx), display_name)
            
        # Add back option
        episode_table.add_row("", "")  # Spacer
        episode_table.add_row("0", "[dim]Back to main menu[/]")
        
        self.console.print("\n")
        self.console.print(episode_table)
        
        panel = Panel(
            "[white]Select an episode from the list above[/]",
            title="[bold magenta]📺 Episode Selection[/]",
            border_style="magenta"
        )
        
        self.console.print("\n")
        self.console.print(panel)
