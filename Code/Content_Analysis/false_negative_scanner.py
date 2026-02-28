"""
False Negative Scanner - Recovery for Missed Content

This module scans rejected segments for potential false negatives - important
content that was incorrectly filtered out. Uses topic coverage analysis and
re-evaluation to recover missed segments.

Recovery Triggers:
1. Rejected segment covers a topic NOT in selected set
2. Segment failed only one gate and passed others strongly
3. High-severity keywords present in rejected content

Author: Claude Code
Created: 2024-12-28
Pipeline: Multi-Pass Quality Control System
"""

import os
import sys
import json
import logging
import re
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict

# Add paths for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from binary_segment_filter import BinarySegmentFilter
except ImportError:
    BinarySegmentFilter = None

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


class FalseNegativeScanner:
    """
    Scans rejected segments for potential false negatives.

    After binary filtering, some important content may be incorrectly rejected.
    This module identifies candidates for recovery based on:
    1. Topic coverage gaps in selected segments
    2. Near-misses (passed most gates, failed one)
    3. High-severity keyword matches
    """

    # High-severity keywords that indicate important content
    # Removed common words (million, billion, government, school, massive, widespread)
    # that cause too many false positives
    HIGH_SEVERITY_KEYWORDS = [
        'death', 'killed', 'murder', 'dangerous', 'lethal', 'fatal',
        'fraud', 'criminal', 'illegal', 'lawsuit', 'sued',
        'children', 'kids', 'hospital',
        'fda', 'cdc', 'who',
    ]

    def __init__(self, config: Optional[Dict] = None, skip_api_init: bool = False):
        """
        Initialize the FalseNegativeScanner.

        Args:
            config: Optional configuration dictionary
            skip_api_init: If True, skip API initialization (for testing)
        """
        self.config = config or {}
        qc_config = self.config.get('quality_control', {}).get('false_negative_recovery', {})

        self.enabled = qc_config.get('enabled', True)
        self.re_evaluate_uncovered = qc_config.get('re_evaluate_uncovered_topics', True)
        self.max_recovery = qc_config.get('max_recovery', 3)

        # Initialize segment filter for re-evaluation (skip API init for testing)
        if BinarySegmentFilter and not skip_api_init:
            try:
                self.segment_filter = BinarySegmentFilter(config, skip_api_init=skip_api_init)
            except Exception:
                self.segment_filter = None
        else:
            self.segment_filter = None

    def scan_rejected(
        self,
        rejected: List[Dict],
        selected: List[Dict]
    ) -> List[Dict]:
        """
        Scan rejected segments for false negatives.

        Args:
            rejected: List of segments that failed filtering
            selected: List of segments that passed filtering

        Returns:
            List of recovered segments to add to selection
        """
        if not self.enabled:
            logger.info("False negative scanning disabled")
            return []

        if not rejected:
            logger.info("No rejected segments to scan")
            return []

        logger.info(f"Scanning {len(rejected)} rejected segments for false negatives")
        print(f"  Scanning {len(rejected)} rejected segments for false negatives...", flush=True)

        candidates = []

        # Strategy 1: Find uncovered topics
        uncovered_candidates = self._find_uncovered_topic_candidates(rejected, selected)
        candidates.extend(uncovered_candidates)

        # Strategy 2: Find near-misses
        near_miss_candidates = self._find_near_miss_candidates(rejected)
        candidates.extend(near_miss_candidates)

        # Strategy 3: Find high-severity keyword matches
        keyword_candidates = self._find_keyword_candidates(rejected)
        candidates.extend(keyword_candidates)

        # Deduplicate candidates
        seen_ids = set()
        unique_candidates = []
        for candidate in candidates:
            seg_id = candidate.get('segment_id', id(candidate))
            if seg_id not in seen_ids:
                seen_ids.add(seg_id)
                unique_candidates.append(candidate)

        logger.info(f"Found {len(unique_candidates)} unique false negative candidates")
        print(f"  Found {len(unique_candidates)} candidates for re-evaluation", flush=True)

        # Re-evaluate candidates if segment filter is available
        if self.segment_filter and unique_candidates:
            recovered = self._re_evaluate_candidates(unique_candidates)
        else:
            # Without re-evaluation, take top candidates by score
            recovered = unique_candidates[:self.max_recovery]

        logger.info(f"Recovered {len(recovered)} false negatives")
        if recovered:
            print(f"  ✅ Recovered {len(recovered)} false negatives", flush=True)
        else:
            print(f"  No false negatives recovered", flush=True)
        return recovered

    def _find_uncovered_topic_candidates(
        self,
        rejected: List[Dict],
        selected: List[Dict]
    ) -> List[Dict]:
        """Find rejected segments covering topics not in selected set."""
        candidates = []

        # Extract topics from selected segments
        selected_topics = set()
        for segment in selected:
            topics = self._extract_topics(segment)
            selected_topics.update(topics)

        logger.debug(f"Selected topics: {selected_topics}")

        # Find rejected segments with uncovered topics
        for segment in rejected:
            segment_topics = set(self._extract_topics(segment))

            # Check for topics not covered by selected
            uncovered = segment_topics - selected_topics

            if uncovered:
                logger.debug(f"Found uncovered topics in rejected segment: {uncovered}")
                candidates.append({
                    **segment,
                    '_recovery_reason': 'uncovered_topic',
                    '_uncovered_topics': list(uncovered)
                })

        return candidates

    def _find_near_miss_candidates(self, rejected: List[Dict]) -> List[Dict]:
        """Find segments that almost passed (failed only one gate)."""
        candidates = []

        for segment in rejected:
            filter_results = segment.get('binary_filter_results', {})
            gate_results = filter_results.get('gate_results', {})

            if not gate_results:
                continue

            # Count passed gates
            passed_count = sum(1 for g in gate_results.values() if g.get('passed'))
            total_gates = len(gate_results)

            # If passed all but one gate, it's a near miss
            if passed_count == total_gates - 1:
                failed_gate = filter_results.get('failed_at', 'unknown')
                logger.debug(f"Near miss found: failed only {failed_gate}")

                candidates.append({
                    **segment,
                    '_recovery_reason': 'near_miss',
                    '_failed_gate': failed_gate
                })

        return candidates

    def _find_keyword_candidates(self, rejected: List[Dict]) -> List[Dict]:
        """Find rejected segments with high-severity keywords."""
        candidates = []

        for segment in rejected:
            text = self._get_segment_text(segment).lower()

            # Check for high-severity keywords
            matched_keywords = []
            for keyword in self.HIGH_SEVERITY_KEYWORDS:
                if re.search(r'\b' + re.escape(keyword) + r'\b', text):
                    matched_keywords.append(keyword)

            # If multiple high-severity keywords, consider for recovery
            if len(matched_keywords) >= 2:
                logger.debug(f"High-severity keywords found: {matched_keywords}")

                candidates.append({
                    **segment,
                    '_recovery_reason': 'high_severity_keywords',
                    '_matched_keywords': matched_keywords
                })

        return candidates

    def _re_evaluate_candidates(self, candidates: List[Dict]) -> List[Dict]:
        """Re-evaluate candidates with a relaxed 'second opinion' prompt."""
        recovered = []
        max_to_evaluate = min(len(candidates), self.max_recovery * 2)

        for i, candidate in enumerate(candidates[:max_to_evaluate], 1):
            if len(recovered) >= self.max_recovery:
                break

            segment_id = candidate.get('segment_id', 'unknown')
            segment_title = candidate.get('narrativeSegmentTitle', 'Unknown')
            recovery_reason = candidate.get('_recovery_reason', 'unknown')
            failed_gate = candidate.get('_failed_gate', candidate.get('binary_filter_results', {}).get('failed_at', 'unknown'))

            logger.info(f"Re-evaluating candidate: {segment_id}")
            print(f"  [{i}/{max_to_evaluate}] Re-evaluating: {segment_id}", flush=True)
            print(f"      Title: {segment_title}", flush=True)
            print(f"      Recovery reason: {recovery_reason}, failed: {failed_gate}", flush=True)

            # Use relaxed "second opinion" prompt instead of re-running identical gates
            should_recover = self._second_opinion_evaluate(candidate, failed_gate)

            if should_recover:
                logger.info(f"  Recovered via second opinion")
                print(f"    ✅ RECOVERED: second opinion approved", flush=True)
                candidate['binary_filter_results'] = {
                    'passed': True,
                    'recovered_via': 'second_opinion',
                    'original_failed_gate': failed_gate,
                    'recovery_reason': recovery_reason
                }
                recovered.append(candidate)
            else:
                logger.info(f"  Still rejected by second opinion")
                print(f"    ❌ Still rejected by second opinion", flush=True)

        return recovered

    def _second_opinion_evaluate(self, candidate: Dict, failed_gate: str) -> bool:
        """
        Get a 'second opinion' with a relaxed prompt that considers the full context
        of why this segment might be worth including despite failing one gate.
        """
        if not self.segment_filter:
            return False

        # Build segment text
        text_parts = []
        if 'narrativeSegmentTitle' in candidate:
            text_parts.append(f"Title: {candidate['narrativeSegmentTitle']}")
        if 'clipContextDescription' in candidate:
            text_parts.append(f"Context: {candidate['clipContextDescription']}")
        if 'suggestedClip' in candidate:
            for clip in candidate['suggestedClip']:
                text_parts.append(f"Quote: {clip.get('speaker', '')}: {clip.get('quote', '')}")

        segment_text = '\n'.join(text_parts)
        recovery_reason = candidate.get('_recovery_reason', 'unknown')

        prompt = f"""You are providing a SECOND OPINION on a segment that was rejected from a media literacy analysis.

This segment was flagged as a potential false negative — it may have been incorrectly filtered out.

## SEGMENT CONTENT
{segment_text}

## WHY IT WAS REJECTED
Failed gate: {failed_gate}

## WHY IT MIGHT BE IMPORTANT
Recovery trigger: {recovery_reason}

## YOUR TASK
Consider this segment with fresh eyes and a slightly more generous interpretation.
Should this segment be INCLUDED in a media literacy analysis? Consider:
- Does it contain content worth analyzing (misinformation, conspiracy theory, pseudoscience, societal damage rhetoric)?
- Would including it provide value to the audience?
- Was the original rejection possibly too strict?

Respond with:
ANSWER: [YES or NO]
REASONING: [2-3 sentences]
"""

        try:
            from google import genai
            from google.genai import types

            client = self.segment_filter._get_client()
            response = client.models.generate_content(
                model='gemini-2.5-pro',
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.4,
                    top_p=0.9,
                    candidate_count=1
                )
            )

            if response.text:
                return 'ANSWER: YES' in response.text.upper() or 'ANSWER:YES' in response.text.upper()
        except Exception as e:
            logger.warning(f"Second opinion evaluation failed: {e}")

        return False

    def _extract_topics(self, segment: Dict) -> List[str]:
        """Extract topic labels from segment content."""
        text = self._get_segment_text(segment).lower()

        # Simple keyword-based topic extraction
        topics = []

        topic_keywords = {
            'health': ['vaccine', 'health', 'medical', 'doctor', 'treatment', 'disease', 'covid'],
            'politics': ['election', 'vote', 'government', 'policy', 'political', 'president'],
            'media': ['media', 'news', 'journalist', 'mainstream', 'propaganda'],
            'science': ['science', 'research', 'study', 'scientist', 'data', 'climate'],
            'economics': ['economy', 'money', 'inflation', 'taxes', 'bank', 'financial'],
        }

        for topic, keywords in topic_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    topics.append(topic)
                    break

        return topics if topics else ['general']

    def _get_segment_text(self, segment: Dict) -> str:
        """Extract all text content from a segment."""
        parts = []

        if 'narrativeSegmentTitle' in segment:
            parts.append(segment['narrativeSegmentTitle'])

        if 'clipContextDescription' in segment:
            parts.append(segment['clipContextDescription'])

        if 'suggestedClip' in segment:
            for clip in segment['suggestedClip']:
                if 'quote' in clip:
                    parts.append(clip['quote'])

        return ' '.join(parts)


if __name__ == "__main__":
    # Simple test
    selected = [
        {'segment_id': '1', 'narrativeSegmentTitle': 'Vaccine safety claims'},
        {'segment_id': '2', 'narrativeSegmentTitle': 'Election fraud allegations'},
    ]

    rejected = [
        {
            'segment_id': '3',
            'narrativeSegmentTitle': 'Climate change denial',
            'binary_filter_results': {
                'passed': False,
                'failed_at': 'harm_assessment',
                'gate_results': {
                    'content_worth_rebutting': {'passed': True},
                    'verifiability': {'passed': True},
                    'accuracy_check': {'passed': True},
                    'harm_assessment': {'passed': False},
                    'rebuttability': {'passed': True}
                }
            }
        },
        {
            'segment_id': '4',
            'narrativeSegmentTitle': 'Random opinion about food',
            'binary_filter_results': {
                'passed': False,
                'failed_at': 'content_worth_rebutting',
                'gate_results': {
                    'content_worth_rebutting': {'passed': False}
                }
            }
        }
    ]

    scanner = FalseNegativeScanner()
    recovered = scanner.scan_rejected(rejected, selected)

    print(f"\nRecovered {len(recovered)} segments:")
    for seg in recovered:
        print(f"  - {seg['segment_id']}: {seg['narrativeSegmentTitle']}")
        print(f"    Reason: {seg.get('_recovery_reason', 'unknown')}")
