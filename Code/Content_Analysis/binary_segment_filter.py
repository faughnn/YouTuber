"""
Binary Segment Filter - Iterative Binary Filtering for Segment Selection

This module replaces the numeric threshold-based quality_assessor.py with a
sequential yes/no gate system. Each segment must pass ALL 5 gates to be included,
with each gate requiring explicit justification.

Gates:
1. CLAIM_DETECTION - Does this contain a specific factual claim?
2. VERIFIABILITY - Is this about real-world events (not metaphysical)?
3. ACCURACY_CHECK - Is this claim false or misleading?
4. HARM_ASSESSMENT - Could this cause real-world harm?
5. REBUTTABILITY - Can this be addressed with evidence or reasoning critique?

Author: Claude Code
Created: 2024-12-28
Pipeline: Multi-Pass Quality Control System
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field, asdict
from google import genai
from google.genai import types

# Global client for Gemini API
_gemini_client = None

# Add paths for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
utils_dir = os.path.join(current_dir, '..', 'Utils')
sys.path.append(utils_dir)

# Import validation framework
try:
    from json_schema_validator import JSONSchemaValidator
except ImportError:
    try:
        from Utils.json_schema_validator import JSONSchemaValidator
    except ImportError:
        JSONSchemaValidator = None

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


@dataclass
class GateResult:
    """Result from evaluating a single gate."""
    gate_name: str
    passed: bool
    justification: str
    evidence: str
    raw_response: str = ""


@dataclass
class FilterResult:
    """Result from filtering a segment through all gates."""
    segment_id: str
    passed: bool
    failed_at: Optional[str] = None
    rejection_reason: Optional[str] = None
    gate_results: Dict[str, Dict] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "segment_id": self.segment_id,
            "passed": self.passed,
            "failed_at": self.failed_at,
            "rejection_reason": self.rejection_reason,
            "gate_results": self.gate_results
        }


class BinarySegmentFilter:
    """
    Sequential yes/no gates for segment selection.

    Replaces numeric 1-10 scoring with binary pass/fail decisions.
    Each gate requires explicit justification and evidence.
    """

    # Deterministic ad/sponsorship keywords — auto-reject before API call
    AD_KEYWORDS = [
        'ag1', 'athletic greens', 'betterhelp', 'better help', 'squarespace',
        'expressvpn', 'express vpn', 'nordvpn', 'nord vpn', 'promo code',
        'discount link', 'sponsored by', 'brought to you by', 'use code',
        'cash app', 'manscaped', 'liquid iv', 'liquid i.v.',
    ]

    # Define the 5 gates with their questions
    GATES = [
        (
            "content_worth_rebutting",
            "Does this segment contain content worth rebutting — a factual claim, conspiracy theory, pseudoscience, or societal damage rhetoric (not opinion, speculation, or advertisement)?",
            "REJECT if this is an advertisement, sponsorship, or promotional content (mentions of AG1, Athletic Greens, BetterHelp, Squarespace, ExpressVPN, promo codes, discount links, 'sponsored by', 'brought to you by', etc.). REJECT pure opinions like 'I think', 'maybe', 'could be' with no factual basis. PASS any of the 4 harm categories: (1) Factual claims — concrete assertions about facts, statistics, events, or causal relationships that could be misinformation. (2) Conspiracy theories — claims of secret coordinated deception by powerful forces. (3) Pseudoscience — claims presented as scientific but lacking scientific method. (4) Societal damage rhetoric — content that erodes social cohesion, promotes harmful stereotypes, undermines democratic norms, or dehumanizes groups, even if not easily falsifiable."
        ),
        (
            "verifiability",
            "Is this a claim about real-world events, people, or phenomena (not purely metaphysical)?",
            "Pass claims about observable reality - even conspiracy theories that make claims about events, cover-ups, or hidden actors. Only reject purely metaphysical/spiritual claims like 'God exists' or 'we live in a simulation' that cannot be addressed with evidence or reasoning."
        ),
        (
            "accuracy_check",
            "Based on scientific consensus or verifiable facts, is this claim FALSE or MISLEADING? For societal damage rhetoric, does it demonstrably distort reality or promote harmful narratives?",
            "Only pass if the claim contradicts established evidence, OR if the rhetoric demonstrably distorts reality, promotes harmful stereotypes, or undermines democratic norms. If the claim is accurate or merely controversial opinion, it should FAIL this gate. We want to identify misinformation and harmful rhetoric."
        ),
        (
            "harm_assessment",
            "Could widespread belief in this misinformation or rhetoric cause real-world harm?",
            "Consider health risks, financial harm, erosion of democratic institutions, discrimination, violence, erosion of social cohesion, or normalization of hate. Harmless errors or entertainment should fail this gate."
        ),
        (
            "rebuttability",
            "Can this claim be effectively addressed through evidence OR by identifying flawed reasoning?",
            "Pass if we can counter with evidence, OR point out logical fallacies, conspiratorial thinking patterns (unfounded assumptions of massive coordinated cover-ups, cherry-picking, goalpost shifting, unfalsifiable premises). Both factual rebuttals and reasoning critiques are valid."
        ),
    ]

    def __init__(self, config: Optional[Dict] = None, skip_api_init: bool = False):
        """
        Initialize the BinarySegmentFilter.

        Args:
            config: Optional configuration dictionary
            skip_api_init: If True, skip Gemini API initialization (for testing)
        """
        self.config = config or {}
        self._api_configured = False

        if not skip_api_init:
            try:
                self._configure_gemini()
                self._api_configured = True
            except ValueError as e:
                logger.warning(f"Gemini API not configured: {e}")
                self._api_configured = False

        # Debug storage
        self._debug_api_calls = []
        self._all_filter_results = []

        # Rate limiting
        self.api_delay = self.config.get('api_delay', 2)
        self.max_retries = self.config.get('max_retries', 3)

    def _configure_gemini(self) -> None:
        """Configure Gemini API using config or environment variable."""
        global _gemini_client
        try:
            api_key = self.config.get('api', {}).get('gemini_api_key')
            if not api_key:
                api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                raise ValueError("Gemini API key not found in config or environment")

            _gemini_client = genai.Client(api_key=api_key)
            logger.info("Gemini API client configured successfully")
        except Exception as e:
            logger.error(f"Failed to configure Gemini API: {e}")
            raise

    def _get_client(self):
        """Get the Gemini client, initializing if needed."""
        global _gemini_client
        if _gemini_client is None:
            self._configure_gemini()
        return _gemini_client

    def filter_segments(
        self,
        segments: List[Dict],
        output_path: Optional[str] = None
    ) -> Tuple[List[Dict], List[Dict], Dict]:
        """
        Filter all segments through the 5-gate system.

        Args:
            segments: List of segment dictionaries from transcript analysis
            output_path: Optional path to save filtered results

        Returns:
            Tuple of (passed_segments, rejected_segments, metadata)
        """
        logger.info(f"=== BINARY SEGMENT FILTERING STARTED ===")
        logger.info(f"Processing {len(segments)} segments through 5 gates")

        passed_segments = []
        rejected_segments = []

        for i, segment in enumerate(segments):
            segment_id = segment.get('segment_id', f'segment_{i}')
            segment_title = segment.get('narrativeSegmentTitle', 'Unknown')
            print(f"  [{i+1}/{len(segments)}] {segment_id}: {segment_title}...", flush=True)
            logger.info(f"Filtering segment {i+1}/{len(segments)}: {segment_id}")

            result = self.filter_segment(segment)
            self._all_filter_results.append(result)

            if result.passed:
                # Add gate results to segment for downstream use
                segment_copy = segment.copy()
                segment_copy['binary_filter_results'] = result.to_dict()
                passed_segments.append(segment_copy)
                print(f"    ✅ PASSED all 5 gates", flush=True)
                logger.info(f"  PASSED all 5 gates")
            else:
                segment_copy = segment.copy()
                segment_copy['binary_filter_results'] = result.to_dict()
                rejected_segments.append(segment_copy)
                print(f"    ❌ REJECTED at gate: {result.failed_at} - {result.rejection_reason if result.rejection_reason else 'No reason'}", flush=True)
                logger.info(f"  REJECTED at gate: {result.failed_at}")

            # Rate limiting between segments
            if i < len(segments) - 1:
                time.sleep(self.api_delay)

        metadata = {
            'filtering_timestamp': datetime.now().isoformat(),
            'total_segments': len(segments),
            'passed_count': len(passed_segments),
            'rejected_count': len(rejected_segments),
            'pass_rate': len(passed_segments) / len(segments) if segments else 0,
            'gates_used': [g[0] for g in self.GATES]
        }

        logger.info(f"=== BINARY FILTERING COMPLETE ===")
        logger.info(f"Results: {len(passed_segments)} passed, {len(rejected_segments)} rejected")

        if output_path:
            self._save_results(passed_segments, rejected_segments, metadata, output_path)

        return passed_segments, rejected_segments, metadata

    def _is_advertisement(self, segment: Dict) -> bool:
        """Deterministic pre-screen: reject ads/sponsorships before API call."""
        text = self._extract_segment_content(segment).lower()
        return any(kw in text for kw in self.AD_KEYWORDS)

    def _check_clip_duration(self, segment: Dict) -> Optional[Tuple[float, str]]:
        """Check if clip duration meets minimum threshold.

        Returns:
            None if duration is acceptable, or (duration, message) if too short.
        """
        clip_config = self.config.get('quality_control', {}).get('clip_duration', {})
        min_seconds = clip_config.get('min_seconds', 25)

        timestamps = segment.get('fullerContextTimestamps', {})
        start = timestamps.get('start')
        end = timestamps.get('end')
        if start is None or end is None:
            return None  # Can't check without timestamps

        try:
            duration = float(end) - float(start)
        except (ValueError, TypeError):
            return None

        if duration < min_seconds:
            return (duration, f"Clip duration ({duration:.1f}s) below minimum ({min_seconds}s)")
        return None

    def filter_segment(self, segment: Dict) -> FilterResult:
        """
        Run a single segment through all gates via consolidated evaluation.

        Args:
            segment: Segment dictionary with suggestedClip and context

        Returns:
            FilterResult with pass/fail status and all gate results
        """
        segment_id = segment.get('segment_id', 'unknown')

        # Deterministic pre-screen: reject advertisements before API call
        if self._is_advertisement(segment):
            print(f"      ❌ AD PRE-SCREEN: rejected (advertisement/sponsorship)", flush=True)
            logger.info(f"  REJECTED by ad pre-screen (deterministic)")
            return FilterResult(
                segment_id=segment_id,
                passed=False,
                failed_at="ad_pre_screen",
                rejection_reason="Deterministic rejection: advertisement or sponsorship content detected",
                gate_results={}
            )

        # Check clip duration (WARNING, not hard rejection)
        duration_issue = self._check_clip_duration(segment)
        if duration_issue:
            duration, msg = duration_issue
            print(f"      ⚠️ SHORT CLIP: {msg}", flush=True)
            logger.warning(f"  SHORT CLIP: {msg}")

        # Extract segment content for evaluation
        segment_content = self._extract_segment_content(segment)

        print(f"      Evaluating all 5 gates...", end=" ", flush=True)

        result = self._evaluate_consolidated(segment_content)

        if result is None:
            print("❌ API FAIL", flush=True)
            return FilterResult(
                segment_id=segment_id,
                passed=False,
                failed_at="api_error",
                rejection_reason="Consolidated evaluation failed",
                gate_results={}
            )

        gate_results, first_failure = result

        if first_failure:
            print(f"❌ FAIL at {first_failure}", flush=True)
            return FilterResult(
                segment_id=segment_id,
                passed=False,
                failed_at=first_failure,
                rejection_reason=gate_results[first_failure]['justification'],
                gate_results=gate_results
            )

        print("✓ all passed", flush=True)
        result = FilterResult(
            segment_id=segment_id,
            passed=True,
            gate_results=gate_results
        )
        if duration_issue:
            result.gate_results['_short_clip_warning'] = {
                'duration': duration_issue[0],
                'message': duration_issue[1]
            }
        return result

    def _evaluate_consolidated(self, segment_content: str):
        """
        Evaluate a segment against all 5 gates in a single API call.

        Returns:
            Tuple of (gate_results_dict, first_failed_gate_name_or_None),
            or None on total failure
        """
        gate_descriptions = ""
        for i, (gate_name, gate_question, gate_guidance) in enumerate(self.GATES, 1):
            gate_descriptions += f"""
## GATE {i}: {gate_name.upper()}
**Question:** {gate_question}
**Guidance:** {gate_guidance}
"""

        prompt = f"""You are evaluating content for a media literacy project that identifies and rebuts misinformation.

Evaluate the segment below against ALL 5 gates sequentially. Each gate MUST consider the results of prior gates.

{gate_descriptions}

## SEGMENT CONTENT
{segment_content}

## INSTRUCTIONS
For EACH gate, provide your evaluation in this EXACT format:

GATE_1_ANSWER: [YES or NO]
GATE_1_JUSTIFICATION: [2-3 sentences explaining your reasoning]
GATE_1_EVIDENCE: [Quote specific text or state "No specific evidence"]

GATE_2_ANSWER: [YES or NO]
GATE_2_JUSTIFICATION: [2-3 sentences]
GATE_2_EVIDENCE: [Quote or state "No specific evidence"]

GATE_3_ANSWER: [YES or NO]
GATE_3_JUSTIFICATION: [2-3 sentences]
GATE_3_EVIDENCE: [Quote or state "No specific evidence"]

GATE_4_ANSWER: [YES or NO]
GATE_4_JUSTIFICATION: [2-3 sentences]
GATE_4_EVIDENCE: [Quote or state "No specific evidence"]

GATE_5_ANSWER: [YES or NO]
GATE_5_JUSTIFICATION: [2-3 sentences]
GATE_5_EVIDENCE: [Quote or state "No specific evidence"]

Be rigorous and conservative. When in doubt, the segment should FAIL the gate.
"""

        for attempt in range(self.max_retries):
            try:
                client = self._get_client()
                response = client.models.generate_content(
                    model='gemini-2.5-pro',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.3,
                        top_p=0.9,
                        candidate_count=1
                    )
                )

                if not response.text:
                    raise ValueError("Empty response from Gemini")

                self._debug_api_calls.append({
                    'gate': 'consolidated',
                    'timestamp': datetime.now().isoformat(),
                    'prompt_length': len(prompt),
                    'response_length': len(response.text),
                    'attempt': attempt + 1,
                    'success': True
                })

                return self._parse_consolidated_response(response.text)

            except Exception as e:
                logger.warning(f"Consolidated evaluation attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 * (attempt + 1))
                else:
                    return None

    def _parse_consolidated_response(self, response_text: str):
        """Parse consolidated gate response into individual gate results."""
        gate_results = {}
        first_failure = None
        lines = response_text.strip().split('\n')

        gate_names = [g[0] for g in self.GATES]

        for gate_idx in range(1, 6):
            gate_name = gate_names[gate_idx - 1]
            answer = None
            justification = ""
            evidence = ""

            for line in lines:
                line_stripped = line.strip()
                prefix_answer = f"GATE_{gate_idx}_ANSWER:"
                prefix_just = f"GATE_{gate_idx}_JUSTIFICATION:"
                prefix_ev = f"GATE_{gate_idx}_EVIDENCE:"

                if line_stripped.startswith(prefix_answer):
                    answer_text = line_stripped[len(prefix_answer):].strip().upper()
                    answer = 'YES' in answer_text
                elif line_stripped.startswith(prefix_just):
                    justification = line_stripped[len(prefix_just):].strip()
                elif line_stripped.startswith(prefix_ev):
                    evidence = line_stripped[len(prefix_ev):].strip()

            # Fallback: if couldn't parse, conservative rejection
            if answer is None:
                answer = False
                justification = f"Could not parse gate {gate_idx} answer from response"

            gate_results[gate_name] = {
                'passed': answer,
                'justification': justification,
                'evidence': evidence
            }

            if not answer and first_failure is None:
                first_failure = gate_name

        return gate_results, first_failure

    def _extract_segment_content(self, segment: Dict) -> str:
        """Extract readable content from segment for gate evaluation."""
        parts = []

        # Add title if available
        if 'narrativeSegmentTitle' in segment:
            parts.append(f"TITLE: {segment['narrativeSegmentTitle']}")

        # Add context description
        if 'clipContextDescription' in segment:
            parts.append(f"CONTEXT: {segment['clipContextDescription']}")

        # Add upstream analysis metadata if available
        if 'harm_category' in segment:
            parts.append(f"HARM CATEGORY: {segment['harm_category']}")
        if 'identified_rhetorical_strategies' in segment:
            strategies = segment['identified_rhetorical_strategies']
            if isinstance(strategies, list):
                strategies = ', '.join(strategies)
            parts.append(f"RHETORICAL STRATEGIES: {strategies}")
        if 'potential_societal_impacts' in segment:
            impacts = segment['potential_societal_impacts']
            if isinstance(impacts, list):
                impacts = ', '.join(impacts)
            parts.append(f"POTENTIAL SOCIETAL IMPACTS: {impacts}")
        if 'brief_reasoning_for_classification' in segment:
            parts.append(f"CLASSIFICATION REASONING: {segment['brief_reasoning_for_classification']}")

        # Add quotes from suggestedClip
        if 'suggestedClip' in segment:
            parts.append("QUOTES:")
            for clip in segment['suggestedClip']:
                speaker = clip.get('speaker', 'Unknown')
                quote = clip.get('quote', '')
                timestamp = clip.get('timestamp', '')
                parts.append(f"  [{timestamp}] {speaker}: \"{quote}\"")

        return "\n".join(parts)

    def _save_results(
        self,
        passed_segments: List[Dict],
        rejected_segments: List[Dict],
        metadata: Dict,
        output_path: str
    ) -> None:
        """Save filtering results to files."""
        try:
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # Save passed segments (main output)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(passed_segments, f, indent=2, ensure_ascii=False)
            logger.info(f"Passed segments saved to: {output_path}")

            # Save full results to Quality_Control directory
            qc_dir = os.path.join(output_dir, 'Quality_Control')
            if not os.path.exists(qc_dir):
                os.makedirs(qc_dir)

            # All filter results
            all_results_path = os.path.join(qc_dir, 'binary_filter_all_results.json')
            all_results_data = {
                'metadata': metadata,
                'passed_segments': [s.get('binary_filter_results', {}) for s in passed_segments],
                'rejected_segments': [s.get('binary_filter_results', {}) for s in rejected_segments]
            }
            with open(all_results_path, 'w', encoding='utf-8') as f:
                json.dump(all_results_data, f, indent=2, ensure_ascii=False)
            logger.info(f"All filter results saved to: {all_results_path}")

            # Save rejected segments for analysis
            rejected_path = os.path.join(qc_dir, 'rejected_segments.json')
            with open(rejected_path, 'w', encoding='utf-8') as f:
                json.dump(rejected_segments, f, indent=2, ensure_ascii=False)
            logger.info(f"Rejected segments saved to: {rejected_path}")

            # Save API debug info
            debug_path = os.path.join(qc_dir, 'binary_filter_api_debug.json')
            with open(debug_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'total_api_calls': len(self._debug_api_calls),
                    'calls': self._debug_api_calls
                }, f, indent=2, ensure_ascii=False)
            logger.info(f"API debug info saved to: {debug_path}")

        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            raise


def main():
    """Main function for command-line usage."""
    if len(sys.argv) < 2:
        print("Usage: python binary_segment_filter.py <input_file> [output_file]")
        print("  input_file: Pass 1 analysis results (JSON)")
        print("  output_file: Optional output path for passed segments")
        sys.exit(1)

    input_file = sys.argv[1]

    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}_binary_filtered.json"

    try:
        # Load input segments
        with open(input_file, 'r', encoding='utf-8') as f:
            segments = json.load(f)

        # Initialize filter
        filter_instance = BinarySegmentFilter()

        # Run filtering
        passed, rejected, metadata = filter_instance.filter_segments(
            segments=segments,
            output_path=output_file
        )

        print(f"\nBinary Segment Filtering Complete!")
        print(f"  Total segments: {metadata['total_segments']}")
        print(f"  Passed: {metadata['passed_count']}")
        print(f"  Rejected: {metadata['rejected_count']}")
        print(f"  Pass rate: {metadata['pass_rate']:.1%}")
        print(f"\nResults saved to: {output_file}")

    except Exception as e:
        logger.error(f"Binary filtering failed: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
