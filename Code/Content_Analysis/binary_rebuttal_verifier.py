"""
Binary Rebuttal Verifier - Self-Correcting Rebuttal Verification

This module replaces numeric threshold-based rebuttal verification with a
binary gate system that includes automatic rewriting and re-verification loops.

Gates:
1. ACCURACY - Is every factual claim in this rebuttal verifiably accurate?
2. COMPLETENESS - Does this rebuttal address all key false claims?
3. SOURCES - Are counter-claims backed by credible sources?
4. CLARITY - Would a general audience understand this?

Self-correction: If any gate fails, the rebuttal is automatically rewritten
targeting the specific failure, then re-verified through ALL gates.
Maximum 3 iterations per rebuttal.

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
from dataclasses import dataclass, field
from google import genai
from google.genai import types

# Global client for Gemini API
_gemini_client = None

# Add paths for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
utils_dir = os.path.join(current_dir, '..', 'Utils')
sys.path.append(utils_dir)

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
    specific_issues: List[str] = field(default_factory=list)


@dataclass
class VerificationResult:
    """Result from verifying a single rebuttal."""
    section_id: str
    passed: bool
    iterations: int
    final_content: str
    gate_results: Dict[str, Dict]
    warning: Optional[str] = None
    rewrite_history: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "section_id": self.section_id,
            "passed": self.passed,
            "iterations": self.iterations,
            "gate_results": self.gate_results,
            "warning": self.warning,
            "rewrite_count": len(self.rewrite_history)
        }


def get_rebuttal_word_limit(clip_duration: float, config: Dict) -> int:
    """Look up max_words from proportionality tier config based on clip duration.

    Args:
        clip_duration: Clip duration in seconds
        config: Full pipeline config dictionary

    Returns:
        Maximum word count for the rebuttal
    """
    proportionality = config.get('quality_control', {}).get('rebuttal_proportionality', {})
    if not proportionality.get('enabled', False):
        # Fall back to flat max
        return config.get('quality_control', {}).get('rebuttal_length', {}).get('max_words', 500)

    tiers = proportionality.get('tiers', [])
    for tier in tiers:
        if clip_duration <= tier.get('max_clip_seconds', 999):
            return tier.get('max_words', 500)

    # If duration exceeds all tiers, use the last tier's limit
    if tiers:
        return tiers[-1].get('max_words', 600)
    return 500


class BinaryRebuttalVerifier:
    """
    4-gate verification system with automatic rewriting for rebuttals.

    Replaces numeric 1-10 scoring with binary pass/fail decisions.
    Implements self-correction loop: fail -> rewrite -> re-verify.
    """

    # Define the 4 gates for rebuttal verification
    GATES = [
        (
            "accuracy",
            "Is every factual claim in this rebuttal verifiably accurate?",
            "Check for specific facts, statistics, and claims. Verify against known scientific consensus. Flag any unsupported or potentially false statements."
        ),
        (
            "completeness",
            "Does this rebuttal address all the key false claims from the original segment?",
            "Compare the rebuttal to the claims in the video segment. Ensure no major misinformation is left unaddressed. Minor points can be skipped but core claims must be countered. NOTE: A rebuttal that acknowledges a valid underlying point before showing how the guest overextends or distorts it is COMPLETE — steelmanning strengthens the analysis, it does not indicate a missed claim."
        ),
        (
            "sources",
            "Are the counter-claims backed by credible, verifiable sources?",
            "Look for references to studies, expert opinions, official data, or established facts. Vague claims like 'studies show' without specifics should fail. Named sources or specific citations pass."
        ),
        (
            "clarity",
            "Would a general audience understand this rebuttal without specialized knowledge?",
            "Check for jargon, overly complex explanations, or assumed knowledge. The rebuttal should be accessible to viewers of the original content."
        ),
    ]

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the BinaryRebuttalVerifier.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._configure_gemini()

        # Configuration
        qc_rebuttal = self.config.get('quality_control', {}).get('rebuttal_verification', {})
        self.max_iterations = qc_rebuttal.get('max_correction_iterations', self.config.get('max_iterations', 3))
        self.api_delay = self.config.get('api_delay', 2)
        self.max_retries = self.config.get('max_retries', 3)

        # Temperature increases slightly each iteration for variety
        self.base_temperature = 0.4

        # Debug storage
        self._debug_api_calls = []
        self._all_verification_results = []

    def _load_persona(self) -> str:
        """Load the canonical persona definition from file."""
        persona_path = os.path.join(current_dir, 'Generation_Templates', 'persona_definition.txt')
        try:
            with open(persona_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            logger.error(f"Error loading persona definition: {e}")
            raise

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

    def verify_script_rebuttals(
        self,
        script_data: Dict,
        output_path: Optional[str] = None
    ) -> Tuple[Dict, Dict]:
        """
        Verify and improve all rebuttals in a unified script.

        Args:
            script_data: Unified podcast script data
            output_path: Optional path to save verified script

        Returns:
            Tuple of (verified_script_data, verification_metadata)
        """
        logger.info("=== BINARY REBUTTAL VERIFICATION STARTED ===")

        # Extract post_clip sections (rebuttals)
        post_clips = self._extract_post_clips(script_data)

        if not post_clips:
            logger.warning("No post_clip sections found")
            return script_data, {"rebuttals_verified": 0}

        logger.info(f"Found {len(post_clips)} rebuttals to verify")

        # Verify each rebuttal with self-correction loop
        verified_sections = {}
        total_rewrites = 0

        for i, post_clip in enumerate(post_clips):
            section_id = post_clip.get('section_id', f'post_clip_{i}')
            clip_reference = post_clip.get('clip_reference', '')

            # Find the associated video_clip for context
            video_clip = self._find_associated_clip(script_data, clip_reference)

            logger.info(f"Verifying rebuttal {i+1}/{len(post_clips)}: {section_id}")

            result = self.verify_with_correction(
                rebuttal=post_clip,
                video_clip=video_clip
            )

            self._all_verification_results.append(result)
            verified_sections[section_id] = result

            if result.warning:
                logger.warning(f"  {section_id}: {result.warning}")
            else:
                logger.info(f"  PASSED after {result.iterations} iteration(s)")

            total_rewrites += len(result.rewrite_history)

            # Rate limiting
            if i < len(post_clips) - 1:
                time.sleep(self.api_delay)

        # Update script with verified rebuttals
        verified_script = self._update_script_with_verified(script_data, verified_sections)

        metadata = {
            'verification_timestamp': datetime.now().isoformat(),
            'rebuttals_verified': len(post_clips),
            'total_rewrites': total_rewrites,
            'fully_passed': sum(1 for r in verified_sections.values() if r.passed and not r.warning),
            'passed_with_warnings': sum(1 for r in verified_sections.values() if r.warning),
            'gates_used': [g[0] for g in self.GATES],
            'max_iterations': self.max_iterations
        }

        logger.info("=== BINARY REBUTTAL VERIFICATION COMPLETE ===")
        logger.info(f"Results: {metadata['fully_passed']} passed, {metadata['passed_with_warnings']} with warnings")
        logger.info(f"Total rewrites performed: {total_rewrites}")

        if output_path:
            self._save_results(verified_script, metadata, verified_sections, output_path)

        return verified_script, metadata

    def _get_clip_duration(self, video_clip: Optional[Dict]) -> Optional[float]:
        """Extract clip duration in seconds from video_clip metadata."""
        if not video_clip:
            return None
        try:
            start = float(video_clip.get('start_time', 0))
            end = float(video_clip.get('end_time', 0))
            duration = end - start
            return duration if duration > 0 else None
        except (ValueError, TypeError):
            return None

    def _truncate_to_word_limit(self, text: str, max_words: int) -> Tuple[str, bool]:
        """Truncate text at last complete sentence within word limit.

        Returns:
            Tuple of (truncated_text, was_truncated)
        """
        words = text.split()
        if len(words) <= max_words:
            return text, False

        # Take first max_words words
        truncated = ' '.join(words[:max_words])

        # Find last sentence boundary (. ! ?)
        last_period = max(
            truncated.rfind('. '),
            truncated.rfind('! '),
            truncated.rfind('? '),
            truncated.rfind('."'),
            truncated.rfind('!"'),
            truncated.rfind('?"'),
        )

        # Also check if the truncated text ends at a sentence boundary
        if truncated.rstrip().endswith(('.', '!', '?', '."', '!"', '?"')):
            return truncated.rstrip(), True

        if last_period > len(truncated) * 0.5:
            # Cut at the last sentence boundary if it's past halfway
            truncated = truncated[:last_period + 1].rstrip()
        else:
            # Otherwise just cut at the word limit
            truncated = truncated.rstrip()

        return truncated, True

    def verify_with_correction(
        self,
        rebuttal: Dict,
        video_clip: Optional[Dict] = None
    ) -> VerificationResult:
        """
        Verify a rebuttal with self-correction loop.

        Args:
            rebuttal: Post_clip section containing the rebuttal
            video_clip: Optional associated video clip for context

        Returns:
            VerificationResult with final content and gate results
        """
        section_id = rebuttal.get('section_id', 'unknown')
        current_content = rebuttal.get('script_content', '')
        rewrite_history = []

        # Calculate proportional word limit based on clip duration
        clip_duration = self._get_clip_duration(video_clip)
        word_limit = get_rebuttal_word_limit(
            clip_duration or 90,  # default to 90s if unknown
            self.config
        )
        length_config = self.config.get('quality_control', {}).get('rebuttal_length', {})
        enforce_hard_limit = length_config.get('enforce_hard_limit', True)
        max_growth_percent = length_config.get('max_growth_percent', 15)

        if clip_duration:
            logger.info(f"  Clip duration: {clip_duration:.0f}s — word limit: {word_limit}")

        for iteration in range(self.max_iterations):
            logger.debug(f"  Iteration {iteration + 1}/{self.max_iterations}")

            # Evaluate all gates in single consolidated call — adjust
            # COMPLETENESS context for short clips
            gate_results, first_failure, failure_justification = self._evaluate_all_gates(
                current_content, video_clip, clip_duration=clip_duration
            )

            # Check if all gates passed
            if first_failure is None:
                # Apply hard word limit on final passing content
                if enforce_hard_limit:
                    current_content, was_truncated = self._truncate_to_word_limit(
                        current_content, word_limit
                    )
                    if was_truncated:
                        logger.info(f"  Truncated passing rebuttal to {word_limit} word limit")

                return VerificationResult(
                    section_id=section_id,
                    passed=True,
                    iterations=iteration + 1,
                    final_content=current_content,
                    gate_results=gate_results,
                    rewrite_history=rewrite_history
                )

            # If this is the last iteration, return with warning
            if iteration == self.max_iterations - 1:
                # Still enforce hard limit even on failed rebuttals
                if enforce_hard_limit:
                    current_content, _ = self._truncate_to_word_limit(
                        current_content, word_limit
                    )

                return VerificationResult(
                    section_id=section_id,
                    passed=False,
                    iterations=self.max_iterations,
                    final_content=current_content,
                    gate_results=gate_results,
                    warning=f"Max iterations reached. Failed gate: {first_failure}",
                    rewrite_history=rewrite_history
                )

            # Track word count before rewrite
            original_word_count = len(current_content.split())

            # Perform targeted rewrite with length constraint
            logger.debug(f"  Rewriting to fix: {first_failure}")

            new_content = self._targeted_rewrite(
                current_content=current_content,
                failed_gate=first_failure,
                failure_reason=failure_justification,
                specific_issues=gate_results[first_failure].get('specific_issues', []),
                video_clip=video_clip,
                iteration=iteration,
                word_limit=word_limit,
                clip_duration=clip_duration,
            )

            # Post-rewrite enforcement
            rewritten_word_count = len(new_content.split())
            was_truncated = False

            if enforce_hard_limit and rewritten_word_count > word_limit:
                new_content, was_truncated = self._truncate_to_word_limit(
                    new_content, word_limit
                )
                rewritten_word_count = len(new_content.split())

            growth_percent = (
                ((rewritten_word_count - original_word_count) / original_word_count * 100)
                if original_word_count > 0 else 0
            )

            rewrite_history.append({
                'iteration': iteration + 1,
                'failed_gate': first_failure,
                'failure_reason': failure_justification,
                'original_content': current_content[:200] + "..." if len(current_content) > 200 else current_content,
                'original_word_count': original_word_count,
                'rewritten_word_count': rewritten_word_count,
                'growth_percent': round(growth_percent, 1),
                'was_truncated': was_truncated,
                'word_limit': word_limit,
            })

            current_content = new_content
            time.sleep(self.api_delay)

        # Should not reach here, but just in case
        return VerificationResult(
            section_id=section_id,
            passed=False,
            iterations=self.max_iterations,
            final_content=current_content,
            gate_results=gate_results,
            warning="Verification loop exited unexpectedly",
            rewrite_history=rewrite_history
        )

    def _evaluate_all_gates(
        self,
        rebuttal_content: str,
        video_clip: Optional[Dict],
        clip_duration: Optional[float] = None,
    ):
        """
        Evaluate rebuttal against all 4 gates in a single API call.

        Returns:
            Tuple of (gate_results_dict, first_failed_gate_name_or_None, failure_justification)
        """
        # Build context from video clip if available
        clip_context = ""
        if video_clip:
            clip_context = f"""
## ORIGINAL CLAIMS BEING REBUTTED
Title: {video_clip.get('title', 'Unknown')}
Key Claims: {json.dumps(video_clip.get('key_claims', []))}
"""
            if 'suggestedClip' in video_clip:
                clip_context += "\nQuotes:\n"
                for clip in video_clip.get('suggestedClip', []):
                    quote = clip.get('quote', '')
                    if len(quote) > 500:
                        quote = quote[:500] + "..."
                    clip_context += f"  - {clip.get('speaker', 'Unknown')}: \"{quote}\"\n"

        # Build gate descriptions, adjusting COMPLETENESS for short clips
        gate_descriptions = ""
        for i, (gate_name, gate_question, gate_guidance) in enumerate(self.GATES, 1):
            guidance = gate_guidance
            if gate_name == 'completeness' and clip_duration and clip_duration < 30:
                guidance += (
                    " NOTE: This is a SHORT clip (<30s). Completeness means addressing "
                    "the CORE claim concisely, not exhaustively covering every detail. "
                    "A focused, brief rebuttal is expected."
                )
            gate_descriptions += f"""
## GATE {i}: {gate_name.upper()}
**Question:** {gate_question}
**Guidance:** {guidance}
"""

        prompt = f"""You are verifying rebuttal content for a media literacy project.

Evaluate the rebuttal below against ALL 4 gates. Each gate MUST consider the results of prior gates.

{gate_descriptions}
{clip_context}

## REBUTTAL CONTENT TO VERIFY
{rebuttal_content}

## INSTRUCTIONS
For EACH gate, provide your evaluation in this EXACT format:

GATE_1_ANSWER: [YES or NO]
GATE_1_JUSTIFICATION: [2-3 sentences explaining your reasoning]
GATE_1_SPECIFIC_ISSUES: [Comma-separated list of specific problems, or "None"]

GATE_2_ANSWER: [YES or NO]
GATE_2_JUSTIFICATION: [2-3 sentences]
GATE_2_SPECIFIC_ISSUES: [Problems or "None"]

GATE_3_ANSWER: [YES or NO]
GATE_3_JUSTIFICATION: [2-3 sentences]
GATE_3_SPECIFIC_ISSUES: [Problems or "None"]

GATE_4_ANSWER: [YES or NO]
GATE_4_JUSTIFICATION: [2-3 sentences]
GATE_4_SPECIFIC_ISSUES: [Problems or "None"]

Be rigorous. Weak or unsupported claims should FAIL. We want high-quality rebuttals.
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
                    'type': 'consolidated_gate_evaluation',
                    'timestamp': datetime.now().isoformat(),
                    'success': True
                })

                return self._parse_consolidated_gate_response(response.text)

            except Exception as e:
                logger.warning(f"Consolidated gate evaluation attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 * (attempt + 1))
                else:
                    # Return all-failed result
                    gate_results = {}
                    for gate_name, _, _ in self.GATES:
                        gate_results[gate_name] = {
                            'passed': False,
                            'justification': f"Evaluation failed: {str(e)}",
                            'specific_issues': ["API error - conservative rejection"]
                        }
                    return gate_results, self.GATES[0][0], f"API error: {str(e)}"

    def _parse_consolidated_gate_response(self, response_text: str):
        """Parse consolidated gate response into individual results."""
        gate_results = {}
        first_failure = None
        failure_justification = None
        lines = response_text.strip().split('\n')

        gate_names = [g[0] for g in self.GATES]

        for gate_idx in range(1, len(self.GATES) + 1):
            gate_name = gate_names[gate_idx - 1]
            answer = None
            justification = ""
            specific_issues = []

            for line in lines:
                line_stripped = line.strip()
                prefix_answer = f"GATE_{gate_idx}_ANSWER:"
                prefix_just = f"GATE_{gate_idx}_JUSTIFICATION:"
                prefix_issues = f"GATE_{gate_idx}_SPECIFIC_ISSUES:"

                if line_stripped.startswith(prefix_answer):
                    answer_text = line_stripped[len(prefix_answer):].strip().upper()
                    answer = 'YES' in answer_text
                elif line_stripped.startswith(prefix_just):
                    justification = line_stripped[len(prefix_just):].strip()
                elif line_stripped.startswith(prefix_issues):
                    issues_text = line_stripped[len(prefix_issues):].strip()
                    if issues_text.lower() != 'none':
                        specific_issues = [i.strip() for i in issues_text.split(',') if i.strip()]

            if answer is None:
                answer = False
                justification = f"Could not parse gate {gate_idx} answer"

            gate_results[gate_name] = {
                'passed': answer,
                'justification': justification,
                'specific_issues': specific_issues
            }

            if not answer and first_failure is None:
                first_failure = gate_name
                failure_justification = justification

        return gate_results, first_failure, failure_justification

    def _targeted_rewrite(
        self,
        current_content: str,
        failed_gate: str,
        failure_reason: str,
        specific_issues: List[str],
        video_clip: Optional[Dict],
        iteration: int,
        word_limit: int = 500,
        clip_duration: Optional[float] = None,
    ) -> str:
        """Rewrite rebuttal targeting the specific failed gate."""

        # Increase temperature slightly each iteration for more variety
        temperature = min(0.7, self.base_temperature + (iteration * 0.1))

        issues_str = "\n".join(f"- {issue}" for issue in specific_issues) if specific_issues else "See justification above"

        clip_context = ""
        if video_clip:
            clip_context = f"""
## CLAIMS TO REBUT
{json.dumps(video_clip.get('key_claims', []), indent=2)}
"""

        # Calculate allowed max: tighter of growth cap and tier limit
        current_word_count = len(current_content.split())
        max_growth = self.config.get('quality_control', {}).get('rebuttal_length', {}).get('max_growth_percent', 15)
        allowed_max = min(
            int(current_word_count * (1 + max_growth / 100)),
            word_limit
        )

        # Build duration context string
        duration_context = ""
        if clip_duration:
            duration_context = f"\nThis clip is {clip_duration:.0f}s — target rebuttal: {word_limit} words max."

        persona = self._load_persona()
        prompt = f"""You are Alternative Media Literacy, rewriting a rebuttal to fix a specific quality issue while maintaining your signature voice.

## YOUR CHARACTER VOICE
{persona}

## FAILED QUALITY CHECK: {failed_gate.upper()}

## FAILURE REASON
{failure_reason}

## SPECIFIC ISSUES TO FIX
{issues_str}

## CURRENT REBUTTAL (needs improvement)
{current_content}
{clip_context}

## REWRITING INSTRUCTIONS
1. MAINTAIN YOUR VOICE: Keep the snarky, sharp, entertaining tone throughout. Don't sanitize the personality out of it.
2. Specifically address the {failed_gate} issue identified above
3. If accuracy is the issue: Add specific sources, correct any errors, use verifiable facts - but deliver them with your characteristic wit
4. If completeness is the issue: Address all major claims, don't skip important points - make each takedown count
5. If sources is the issue: Search for and cite REAL, SPECIFIC sources - name actual studies with years (e.g., "a 2023 study in The Lancet"), real experts with credentials (e.g., "Doctor Jane Smith, epidemiologist at Johns Hopkins"), or official organizations with specific reports. NO vague references like "studies show" or "experts say". Weave sources naturally into your commentary.
6. If clarity is the issue: Simplify language, explain jargon, use concrete examples - but keep the snark
7. Maintain TTS-friendly formatting (no abbreviations, spell out numbers, no periods in names like "Dr.")

STRICT LENGTH LIMIT: Your rewrite must be {allowed_max} words or fewer.
Current rebuttal: {current_word_count} words. Maximum allowed: {allowed_max} words.
If you add sources or address completeness, CUT less important material to stay within limits.
Brevity is a feature.{duration_context}

## OUTPUT
Write ONLY the improved rebuttal content in your Alternative Media Literacy voice. No explanations or meta-commentary.
"""

        for attempt in range(self.max_retries):
            try:
                client = self._get_client()

                # Use Google Search grounding when fixing sources gate
                # This allows Gemini to find real studies, experts, and citations
                if failed_gate == "sources":
                    logger.info("  Using Google Search to find real sources...")
                    print(f"      Using Google Search to find real sources...", flush=True)
                    config = types.GenerateContentConfig(
                        temperature=temperature,
                        top_p=0.9,
                        candidate_count=1,
                        tools=[types.Tool(google_search=types.GoogleSearch())]
                    )
                else:
                    config = types.GenerateContentConfig(
                        temperature=temperature,
                        top_p=0.9,
                        candidate_count=1
                    )

                response = client.models.generate_content(
                    model='gemini-2.5-pro',
                    contents=prompt,
                    config=config
                )

                if not response.text:
                    raise ValueError("Empty response from Gemini")

                self._debug_api_calls.append({
                    'type': 'rewrite',
                    'failed_gate': failed_gate,
                    'iteration': iteration,
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'used_grounding': failed_gate == "sources"
                })

                return response.text.strip()

            except Exception as e:
                logger.warning(f"Rewrite attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 * (attempt + 1))
                else:
                    logger.error(f"Rewrite failed after {self.max_retries} attempts")
                    return current_content  # Return original on failure

    def _extract_post_clips(self, script_data: Dict) -> List[Dict]:
        """Extract post_clip sections from script."""
        post_clips = []
        for section in script_data.get('podcast_sections', []):
            if section.get('section_type') == 'post_clip':
                post_clips.append(section)
        return post_clips

    def _find_associated_clip(self, script_data: Dict, clip_reference: str) -> Optional[Dict]:
        """Find the video_clip associated with a post_clip."""
        for section in script_data.get('podcast_sections', []):
            if section.get('section_type') == 'video_clip':
                if section.get('clip_id') == clip_reference:
                    return section
        return None

    def _update_script_with_verified(
        self,
        script_data: Dict,
        verified_sections: Dict[str, VerificationResult]
    ) -> Dict:
        """Update script with verified/rewritten rebuttal content."""
        updated_script = script_data.copy()
        updated_sections = []

        for section in script_data.get('podcast_sections', []):
            section_copy = section.copy()

            if section.get('section_type') == 'post_clip':
                section_id = section.get('section_id')
                if section_id in verified_sections:
                    result = verified_sections[section_id]
                    # Update content with final verified version
                    section_copy['script_content'] = result.final_content
                    # Flag sections that failed verification
                    if not result.passed:
                        section_copy['_verification_failed'] = True

            updated_sections.append(section_copy)

        updated_script['podcast_sections'] = updated_sections
        return updated_script

    def _save_results(
        self,
        verified_script: Dict,
        metadata: Dict,
        verified_sections: Dict[str, VerificationResult],
        output_path: str
    ) -> None:
        """Save verification results."""
        try:
            output_dir = os.path.dirname(output_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # Save verified script (main output)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(verified_script, f, indent=2, ensure_ascii=False)
            logger.info(f"Verified script saved to: {output_path}")

            # Save verification details to Quality_Control
            qc_dir = os.path.join(output_dir, 'Quality_Control')
            if not os.path.exists(qc_dir):
                os.makedirs(qc_dir)

            # Verification results
            results_path = os.path.join(qc_dir, 'binary_rebuttal_verification_results.json')
            results_data = {
                'metadata': metadata,
                'section_results': {k: v.to_dict() for k, v in verified_sections.items()}
            }
            with open(results_path, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Verification results saved to: {results_path}")

            # API debug info
            debug_path = os.path.join(qc_dir, 'binary_rebuttal_api_debug.json')
            with open(debug_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'total_api_calls': len(self._debug_api_calls),
                    'calls': self._debug_api_calls
                }, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            raise


def main():
    """Main function for command-line usage."""
    if len(sys.argv) < 2:
        print("Usage: python binary_rebuttal_verifier.py <input_script> [output_script]")
        print("  input_script: Unified podcast script (JSON)")
        print("  output_script: Optional output path for verified script")
        sys.exit(1)

    input_file = sys.argv[1]

    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}_verified.json"

    try:
        # Load input script
        with open(input_file, 'r', encoding='utf-8') as f:
            script_data = json.load(f)

        # Initialize verifier
        verifier = BinaryRebuttalVerifier()

        # Run verification
        verified_script, metadata = verifier.verify_script_rebuttals(
            script_data=script_data,
            output_path=output_file
        )

        print(f"\nBinary Rebuttal Verification Complete!")
        print(f"  Rebuttals verified: {metadata['rebuttals_verified']}")
        print(f"  Total rewrites: {metadata['total_rewrites']}")
        print(f"  Fully passed: {metadata['fully_passed']}")
        print(f"  Passed with warnings: {metadata['passed_with_warnings']}")
        print(f"\nVerified script saved to: {output_file}")

    except Exception as e:
        logger.error(f"Verification failed: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
