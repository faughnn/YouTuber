"""
Recent Events Verifier - Web Search Verification for Date-Sensitive Claims

This module verifies claims about recent events (deaths, assassinations, elections,
legislation, etc.) using web search to prevent false fact-checks based on outdated
AI training data.

Pipeline Position: Runs AFTER Binary Segment Filtering, BEFORE Script Generation

Author: Claude Code
Created: 2024-12-29
"""

import os
import re
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, field

# Try to import google.genai for Gemini with grounding
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """Result of a single claim verification"""
    claim_text: str
    claim_type: str  # 'death', 'assassination', 'election', 'legislation', 'event'
    original_assessment: str  # What the AI originally said
    verified_status: str  # 'CONFIRMED_TRUE', 'CONFIRMED_FALSE', 'UNVERIFIED', 'NEEDS_REVIEW'
    search_evidence: str  # Summary of web search findings
    sources: List[str] = field(default_factory=list)
    confidence: float = 0.0  # 0.0 to 1.0


@dataclass
class VerificationReport:
    """Complete verification report for a segment"""
    segment_id: str
    total_claims_checked: int
    claims_confirmed_true: int
    claims_confirmed_false: int
    claims_unverified: int
    verification_results: List[VerificationResult] = field(default_factory=list)
    requires_correction: bool = False
    corrected_assessment: Optional[str] = None


class RecentEventsVerifier:
    """
    Verifies claims about recent events using web search.

    Prevents false fact-checks caused by AI knowledge cutoff dates.
    Uses Gemini with Google Search grounding for real-time verification.
    """

    # Keywords that indicate date-sensitive claims requiring verification
    DATE_SENSITIVE_KEYWORDS = {
        'death': ['died', 'dead', 'death', 'passed away', 'killed', 'deceased', 'funeral', 'obituary'],
        'assassination': ['assassinated', 'assassination', 'murdered', 'murder', 'shot dead', 'shooting'],
        'election': ['elected', 'won election', 'lost election', 'vote', 'ballot', 'primary', 'inaugurat'],
        'legislation': ['signed into law', 'passed bill', 'enacted', 'repealed', 'executive order'],
        'event': ['happened', 'occurred', 'took place', 'announced', 'resigned', 'appointed', 'fired']
    }

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Recent Events Verifier.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}

        # Initialize Gemini client with grounding capability
        api_key = self.config.get('api', {}).get('gemini_api_key') or os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in config or environment")

        if GENAI_AVAILABLE:
            self.client = genai.Client(api_key=api_key)
        else:
            raise ImportError("google.genai package not available")

        # Rate limiting
        self.api_delay = self.config.get('quality_control', {}).get('api_delay', 2)

        logger.info("RecentEventsVerifier initialized with Gemini grounding")

    def identify_date_sensitive_claims(self, segment: Dict) -> List[Dict]:
        """
        Identify claims in a segment that may be date-sensitive.

        Args:
            segment: Segment dictionary from analysis

        Returns:
            List of claims requiring verification
        """
        claims_to_verify = []

        # Get text content to scan
        text_fields = [
            segment.get('clipContextDescription', ''),
            segment.get('selection_reason', ''),
            segment.get('why_harmful', ''),
            segment.get('rebuttal', ''),
        ]

        # Also check suggested clips
        suggested_clips = segment.get('suggestedClip', [])
        for clip in suggested_clips:
            if isinstance(clip, dict):
                text_fields.append(clip.get('quote', ''))

        combined_text = ' '.join(text_fields).lower()

        # Check for date-sensitive keywords
        for claim_type, keywords in self.DATE_SENSITIVE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in combined_text:
                    # Extract the relevant claim context
                    claims_to_verify.append({
                        'type': claim_type,
                        'keyword': keyword,
                        'context': self._extract_claim_context(combined_text, keyword),
                        'segment_id': segment.get('segment_identifier', 'unknown')
                    })
                    break  # One match per type is enough

        return claims_to_verify

    def _extract_claim_context(self, text: str, keyword: str, window: int = 100) -> str:
        """Extract context around a keyword for verification."""
        idx = text.find(keyword)
        if idx == -1:
            return ""

        start = max(0, idx - window)
        end = min(len(text), idx + len(keyword) + window)

        return text[start:end].strip()

    def verify_claim_with_search(self, claim: Dict, segment: Dict) -> VerificationResult:
        """
        Verify a single claim using Gemini with Google Search grounding.

        Args:
            claim: Claim dictionary with type and context
            segment: Full segment for additional context

        Returns:
            VerificationResult with search findings
        """
        # Build verification query
        claim_context = claim.get('context', '')
        claim_type = claim.get('type', 'event')

        # Extract names and key details from the segment
        names = self._extract_names_from_segment(segment)

        verification_prompt = f"""You are a fact-checker verifying recent events. Use Google Search to verify the following claim.

CLAIM TYPE: {claim_type}
CLAIM CONTEXT: {claim_context}
NAMES MENTIONED: {', '.join(names) if names else 'None identified'}

TASK:
1. Search for recent news about this claim
2. Determine if the claimed event actually happened
3. Provide sources for your verification

RESPOND IN THIS EXACT JSON FORMAT:
{{
    "verified_status": "CONFIRMED_TRUE" or "CONFIRMED_FALSE" or "UNVERIFIED",
    "summary": "Brief summary of what you found",
    "key_facts": ["fact 1", "fact 2"],
    "sources": ["source 1 title/url", "source 2 title/url"],
    "confidence": 0.0 to 1.0
}}

Be extremely careful: If someone is reported as dead/murdered, verify this with multiple recent news sources before confirming."""

        try:
            # Use Gemini with Google Search grounding
            response = self.client.models.generate_content(
                model='gemini-2.5-pro',
                contents=verification_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                )
            )

            # Parse response
            response_text = response.text if hasattr(response, 'text') else str(response)

            # Extract JSON from response
            result_data = self._parse_verification_response(response_text)

            return VerificationResult(
                claim_text=claim_context,
                claim_type=claim_type,
                original_assessment=segment.get('why_harmful', ''),
                verified_status=result_data.get('verified_status', 'UNVERIFIED'),
                search_evidence=result_data.get('summary', ''),
                sources=result_data.get('sources', []),
                confidence=result_data.get('confidence', 0.0)
            )

        except Exception as e:
            logger.error(f"Verification failed for claim: {e}")
            return VerificationResult(
                claim_text=claim_context,
                claim_type=claim_type,
                original_assessment=segment.get('why_harmful', ''),
                verified_status='UNVERIFIED',
                search_evidence=f"Verification failed: {str(e)}",
                sources=[],
                confidence=0.0
            )

    def _extract_names_from_segment(self, segment: Dict) -> List[str]:
        """Extract person names from segment for search queries."""
        names = []

        # Check suggested clips for speaker names
        suggested_clips = segment.get('suggestedClip', [])
        for clip in suggested_clips:
            if isinstance(clip, dict):
                speaker = clip.get('speaker', '')
                if speaker and speaker not in names:
                    # Clean up speaker name (remove "Speaker 1:" type prefixes)
                    clean_name = re.sub(r'^(Speaker\s*\d+|SPEAKER\s*\d+):\s*', '', speaker).strip()
                    if clean_name and len(clean_name) > 2:
                        names.append(clean_name)

        # Also look for names in the context description
        context = segment.get('clipContextDescription', '')
        # Simple name extraction - look for capitalized words
        potential_names = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', context)
        for name in potential_names:
            if name not in names and len(name) > 3:
                names.append(name)

        return names[:5]  # Limit to top 5 names

    def _parse_verification_response(self, response_text: str) -> Dict:
        """Parse the verification response JSON."""
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

        # Fallback: try to extract key information
        result = {
            'verified_status': 'UNVERIFIED',
            'summary': response_text[:500] if response_text else '',
            'sources': [],
            'confidence': 0.0
        }

        # Check for confirmation keywords
        lower_text = response_text.lower()
        if 'confirmed' in lower_text and ('true' in lower_text or 'did happen' in lower_text or 'did occur' in lower_text):
            result['verified_status'] = 'CONFIRMED_TRUE'
            result['confidence'] = 0.7
        elif 'false' in lower_text or 'did not happen' in lower_text or 'no evidence' in lower_text:
            result['verified_status'] = 'CONFIRMED_FALSE'
            result['confidence'] = 0.7

        return result

    def verify_segments(
        self,
        segments: List[Dict],
        output_path: Optional[str] = None
    ) -> Tuple[List[Dict], Dict[str, Any]]:
        """
        Verify all segments for date-sensitive claims.

        Args:
            segments: List of segment dictionaries
            output_path: Optional path to save verification report

        Returns:
            Tuple of (updated_segments, verification_metadata)
        """
        logger.info(f"Starting recent events verification for {len(segments)} segments")

        verification_reports = []
        updated_segments = []

        total_claims_checked = 0
        total_corrections = 0

        for segment in segments:
            segment_id = segment.get('segment_identifier', 'unknown')

            # Identify date-sensitive claims
            claims = self.identify_date_sensitive_claims(segment)

            if not claims:
                # No date-sensitive claims, pass through unchanged
                updated_segments.append(segment)
                continue

            logger.info(f"Segment {segment_id}: Found {len(claims)} date-sensitive claims to verify")

            # Verify each claim
            verification_results = []
            requires_correction = False

            for claim in claims:
                time.sleep(self.api_delay)  # Rate limiting

                result = self.verify_claim_with_search(claim, segment)
                verification_results.append(result)
                total_claims_checked += 1

                # Check if this verification contradicts the original assessment
                if result.verified_status == 'CONFIRMED_TRUE':
                    # The event DID happen - check if we incorrectly called it misinformation
                    original = segment.get('why_harmful', '').lower()
                    if 'false' in original or 'fabricat' in original or 'misinformation' in original:
                        requires_correction = True
                        logger.warning(f"CORRECTION NEEDED: Segment {segment_id} - Event confirmed TRUE but marked as misinformation")

            # Create verification report
            report = VerificationReport(
                segment_id=segment_id,
                total_claims_checked=len(verification_results),
                claims_confirmed_true=sum(1 for r in verification_results if r.verified_status == 'CONFIRMED_TRUE'),
                claims_confirmed_false=sum(1 for r in verification_results if r.verified_status == 'CONFIRMED_FALSE'),
                claims_unverified=sum(1 for r in verification_results if r.verified_status == 'UNVERIFIED'),
                verification_results=verification_results,
                requires_correction=requires_correction
            )

            verification_reports.append(report)

            # Update segment with verification data
            updated_segment = segment.copy()
            updated_segment['_verification'] = {
                'checked': True,
                'requires_correction': requires_correction,
                'claims_verified': len(verification_results),
                'results': [
                    {
                        'claim': r.claim_text[:100],
                        'status': r.verified_status,
                        'evidence': r.search_evidence[:200]
                    }
                    for r in verification_results
                ]
            }

            if requires_correction:
                total_corrections += 1
                # Mark segment for special handling - don't flag confirmed true events as misinformation
                updated_segment['_correction_needed'] = True
                updated_segment['_verified_events'] = [
                    r.claim_text for r in verification_results
                    if r.verified_status == 'CONFIRMED_TRUE'
                ]

            updated_segments.append(updated_segment)

        # Compile metadata
        metadata = {
            'total_segments': len(segments),
            'segments_with_date_sensitive_claims': len(verification_reports),
            'total_claims_checked': total_claims_checked,
            'corrections_needed': total_corrections,
            'timestamp': datetime.now().isoformat()
        }

        # Save report if path provided
        if output_path:
            report_data = {
                'metadata': metadata,
                'reports': [
                    {
                        'segment_id': r.segment_id,
                        'claims_checked': r.total_claims_checked,
                        'confirmed_true': r.claims_confirmed_true,
                        'confirmed_false': r.claims_confirmed_false,
                        'requires_correction': r.requires_correction,
                        'results': [
                            {
                                'claim': vr.claim_text,
                                'type': vr.claim_type,
                                'status': vr.verified_status,
                                'evidence': vr.search_evidence,
                                'confidence': vr.confidence
                            }
                            for vr in r.verification_results
                        ]
                    }
                    for r in verification_reports
                ]
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Verification report saved to: {output_path}")

        logger.info(f"Verification complete: {total_claims_checked} claims checked, {total_corrections} corrections needed")

        return updated_segments, metadata


def create_recent_events_verifier(config: Dict[str, Any] = None) -> RecentEventsVerifier:
    """Factory function to create RecentEventsVerifier instance."""
    return RecentEventsVerifier(config)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python recent_events_verifier.py <segments_json_path> [output_path]")
        sys.exit(1)

    segments_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    # Load segments
    with open(segments_path, 'r', encoding='utf-8') as f:
        segments = json.load(f)

    # Create verifier
    config = {'api': {'gemini_api_key': os.getenv('GEMINI_API_KEY')}}
    verifier = create_recent_events_verifier(config)

    # Run verification
    updated_segments, metadata = verifier.verify_segments(segments, output_path)

    print(f"\n✓ Verification complete")
    print(f"  Claims checked: {metadata['total_claims_checked']}")
    print(f"  Corrections needed: {metadata['corrections_needed']}")
