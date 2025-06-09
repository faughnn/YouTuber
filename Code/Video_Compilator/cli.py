"""
Command Line Interface for Video Compilator

Simple CLI to compile episodes using the proven working method.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from Video_Compilator import SimpleCompiler


def setup_logging(verbose: bool = False):
    """Set up logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    format_string = '%(asctime)s - %(levelname)s - %(message)s' if verbose else '%(levelname)s: %(message)s'
    
    logging.basicConfig(
        level=level,
        format=format_string,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def validate_episode_directory(episode_path: Path) -> bool:
    """Validate that the episode directory exists and has expected structure"""
    if not episode_path.exists():
        print(f"✗ Episode directory not found: {episode_path}")
        return False
    
    if not episode_path.is_dir():
        print(f"✗ Path is not a directory: {episode_path}")
        return False
    
    # Check for common episode directory contents
    expected_subdirs = ['Scripts', 'Audio', 'Video', 'Output']
    found_subdirs = []
    
    for subdir in expected_subdirs:
        if (episode_path / subdir).exists():
            found_subdirs.append(subdir)
    
    if not found_subdirs:
        print(f"⚠ No standard subdirectories found in {episode_path}")
        print(f"  Expected one of: {', '.join(expected_subdirs)}")
        print(f"  Will attempt file discovery...")
    else:
        print(f"✓ Found subdirectories: {', '.join(found_subdirs)}")
    
    return True


def compile_episode(args):
    """Compile a single episode"""
    episode_path = Path(args.episode_path).resolve()
    
    # Validate episode directory
    if not validate_episode_directory(episode_path):
        return False
    
    # Initialize compiler
    compiler = SimpleCompiler(
        keep_temp_files=args.keep_temp,
        validate_segments=args.validate
    )
    
    print(f"Starting compilation for: {episode_path.name}")
    print(f"Keep temp files: {args.keep_temp}")
    print(f"Validate segments: {args.validate}")
    print("-" * 50)
    
    # Compile the episode
    result = compiler.compile_episode(episode_path, args.output)
    
    print("-" * 50)
    
    if result.success:
        print(f"✓ Compilation successful!")
        print(f"  Output: {result.output_path}")
        print(f"  Segments processed: {result.segments_processed}")
        print(f"  Audio segments converted: {result.audio_segments_converted}")
        
        if result.duration:
            print(f"  Duration: {result.duration:.2f} seconds ({result.duration/60:.1f} minutes)")
        
        if result.file_size:
            size_mb = result.file_size / (1024 * 1024)
            print(f"  File size: {size_mb:.1f} MB")
        
        return True
    else:
        print(f"✗ Compilation failed!")
        print(f"  Error: {result.error}")
        if result.segments_processed > 0:
            print(f"  Segments processed before failure: {result.segments_processed}")
        return False


def list_episodes(args):
    """List available episodes"""
    content_path = Path(args.content_dir).resolve()
    
    if not content_path.exists():
        print(f"✗ Content directory not found: {content_path}")
        return False
    
    print(f"Scanning for episodes in: {content_path}")
    print("-" * 50)
    
    episodes_found = 0
    
    for show_dir in content_path.iterdir():
        if show_dir.is_dir():
            print(f"\n📺 {show_dir.name}")
            
            show_episodes = 0
            for episode_dir in show_dir.iterdir():
                if episode_dir.is_dir():
                    # Check if it looks like an episode
                    has_audio = (episode_dir / 'Audio').exists() or (episode_dir / 'Output' / 'Audio').exists()
                    has_video = (episode_dir / 'Video').exists() or (episode_dir / 'Output' / 'Video').exists()
                    has_script = (episode_dir / 'Scripts').exists()
                    
                    status_indicators = []
                    if has_script:
                        status_indicators.append("📄")
                    if has_audio:
                        status_indicators.append("🔊")
                    if has_video:
                        status_indicators.append("🎬")
                    
                    status = "".join(status_indicators) if status_indicators else "❓"
                    print(f"  {status} {episode_dir.name}")
                    show_episodes += 1
                    episodes_found += 1
            
            if show_episodes == 0:
                print(f"  (No episodes found)")
    
    print("-" * 50)
    print(f"Total episodes found: {episodes_found}")
    print("\nLegend: 📄 = Script, 🔊 = Audio, 🎬 = Video, ❓ = Unknown structure")
    
    return True


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Video Compilator - Compile podcast episodes using the proven working method",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compile a specific episode
  python cli.py compile "C:/path/to/episode/directory"
  
  # Compile with custom output filename
  python cli.py compile "C:/path/to/episode" --output "my_episode.mp4"
  
  # List available episodes
  python cli.py list --content-dir "C:/Users/nfaug/OneDrive - LIR/Desktop/YouTuber/Content"
  
  # Compile with verbose logging and keep temp files
  python cli.py compile "C:/path/to/episode" --verbose --keep-temp
        """
    )
    
    # Global options
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose logging')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Compile command
    compile_parser = subparsers.add_parser('compile', help='Compile an episode')
    compile_parser.add_argument('episode_path', 
                               help='Path to the episode directory')
    compile_parser.add_argument('--output', '-o', 
                               help='Output filename (default: auto-generated)')
    compile_parser.add_argument('--keep-temp', action='store_true',
                               help='Keep temporary files for debugging')
    compile_parser.add_argument('--no-validate', dest='validate', action='store_false',
                               help='Skip segment validation (faster but less safe)')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List available episodes')
    list_parser.add_argument('--content-dir', 
                            default='C:/Users/nfaug/OneDrive - LIR/Desktop/YouTuber/Content',
                            help='Path to content directory (default: %(default)s)')
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return False
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Execute command
    try:
        if args.command == 'compile':
            return compile_episode(args)
        elif args.command == 'list':
            return list_episodes(args)
        else:
            print(f"Unknown command: {args.command}")
            return False
    except KeyboardInterrupt:
        print("\n✗ Operation cancelled by user")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
