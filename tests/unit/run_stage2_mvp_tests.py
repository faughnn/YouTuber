#!/usr/bin/env python3
"""
MVP Stage 2 Test Runner

This script executes the MVP Stage 2 tests with performance monitoring
and validates against the MVP targets:
- Execution time: < 3 minutes
- Memory usage: < 50MB
- All critical tests pass

Usage:
    python run_stage2_mvp_tests.py [--verbose] [--report]
    
Options:
    --verbose: Enable verbose output
    --report: Generate detailed performance report
"""

import sys
import os
import time
import psutil
import subprocess
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "Code"))

def get_memory_usage():
    """Get current memory usage in MB."""
    return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)

def run_mvp_tests(verbose=False, report=False):
    """
    Run MVP Stage 2 tests with performance monitoring.
    
    Returns:
        dict: Test results and performance metrics
    """
    print("🚀 Starting MVP Stage 2 Tests")
    print("=" * 50)
    
    # Performance tracking setup
    start_time = time.time()
    start_memory = get_memory_usage()
    peak_memory = start_memory
    
    # Test configuration
    test_file = Path(__file__).parent / "test_stage_2_mvp.py"
    pytest_args = [
        "python", "-m", "pytest",
        str(test_file),
        "-v" if verbose else "-q",
        "--tb=short",
        "-x",  # Stop on first failure for MVP speed
        "--durations=10",
        "--disable-warnings",
        "--no-header",
        "--cache-clear",  # Fresh run each time
    ]
    
    # Add performance markers
    pytest_args.extend([
        "-m", "not slow",  # Skip slow tests for MVP
        "--maxfail=1",     # Stop after first failure
    ])
    
    try:
        print(f"📋 Running tests: {test_file.name}")
        print(f"🕐 Start time: {time.strftime('%H:%M:%S')}")
        print(f"💾 Initial memory: {start_memory:.2f} MB")
        print()
        
        # Execute tests
        result = subprocess.run(
            pytest_args,
            capture_output=True,
            text=True,
            timeout=180,  # 3-minute timeout
            cwd=project_root
        )
        
        # Track peak memory during execution
        current_memory = get_memory_usage()
        if current_memory > peak_memory:
            peak_memory = current_memory
        
        # Calculate metrics
        end_time = time.time()
        execution_time = end_time - start_time
        memory_used = peak_memory - start_memory
        
        # Results
        results = {
            'success': result.returncode == 0,
            'execution_time': execution_time,
            'memory_used': memory_used,
            'peak_memory': peak_memory,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'mvp_targets_met': execution_time < 180 and memory_used < 50
        }
        
        # Output results
        print("\n" + "=" * 50)
        print("📊 MVP TEST RESULTS")
        print("=" * 50)
        
        # Test status
        if results['success']:
            print("✅ All MVP tests PASSED")
        else:
            print("❌ MVP tests FAILED")
            print(f"Exit code: {result.returncode}")
        
        # Performance metrics
        print(f"⏱️  Execution time: {execution_time:.2f}s (target: <180s)")
        print(f"💾 Memory used: {memory_used:.2f} MB (target: <50MB)")
        print(f"🎯 MVP targets met: {'✅ YES' if results['mvp_targets_met'] else '❌ NO'}")
        
        # Performance validation
        if execution_time >= 180:
            print("⚠️  WARNING: Execution time exceeded 3-minute MVP target!")
        if memory_used >= 50:
            print("⚠️  WARNING: Memory usage exceeded 50MB MVP target!")
        
        # Detailed output
        if verbose or not results['success']:
            print("\n📝 Test Output:")
            print("-" * 30)
            print(result.stdout)
            if result.stderr:
                print("\n🔍 Error Output:")
                print("-" * 30)
                print(result.stderr)
        
        # Report generation
        if report:
            generate_performance_report(results)
        
        return results
        
    except subprocess.TimeoutExpired:
        print("❌ Tests exceeded 3-minute timeout limit!")
        return {
            'success': False,
            'execution_time': 180,
            'memory_used': get_memory_usage() - start_memory,
            'mvp_targets_met': False,
            'error': 'Timeout exceeded'
        }
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return {
            'success': False,
            'execution_time': time.time() - start_time,
            'memory_used': get_memory_usage() - start_memory,
            'mvp_targets_met': False,
            'error': str(e)
        }

def generate_performance_report(results):
    """Generate a detailed performance report."""
    report_file = Path(__file__).parent / "mvp_stage2_performance_report.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("MVP Stage 2 Performance Report\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Execution Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Test Status: {'PASSED' if results['success'] else 'FAILED'}\n")
        f.write(f"Execution Time: {results['execution_time']:.2f}s\n")
        f.write(f"Memory Used: {results['memory_used']:.2f} MB\n")
        f.write(f"Peak Memory: {results['peak_memory']:.2f} MB\n")
        f.write(f"MVP Targets Met: {results['mvp_targets_met']}\n\n")
          # MVP Target Analysis
        f.write("MVP Target Analysis:\n")
        f.write("-" * 20 + "\n")
        f.write(f"Time Target (<180s): {'PASS' if results['execution_time'] < 180 else 'FAIL'}\n")
        f.write(f"Memory Target (<50MB): {'PASS' if results['memory_used'] < 50 else 'FAIL'}\n\n")
        
        # Test Output
        if 'stdout' in results:
            f.write("Test Output:\n")
            f.write("-" * 20 + "\n")
            f.write(results['stdout'])
            f.write("\n\n")
        
        if 'stderr' in results and results['stderr']:
            f.write("Error Output:\n")
            f.write("-" * 20 + "\n")
            f.write(results['stderr'])
    
    print(f"📄 Performance report saved to: {report_file}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run MVP Stage 2 tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--report", "-r", action="store_true", help="Generate performance report")
    parser.add_argument("--check-deps", action="store_true", help="Check test dependencies")
    
    args = parser.parse_args()
    
    if args.check_deps:
        print("🔍 Checking test dependencies...")
        try:
            import pytest
            import psutil
            print("✅ All dependencies available")
            return 0
        except ImportError as e:
            print(f"❌ Missing dependency: {e}")
            print("Install with: pip install pytest psutil")
            return 1
    
    # Run MVP tests
    results = run_mvp_tests(verbose=args.verbose, report=args.report)
    
    # Exit with appropriate code
    if results['success'] and results['mvp_targets_met']:
        print("\n🎉 MVP Stage 2 tests completed successfully!")
        return 0
    elif results['success']:
        print("\n⚠️  MVP Stage 2 tests passed but performance targets not met")
        return 1
    else:
        print("\n💥 MVP Stage 2 tests failed")
        return 2

if __name__ == "__main__":
    sys.exit(main())
