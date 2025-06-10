#!/usr/bin/env python3
"""
Comprehensive YouTube Download Method Testing Script

This script systematically tests various download methods, format combinations,
and strategies to identify what works with current YouTube restrictions.

Usage:
    python test_youtube_download_methods.py "https://www.youtube.com/watch?v=VIDEO_ID"
    python test_youtube_download_methods.py --batch  # Test with multiple videos
"""

import subprocess
import json
import time
import os
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import argparse

class YouTubeDownloadTester:
    def __init__(self, test_dir: str = "download_tests"):
        self.test_dir = test_dir
        self.results = []
        self.setup_test_directory()
        
    def setup_test_directory(self):
        """Create test directory for downloads."""
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)
            
    def log_result(self, test_name: str, url: str, success: bool, 
                   error_msg: str = "", details: Dict = None):
        """Log test result."""
        result = {
            'timestamp': datetime.now().isoformat(),
            'test_name': test_name,
            'url': url,
            'success': success,
            'error_msg': error_msg,
            'details': details or {}
        }
        self.results.append(result)
        
        # Print result immediately
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{status}: {test_name}")
        if error_msg:
            print(f"   Error: {error_msg}")
        if details:
            print(f"   Details: {details}")
        print()
        
    def run_yt_dlp_command(self, args: List[str], timeout: int = 60) -> Tuple[bool, str, str]:
        """Run yt-dlp command and return success status, stdout, stderr."""
        try:
            result = subprocess.run(
                ['yt-dlp'] + args,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.test_dir
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
            
    def test_video_availability(self, url: str) -> bool:
        """Test if video is available at all."""
        print(f"🔍 Testing video availability: {url}")
        
        success, stdout, stderr = self.run_yt_dlp_command([
            '--get-title', '--no-warnings', url
        ])
        
        self.log_result(
            "Video Availability Check",
            url,
            success,
            stderr if not success else "",
            {'title': stdout.strip() if success else None}
        )
        
        return success
        
    def test_format_listing(self, url: str) -> Optional[List[Dict]]:
        """Get available formats for the video."""
        print(f"📋 Getting available formats: {url}")
        
        success, stdout, stderr = self.run_yt_dlp_command([
            '--list-formats', '--dump-json', url
        ])
        
        formats = None
        if success:
            try:
                # Parse JSON output to get format information
                lines = stdout.strip().split('\n')
                for line in lines:
                    if line.startswith('{'):
                        data = json.loads(line)
                        formats = data.get('formats', [])
                        break
            except json.JSONDecodeError:
                pass
                
        self.log_result(
            "Format Listing",
            url,
            success,
            stderr if not success else "",
            {'format_count': len(formats) if formats else 0}
        )
        
        return formats
        
    def test_format_combinations(self, url: str) -> None:
        """Test various format selection strategies."""
        print(f"🎯 Testing format combinations: {url}")
        
        # Format strategies to test
        format_strategies = [
            # Generic strategies
            ("best", "Best available quality"),
            ("worst", "Worst available quality"),
            ("best[height<=1080]", "Best up to 1080p"),
            ("best[height<=720]", "Best up to 720p"),
            ("best[height<=480]", "Best up to 480p"),
            
            # Video + Audio combinations
            ("bestvideo+bestaudio", "Best video + best audio"),
            ("bestvideo[height<=1080]+bestaudio", "Best 1080p video + audio"),
            ("bestvideo[height<=720]+bestaudio", "Best 720p video + audio"),
            
            # Codec-specific
            ("best[ext=mp4]", "Best MP4 format"),
            ("best[vcodec^=avc]", "Best H.264 video"),
            ("best[acodec^=mp4a]", "Best AAC audio"),
            
            # Specific format IDs (based on common YouTube formats)
            ("18", "360p MP4 (format 18)"),
            ("22", "720p MP4 (format 22)"),
            ("136+140", "720p video + 128k audio"),
            ("137+140", "1080p video + 128k audio"),
            ("232+233", "720p HLS + audio"),
            ("270+233", "1080p HLS + audio"),
            
            # Protocol-specific
            ("best[protocol^=https]", "HTTPS protocols only"),
            ("best[protocol^=m3u8]", "HLS streams only"),
            
            # Fallback strategies
            ("best/worst", "Best with worst fallback"),
            ("bestvideo+bestaudio/best", "Combined with single file fallback"),
        ]
        
        for format_selector, description in format_strategies:
            self._test_single_format(url, format_selector, description)
            
    def _test_single_format(self, url: str, format_selector: str, description: str):
        """Test a single format selector."""
        test_name = f"Format: {format_selector}"
        output_template = f"test_{format_selector.replace('+', '_').replace('/', '_')}_{int(time.time())}"
        
        success, stdout, stderr = self.run_yt_dlp_command([
            '-f', format_selector,
            '-o', f"{output_template}.%(ext)s",
            '--no-warnings',
            '--test',  # Don't actually download
            url
        ])
        
        self.log_result(
            test_name,
            url,
            success,
            stderr if not success else "",
            {'description': description, 'format': format_selector}
        )
        
    def test_extraction_methods(self, url: str) -> None:
        """Test different extraction methods and clients."""
        print(f"🔧 Testing extraction methods: {url}")
        
        extraction_methods = [
            # Default method
            ([], "Default extraction"),
            
            # Different clients
            (['--extractor-args', 'youtube:player_client=web'], "Web client"),
            (['--extractor-args', 'youtube:player_client=android'], "Android client"),
            (['--extractor-args', 'youtube:player_client=ios'], "iOS client"),
            (['--extractor-args', 'youtube:player_client=mweb'], "Mobile web client"),
            
            # Skip certain features
            (['--extractor-args', 'youtube:skip=dash'], "Skip DASH"),
            (['--extractor-args', 'youtube:skip=hls'], "Skip HLS"),
            
            # Different approaches
            (['--youtube-skip-dash-manifest'], "Skip DASH manifest"),
            (['--no-check-certificates'], "Skip certificate check"),
            (['--socket-timeout', '30'], "30s socket timeout"),
            
            # User agent variations
            (['--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'], "Desktop user agent"),
            (['--user-agent', 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'], "iPhone user agent"),
        ]
        
        for extra_args, description in extraction_methods:
            self._test_extraction_method(url, extra_args, description)
            
    def _test_extraction_method(self, url: str, extra_args: List[str], description: str):
        """Test a single extraction method."""
        test_name = f"Extraction: {description}"
        
        args = extra_args + [
            '--get-title',
            '--no-warnings',
            url
        ]
        
        success, stdout, stderr = self.run_yt_dlp_command(args)
        
        self.log_result(
            test_name,
            url,
            success,
            stderr if not success else "",
            {'method': description, 'title': stdout.strip() if success else None}
        )
        
    def test_download_strategies(self, url: str) -> None:
        """Test actual download with different strategies."""
        print(f"📥 Testing download strategies: {url}")
        
        download_strategies = [
            # Basic downloads
            (['--format', 'best[height<=480]', '-o', 'strategy_basic_%(title)s.%(ext)s'], 
             "Basic 480p download"),
            
            # With specific options
            (['--format', '232+233', '--merge-output-format', 'mp4', 
              '-o', 'strategy_hls_%(title)s.%(ext)s'], 
             "HLS merge download"),
             
            # Audio only
            (['-x', '--audio-format', 'mp3', 
              '-o', 'strategy_audio_%(title)s.%(ext)s'], 
             "Audio extraction"),
             
            # With retries
            (['--format', 'best[height<=720]', '--retries', '3', 
              '--fragment-retries', '3', '-o', 'strategy_retry_%(title)s.%(ext)s'], 
             "Download with retries"),
        ]
        
        for args, description in download_strategies:
            self._test_download_strategy(url, args, description)
            
    def _test_download_strategy(self, url: str, args: List[str], description: str):
        """Test a single download strategy."""
        test_name = f"Download: {description}"
        
        # Add test flag to avoid actual large downloads
        test_args = args + ['--test', url]
        
        success, stdout, stderr = self.run_yt_dlp_command(test_args, timeout=120)
        
        self.log_result(
            test_name,
            url,
            success,
            stderr if not success else "",
            {'strategy': description}
        )
        
    def run_comprehensive_test(self, url: str) -> None:
        """Run all tests for a single URL."""
        print(f"🚀 Starting comprehensive test for: {url}")
        print("=" * 80)
        
        # Test 1: Basic availability
        if not self.test_video_availability(url):
            print("❌ Video unavailable - skipping further tests")
            return
            
        # Test 2: Get available formats
        formats = self.test_format_listing(url)
        
        # Test 3: Try different format combinations
        self.test_format_combinations(url)
        
        # Test 4: Try different extraction methods
        self.test_extraction_methods(url)
        
        # Test 5: Try actual downloads (with --test flag)
        self.test_download_strategies(url)
        
        print("=" * 80)
        print(f"✅ Comprehensive test completed for: {url}")
        
    def generate_report(self) -> str:
        """Generate a detailed test report."""
        report = []
        report.append("# YouTube Download Method Test Report")
        report.append(f"**Generated**: {datetime.now().isoformat()}")
        report.append(f"**Total Tests**: {len(self.results)}")
        report.append("")
        
        # Success/failure summary
        successful = sum(1 for r in self.results if r['success'])
        failed = len(self.results) - successful
        success_rate = (successful / len(self.results)) * 100 if self.results else 0
        
        report.append("## Summary")
        report.append(f"- **Successful Tests**: {successful}")
        report.append(f"- **Failed Tests**: {failed}")
        report.append(f"- **Success Rate**: {success_rate:.1f}%")
        report.append("")
        
        # Group results by test type
        test_types = {}
        for result in self.results:
            test_type = result['test_name'].split(':')[0]
            if test_type not in test_types:
                test_types[test_type] = {'success': 0, 'failed': 0, 'results': []}
            
            if result['success']:
                test_types[test_type]['success'] += 1
            else:
                test_types[test_type]['failed'] += 1
            test_types[test_type]['results'].append(result)
            
        # Report by test type
        for test_type, data in test_types.items():
            report.append(f"## {test_type}")
            total = data['success'] + data['failed']
            success_rate = (data['success'] / total) * 100 if total > 0 else 0
            report.append(f"**Success Rate**: {success_rate:.1f}% ({data['success']}/{total})")
            report.append("")
            
            # Show successful methods
            successful_results = [r for r in data['results'] if r['success']]
            if successful_results:
                report.append("### ✅ Working Methods")
                for result in successful_results:
                    details = result.get('details', {})
                    desc = details.get('description', details.get('method', details.get('strategy', '')))
                    report.append(f"- {result['test_name']}: {desc}")
                report.append("")
                
            # Show failed methods with errors
            failed_results = [r for r in data['results'] if not r['success']]
            if failed_results:
                report.append("### ❌ Failed Methods")
                for result in failed_results:
                    details = result.get('details', {})
                    desc = details.get('description', details.get('method', details.get('strategy', '')))
                    error = result['error_msg'][:100] + "..." if len(result['error_msg']) > 100 else result['error_msg']
                    report.append(f"- {result['test_name']}: {desc}")
                    if error:
                        report.append(f"  - Error: {error}")
                report.append("")
                
        # Raw results
        report.append("## Detailed Results")
        report.append("```json")
        report.append(json.dumps(self.results, indent=2))
        report.append("```")
        
        return "\n".join(report)
        
    def save_report(self, filename: str = None) -> str:
        """Save test report to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"youtube_download_test_report_{timestamp}.md"
            
        report_content = self.generate_report()
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_content)
            
        print(f"📄 Report saved to: {filename}")
        return filename

def main():
    parser = argparse.ArgumentParser(description="Test YouTube download methods comprehensively")
    parser.add_argument('url', nargs='?', help='YouTube URL to test')
    parser.add_argument('--batch', action='store_true', help='Test with multiple predefined URLs')
    parser.add_argument('--report-only', action='store_true', help='Generate report from existing results')
    parser.add_argument('--output', help='Output report filename')
    
    args = parser.parse_args()
    
    tester = YouTubeDownloadTester()
    
    if args.report_only:
        if os.path.exists('download_test_results.json'):
            with open('download_test_results.json', 'r') as f:
                tester.results = json.load(f)
            tester.save_report(args.output)
        else:
            print("No existing results found. Run tests first.")
        return
        
    if args.batch:
        # Test with multiple URLs
        test_urls = [
            "https://www.youtube.com/watch?v=C81bFx8CSA8",  # Known working video
            "https://www.youtube.com/watch?v=TJb4SqJRCrM",  # Known failing video
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll (short video)
            "https://www.youtube.com/watch?v=9bZkp7q19f0",  # Popular music video
        ]
        
        for url in test_urls:
            try:
                tester.run_comprehensive_test(url)
            except KeyboardInterrupt:
                print("\n🛑 Test interrupted by user")
                break
            except Exception as e:
                print(f"❌ Error testing {url}: {e}")
                
    elif args.url:
        tester.run_comprehensive_test(args.url)
    else:
        parser.print_help()
        return
        
    # Save results
    with open('download_test_results.json', 'w') as f:
        json.dump(tester.results, f, indent=2)
        
    # Generate and save report
    report_file = tester.save_report(args.output)
    
    print("\n🎯 Test Summary:")
    successful = sum(1 for r in tester.results if r['success'])
    total = len(tester.results)
    print(f"   Successful: {successful}/{total} ({(successful/total)*100:.1f}%)")
    print(f"   Report: {report_file}")

if __name__ == "__main__":
    main()
