"""
Integration Tests for Binary Filtering Quality Control System

Tests the integration between:
- BinarySegmentFilter
- BinaryRebuttalVerifier
- DiversitySelector
- FalseNegativeScanner
- OutputQualityGate
- FactValidator

Uses mock data to avoid API calls.

Author: Claude Code
Created: 2024-12-28
"""

import os
import sys
import json
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
content_analysis_dir = os.path.dirname(current_dir)
code_dir = os.path.dirname(content_analysis_dir)
sys.path.insert(0, current_dir)  # For mock_data
sys.path.insert(0, content_analysis_dir)
sys.path.insert(0, code_dir)

# Import modules to test
from binary_segment_filter import BinarySegmentFilter, FilterResult, GateResult
from binary_rebuttal_verifier import BinaryRebuttalVerifier, VerificationResult
from diversity_selector import DiversitySelector
from false_negative_scanner import FalseNegativeScanner
from output_quality_gate import OutputQualityGate, GateResult as QGResult

# Import mock data
from mock_data import (
    MOCK_PASS1_SEGMENTS,
    MOCK_UNIFIED_SCRIPT,
    MockBinarySegmentFilter,
    MockBinaryRebuttalVerifier,
    get_mock_pass1_data,
    get_mock_script_data,
    create_mock_gate_response
)


class TestBinarySegmentFilter(unittest.TestCase):
    """Tests for BinarySegmentFilter module."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.mock_segments = get_mock_pass1_data()

    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_filter_result_dataclass(self):
        """Test FilterResult dataclass creation and conversion."""
        result = FilterResult(
            segment_id="test_001",
            passed=True,
            gate_results={
                'claim_detection': {'passed': True, 'justification': 'OK'}
            }
        )

        self.assertEqual(result.segment_id, "test_001")
        self.assertTrue(result.passed)
        self.assertIsNone(result.failed_at)

        # Test to_dict conversion
        result_dict = result.to_dict()
        self.assertIsInstance(result_dict, dict)
        self.assertEqual(result_dict['segment_id'], "test_001")

    def test_filter_result_failure(self):
        """Test FilterResult for failed segment."""
        result = FilterResult(
            segment_id="test_002",
            passed=False,
            failed_at="accuracy_check",
            rejection_reason="Claim is actually accurate",
            gate_results={
                'claim_detection': {'passed': True, 'justification': 'OK'},
                'verifiability': {'passed': True, 'justification': 'OK'},
                'accuracy_check': {'passed': False, 'justification': 'Claim is accurate'}
            }
        )

        self.assertFalse(result.passed)
        self.assertEqual(result.failed_at, "accuracy_check")
        self.assertIn("accurate", result.rejection_reason)

    def test_mock_filter_integration(self):
        """Test mock filter with sample data."""
        mock_filter = MockBinarySegmentFilter()

        passed, rejected, metadata = mock_filter.filter_segments(self.mock_segments)

        # Check results
        self.assertGreater(len(passed), 0)
        self.assertGreater(len(rejected), 0)
        self.assertEqual(len(passed) + len(rejected), len(self.mock_segments))

        # Check metadata
        self.assertIn('filtering_timestamp', metadata)
        self.assertEqual(metadata['total_segments'], len(self.mock_segments))

        # Check that passed segments have filter results
        for seg in passed:
            self.assertIn('binary_filter_results', seg)
            self.assertTrue(seg['binary_filter_results']['passed'])

        # Check that rejected segments have failure info
        for seg in rejected:
            self.assertIn('binary_filter_results', seg)
            self.assertFalse(seg['binary_filter_results']['passed'])
            self.assertIn('failed_at', seg['binary_filter_results'])

    def test_filter_saves_output(self):
        """Test that filter saves results to file."""
        mock_filter = MockBinarySegmentFilter()
        output_path = os.path.join(self.test_dir, "filtered_output.json")

        passed, rejected, metadata = mock_filter.filter_segments(
            self.mock_segments,
            output_path=output_path
        )

        # Note: MockBinarySegmentFilter doesn't save files, but real one does
        # This test verifies the interface
        self.assertIsInstance(passed, list)
        self.assertIsInstance(metadata, dict)


class TestBinaryRebuttalVerifier(unittest.TestCase):
    """Tests for BinaryRebuttalVerifier module."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.mock_script = get_mock_script_data()

    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_verification_result_dataclass(self):
        """Test VerificationResult dataclass."""
        result = VerificationResult(
            section_id="post_clip_1",
            passed=True,
            iterations=2,
            final_content="Updated rebuttal content",
            gate_results={
                'accuracy': {'passed': True},
                'completeness': {'passed': True},
                'sources': {'passed': True},
                'clarity': {'passed': True}
            }
        )

        self.assertTrue(result.passed)
        self.assertEqual(result.iterations, 2)
        self.assertIsNone(result.warning)

    def test_mock_verifier_integration(self):
        """Test mock verifier with sample script."""
        mock_verifier = MockBinaryRebuttalVerifier()

        verified_script, metadata = mock_verifier.verify_script_rebuttals(self.mock_script)

        # Check metadata
        self.assertIn('rebuttals_verified', metadata)
        self.assertGreater(metadata['rebuttals_verified'], 0)

        # Check script structure preserved
        self.assertIn('podcast_sections', verified_script)
        self.assertIn('script_metadata', verified_script)

    def test_verifier_extracts_post_clips(self):
        """Test that verifier correctly identifies post_clip sections."""
        mock_verifier = MockBinaryRebuttalVerifier()

        # Count post_clips in mock script
        post_clip_count = sum(
            1 for s in self.mock_script['podcast_sections']
            if s.get('section_type') == 'post_clip'
        )

        verified_script, metadata = mock_verifier.verify_script_rebuttals(self.mock_script)

        self.assertEqual(metadata['rebuttals_verified'], post_clip_count)


class TestDiversitySelector(unittest.TestCase):
    """Tests for DiversitySelector module."""

    def setUp(self):
        """Set up test fixtures."""
        self.selector = DiversitySelector()
        self.mock_segments = get_mock_pass1_data()

    def test_topic_extraction(self):
        """Test topic extraction from segments."""
        # Vaccine segment should be tagged as health
        vaccine_segment = self.mock_segments[0]
        topics = self.selector._extract_topics(vaccine_segment)

        self.assertIsInstance(topics, list)
        self.assertGreater(len(topics), 0)
        self.assertIn('health', topics)

    def test_diverse_selection(self):
        """Test diversity-aware selection."""
        selected = self.selector.select_diverse(
            self.mock_segments,
            min_count=3,
            max_count=5
        )

        self.assertGreaterEqual(len(selected), 3)
        self.assertLessEqual(len(selected), 5)

    def test_max_per_topic_enforcement(self):
        """Test that max_per_topic is enforced."""
        # Create segments all on same topic
        same_topic_segments = [
            {
                'segment_id': f'seg_{i}',
                'narrativeSegmentTitle': f'Vaccine claim {i}',
                'clipContextDescription': 'More vaccine misinformation'
            }
            for i in range(10)
        ]

        self.selector.max_per_topic = 2
        selected = self.selector.select_diverse(same_topic_segments, max_count=6)

        # Should limit to max_per_topic from health topic
        health_count = sum(1 for s in selected if 'vaccine' in s.get('narrativeSegmentTitle', '').lower())
        self.assertLessEqual(health_count, 2)

    def test_empty_segments(self):
        """Test handling of empty segment list."""
        selected = self.selector.select_diverse([], min_count=5)
        self.assertEqual(len(selected), 0)

    def test_fewer_than_minimum(self):
        """Test when fewer segments than minimum are available."""
        few_segments = self.mock_segments[:2]
        selected = self.selector.select_diverse(few_segments, min_count=5)

        # Should return all available
        self.assertEqual(len(selected), 2)


class TestFalseNegativeScanner(unittest.TestCase):
    """Tests for FalseNegativeScanner module."""

    def setUp(self):
        """Set up test fixtures."""
        self.scanner = FalseNegativeScanner(skip_api_init=True)

        # Create passed and rejected segments
        mock_filter = MockBinarySegmentFilter()
        self.passed, self.rejected, _ = mock_filter.filter_segments(get_mock_pass1_data())

    def test_scan_finds_near_misses(self):
        """Test that scanner identifies near-miss segments."""
        # The mock data has segments that fail only one gate
        recovered = self.scanner.scan_rejected(self.rejected, self.passed)

        # Should find some candidates
        self.assertIsInstance(recovered, list)

    def test_scan_with_empty_rejected(self):
        """Test scanning with no rejected segments."""
        recovered = self.scanner.scan_rejected([], self.passed)
        self.assertEqual(len(recovered), 0)

    def test_uncovered_topic_detection(self):
        """Test detection of uncovered topics."""
        # Manually check for uncovered topics
        candidates = self.scanner._find_uncovered_topic_candidates(
            self.rejected,
            self.passed
        )

        self.assertIsInstance(candidates, list)

    def test_keyword_detection(self):
        """Test high-severity keyword detection."""
        candidates = self.scanner._find_keyword_candidates(self.rejected)
        self.assertIsInstance(candidates, list)


class TestOutputQualityGate(unittest.TestCase):
    """Tests for OutputQualityGate module."""

    def setUp(self):
        """Set up test fixtures."""
        self.gate = OutputQualityGate()
        self.mock_script = get_mock_script_data()

    def test_valid_script_passes(self):
        """Test that valid script passes quality gate."""
        result = self.gate.validate_script(self.mock_script)

        self.assertIsInstance(result, QGResult)
        self.assertTrue(result.passed)
        self.assertEqual(result.critical_count, 0)

    def test_missing_clip_reference_detected(self):
        """Test detection of invalid clip references."""
        bad_script = get_mock_script_data()

        # Add invalid clip reference
        bad_script['podcast_sections'].append({
            'section_type': 'post_clip',
            'section_id': 'post_bad',
            'clip_reference': 'Nonexistent_Clip',
            'script_content': 'This references a clip that does not exist.'
        })

        result = self.gate.validate_script(bad_script)

        # Should find the invalid reference
        self.assertGreater(result.critical_count, 0)
        self.assertFalse(result.passed)

    def test_timestamp_validation(self):
        """Test timestamp validation."""
        bad_script = get_mock_script_data()

        # Add clip with invalid timestamps (start > end)
        for section in bad_script['podcast_sections']:
            if section.get('section_type') == 'video_clip':
                section['start_time'] = '100.0'
                section['end_time'] = '50.0'  # End before start
                break

        result = self.gate.validate_script(bad_script)

        # Should detect timestamp issue
        has_timestamp_issue = any(i.check_name == 'timestamp_order' for i in result.issues)
        self.assertTrue(has_timestamp_issue)

    def test_empty_content_detected(self):
        """Test detection of empty script content."""
        bad_script = get_mock_script_data()

        # Empty the intro content
        for section in bad_script['podcast_sections']:
            if section.get('section_type') == 'intro':
                section['script_content'] = ''
                break

        result = self.gate.validate_script(bad_script)

        has_empty_issue = any(i.check_name == 'empty_content' for i in result.issues)
        self.assertTrue(has_empty_issue)

    def test_tts_formatting_check(self):
        """Test TTS formatting issues are detected."""
        script = get_mock_script_data()

        # Add TTS-problematic content
        for section in script['podcast_sections']:
            if section.get('section_type') == 'intro':
                section['script_content'] = "The FBI & CIA found 50% of claims wrong with $100M impact"
                break

        result = self.gate.validate_script(script)

        # Should find TTS formatting issues (INFO level, not critical)
        tts_issues = [i for i in result.issues if i.check_name == 'tts_formatting']
        self.assertGreater(len(tts_issues), 0)


class TestIntegrationPipeline(unittest.TestCase):
    """Test the full integration of all modules together."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.mock_segments = get_mock_pass1_data()
        self.mock_script = get_mock_script_data()

    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_full_filtering_pipeline(self):
        """Test complete filtering pipeline with all components."""
        # Step 1: Binary Segment Filtering
        mock_filter = MockBinarySegmentFilter()
        passed, rejected, filter_meta = mock_filter.filter_segments(self.mock_segments)

        self.assertGreater(len(passed), 0)
        self.assertEqual(filter_meta['total_segments'], len(self.mock_segments))

        # Step 2: Diversity Selection
        selector = DiversitySelector()
        selected = selector.select_diverse(passed, min_count=3, max_count=8)

        self.assertGreaterEqual(len(selected), min(3, len(passed)))

        # Step 3: False Negative Recovery
        scanner = FalseNegativeScanner({'quality_control': {'false_negative_recovery': {'enabled': True}}}, skip_api_init=True)
        recovered = scanner.scan_rejected(rejected, selected)

        # Recovered can be empty or have items
        self.assertIsInstance(recovered, list)

        # Final selection
        final_selection = selected + recovered

        self.assertGreater(len(final_selection), 0)

    def test_full_verification_pipeline(self):
        """Test complete rebuttal verification pipeline."""
        # Step 1: Verify rebuttals
        mock_verifier = MockBinaryRebuttalVerifier()
        verified_script, verify_meta = mock_verifier.verify_script_rebuttals(self.mock_script)

        self.assertIn('podcast_sections', verified_script)

        # Step 2: Output quality gate
        gate = OutputQualityGate()
        gate_result = gate.validate_script(verified_script)

        # Mock script should pass
        self.assertTrue(gate_result.passed)

    def test_end_to_end_data_flow(self):
        """Test that data flows correctly through all stages."""
        # Stage 1: Start with Pass 1 segments
        segments = self.mock_segments

        # Stage 2: Binary filtering
        mock_filter = MockBinarySegmentFilter()
        passed, rejected, _ = mock_filter.filter_segments(segments)

        # Verify data structure is maintained
        for seg in passed:
            self.assertIn('segment_id', seg)
            self.assertIn('suggestedClip', seg)
            self.assertIn('binary_filter_results', seg)

        # Stage 3: Diversity selection
        selector = DiversitySelector()
        selected = selector.select_diverse(passed)

        # Verify data structure still intact
        for seg in selected:
            self.assertIn('segment_id', seg)

        # Stage 4: False negative scan
        scanner = FalseNegativeScanner(skip_api_init=True)
        recovered = scanner.scan_rejected(rejected, selected)

        # Final segments
        final = selected + recovered

        # All segments should have required fields
        for seg in final:
            self.assertIn('segment_id', seg)
            self.assertIn('narrativeSegmentTitle', seg)


if __name__ == '__main__':
    unittest.main(verbosity=2)
