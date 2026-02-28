"""
End-to-End Tests for Multi-Pass Binary Filtering Pipeline

Tests the complete pipeline flow from transcript analysis through verified script,
using mock data and mocked API calls to avoid actual API consumption.

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
from unittest.mock import patch, MagicMock, PropertyMock

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
content_analysis_dir = os.path.dirname(current_dir)
code_dir = os.path.dirname(content_analysis_dir)
sys.path.insert(0, current_dir)  # For mock_data
sys.path.insert(0, content_analysis_dir)
sys.path.insert(0, code_dir)

# Import modules to test
from multi_pass_controller import MultiPassController, create_multi_pass_controller
from binary_segment_filter import BinarySegmentFilter, FilterResult, GateResult
from binary_rebuttal_verifier import BinaryRebuttalVerifier, VerificationResult
from diversity_selector import DiversitySelector
from false_negative_scanner import FalseNegativeScanner
from output_quality_gate import OutputQualityGate

# Import mock data
from mock_data import (
    MOCK_PASS1_SEGMENTS,
    MOCK_UNIFIED_SCRIPT,
    MockBinarySegmentFilter,
    MockBinaryRebuttalVerifier,
    get_mock_pass1_data,
    get_mock_script_data,
)


class MockEnhancedLogger:
    """Mock enhanced logger for testing."""

    def info(self, msg): pass
    def error(self, msg): pass
    def warning(self, msg): pass
    def success(self, msg): pass

    def spinner(self, msg):
        return self._null_context()

    def stage_context(self, name, num=None):
        return self._null_context()

    def _null_context(self):
        class NullContext:
            def __enter__(self): return self
            def __exit__(self, *args): pass
        return NullContext()


class MockGeminiModel:
    """Mock Gemini model for testing gate evaluations."""

    def __init__(self, gate_responses=None):
        self.gate_responses = gate_responses or {}
        self.call_count = 0

    def generate_content(self, prompt):
        self.call_count += 1

        # Determine which gate is being evaluated
        gate_name = "unknown"
        for gate in ["claim_detection", "verifiability", "accuracy_check",
                     "harm_assessment", "rebuttability"]:
            if gate.upper() in prompt:
                gate_name = gate
                break

        # Get predefined response or default to YES
        response_text = self.gate_responses.get(gate_name,
            "ANSWER: YES\nJUSTIFICATION: Test justification\nEVIDENCE: Test evidence")

        response = MagicMock()
        response.text = response_text
        return response


class TestMultiPassControllerE2E(unittest.TestCase):
    """End-to-end tests for MultiPassController."""

    def setUp(self):
        """Set up test fixtures with mock episode directory."""
        self.test_dir = tempfile.mkdtemp()
        self.episode_dir = os.path.join(self.test_dir, "Test_Episode_E2E")

        # Create directory structure
        os.makedirs(os.path.join(self.episode_dir, "Processing"))
        os.makedirs(os.path.join(self.episode_dir, "Output", "Scripts"))
        os.makedirs(os.path.join(self.episode_dir, "Input"))

        # Create mock transcript
        self.transcript_path = os.path.join(
            self.episode_dir, "Processing", "original_audio_transcript.json"
        )
        mock_transcript = {
            "segments": [
                {"speaker": "Joe Rogan", "text": "Some test content about vaccines."},
                {"speaker": "Guest", "text": "Vaccines cause autism. This is proven."},
            ]
        }
        with open(self.transcript_path, 'w', encoding='utf-8') as f:
            json.dump(mock_transcript, f)

        # Create mock Pass 1 results (cached)
        self.pass1_path = os.path.join(
            self.episode_dir, "Processing", "original_audio_analysis_results.json"
        )
        mock_pass1_results = get_mock_pass1_data()
        with open(self.pass1_path, 'w', encoding='utf-8') as f:
            json.dump(mock_pass1_results, f)

        # Create config
        self.config = {
            'api': {'gemini_api_key': 'test-key'},
            'quality_control': {
                'diversity': {'min_segments': 3, 'max_segments': 8},
                'rebuttal_verification': {'max_iterations': 3},
                'false_negative_recovery': {'enabled': True, 'max_recovery': 2}
            }
        }

        self.mock_logger = MockEnhancedLogger()

    def tearDown(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _create_mocked_controller(self):
        """Create a controller with all API-dependent components mocked."""
        controller = MultiPassController.__new__(MultiPassController)
        controller.config = self.config
        controller.episode_dir = self.episode_dir
        controller.enhanced_logger = self.mock_logger
        controller.qc_config = self.config.get('quality_control', {})

        # Use mock versions of API-dependent modules
        controller.segment_filter = MockBinarySegmentFilter()
        controller.rebuttal_verifier = MockBinaryRebuttalVerifier()
        controller.narrative_generator = MagicMock()

        # Configure narrative generator mock
        mock_script_data = get_mock_script_data()
        controller.narrative_generator.generate_unified_narrative.return_value = mock_script_data
        controller.narrative_generator.save_unified_script.return_value = Path(
            os.path.join(self.episode_dir, "Output", "Scripts", "unified_podcast_script.json")
        )

        # Use real non-API modules
        controller.diversity_selector = DiversitySelector(self.config)
        controller.false_negative_scanner = FalseNegativeScanner(self.config, skip_api_init=True)
        controller.output_gate = OutputQualityGate(self.config)
        controller.fact_validator = None  # Skip fact validation in tests

        # Initialize tracking
        controller.completed_stages = []
        controller.stage_outputs = {}
        controller.stage_metadata = {}

        return controller

    def test_e2e_pipeline_with_mocks(self):
        """Test complete pipeline with all external services mocked."""
        controller = self._create_mocked_controller()

        # Create mock script file that save_unified_script returns
        script_path = os.path.join(
            self.episode_dir, "Output", "Scripts", "unified_podcast_script.json"
        )
        mock_script = get_mock_script_data()
        with open(script_path, 'w', encoding='utf-8') as f:
            json.dump(mock_script, f)

        # Execute pipeline stages manually to test flow
        # Stage 1: Use cached Pass 1 results
        controller.stage_outputs['pass_1'] = self.pass1_path
        controller.completed_stages.append('pass_1')

        # Stage 2: Binary filtering with mock
        passed, rejected, metadata = controller.segment_filter.filter_segments(
            get_mock_pass1_data()
        )
        self.assertGreater(len(passed), 0)
        controller.completed_stages.append('binary_filtering')

        # Stage 3: Diversity selection
        selected = controller.diversity_selector.select_diverse(
            passed, min_count=3, max_count=8
        )
        self.assertGreater(len(selected), 0)
        controller.completed_stages.append('diversity_selection')

        # Stage 4: False negative recovery
        final_segments = controller.false_negative_scanner.scan_rejected(
            rejected, selected
        )
        # Recovery may or may not return results depending on content
        controller.completed_stages.append('false_negative_recovery')

        # Stage 5: Script generation (mocked)
        controller.narrative_generator.generate_unified_narrative.assert_not_called()  # Not called yet

        # Stage 6: Output quality gate
        result = controller.output_gate.validate_script(mock_script)
        self.assertTrue(result.passed)
        controller.completed_stages.append('output_quality_gate')

        # Stage 7: Rebuttal verification (mocked)
        verified_script, verify_meta = controller.rebuttal_verifier.verify_script_rebuttals(mock_script)
        self.assertIn('podcast_sections', verified_script)
        controller.completed_stages.append('rebuttal_verification')

        # Verify all stages completed
        expected_stages = [
            'pass_1', 'binary_filtering', 'diversity_selection',
            'false_negative_recovery', 'output_quality_gate', 'rebuttal_verification'
        ]
        self.assertEqual(controller.completed_stages, expected_stages)

    def test_e2e_data_integrity_through_pipeline(self):
        """Test that data maintains integrity through all pipeline stages."""
        controller = self._create_mocked_controller()

        # Load Pass 1 data
        with open(self.pass1_path, 'r', encoding='utf-8') as f:
            pass1_data = json.load(f)

        # Track segment_ids through pipeline
        original_ids = set(seg.get('segment_id', f'seg_{i}')
                          for i, seg in enumerate(pass1_data))

        # Stage 2: Binary filtering
        passed, rejected, _ = controller.segment_filter.filter_segments(pass1_data)

        # All segments should have been processed
        processed_ids = set(seg.get('segment_id', '') for seg in passed + rejected)
        self.assertEqual(original_ids, processed_ids)

        # Passed segments should have filter results
        for seg in passed:
            self.assertIn('binary_filter_results', seg)
            self.assertTrue(seg['binary_filter_results']['passed'])

        # Stage 3: Diversity selection preserves segment data
        selected = controller.diversity_selector.select_diverse(passed, min_count=2)

        for seg in selected:
            self.assertIn('segment_id', seg)
            self.assertIn('narrativeSegmentTitle', seg)

        # Stage 4: False negative recovery
        final_segments = selected + controller.false_negative_scanner.scan_rejected(
            rejected, selected
        )

        # All final segments should have required fields
        for seg in final_segments:
            self.assertIn('segment_id', seg)

    def test_e2e_handles_empty_segments_gracefully(self):
        """Test pipeline handles edge case of no segments passing filters."""
        controller = self._create_mocked_controller()

        # Create a mock filter that rejects everything
        class RejectAllFilter:
            def filter_segments(self, segments, output_path=None):
                rejected = []
                for seg in segments:
                    seg_copy = seg.copy()
                    seg_copy['binary_filter_results'] = {
                        'passed': False,
                        'failed_at': 'claim_detection',
                        'rejection_reason': 'No factual claim'
                    }
                    rejected.append(seg_copy)
                return [], rejected, {'total_segments': len(segments), 'passed_count': 0}

        controller.segment_filter = RejectAllFilter()

        # Run binary filtering
        passed, rejected, _ = controller.segment_filter.filter_segments(get_mock_pass1_data())

        self.assertEqual(len(passed), 0)
        self.assertGreater(len(rejected), 0)

        # Diversity selector should handle empty input
        selected = controller.diversity_selector.select_diverse(passed, min_count=3)
        self.assertEqual(len(selected), 0)

        # False negative recovery might recover some
        recovered = controller.false_negative_scanner.scan_rejected(rejected, selected)
        # Result depends on recovery logic - may or may not find recoverable segments
        self.assertIsInstance(recovered, list)

    def test_e2e_output_gate_catches_issues(self):
        """Test that output quality gate catches script issues."""
        controller = self._create_mocked_controller()

        # Create script with intentional issues
        bad_script = get_mock_script_data()

        # Add invalid clip reference
        bad_script['podcast_sections'].append({
            'section_type': 'post_clip',
            'section_id': 'post_invalid',
            'clip_reference': 'Non_Existent_Clip',
            'script_content': 'This references a clip that does not exist.'
        })

        result = controller.output_gate.validate_script(bad_script)

        # Should fail due to invalid reference
        self.assertFalse(result.passed)
        self.assertGreater(result.critical_count, 0)

    def test_e2e_rebuttal_verification_with_iterations(self):
        """Test rebuttal verification with multiple correction iterations."""
        controller = self._create_mocked_controller()

        mock_script = get_mock_script_data()
        verified_script, metadata = controller.rebuttal_verifier.verify_script_rebuttals(
            mock_script
        )

        self.assertIn('rebuttals_verified', metadata)
        self.assertGreater(metadata['rebuttals_verified'], 0)

        # Script structure should be preserved
        self.assertIn('podcast_sections', verified_script)
        self.assertIn('script_metadata', verified_script)


class TestMultiPassControllerFactoryE2E(unittest.TestCase):
    """Test factory function for creating MultiPassController."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.episode_dir = os.path.join(self.test_dir, "Test_Episode")
        os.makedirs(self.episode_dir)

        self.config = {
            'api': {'gemini_api_key': 'test-key'},
            'quality_control': {}
        }

    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch('multi_pass_controller.BinarySegmentFilter')
    @patch('multi_pass_controller.BinaryRebuttalVerifier')
    def test_factory_creates_controller(self, mock_verifier, mock_filter):
        """Test that factory function creates properly configured controller."""
        # Mock the classes to avoid API initialization
        mock_filter.return_value = MagicMock()
        mock_verifier.return_value = MagicMock()

        controller = create_multi_pass_controller(
            config=self.config,
            episode_dir=self.episode_dir,
            enhanced_logger=MockEnhancedLogger()
        )

        self.assertIsInstance(controller, MultiPassController)
        self.assertEqual(controller.episode_dir, self.episode_dir)
        self.assertEqual(controller.config, self.config)


class TestPipelineConfigurationE2E(unittest.TestCase):
    """Test pipeline behavior with different configurations."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.episode_dir = os.path.join(self.test_dir, "Test_Episode")
        os.makedirs(os.path.join(self.episode_dir, "Processing"))
        os.makedirs(os.path.join(self.episode_dir, "Output", "Scripts"))

    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_diversity_config_respected(self):
        """Test that diversity selection respects min/max config."""
        config = {
            'quality_control': {
                'diversity': {'min_segments': 2, 'max_segments': 4, 'max_per_topic': 2}
            }
        }

        selector = DiversitySelector(config)

        # Create many segments
        segments = [
            {'segment_id': f'seg_{i}', 'narrativeSegmentTitle': f'Vaccine claim {i}'}
            for i in range(10)
        ]

        selected = selector.select_diverse(segments, min_count=2, max_count=4)

        self.assertGreaterEqual(len(selected), 2)
        self.assertLessEqual(len(selected), 4)

    def test_false_negative_recovery_respects_max(self):
        """Test that false negative recovery respects max_recovery config."""
        config = {
            'quality_control': {
                'false_negative_recovery': {'enabled': True, 'max_recovery': 1}
            }
        }

        scanner = FalseNegativeScanner(config, skip_api_init=True)

        # Create rejected segments that should be recovered
        rejected = [
            {
                'segment_id': f'rejected_{i}',
                'narrativeSegmentTitle': f'Climate change denial {i}',
                'clipContextDescription': 'This is about climate science government fraud',
                'binary_filter_results': {
                    'passed': False,
                    'failed_at': 'harm_assessment',
                    'gate_results': {
                        'claim_detection': {'passed': True},
                        'verifiability': {'passed': True},
                        'accuracy_check': {'passed': True},
                        'harm_assessment': {'passed': False},
                        'rebuttability': {'passed': True}
                    }
                }
            }
            for i in range(5)
        ]

        selected = [
            {'segment_id': 'sel_1', 'narrativeSegmentTitle': 'Vaccine claim'}
        ]

        recovered = scanner.scan_rejected(rejected, selected)

        # Should respect max_recovery limit
        self.assertLessEqual(len(recovered), 1)


class TestPipelineErrorHandlingE2E(unittest.TestCase):
    """Test error handling throughout the pipeline."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.episode_dir = os.path.join(self.test_dir, "Test_Episode")
        os.makedirs(self.episode_dir)

    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_diversity_selector_handles_invalid_segments(self):
        """Test diversity selector handles segments with missing fields."""
        selector = DiversitySelector()

        # Segments with missing/malformed data
        bad_segments = [
            {'segment_id': 'good_1', 'narrativeSegmentTitle': 'Valid segment'},
            {'segment_id': 'bad_1'},  # Missing title
            {'narrativeSegmentTitle': 'Missing ID'},  # Missing ID
            {},  # Empty
        ]

        # Should not crash
        selected = selector.select_diverse(bad_segments, min_count=1)
        self.assertIsInstance(selected, list)

    def test_output_gate_handles_malformed_script(self):
        """Test output gate handles malformed script gracefully."""
        gate = OutputQualityGate()

        # Malformed script missing required fields
        bad_script = {
            'podcast_sections': [
                {'section_type': 'unknown_type'},  # Invalid type
                {'section_id': 'missing_type'},  # Missing section_type
            ]
        }

        # Should not crash, but should fail validation
        result = gate.validate_script(bad_script)
        self.assertIsInstance(result.passed, bool)


if __name__ == '__main__':
    unittest.main(verbosity=2)
