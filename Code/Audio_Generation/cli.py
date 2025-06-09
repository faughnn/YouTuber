"""
Command Line Interface for TTS Audio Generation System

Provides easy-to-use commands for processing single files or batches
of script files to generate audio using Gemini TTS.
"""

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import List, Dict, Optional

from .batch_processor import AudioBatchProcessor, ProcessingReport
from .config import AudioGenerationConfig
from .batch_discovery import BatchDiscovery, DiscoveryResult

logger = logging.getLogger(__name__)


class AudioGenerationCLI:
    """
    Command-line interface for the TTS Audio Generation System.
    
    Provides user-friendly CLI for script processing, batch discovery,
    and configuration overrides.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the CLI interface.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config = AudioGenerationConfig(config_path)
        self.processor = AudioBatchProcessor(config_path)
        
    def run_single_script(self, script_path: str, options: Dict) -> bool:
        """
        Process a single script file.
        
        Args:
            script_path: Path to the script file to process
            options: CLI options and overrides
            
        Returns:
            True if processing was successful
        """
        try:
            print(f"\n🎵 Processing script: {Path(script_path).name}")
            print("-" * 50)
            
            # Validate script file exists
            if not Path(script_path).exists():
                print(f"❌ Error: Script file not found: {script_path}")
                return False
            
            # Process the script
            start_time = time.time()
            report = self.processor.process_script_file(script_path, options)
            processing_time = time.time() - start_time
            
            # Display results
            self._display_single_script_results(report, processing_time)
            
            return report.successful_sections > 0
            
        except Exception as e:
            print(f"❌ Error processing script: {e}")
            logger.error(f"Error in run_single_script: {e}", exc_info=True)
            return False
    
    def run_batch_processing(self, content_root: str, options: Dict) -> Dict:
        """
        Discover and process all pending scripts in content directory.
        
        Args:
            content_root: Root directory to search for scripts
            options: CLI options and overrides
            
        Returns:
            Summary of batch processing results
        """
        try:
            print(f"\n🔍 Discovering scripts in: {content_root}")
            print("=" * 60)
            
            # Discover pending scripts
            pending_scripts = self.discover_pending_scripts(content_root)
            
            if not pending_scripts:
                print("✅ No pending scripts found - all episodes up to date!")
                return {"total_scripts": 0, "processed": 0, "successful": 0}
            
            print(f"📋 Found {len(pending_scripts)} pending scripts:")
            for i, script_path in enumerate(pending_scripts, 1):
                episode_name = self._extract_episode_name(script_path)
                print(f"  {i}. {episode_name}")
            
            # Confirm batch processing
            if not options.get('auto_confirm', False):
                response = input(f"\n🤔 Process all {len(pending_scripts)} scripts? [y/N]: ")
                if response.lower() not in ['y', 'yes']:
                    print("❌ Batch processing cancelled by user")
                    return {"total_scripts": len(pending_scripts), "processed": 0, "successful": 0}
            
            # Process each script
            results = []
            successful_count = 0
            
            print(f"\n🚀 Starting batch processing...")
            print("=" * 60)
            
            for i, script_path in enumerate(pending_scripts, 1):
                print(f"\n[{i}/{len(pending_scripts)}] Processing: {self._extract_episode_name(script_path)}")
                
                try:
                    report = self.processor.process_script_file(script_path, options)
                    results.append(report)
                    
                    if report.successful_sections > 0:
                        successful_count += 1
                        print(f"✅ Success: {report.successful_sections}/{report.total_sections} sections generated")
                    else:
                        print(f"❌ Failed: No sections generated")
                        
                except Exception as e:
                    print(f"❌ Error: {e}")
                    logger.error(f"Error processing {script_path}: {e}")
            
            # Display batch summary
            self._display_batch_results(results, successful_count, len(pending_scripts))
            
            return {
                "total_scripts": len(pending_scripts),
                "processed": len(results),
                "successful": successful_count,
                "results": results
            }
            
        except Exception as e:
            print(f"❌ Error in batch processing: {e}")
            logger.error(f"Error in run_batch_processing: {e}", exc_info=True)
            return {"total_scripts": 0, "processed": 0, "successful": 0}
    
    def discover_pending_scripts(self, content_root: str) -> List[str]:
        """
        Discover script files that need audio generation.
        
        Args:
            content_root: Root directory to search
            
        Returns:
            List of script file paths that need processing
        """
        try:
            content_path = Path(content_root)
            if not content_path.exists():
                logger.warning(f"Content root does not exist: {content_root}")
                return []
            
            pending_scripts = []
            
            # Search for Gemini response files
            script_patterns = [
                "**/debug_gemini_response.txt",
                "**/debug_gemini_response_*.txt",
                "**/gemini_response.json",
                "**/gemini_response_*.json"
            ]
            
            for pattern in script_patterns:
                for script_file in content_path.glob(pattern):
                    # Check if this episode needs audio generation
                    if self._needs_audio_generation(script_file):
                        pending_scripts.append(str(script_file))
            
            # Sort by episode name for consistent processing order
            pending_scripts.sort(key=self._extract_episode_name)
            
            logger.info(f"Discovered {len(pending_scripts)} pending scripts")
            return pending_scripts
            
        except Exception as e:
            logger.error(f"Error discovering scripts: {e}")
            return []
    
    def _needs_audio_generation(self, script_file: Path) -> bool:
        """
        Check if an episode needs audio generation.
        
        Args:
            script_file: Path to the script file
            
        Returns:
            True if audio generation is needed
        """
        try:
            # Look for episode directory
            episode_dir = script_file.parent
            while episode_dir.name in ["Output", "Scripts", "Input"]:
                episode_dir = episode_dir.parent
            
            # Check if Audio directory exists and has content
            audio_dir = episode_dir / "Output" / "Audio"
            
            if not audio_dir.exists():
                return True  # No audio directory = needs generation
            
            # Check if there are any .wav files
            audio_files = list(audio_dir.glob("*.wav"))
            if not audio_files:
                return True  # No audio files = needs generation
            
            # Check if script is newer than audio files
            script_time = script_file.stat().st_mtime
            newest_audio_time = max(f.stat().st_mtime for f in audio_files)
            
            return script_time > newest_audio_time  # Script newer = needs regeneration
            
        except Exception as e:
            logger.debug(f"Error checking audio generation need for {script_file}: {e}")
            return True  # When in doubt, process it
    
    def _extract_episode_name(self, script_path: str) -> str:
        """Extract episode name from script path."""
        try:
            path_parts = Path(script_path).parts
            # Find the episode name (usually 2 levels up from script)
            for i, part in enumerate(path_parts):
                if part in ["Scripts", "Output", "Input"] and i > 0:
                    return path_parts[i-1]
            
            # Fallback to parent directory name
            return Path(script_path).parent.name
            
        except Exception:
            return Path(script_path).name
    
    def _display_single_script_results(self, report: ProcessingReport, processing_time: float) -> None:
        """Display results for single script processing."""
        print(f"\n📊 Processing Results:")
        print(f"• Total sections: {report.total_sections}")
        print(f"• Successful: {report.successful_sections}")
        print(f"• Failed: {report.failed_sections}")
        print(f"• Processing time: {processing_time:.2f} seconds")
        
        if report.generated_files:
            print(f"\n✅ Generated audio files:")
            for file_path in report.generated_files:
                print(f"  • {Path(file_path).name}")
        
        if report.errors:
            print(f"\n❌ Errors encountered:")
            for error in report.errors[:3]:  # Show first 3 errors
                print(f"  • {error}")
            if len(report.errors) > 3:
                print(f"  • ... and {len(report.errors) - 3} more errors")
        
        print(f"\n📁 Output directory: {report.output_directory}")
    
    def _display_batch_results(self, results: List[ProcessingReport], successful_count: int, total_count: int) -> None:
        """Display results for batch processing."""
        print(f"\n" + "=" * 60)
        print(f"🎯 BATCH PROCESSING COMPLETE")
        print(f"=" * 60)
        
        total_sections = sum(r.total_sections for r in results)
        total_successful = sum(r.successful_sections for r in results)
        total_failed = sum(r.failed_sections for r in results)
        
        print(f"📊 Overall Results:")
        print(f"• Scripts processed: {len(results)}/{total_count}")
        print(f"• Scripts successful: {successful_count}/{total_count}")
        print(f"• Total audio sections: {total_sections}")
        print(f"• Total successful generations: {total_successful}")
        print(f"• Total failed generations: {total_failed}")
        
        if total_successful > 0:
            success_rate = (total_successful / total_sections) * 100
            print(f"• Success rate: {success_rate:.1f}%")
        
        print(f"\n✅ Batch processing completed successfully!")
    
    def display_processing_progress(self, current: int, total: int, section: str) -> None:
        """
        Display processing progress.
        
        Args:
            current: Current section number
            total: Total sections to process
            section: Current section name
        """
        percent = (current / total) * 100
        bar_length = 40
        filled_length = int(bar_length * current // total)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        
        print(f"\r🔄 Progress: |{bar}| {percent:.1f}% ({current}/{total}) - {section}", end='', flush=True)
        
        if current == total:
            print()  # New line when complete


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="TTS Audio Generation System - Generate audio files from Gemini response scripts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single script
  python -m Code.Audio_Generation.cli --script "Content/Episode/debug_gemini_response.txt"
  
  # Process all scripts in content directory
  python -m Code.Audio_Generation.cli --batch --content-root "Content/"
  
  # Override voice and processing options
  python -m Code.Audio_Generation.cli --script "script.txt" --voice "Algenib" --concurrent 2
        """
    )
    
    # Main action group
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument(
        '--script', 
        type=str,
        help='Process a single script file'
    )
    action_group.add_argument(
        '--batch',
        action='store_true',
        help='Process all pending scripts in content directory'
    )
    
    # Configuration options
    parser.add_argument(
        '--content-root',
        type=str,
        default='Content',
        help='Root directory for content (default: Content)'
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file'
    )
    
    # TTS options
    parser.add_argument(
        '--voice',
        type=str,
        help='Override default voice (e.g., Algenib)'
    )
    parser.add_argument(
        '--concurrent',
        type=int,
        default=3,
        help='Number of concurrent audio generations (default: 3)'
    )
    parser.add_argument(
        '--retry',
        type=int,
        default=2,
        help='Number of retry attempts for failed generations (default: 2)'
    )
    
    # Output options
    parser.add_argument(
        '--auto-confirm',
        action='store_true',
        help='Auto-confirm batch processing without user prompt'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.debug else (logging.INFO if args.verbose else logging.WARNING)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Prepare options
    options = {
        'voice': args.voice,
        'max_concurrent': args.concurrent,
        'retry_attempts': args.retry,
        'auto_confirm': args.auto_confirm
    }
    
    # Remove None values
    options = {k: v for k, v in options.items() if v is not None}
    
    try:
        # Initialize CLI
        cli = AudioGenerationCLI(args.config)
        
        print("🎵 TTS Audio Generation System")
        print("=" * 40)
        
        success = False
        
        if args.script:
            # Process single script
            success = cli.run_single_script(args.script, options)
            
        elif args.batch:
            # Process batch
            results = cli.run_batch_processing(args.content_root, options)
            success = results['successful'] > 0
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main(), DiscoveryResult
from config import AudioGenerationConfig


def setup_logging(verbose: bool = False, log_file: Optional[str] = None) -> None:
    """Setup logging configuration for CLI."""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Create formatters
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)


def print_banner():
    """Print the application banner."""
    print("=" * 60)
    print("🎤 TTS Audio Generation System")
    print("   Powered by Gemini TTS API")
    print("=" * 60)


def print_discovery_results(results: DiscoveryResult) -> None:
    """Print discovery results in a formatted way."""
    print(f"\n📁 Discovery Results:")
    print(f"   • Total episodes found: {len(results.episodes)}")
    print(f"   • Script files found: {len(results.script_files)}")
    print(f"   • Episodes needing audio: {len(results.pending_episodes)}")
    print(f"   • Episodes with existing audio: {len(results.completed_episodes)}")
    
    if results.pending_episodes:
        print(f"\n📝 Episodes ready for processing:")
        for episode in results.pending_episodes[:10]:  # Show first 10
            episode_name = Path(episode.episode_path).name
            script_count = len(episode.script_files)
            print(f"   • {episode_name} ({script_count} script files)")
        
        if len(results.pending_episodes) > 10:
            print(f"   ... and {len(results.pending_episodes) - 10} more episodes")


def print_processing_results(report: ProcessingReport) -> None:
    """Print processing results in a formatted way."""
    print(f"\n🎯 Processing Results:")
    print(f"   • Total files processed: {report.total_files}")
    print(f"   • Successful: {report.successful_files}")
    print(f"   • Failed: {report.failed_files}")
    print(f"   • Success rate: {report.success_rate:.1f}%")
    print(f"   • Total time: {report.total_time:.2f} seconds")
    
    if report.successful_files > 0:
        print(f"\n✅ Generated audio files:")
        for result in report.file_results[:10]:  # Show first 10 successful
            if result.success:
                filename = Path(result.audio_file_path).name
                print(f"   • {filename} ({result.audio_duration:.1f}s)")
    
    if report.failed_files > 0:
        print(f"\n❌ Failed files:")
        for result in report.file_results:
            if not result.success:
                print(f"   • {result.section_id}: {result.error_message}")


def cmd_process_file(args) -> int:
    """Process a single script file."""
    try:
        print_banner()
        print(f"🔄 Processing single file: {args.file}")
        
        # Initialize processor
        processor = AudioBatchProcessor(args.config)
        
        # Process the file
        report = processor.process_script_file(args.file, force_regenerate=args.force)
        
        # Print results
        print_processing_results(report)
        
        return 0 if report.failed_files == 0 else 1
        
    except Exception as e:
        logging.error(f"Failed to process file {args.file}: {e}")
        return 1


def cmd_discover(args) -> int:
    """Discover episodes and script files."""
    try:
        print_banner()
        print(f"🔍 Discovering episodes in: {args.content_root or 'Content/'}")
        
        # Initialize discovery
        discovery = BatchDiscovery(content_root=args.content_root)
        
        # Discover episodes
        results = discovery.discover_episodes(
            require_gemini_format=not args.all_scripts,
            include_completed=args.include_completed
        )
        
        # Print results
        print_discovery_results(results)
        
        # Save results if requested
        if args.output:
            discovery.save_discovery_report(results, args.output)
            print(f"\n💾 Discovery report saved to: {args.output}")
        
        return 0
        
    except Exception as e:
        logging.error(f"Discovery failed: {e}")
        return 1


def cmd_process_batch(args) -> int:
    """Process multiple episodes in batch."""
    try:
        print_banner()
        print(f"🚀 Starting batch processing...")
        
        # Initialize components
        discovery = BatchDiscovery(content_root=args.content_root)
        processor = AudioBatchProcessor(args.config)
        
        # Discover episodes
        print("🔍 Discovering episodes...")
        results = discovery.discover_episodes(
            require_gemini_format=not args.all_scripts,
            include_completed=args.include_completed
        )
        
        print_discovery_results(results)
        
        if not results.pending_episodes:
            print("\n✨ No episodes need processing!")
            return 0
        
        # Process episodes
        episodes_to_process = results.pending_episodes
        if args.limit:
            episodes_to_process = episodes_to_process[:args.limit]
            print(f"\n🔢 Limited to {args.limit} episodes")
        
        print(f"\n🎬 Processing {len(episodes_to_process)} episodes...")
        
        overall_report = ProcessingReport(
            total_files=0,
            successful_files=0,
            failed_files=0,
            total_time=0.0,
            file_results=[],
            episode_reports={}
        )
        
        for i, episode in enumerate(episodes_to_process, 1):
            episode_name = Path(episode.episode_path).name
            print(f"\n[{i}/{len(episodes_to_process)}] Processing: {episode_name}")
            
            # Process each script file in the episode
            for script_file in episode.script_files:
                try:
                    report = processor.process_script_file(
                        script_file, 
                        force_regenerate=args.force
                    )
                    
                    # Aggregate results
                    overall_report.total_files += report.total_files
                    overall_report.successful_files += report.successful_files
                    overall_report.failed_files += report.failed_files
                    overall_report.total_time += report.total_time
                    overall_report.file_results.extend(report.file_results)
                    overall_report.episode_reports[script_file] = report
                    
                    print(f"   ✓ {Path(script_file).name}: {report.successful_files}/{report.total_files} sections")
                    
                except Exception as e:
                    logging.error(f"Failed to process {script_file}: {e}")
                    overall_report.failed_files += 1
        
        # Calculate success rate
        if overall_report.total_files > 0:
            overall_report.success_rate = (overall_report.successful_files / overall_report.total_files) * 100
        
        # Print final results
        print_processing_results(overall_report)
        
        # Save report if requested
        if args.output:
            processor.save_batch_report(overall_report, args.output)
            print(f"\n💾 Batch report saved to: {args.output}")
        
        return 0 if overall_report.failed_files == 0 else 1
        
    except Exception as e:
        logging.error(f"Batch processing failed: {e}")
        return 1


def cmd_validate(args) -> int:
    """Validate configuration and system setup."""
    try:
        print_banner()
        print("🔧 Validating system configuration...")
        
        # Load and validate config
        config = AudioGenerationConfig(args.config)
        validation = config.validate_configuration()
        
        print(f"\n📋 Configuration Status:")
        print(f"   • Config file: {config.config_path}")
        print(f"   • Valid: {'✓' if validation.is_valid else '✗'}")
        
        if validation.errors:
            print(f"\n❌ Errors:")
            for error in validation.errors:
                print(f"   • {error}")
        
        if validation.warnings:
            print(f"\n⚠️  Warnings:")
            for warning in validation.warnings:
                print(f"   • {warning}")
        
        # Test TTS connection
        try:
            from tts_engine import GeminiTTSEngine
            tts = GeminiTTSEngine(config)
            print(f"   • TTS connection: ✓")
        except Exception as e:
            print(f"   • TTS connection: ✗ ({e})")
            validation.is_valid = False
        
        # Check content root
        content_root = Path(config.file_settings.content_root)
        print(f"   • Content root: {'✓' if content_root.exists() else '✗'} ({content_root})")
        
        return 0 if validation.is_valid else 1
        
    except Exception as e:
        logging.error(f"Validation failed: {e}")
        return 1


def create_parser() -> argparse.ArgumentParser:
    """Create the command line argument parser."""
    parser = argparse.ArgumentParser(
        description="TTS Audio Generation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s discover                          # Discover all episodes
  %(prog)s process-file script.json          # Process single file
  %(prog)s batch                             # Process all pending episodes
  %(prog)s batch --limit 5                   # Process max 5 episodes
  %(prog)s validate                          # Check system setup
        """
    )
    
    # Global options
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='Path to configuration file'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--log-file',
        type=str,
        help='Path to log file'
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Discover command
    discover_parser = subparsers.add_parser('discover', help='Discover episodes and script files')
    discover_parser.add_argument(
        '--content-root',
        type=str,
        help='Content root directory (default: Content/)'
    )
    discover_parser.add_argument(
        '--all-scripts',
        action='store_true',
        help='Include all script files, not just Gemini format'
    )
    discover_parser.add_argument(
        '--include-completed',
        action='store_true',
        help='Include episodes that already have audio'
    )
    discover_parser.add_argument(
        '--output', '-o',
        type=str,
        help='Save discovery report to file'
    )
    
    # Process file command
    file_parser = subparsers.add_parser('process-file', help='Process a single script file')
    file_parser.add_argument(
        'file',
        type=str,
        help='Path to script file to process'
    )
    file_parser.add_argument(
        '--force',
        action='store_true',
        help='Force regeneration of existing audio files'
    )
    
    # Batch processing command
    batch_parser = subparsers.add_parser('batch', help='Process multiple episodes')
    batch_parser.add_argument(
        '--content-root',
        type=str,
        help='Content root directory (default: Content/)'
    )
    batch_parser.add_argument(
        '--limit',
        type=int,
        help='Maximum number of episodes to process'
    )
    batch_parser.add_argument(
        '--force',
        action='store_true',
        help='Force regeneration of existing audio files'
    )
    batch_parser.add_argument(
        '--all-scripts',
        action='store_true',
        help='Include all script files, not just Gemini format'
    )
    batch_parser.add_argument(
        '--include-completed',
        action='store_true',
        help='Include episodes that already have audio'
    )
    batch_parser.add_argument(
        '--output', '-o',
        type=str,
        help='Save batch report to file'
    )
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate configuration and setup')
    
    return parser


def main() -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose, args.log_file)
    
    # Handle no command
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to command handlers
    command_handlers = {
        'discover': cmd_discover,
        'process-file': cmd_process_file,
        'batch': cmd_process_batch,
        'validate': cmd_validate
    }
    
    handler = command_handlers.get(args.command)
    if not handler:
        logging.error(f"Unknown command: {args.command}")
        return 1
    
    return handler(args)


if __name__ == '__main__':
    sys.exit(main())
