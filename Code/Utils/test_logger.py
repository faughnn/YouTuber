"""
Test Logger - Enhanced logging for test operations and validation
================================================================

Provides beautiful test result displays with pass/fail indicators, summaries,
and detailed reporting for development and validation workflows.

Features:
- Individual test result tracking
- Summary statistics with visual indicators
- Colorful pass/fail displays
- Test suite completion celebrations
- Detailed error reporting

Created: June 26, 2025
Based on: Enhanced Logging System specification
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from datetime import datetime

class TestLogger:
    """
    Logger for test operations and validation workflows.
    
    Provides beautiful formatting for test results, summaries, and validation
    processes with clear pass/fail indicators and detailed reporting.
    """
    
    def __init__(self):
        """Initialize the test logger."""
        self.console = Console()
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []
        self.start_time = None
        
    def test_suite_start(self, suite_name):
        """
        Display test suite start message.
        
        Args:
            suite_name (str): Name of the test suite
        """
        self.start_time = datetime.now()
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []
        
        panel = Panel(
            f"[bold cyan]🧪 Starting Test Suite: {suite_name}[/]\n"
            f"[white]Started at:[/] {self.start_time.strftime('%H:%M:%S')}",
            title="[bold blue]Test Suite[/]",
            border_style="blue"
        )
        self.console.print(panel)
        
    def test_start(self, test_name):
        """
        Display test start message.
        
        Args:
            test_name (str): Name of the test being started
        """
        self.console.print(f"\n[bold blue]🧪 Testing: {test_name}[/]")
        
        # Track test start
        self.test_results.append({
            'name': test_name,
            'start_time': datetime.now(),
            'status': 'running',
            'message': None,
            'details': None
        })
        
    def test_success(self, message, details=None):
        """
        Record and display a test success.
        
        Args:
            message (str): Success message
            details (str, optional): Additional details about the success
        """
        self.console.print(f"[green]  ✅ {message}[/]")
        if details:
            self.console.print(f"[dim]     {details}[/]")
            
        self.tests_passed += 1
        
        # Update the most recent test result
        if self.test_results:
            self.test_results[-1].update({
                'status': 'passed',
                'message': message,
                'details': details,
                'end_time': datetime.now()
            })
        
    def test_failure(self, message, details=None):
        """
        Record and display a test failure.
        
        Args:
            message (str): Failure message
            details (str, optional): Additional details about the failure
        """
        self.console.print(f"[red]  ❌ {message}[/]")
        if details:
            self.console.print(f"[dim red]     {details}[/]")
            
        self.tests_failed += 1
        
        # Update the most recent test result
        if self.test_results:
            self.test_results[-1].update({
                'status': 'failed',
                'message': message,
                'details': details,
                'end_time': datetime.now()
            })
        
    def test_warning(self, message, details=None):
        """
        Display a test warning (doesn't count as pass or fail).
        
        Args:
            message (str): Warning message
            details (str, optional): Additional details about the warning
        """
        self.console.print(f"[yellow]  ⚠️  {message}[/]")
        if details:
            self.console.print(f"[dim yellow]     {details}[/]")
            
    def test_info(self, message):
        """
        Display test information.
        
        Args:
            message (str): Information message
        """
        self.console.print(f"[cyan]  ℹ️  {message}[/]")
        
    def test_summary(self):
        """
        Display test summary and return success status.
        
        Returns:
            bool: True if all tests passed, False otherwise
        """
        total = self.tests_passed + self.tests_failed
        elapsed = datetime.now() - self.start_time if self.start_time else None
        
        if self.tests_failed == 0 and total > 0:
            # All tests passed celebration
            celebration = """
🎉✅🎉✅🎉✅🎉✅🎉✅🎉

    ALL TESTS PASSED!
    
🎉✅🎉✅🎉✅🎉✅🎉✅🎉
            """
            
            panel = Panel(
                f"[bold green]{celebration}[/]\n"
                f"[white]Tests Passed:[/] [green]{self.tests_passed}[/]\n"
                f"[white]Duration:[/] [yellow]{elapsed}[/]\n"
                f"[green]✅ Implementation is complete and ready for production[/]",
                title="[bold green]🏆 TEST SUITE SUCCESS! 🏆[/]",
                border_style="green",
                padding=(1, 2)
            )
            
            self.console.print("\n")
            self.console.print(Align.center(panel))
            
        elif total == 0:
            # No tests run
            panel = Panel(
                f"[yellow]⚠️  No tests were executed[/]\n"
                f"[white]Duration:[/] [yellow]{elapsed}[/]",
                title="[bold yellow]No Tests Run[/]",
                border_style="yellow"
            )
            self.console.print("\n")
            self.console.print(panel)
            
        else:
            # Some tests failed
            panel = Panel(
                f"[white]Tests Passed:[/] [green]{self.tests_passed}[/]\n"
                f"[white]Tests Failed:[/] [red]{self.tests_failed}[/]\n"
                f"[white]Success Rate:[/] [yellow]{(self.tests_passed/total)*100:.1f}%[/]\n"
                f"[white]Duration:[/] [yellow]{elapsed}[/]\n"
                f"[red]❌ Please check the implementation[/]",
                title="[bold red]Test Results[/]",
                border_style="red"
            )
            self.console.print("\n")
            self.console.print(panel)
        
        # Show detailed results table if there are test results
        if self.test_results:
            self.show_detailed_results()
            
        return self.tests_failed == 0 and total > 0
    
    def show_detailed_results(self):
        """Display a detailed table of all test results."""
        table = Table(title="Detailed Test Results")
        table.add_column("Test Name", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Duration", style="yellow")
        table.add_column("Message", style="white")
        
        for test in self.test_results:
            # Calculate duration if both times are available
            duration = "N/A"
            if 'end_time' in test and test['end_time']:
                duration_delta = test['end_time'] - test['start_time']
                duration = f"{duration_delta.total_seconds():.2f}s"
            
            # Status icon and color
            if test['status'] == 'passed':
                status = "[green]✅ PASS[/]"
            elif test['status'] == 'failed':
                status = "[red]❌ FAIL[/]"
            else:
                status = "[yellow]🔄 RUNNING[/]"
            
            table.add_row(
                test['name'],
                status,
                duration,
                test.get('message', '')
            )
        
        self.console.print("\n")
        self.console.print(table)
        
    def validation_start(self, validation_name):
        """
        Start a validation process.
        
        Args:
            validation_name (str): Name of the validation process
        """
        self.console.print(f"\n[bold magenta]🔍 Validation: {validation_name}[/]")
        
    def validation_pass(self, message):
        """
        Record a validation pass.
        
        Args:
            message (str): Validation success message
        """
        self.console.print(f"[green]  ✅ {message}[/]")
        
    def validation_fail(self, message):
        """
        Record a validation failure.
        
        Args:
            message (str): Validation failure message
        """
        self.console.print(f"[red]  ❌ {message}[/]")
        
    def show_validation_summary(self, passed, failed):
        """
        Show validation summary.
        
        Args:
            passed (int): Number of validations passed
            failed (int): Number of validations failed
        """
        total = passed + failed
        
        if failed == 0 and total > 0:
            panel = Panel(
                f"[bold green]🎉 All {total} validations passed![/]\n"
                f"[green]✅ System is ready for use[/]",
                title="[bold green]Validation Success[/]",
                border_style="green"
            )
        else:
            panel = Panel(
                f"[white]Validations Passed:[/] [green]{passed}[/]\n"
                f"[white]Validations Failed:[/] [red]{failed}[/]\n"
                f"[red]❌ System requires attention[/]",
                title="[bold red]Validation Results[/]",
                border_style="red"
            )
        
        self.console.print("\n")
        self.console.print(panel)
