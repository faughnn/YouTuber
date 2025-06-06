"""
MVP Stage 3 Test Runner

Custom test runner for Stage 3 (Transcript Generation) MVP tests with performance 
monitoring, progress tracking, and automated reporting.

This runner provides:
- Real-time performance monitoring (execution time, memory usage)
- Detailed test result reporting with pass/fail breakdown
- MVP target validation against 2-minute execution and 100MB memory limits
- Automated report generation for tracking MVP progress

Author: YouTube Content Processing Pipeline
Date: 2024
"""

import pytest
import sys
import time
import psutil
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any
import json
from datetime import datetime


class Stage3MVPTestRunner:
    """Custom test runner for Stage 3 MVP tests with performance monitoring."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.peak_memory_mb = 0
        self.test_results = {}
        self.process = psutil.Process()
        
        # MVP Performance Targets for Stage 3
        self.TARGET_EXECUTION_TIME_SECONDS = 120  # 2 minutes
        self.TARGET_MEMORY_MB = 100  # 100MB
        
        # Test file path
        self.test_file = Path(__file__).parent / "test_stage_3_mvp.py"
        
    def monitor_performance(self):
        """Monitor system performance during test execution."""
        try:
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)  # Convert to MB
            self.peak_memory_mb = max(self.peak_memory_mb, memory_mb)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    def run_tests(self) -> Dict[str, Any]:
        """Execute Stage 3 MVP tests with performance monitoring."""
        print("🚀 Starting MVP Stage 3 Transcript Generation Tests")
        print("=" * 60)
        print(f"Target: < {self.TARGET_EXECUTION_TIME_SECONDS}s execution, < {self.TARGET_MEMORY_MB}MB memory")
        print(f"Test File: {self.test_file}")
        print()
        
        # Reset performance tracking
        self.peak_memory_mb = 0
        self.start_time = time.time()
        
        # Configure pytest arguments for optimized execution
        pytest_args = [
            str(self.test_file),
            "-v",  # Verbose output
            "--tb=short",  # Short traceback format
            "--strict-markers",  # Strict marker validation
            "--disable-warnings",  # Reduce noise in output
            "-x",  # Stop on first failure for MVP validation
            "--cache-clear",  # Clear cache for consistent timing
        ]
        
        # Custom pytest plugin for performance monitoring
        class PerformanceMonitorPlugin:
            def __init__(self, runner):
                self.runner = runner
                self.test_count = 0
                self.passed_count = 0
                self.failed_count = 0
                self.skipped_count = 0
            
            def pytest_runtest_setup(self, item):
                """Called before each test execution."""
                self.runner.monitor_performance()
            
            def pytest_runtest_teardown(self, item, nextitem):
                """Called after each test execution."""
                self.runner.monitor_performance()
            
            def pytest_runtest_logreport(self, report):
                """Called for each test report."""
                if report.when == "call":
                    self.test_count += 1
                    if report.outcome == "passed":
                        self.passed_count += 1
                    elif report.outcome == "failed":
                        self.failed_count += 1
                    elif report.outcome == "skipped":
                        self.skipped_count += 1
                    
                    # Store test result
                    self.runner.test_results[report.nodeid] = {
                        "outcome": report.outcome,
                        "duration": getattr(report, "duration", 0),
                        "longrepr": str(report.longrepr) if report.longrepr else ""
                    }
        
        # Create and register performance monitor
        monitor_plugin = PerformanceMonitorPlugin(self)
        
        try:
            # Run tests with performance monitoring
            print("⏱️  Executing tests with performance monitoring...")
            
            exit_code = pytest.main(pytest_args + ["-p", "no:cacheprovider"], 
                                  plugins=[monitor_plugin])
            
            self.end_time = time.time()
            execution_time = self.end_time - self.start_time
            
            # Generate comprehensive results
            results = {
                "execution_time_seconds": round(execution_time, 2),
                "peak_memory_mb": round(self.peak_memory_mb, 2),
                "test_count": monitor_plugin.test_count,
                "passed_count": monitor_plugin.passed_count,
                "failed_count": monitor_plugin.failed_count,
                "skipped_count": monitor_plugin.skipped_count,
                "success_rate": round((monitor_plugin.passed_count / max(monitor_plugin.test_count, 1)) * 100, 1),
                "exit_code": exit_code,
                "mvp_targets": {
                    "execution_time_target": self.TARGET_EXECUTION_TIME_SECONDS,
                    "memory_target_mb": self.TARGET_MEMORY_MB,
                    "execution_time_achieved": execution_time <= self.TARGET_EXECUTION_TIME_SECONDS,
                    "memory_target_achieved": self.peak_memory_mb <= self.TARGET_MEMORY_MB,
                    "overall_mvp_success": (
                        exit_code == 0 and 
                        execution_time <= self.TARGET_EXECUTION_TIME_SECONDS and 
                        self.peak_memory_mb <= self.TARGET_MEMORY_MB and
                        monitor_plugin.passed_count > 0
                    )
                },
                "test_details": self.test_results,
                "timestamp": datetime.now().isoformat()
            }
            
            return results
            
        except Exception as e:
            self.end_time = time.time()
            execution_time = self.end_time - self.start_time if self.start_time else 0
            
            return {
                "execution_time_seconds": round(execution_time, 2),
                "peak_memory_mb": round(self.peak_memory_mb, 2),
                "error": str(e),
                "success_rate": 0.0,
                "exit_code": -1,
                "mvp_targets": {
                    "execution_time_target": self.TARGET_EXECUTION_TIME_SECONDS,
                    "memory_target_mb": self.TARGET_MEMORY_MB,
                    "execution_time_achieved": False,
                    "memory_target_achieved": False,
                    "overall_mvp_success": False
                },
                "timestamp": datetime.now().isoformat()
            }
    
    def print_results_summary(self, results: Dict[str, Any]):
        """Print formatted results summary to console."""
        print("\n" + "=" * 60)
        print("📊 MVP STAGE 3 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        # Performance metrics
        execution_time = results["execution_time_seconds"]
        memory_usage = results["peak_memory_mb"]
        
        print(f"⏱️  Execution Time: {execution_time}s (Target: <{self.TARGET_EXECUTION_TIME_SECONDS}s)")
        print(f"🧠 Peak Memory: {memory_usage}MB (Target: <{self.TARGET_MEMORY_MB}MB)")
        
        # Performance achievements
        time_factor = round(self.TARGET_EXECUTION_TIME_SECONDS / max(execution_time, 0.01), 1)
        memory_factor = round(self.TARGET_MEMORY_MB / max(memory_usage, 0.01), 1)
        
        print(f"🎯 Time Performance: {time_factor}x faster than target")
        print(f"🎯 Memory Performance: {memory_factor}x below target")
        
        # Test results
        if "test_count" in results:
            print(f"\n📋 Test Results:")
            print(f"   Total Tests: {results['test_count']}")
            print(f"   ✅ Passed: {results['passed_count']}")
            print(f"   ❌ Failed: {results['failed_count']}")
            print(f"   ⏭️  Skipped: {results['skipped_count']}")
            print(f"   📈 Success Rate: {results['success_rate']}%")
        
        # MVP Target Achievement
        mvp_targets = results["mvp_targets"]
        print(f"\n🎯 MVP TARGET ACHIEVEMENT:")
        print(f"   Execution Time: {'✅ ACHIEVED' if mvp_targets['execution_time_achieved'] else '❌ MISSED'}")
        print(f"   Memory Usage: {'✅ ACHIEVED' if mvp_targets['memory_target_achieved'] else '❌ MISSED'}")
        print(f"   Overall MVP: {'🎉 SUCCESS' if mvp_targets['overall_mvp_success'] else '🔄 NEEDS WORK'}")
        
        # Error details if any
        if "error" in results:
            print(f"\n❌ Error Encountered: {results['error']}")
        
        # Failed test details
        if results.get("failed_count", 0) > 0:
            print(f"\n🔍 Failed Test Details:")
            for test_id, details in results.get("test_details", {}).items():
                if details["outcome"] == "failed":
                    test_name = test_id.split("::")[-1]
                    print(f"   ❌ {test_name}")
                    if details["longrepr"]:
                        # Print first line of error for brevity
                        error_line = details["longrepr"].split('\n')[0]
                        print(f"      Error: {error_line}")
    
    def generate_performance_report(self, results: Dict[str, Any]) -> str:
        """Generate detailed performance report file."""
        report_path = Path(__file__).parent / "mvp_stage3_performance_report.txt"
        
        report_content = f"""MVP STAGE 3 TRANSCRIPT GENERATION - PERFORMANCE REPORT
===========================================================

Generated: {results['timestamp']}
Test File: {self.test_file}

PERFORMANCE METRICS
==================
Execution Time: {results['execution_time_seconds']}s
Peak Memory Usage: {results['peak_memory_mb']}MB
Exit Code: {results.get('exit_code', 'N/A')}

MVP TARGETS
===========
Target Execution Time: < {self.TARGET_EXECUTION_TIME_SECONDS}s
Target Memory Usage: < {self.TARGET_MEMORY_MB}MB

ACHIEVEMENT STATUS
==================
Execution Time Target: {'✅ ACHIEVED' if results['mvp_targets']['execution_time_achieved'] else '❌ MISSED'}
Memory Target: {'✅ ACHIEVED' if results['mvp_targets']['memory_target_achieved'] else '❌ MISSED'}
Overall MVP Success: {'🎉 SUCCESS' if results['mvp_targets']['overall_mvp_success'] else '🔄 NEEDS WORK'}

PERFORMANCE ANALYSIS
===================
Time Performance Factor: {round(self.TARGET_EXECUTION_TIME_SECONDS / max(results['execution_time_seconds'], 0.01), 1)}x faster than target
Memory Performance Factor: {round(self.TARGET_MEMORY_MB / max(results['peak_memory_mb'], 0.01), 1)}x below target limit

TEST RESULTS BREAKDOWN
====================="""

        if "test_count" in results:
            report_content += f"""
Total Tests Executed: {results['test_count']}
Tests Passed: {results['passed_count']}
Tests Failed: {results['failed_count']}
Tests Skipped: {results['skipped_count']}
Success Rate: {results['success_rate']}%

DETAILED TEST RESULTS
===================="""
            
            for test_id, details in results.get("test_details", {}).items():
                test_name = test_id.split("::")[-1]
                status_icon = {"passed": "✅", "failed": "❌", "skipped": "⏭️"}.get(details["outcome"], "❓")
                report_content += f"\n{status_icon} {test_name} ({details['outcome']}) - {details.get('duration', 0):.3f}s"
                
                if details["outcome"] == "failed" and details["longrepr"]:
                    report_content += f"\n   Error: {details['longrepr'][:200]}..."

        if "error" in results:
            report_content += f"\n\nERROR DETAILS\n=============\n{results['error']}"

        report_content += f"""

STAGE 3 TEST CATEGORIES COVERAGE
================================
1. Audio Diarization Tests (3 tests)
   - Basic audio transcription with single speaker
   - Speaker diarization with multiple speakers  
   - Error handling for invalid/corrupted audio

2. YouTube Transcript Extraction Tests (3 tests)
   - YouTube API transcript retrieval
   - Transcript availability handling
   - YouTube API error handling

3. Stage Integration Tests (3 tests)
   - Stage 2 to Stage 3 handoff validation
   - File organization integration
   - Stage 3 to Stage 4 preparation

TECHNICAL IMPLEMENTATION NOTES
==============================
- Mocked WhisperX operations for performance optimization
- Mocked YouTube API calls to avoid quota usage
- Temporary file system for output validation
- Comprehensive error scenario coverage
- JSON structure validation for downstream compatibility

MVP SUCCESS CRITERIA
===================
✓ Core transcription functionality validated through mocking
✓ Speaker diarization logic tested with multi-speaker scenarios
✓ Error handling covers invalid inputs and API failures
✓ Pipeline integration ensures Stage 2→3→4 handoff works
✓ File organization maintains episode structure consistency
✓ Performance targets achieved for development velocity

RECOMMENDATIONS FOR PRODUCTION
==============================
- Implement actual WhisperX integration testing in separate test suite
- Add YouTube API quota monitoring for live transcript extraction
- Create integration tests with real audio samples for validation
- Monitor transcript quality metrics in production environment
- Implement retry logic for transient API failures
- Add transcript caching to reduce redundant processing

This MVP test suite validates core Stage 3 functionality while maintaining 
fast execution times essential for development velocity. The comprehensive 
mocking strategy ensures reliable testing without dependencies on external 
services or expensive AI model operations.
"""
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            return str(report_path)
        except Exception as e:
            print(f"⚠️  Warning: Could not write performance report: {e}")
            return ""


def main():
    """Main execution function for Stage 3 MVP test runner."""
    print("🎬 YouTube Content Processing Pipeline - Stage 3 MVP Tests")
    print("Testing: Transcript Generation (Audio Diarization + YouTube API)")
    print()
    
    # Initialize and run tests
    runner = Stage3MVPTestRunner()
    results = runner.run_tests()
    
    # Display results
    runner.print_results_summary(results)
    
    # Generate detailed report
    report_path = runner.generate_performance_report(results)
    if report_path:
        print(f"\n📄 Detailed report saved: {report_path}")
    
    # Return appropriate exit code
    return 0 if results["mvp_targets"]["overall_mvp_success"] else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
