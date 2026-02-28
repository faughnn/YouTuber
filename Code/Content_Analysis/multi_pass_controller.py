"""
Multi-Pass Content Analysis Controller - Binary Filtering Pipeline

This module orchestrates the complete multi-pass quality control pipeline using
binary filtering instead of numeric thresholds. Coordinates all stages from
transcript analysis through verified script output.

Pipeline Stages:
1. Pass 1: Transcript Analysis (from transcript_analyzer.py)
2. Binary Segment Filtering (5-gate system)
3. Diversity-Aware Selection
4. False Negative Recovery Scan
5. Script Generation
6. Output Quality Gate
7. Binary Rebuttal Verification (4-gate self-correcting loop)
8. External Fact Validation (optional)

Author: Claude Code
Created: 2024-12-28
Pipeline: Multi-Pass Quality Control System
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging
import traceback

# Add paths for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
utils_dir = os.path.join(current_dir, '..', 'Utils')
code_dir = os.path.join(current_dir, '..')

for path in [utils_dir, current_dir, code_dir]:
    if path not in sys.path:
        sys.path.append(path)

# Import pipeline modules - use multiple import strategies
try:
    from .binary_segment_filter import BinarySegmentFilter
    from .binary_rebuttal_verifier import BinaryRebuttalVerifier
    from .podcast_narrative_generator import NarrativeCreatorGenerator
    from .transcript_analyzer import upload_transcript_to_gemini, analyze_with_gemini_file_upload
except ImportError:
    try:
        from Content_Analysis.binary_segment_filter import BinarySegmentFilter
        from Content_Analysis.binary_rebuttal_verifier import BinaryRebuttalVerifier
        from Content_Analysis.podcast_narrative_generator import NarrativeCreatorGenerator
        from Content_Analysis.transcript_analyzer import upload_transcript_to_gemini, analyze_with_gemini_file_upload
    except ImportError:
        from binary_segment_filter import BinarySegmentFilter
        from binary_rebuttal_verifier import BinaryRebuttalVerifier
        from podcast_narrative_generator import NarrativeCreatorGenerator
        from transcript_analyzer import upload_transcript_to_gemini, analyze_with_gemini_file_upload

# Optional imports for additional stages
try:
    from .diversity_selector import DiversitySelector
    DIVERSITY_AVAILABLE = True
except ImportError:
    DIVERSITY_AVAILABLE = False

try:
    from .false_negative_scanner import FalseNegativeScanner
    FALSE_NEGATIVE_AVAILABLE = True
except ImportError:
    FALSE_NEGATIVE_AVAILABLE = False

try:
    from .output_quality_gate import OutputQualityGate
    OUTPUT_GATE_AVAILABLE = True
except ImportError:
    OUTPUT_GATE_AVAILABLE = False

try:
    from .tts_formatter import TTSFormatter
    TTS_FORMATTER_AVAILABLE = True
except ImportError:
    try:
        from Content_Analysis.tts_formatter import TTSFormatter
        TTS_FORMATTER_AVAILABLE = True
    except ImportError:
        TTS_FORMATTER_AVAILABLE = False

try:
    from .chunked_transcript_analyzer import ChunkedTranscriptAnalyzer
    CHUNKED_ANALYZER_AVAILABLE = True
except ImportError:
    try:
        from Content_Analysis.chunked_transcript_analyzer import ChunkedTranscriptAnalyzer
        CHUNKED_ANALYZER_AVAILABLE = True
    except ImportError:
        try:
            from chunked_transcript_analyzer import ChunkedTranscriptAnalyzer
            CHUNKED_ANALYZER_AVAILABLE = True
        except ImportError:
            CHUNKED_ANALYZER_AVAILABLE = False

try:
    from .fact_validator import FactValidator
    FACT_VALIDATOR_AVAILABLE = True
except ImportError:
    FACT_VALIDATOR_AVAILABLE = False

try:
    from .recent_events_verifier import RecentEventsVerifier
    RECENT_EVENTS_VERIFIER_AVAILABLE = True
except ImportError:
    try:
        from Content_Analysis.recent_events_verifier import RecentEventsVerifier
        RECENT_EVENTS_VERIFIER_AVAILABLE = True
    except ImportError:
        RECENT_EVENTS_VERIFIER_AVAILABLE = False

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


class MultiPassControllerError(Exception):
    """Custom exception for multi-pass controller failures."""
    def __init__(self, message: str, stage: str = None, recoverable: bool = False):
        self.stage = stage
        self.recoverable = recoverable
        super().__init__(message)


class MultiPassController:
    """
    Central orchestration module for the multi-pass binary filtering pipeline.

    Coordinates:
    - Pass 1: Transcript Analysis
    - Binary Segment Filtering (5-gate)
    - Diversity-Aware Selection
    - False Negative Recovery
    - Script Generation
    - Output Quality Gate
    - Binary Rebuttal Verification (4-gate)
    - External Fact Validation
    """

    def __init__(
        self,
        config: Dict[str, Any],
        episode_dir: str,
        enhanced_logger=None
    ):
        """
        Initialize the Multi-Pass Controller.

        Args:
            config: Configuration dictionary
            episode_dir: Path to episode directory
            enhanced_logger: Optional enhanced logger instance
        """
        self.config = config
        self.episode_dir = episode_dir
        self.enhanced_logger = enhanced_logger or self._create_fallback_logger()

        # Load verified names from episode metadata
        self.verified_names = self._load_verified_names()

        # Initialize pipeline modules
        self.segment_filter = BinarySegmentFilter(config)
        self.rebuttal_verifier = BinaryRebuttalVerifier(config)
        self.narrative_generator = NarrativeCreatorGenerator()

        # Optional modules — pass verified names to quality gate and TTS formatter
        self.diversity_selector = DiversitySelector(config) if DIVERSITY_AVAILABLE else None
        self.false_negative_scanner = FalseNegativeScanner(config) if FALSE_NEGATIVE_AVAILABLE else None
        self.output_gate = OutputQualityGate(config, verified_names=self.verified_names) if OUTPUT_GATE_AVAILABLE else None
        self.tts_formatter = TTSFormatter(verified_names=self.verified_names) if TTS_FORMATTER_AVAILABLE else None
        self.fact_validator = FactValidator(config) if FACT_VALIDATOR_AVAILABLE else None
        self.recent_events_verifier = RecentEventsVerifier(config) if RECENT_EVENTS_VERIFIER_AVAILABLE else None

        # Stage tracking
        self.completed_stages = []
        self.stage_outputs = {}
        self.stage_metadata = {}

        # Configuration
        self.qc_config = config.get('quality_control', {})

    def _load_guest_profile(self) -> str:
        """Load guest-specific analysis profile if one exists.

        Matches guest name from episode directory path against profile filenames
        in Analysis_Guidelines/Guest_Profiles/. Filenames use lowercase with
        underscores (e.g., rfk_jr.txt, bret_weinstein.txt).

        Returns:
            Profile text to append to analysis rules, or empty string.
        """
        profiles_dir = os.path.join(
            current_dir, 'Analysis_Guidelines', 'Guest_Profiles'
        )
        if not os.path.isdir(profiles_dir):
            return ""

        # Extract guest name from episode_dir: Content/{Host}/{Host_Guest}/
        try:
            episode_folder = os.path.basename(self.episode_dir.rstrip('/\\'))
            # Find parent folder (host name) to strip prefix
            host_folder = os.path.basename(os.path.dirname(self.episode_dir.rstrip('/\\')))
            if episode_folder.startswith(host_folder + '_'):
                guest_part = episode_folder[len(host_folder) + 1:]
            else:
                guest_part = episode_folder
            guest_normalized = guest_part.lower().strip()
        except Exception:
            return ""

        # Try to match against available profiles
        for filename in os.listdir(profiles_dir):
            if not filename.endswith('.txt'):
                continue
            profile_name = filename[:-4]  # strip .txt
            # Match if guest folder contains the profile name or vice versa
            if profile_name in guest_normalized or guest_normalized in profile_name:
                profile_path = os.path.join(profiles_dir, filename)
                with open(profile_path, 'r', encoding='utf-8') as f:
                    profile_text = f.read()
                logger.info(f"Loaded guest profile: {filename} (matched '{guest_part}')")
                self.enhanced_logger.info(f"  📋 Guest profile loaded: {filename}")
                return profile_text

        logger.info(f"No guest profile found for '{guest_part}'")
        return ""

    def _load_verified_names(self) -> Dict[str, str]:
        """Load verified host/guest names from episode_metadata.json.

        Returns:
            Dict with 'host' and 'guest' keys, or empty dict if unavailable.
        """
        metadata_path = os.path.join(self.episode_dir, 'Input', 'episode_metadata.json')
        if not os.path.exists(metadata_path):
            logger.debug(f"No episode metadata at {metadata_path}")
            return {}

        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            names = {}
            if metadata.get('host_name'):
                names['host'] = metadata['host_name']
            if metadata.get('guest_name'):
                names['guest'] = metadata['guest_name']

            if names:
                logger.info(f"Loaded verified names: {names}")
            return names
        except Exception as e:
            logger.warning(f"Failed to load episode metadata for names: {e}")
            return {}

    def _create_fallback_logger(self):
        """Create a fallback logger wrapper."""
        class FallbackLogger:
            def info(self, msg): logger.info(msg)
            def error(self, msg): logger.error(msg)
            def warning(self, msg): logger.warning(msg)
            def success(self, msg): logger.info(f"✓ {msg}")
            def spinner(self, msg): return self._null_context()
            def stage_context(self, name, num): return self._null_context()
            def _null_context(self):
                class NullContext:
                    def __enter__(self): return self
                    def __exit__(self, *args): pass
                return NullContext()
        return FallbackLogger()

    def run_full_pipeline(
        self,
        transcript_path: str,
        narrative_format: str = "with_hook"
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Execute the complete multi-pass pipeline.

        Args:
            transcript_path: Path to transcript JSON file
            narrative_format: Format for narrative generation

        Returns:
            Tuple of (final_output_path, pipeline_metadata)
        """
        self.enhanced_logger.info("=" * 60)
        self.enhanced_logger.info("MULTI-PASS BINARY FILTERING PIPELINE")
        self.enhanced_logger.info("=" * 60)

        pipeline_start = datetime.now()

        try:
            # Stage 1: Transcript Analysis (Pass 1)
            pass1_output = self._execute_pass_1_analysis(transcript_path)
            self.completed_stages.append('pass_1')

            # Stage 2: Binary Segment Filtering (5 gates)
            filtered_segments, rejected_segments = self._execute_binary_filtering(pass1_output)
            self.completed_stages.append('binary_filtering')

            # Stage 2.5: Recent Events Verification (web search for date-sensitive claims)
            verified_segments = self._execute_recent_events_verification(filtered_segments)
            self.completed_stages.append('recent_events_verification')

            # Stage 3: Diversity Selection (if available)
            selected_segments = self._execute_diversity_selection(
                verified_segments, rejected_segments
            )
            self.completed_stages.append('diversity_selection')

            # Stage 4: False Negative Recovery (if available)
            final_segments = self._execute_false_negative_recovery(
                selected_segments, rejected_segments
            )
            self.completed_stages.append('false_negative_recovery')

            # Stage 5: Script Generation
            script_path = self._execute_script_generation(final_segments, narrative_format)
            self.completed_stages.append('script_generation')

            # Stage 5.5: TTS Formatting (deterministic post-processing)
            self._execute_tts_formatting(script_path)
            self.completed_stages.append('tts_formatting')

            # Stage 6: Output Quality Gate (if available)
            validated_script_path = self._execute_output_quality_gate(script_path)
            self.completed_stages.append('output_quality_gate')

            # Stage 7: Binary Rebuttal Verification (4 gates + self-correction)
            verified_script_path = self._execute_rebuttal_verification(validated_script_path)
            self.completed_stages.append('rebuttal_verification')

            # Stage 8: External Fact Validation (if available)
            final_script_path = self._execute_fact_validation(verified_script_path)
            self.completed_stages.append('fact_validation')

            pipeline_end = datetime.now()

            pipeline_metadata = {
                'pipeline_start': pipeline_start.isoformat(),
                'pipeline_end': pipeline_end.isoformat(),
                'total_duration_seconds': (pipeline_end - pipeline_start).total_seconds(),
                'completed_stages': self.completed_stages,
                'stage_metadata': self.stage_metadata,
                'final_output': final_script_path
            }

            self.enhanced_logger.info("=" * 60)
            self.enhanced_logger.success("PIPELINE COMPLETE")
            self.enhanced_logger.info(f"Final output: {final_script_path}")
            self.enhanced_logger.info("=" * 60)

            return final_script_path, pipeline_metadata

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            logger.error(traceback.format_exc())
            raise

    def _execute_pass_1_analysis(self, transcript_path: str) -> str:
        """Execute Pass 1: Transcript Analysis.

        Routes to ChunkedTranscriptAnalyzer for long podcasts (>30 min) when
        chunked_analysis.enabled is true. Falls back to single-call analysis
        for short podcasts or when chunked analysis is unavailable.
        """
        self.enhanced_logger.info("📊 Stage 1: Transcript Analysis")

        processing_dir = os.path.join(self.episode_dir, "Processing")
        output_path = os.path.join(processing_dir, "original_audio_analysis_results.json")

        # Check for cached result
        if os.path.exists(output_path):
            self.enhanced_logger.warning("  Using cached Pass 1 results")
            self.stage_outputs['pass_1'] = output_path
            return output_path

        os.makedirs(processing_dir, exist_ok=True)

        if not os.path.exists(transcript_path):
            raise MultiPassControllerError(
                f"Transcript file not found: {transcript_path}",
                stage="pass_1"
            )

        try:
            # Load analysis rules
            rules_path = os.path.join(
                current_dir,
                'Analysis_Guidelines',
                'selective_analysis_rules.txt'
            )
            analysis_rules = ""
            if os.path.exists(rules_path):
                with open(rules_path, 'r', encoding='utf-8') as f:
                    analysis_rules = f.read()

            # Load guest-specific profile if one exists
            guest_profile = self._load_guest_profile()
            if guest_profile:
                analysis_rules += f"\n\n{guest_profile}"

            # Decide whether to use chunked analysis
            chunked_config = self.config.get('chunked_analysis', {})
            use_chunked = (
                chunked_config.get('enabled', False)
                and CHUNKED_ANALYZER_AVAILABLE
            )

            if use_chunked:
                self.enhanced_logger.info("  Using chunked transcript analysis")
                chunked_analyzer = ChunkedTranscriptAnalyzer(
                    config=self.config,
                    enhanced_logger=self.enhanced_logger,
                )
                analysis_content = chunked_analyzer.analyze_transcript(
                    transcript_path=transcript_path,
                    analysis_rules=analysis_rules,
                    processing_dir=processing_dir,
                )
            else:
                # Original single-call path
                if not CHUNKED_ANALYZER_AVAILABLE and chunked_config.get('enabled', False):
                    self.enhanced_logger.warning(
                        "  Chunked analyzer not available — falling back to single-call"
                    )

                from google import genai
                api_key = self.config.get('api', {}).get('gemini_api_key')
                if not api_key:
                    api_key = os.getenv('GEMINI_API_KEY')

                display_name = f"transcript_{os.path.basename(transcript_path)}"
                file_object = upload_transcript_to_gemini(transcript_path, display_name)

                if not file_object:
                    raise MultiPassControllerError(
                        "Failed to upload transcript to Gemini",
                        stage="pass_1"
                    )

                analysis_content = analyze_with_gemini_file_upload(
                    file_object=file_object,
                    analysis_rules=analysis_rules,
                    output_dir=processing_dir,
                    file_path=transcript_path
                )

            if not analysis_content:
                raise MultiPassControllerError(
                    "Analysis failed - no content returned",
                    stage="pass_1"
                )

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(analysis_content)

            self.enhanced_logger.success(f"  Pass 1 complete: {os.path.basename(output_path)}")
            self.stage_outputs['pass_1'] = output_path
            return output_path

        except Exception as e:
            raise MultiPassControllerError(f"Pass 1 failed: {str(e)}", stage="pass_1")

    def _execute_binary_filtering(self, pass1_output: str) -> Tuple[List[Dict], List[Dict]]:
        """Execute Binary Segment Filtering (5 gates)."""
        self.enhanced_logger.info("🎯 Stage 2: Binary Segment Filtering (5 gates)")

        processing_dir = os.path.join(self.episode_dir, "Processing")
        output_path = os.path.join(processing_dir, "binary_filtered_segments.json")

        # Load Pass 1 results
        with open(pass1_output, 'r', encoding='utf-8') as f:
            segments = json.load(f)

        self.enhanced_logger.info(f"  Filtering {len(segments)} segments through 5 gates...")

        passed, rejected, metadata = self.segment_filter.filter_segments(
            segments=segments,
            output_path=output_path
        )

        self.stage_metadata['binary_filtering'] = metadata
        self.enhanced_logger.success(
            f"  Filtering complete: {len(passed)} passed, {len(rejected)} rejected"
        )

        self.stage_outputs['binary_filtering'] = output_path
        return passed, rejected

    def _execute_recent_events_verification(self, segments: List[Dict]) -> List[Dict]:
        """Execute Recent Events Verification using web search."""
        self.enhanced_logger.info("🔍 Stage 2.5: Recent Events Verification (Web Search)")

        if not self.recent_events_verifier:
            self.enhanced_logger.warning("  Recent events verifier not available - skipping")
            self.enhanced_logger.warning("  WARNING: Date-sensitive claims will NOT be verified against current events!")
            return segments

        processing_dir = os.path.join(self.episode_dir, "Processing")
        output_path = os.path.join(processing_dir, "recent_events_verification.json")

        try:
            verified_segments, metadata = self.recent_events_verifier.verify_segments(
                segments=segments,
                output_path=output_path
            )

            self.stage_metadata['recent_events_verification'] = metadata

            if metadata.get('corrections_needed', 0) > 0:
                self.enhanced_logger.warning(
                    f"  ⚠️ {metadata['corrections_needed']} segments need correction due to verified recent events"
                )
            else:
                self.enhanced_logger.success(
                    f"  Verified {metadata.get('total_claims_checked', 0)} date-sensitive claims"
                )

            self.stage_outputs['recent_events_verification'] = output_path

            # Filter out segments where claims were confirmed true (no longer worth rebutting)
            filtered = [s for s in verified_segments if not s.get('_correction_needed')]
            if len(filtered) < len(verified_segments):
                removed = len(verified_segments) - len(filtered)
                self.enhanced_logger.info(
                    f"  Filtered out {removed} segments with confirmed-true claims"
                )
            return filtered

        except Exception as e:
            self.enhanced_logger.error(f"  Recent events verification failed: {e}")
            self.enhanced_logger.warning("  Continuing with unverified segments - manual review recommended")
            return segments

    def _execute_diversity_selection(
        self,
        passed_segments: List[Dict],
        rejected_segments: List[Dict]
    ) -> List[Dict]:
        """Execute Diversity-Aware Selection."""
        self.enhanced_logger.info("🌈 Stage 3: Diversity-Aware Selection")

        if not self.diversity_selector:
            self.enhanced_logger.warning("  Diversity selector not available - using all passed segments")
            return passed_segments

        min_segments = self.qc_config.get('diversity', {}).get('min_segments', 6)
        max_segments = self.qc_config.get('diversity', {}).get('max_segments', 12)

        selected = self.diversity_selector.select_diverse(
            passed_segments,
            min_count=min_segments,
            max_count=max_segments
        )

        self.enhanced_logger.success(f"  Selected {len(selected)} diverse segments")
        return selected

    def _execute_false_negative_recovery(
        self,
        selected_segments: List[Dict],
        rejected_segments: List[Dict]
    ) -> List[Dict]:
        """Execute False Negative Recovery Scan."""
        self.enhanced_logger.info("🔍 Stage 4: False Negative Recovery")

        if not self.false_negative_scanner:
            self.enhanced_logger.warning("  False negative scanner not available - skipping")
            return selected_segments

        recovered = self.false_negative_scanner.scan_rejected(
            rejected=rejected_segments,
            selected=selected_segments
        )

        if recovered:
            self.enhanced_logger.info(f"  Recovered {len(recovered)} false negatives")
            selected_segments.extend(recovered)
        else:
            self.enhanced_logger.info("  No false negatives recovered")

        return selected_segments

    def _execute_script_generation(
        self,
        final_segments: List[Dict],
        narrative_format: str
    ) -> str:
        """Execute Script Generation."""
        self.enhanced_logger.info("📝 Stage 5: Script Generation")

        output_dir = os.path.join(self.episode_dir, "Output", "Scripts")
        os.makedirs(output_dir, exist_ok=True)

        # Save filtered segments for script generation
        filtered_path = os.path.join(
            self.episode_dir, "Processing", "final_filtered_for_script.json"
        )
        with open(filtered_path, 'w', encoding='utf-8') as f:
            json.dump(final_segments, f, indent=2, ensure_ascii=False)

        episode_title = os.path.basename(self.episode_dir)

        self.enhanced_logger.info(f"  Generating narrative for: {episode_title}")

        script_data = self.narrative_generator.generate_unified_narrative(
            analysis_json_path=filtered_path,
            episode_title=episode_title,
            narrative_format=narrative_format
        )

        script_path = self.narrative_generator.save_unified_script(
            script_data=script_data,
            episode_output_path=os.path.join(self.episode_dir, "Output")
        )

        script_path_str = str(script_path)
        self.enhanced_logger.success(f"  Script generated: {os.path.basename(script_path_str)}")
        self.stage_outputs['script_generation'] = script_path_str
        return script_path_str

    def _execute_tts_formatting(self, script_path: str) -> None:
        """Apply deterministic TTS formatting to script content."""
        self.enhanced_logger.info("🔤 Stage 5.5: TTS Formatting")

        if not self.tts_formatter:
            self.enhanced_logger.warning("  TTS formatter not available - skipping")
            return

        with open(script_path, 'r', encoding='utf-8') as f:
            script_data = json.load(f)

        formatted_data = self.tts_formatter.format_script(script_data)

        with open(script_path, 'w', encoding='utf-8') as f:
            json.dump(formatted_data, f, indent=2, ensure_ascii=False)

        self.enhanced_logger.success("  TTS formatting applied")

    def _execute_output_quality_gate(self, script_path: str) -> str:
        """Execute Output Quality Gate."""
        self.enhanced_logger.info("🚧 Stage 6: Output Quality Gate")

        if not self.output_gate:
            self.enhanced_logger.warning("  Output quality gate not available - skipping")
            return script_path

        with open(script_path, 'r', encoding='utf-8') as f:
            script_data = json.load(f)

        result = self.output_gate.validate_script(script_data)

        if result.passed:
            self.enhanced_logger.success("  Script passed output quality gate")
        else:
            self.enhanced_logger.warning(f"  Quality gate issues: {result.issues}")
            # Attempt auto-correction if available
            if hasattr(self.output_gate, 'auto_correct'):
                corrected = self.output_gate.auto_correct(script_data, result.issues)
                with open(script_path, 'w', encoding='utf-8') as f:
                    json.dump(corrected, f, indent=2, ensure_ascii=False)
                self.enhanced_logger.info("  Auto-correction applied")

        return script_path

    def _execute_rebuttal_verification(self, script_path: str) -> str:
        """Execute Binary Rebuttal Verification (4 gates + self-correction)."""
        self.enhanced_logger.info("✅ Stage 7: Binary Rebuttal Verification")

        output_dir = os.path.join(self.episode_dir, "Output", "Scripts")
        verified_path = os.path.join(output_dir, "verified_unified_script.json")

        with open(script_path, 'r', encoding='utf-8') as f:
            script_data = json.load(f)

        verified_script, metadata = self.rebuttal_verifier.verify_script_rebuttals(
            script_data=script_data,
            output_path=verified_path
        )

        self.stage_metadata['rebuttal_verification'] = metadata
        self.enhanced_logger.success(
            f"  Verified {metadata['rebuttals_verified']} rebuttals, "
            f"{metadata['total_rewrites']} rewrites"
        )

        # Log warnings for sections that failed verification
        if metadata.get('passed_with_warnings', 0) > 0:
            self.enhanced_logger.warning(
                f"  ⚠️ {metadata['passed_with_warnings']} rebuttals failed verification after max iterations"
            )
            # Check script for failed sections
            with open(verified_path, 'r', encoding='utf-8') as f:
                script = json.load(f)
            for section in script.get('podcast_sections', []):
                if section.get('_verification_failed'):
                    self.enhanced_logger.warning(
                        f"    Failed section: {section.get('section_id')} - rebuttal may contain inaccuracies"
                    )

        self.stage_outputs['rebuttal_verification'] = verified_path
        return verified_path

    def _execute_fact_validation(self, script_path: str) -> str:
        """Execute External Fact Validation."""
        self.enhanced_logger.info("🔬 Stage 8: External Fact Validation")

        if not self.fact_validator:
            self.enhanced_logger.warning("  Fact validator not available - skipping")
            return script_path

        with open(script_path, 'r', encoding='utf-8') as f:
            script_data = json.load(f)

        validated_script = self.fact_validator.validate_script(script_data)

        # Save validated script
        with open(script_path, 'w', encoding='utf-8') as f:
            json.dump(validated_script, f, indent=2, ensure_ascii=False)

        self.enhanced_logger.success("  External fact validation complete")
        return script_path

    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline progress information."""
        return {
            "completed_stages": self.completed_stages,
            "stage_outputs": self.stage_outputs,
            "stage_metadata": self.stage_metadata,
            "total_stages": 9,
            "progress_percentage": (len(self.completed_stages) / 9) * 100
        }


def create_multi_pass_controller(
    config: Dict[str, Any],
    episode_dir: str,
    enhanced_logger=None
) -> MultiPassController:
    """
    Factory function to create MultiPassController instance.

    Args:
        config: Configuration dictionary
        episode_dir: Episode directory path
        enhanced_logger: Optional enhanced logger

    Returns:
        MultiPassController: Configured controller instance
    """
    return MultiPassController(config, episode_dir, enhanced_logger)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python multi_pass_controller.py <transcript_path> <episode_dir> [narrative_format]")
        sys.exit(1)

    transcript_path = sys.argv[1]
    episode_dir = sys.argv[2]
    narrative_format = sys.argv[3] if len(sys.argv) > 3 else "with_hook"

    # Create config from environment
    config = {
        'api': {'gemini_api_key': os.getenv('GEMINI_API_KEY')},
        'quality_control': {
            'diversity': {'min_segments': 6, 'max_segments': 12},
            'rebuttal_verification': {'max_iterations': 3}
        }
    }

    controller = create_multi_pass_controller(config, episode_dir)

    try:
        final_path, metadata = controller.run_full_pipeline(
            transcript_path=transcript_path,
            narrative_format=narrative_format
        )
        print(f"\n✓ Pipeline complete: {final_path}")
        print(f"  Duration: {metadata['total_duration_seconds']:.1f}s")
        print(f"  Stages completed: {len(metadata['completed_stages'])}/8")
    except Exception as e:
        print(f"\n✗ Pipeline failed: {e}")
        sys.exit(1)
