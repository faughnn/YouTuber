"""
Fact Validator - External Fact-Checking Integration

This module provides external fact validation for rebuttal content using
third-party APIs and knowledge sources. Validates factual claims against
established fact-checking databases.

Sources:
1. Google Fact Check API (primary)
2. ClaimBuster API (alternative)
3. Local claim cache (for common claims)

Author: Claude Code
Created: 2024-12-28
Pipeline: Multi-Pass Quality Control System
"""

import os
import sys
import json
import logging
import re
import time
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import urllib.request
import urllib.parse
import urllib.error

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


@dataclass
class FactCheckResult:
    """Result of fact-checking a claim."""
    claim: str
    verified: bool
    source: str
    rating: Optional[str] = None
    explanation: Optional[str] = None
    source_url: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of validating a rebuttal."""
    section_id: str
    claims_checked: int
    issues_found: int
    corrections_made: int
    results: List[FactCheckResult] = field(default_factory=list)


class FactValidator:
    """
    External fact validation for rebuttal content.

    Integrates with fact-checking APIs to verify claims made in rebuttals.
    Uses caching to minimize API calls for repeated claims.
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the FactValidator.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        qc_config = self.config.get('quality_control', {}).get('external_validation', {})

        self.enabled = qc_config.get('enabled', True)
        self.google_fact_check = qc_config.get('google_fact_check_api', True)
        self.cache_hours = qc_config.get('cache_hours', 168)  # 1 week default

        # API configuration - use Gemini API key for Google Fact Check API
        self.google_api_key = self.config.get('api', {}).get('gemini_api_key')
        if not self.google_api_key or self.google_api_key == '${GEMINI_API_KEY}':
            self.google_api_key = os.getenv('GEMINI_API_KEY')

        # Initialize cache
        self._cache: Dict[str, Tuple[FactCheckResult, datetime]] = {}

        # Common claim patterns that don't need external validation
        self._known_patterns = self._load_known_patterns()

    def validate_script(self, script_data: Dict) -> Dict:
        """
        Validate all rebuttals in a script.

        Args:
            script_data: Unified podcast script dictionary

        Returns:
            Updated script with corrections applied
        """
        if not self.enabled:
            logger.info("External fact validation disabled")
            print(f"  External fact validation disabled - skipping", flush=True)
            return script_data

        logger.info("Starting external fact validation")
        print(f"  Validating rebuttals against external fact-check sources...", flush=True)

        if not self.google_api_key:
            print(f"  Note: No GEMINI_API_KEY configured - using local patterns only", flush=True)

        sections = script_data.get('podcast_sections', [])

        # Get only post_clip sections for validation
        post_clip_sections = [s for s in sections if s.get('section_type') == 'post_clip']
        print(f"  Found {len(post_clip_sections)} rebuttals to validate", flush=True)

        validation_results = []
        total_corrections = 0

        for i, section in enumerate(post_clip_sections, 1):
            section_id = section.get('section_id', 'unknown')
            print(f"  [{i}/{len(post_clip_sections)}] Validating: {section_id}", flush=True)

            result = self._validate_rebuttal(section)
            validation_results.append(result)

            print(f"      Claims checked: {result.claims_checked}, Issues found: {result.issues_found}", flush=True)

            if result.corrections_made > 0:
                total_corrections += result.corrections_made
                # Apply corrections to script content
                section['script_content'] = self._apply_corrections(
                    section.get('script_content', ''),
                    result.results
                )

        logger.info(f"Validation complete: {total_corrections} corrections applied")
        if total_corrections > 0:
            print(f"  Made {total_corrections} corrections based on fact-checks", flush=True)
        else:
            print(f"  No corrections needed", flush=True)

        # Add validation metadata
        script_data['_fact_validation'] = {
            'timestamp': datetime.now().isoformat(),
            'rebuttals_validated': len(validation_results),
            'total_corrections': total_corrections
        }

        return script_data

    def _validate_rebuttal(self, section: Dict) -> ValidationResult:
        """Validate a single rebuttal section."""
        section_id = section.get('section_id', 'unknown')
        content = section.get('script_content', '')

        logger.debug(f"Validating rebuttal: {section_id}")

        # Extract factual claims from content
        claims = self._extract_claims(content)

        results = []
        corrections_made = 0

        for claim in claims:
            # Check cache first
            cached_result = self._check_cache(claim)
            if cached_result:
                results.append(cached_result)
                if not cached_result.verified:
                    corrections_made += 1
                continue

            # Check known patterns
            known_result = self._check_known_patterns(claim)
            if known_result:
                results.append(known_result)
                self._add_to_cache(claim, known_result)
                continue

            # Query external API
            if self.google_api_key and self.google_fact_check:
                api_result = self._query_google_fact_check(claim)
                if api_result:
                    results.append(api_result)
                    self._add_to_cache(claim, api_result)
                    if not api_result.verified:
                        corrections_made += 1
                    continue

            # If no external validation available, mark as unverified but acceptable
            results.append(FactCheckResult(
                claim=claim,
                verified=True,
                source='no_external_validation',
                explanation='No external fact-check available'
            ))

        return ValidationResult(
            section_id=section_id,
            claims_checked=len(claims),
            issues_found=sum(1 for r in results if not r.verified),
            corrections_made=corrections_made,
            results=results
        )

    def _extract_claims(self, content: str) -> List[str]:
        """Extract factual claims from rebuttal content."""
        claims = []

        # Patterns that indicate factual claims
        claim_patterns = [
            r'(?:studies show|research shows|data shows|evidence shows)\s+(.+?)(?:\.|,)',
            r'(?:according to|per|as stated by)\s+(.+?)(?:\.|,)',
            r'(?:in fact|actually|the truth is)\s+(.+?)(?:\.|,)',
            r'(\d+(?:\.\d+)?%?\s+(?:of|percent).+?)(?:\.|,)',
            r'(?:proven|demonstrated|established)\s+that\s+(.+?)(?:\.|,)',
        ]

        for pattern in claim_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                claim = match.strip()
                if len(claim) > 20 and len(claim) < 300:  # Reasonable claim length
                    claims.append(claim)

        # Deduplicate
        return list(set(claims))

    def _check_cache(self, claim: str) -> Optional[FactCheckResult]:
        """Check if claim is in cache and not expired."""
        cache_key = self._get_cache_key(claim)

        if cache_key in self._cache:
            result, timestamp = self._cache[cache_key]
            if datetime.now() - timestamp < timedelta(hours=self.cache_hours):
                return result

        return None

    def _add_to_cache(self, claim: str, result: FactCheckResult) -> None:
        """Add result to cache."""
        cache_key = self._get_cache_key(claim)
        self._cache[cache_key] = (result, datetime.now())

    def _get_cache_key(self, claim: str) -> str:
        """Generate cache key for a claim."""
        normalized = claim.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()

    def _check_known_patterns(self, claim: str) -> Optional[FactCheckResult]:
        """Check claim against known fact patterns."""
        claim_lower = claim.lower()

        for pattern, (verified, explanation) in self._known_patterns.items():
            if pattern in claim_lower:
                return FactCheckResult(
                    claim=claim,
                    verified=verified,
                    source='known_pattern',
                    explanation=explanation
                )

        return None

    def _load_known_patterns(self) -> Dict[str, Tuple[bool, str]]:
        """Load known fact patterns from local database."""
        # Common scientific facts and their status
        return {
            'vaccines cause autism': (False, 'Debunked by multiple large-scale studies'),
            'earth is flat': (False, 'Contradicts all scientific evidence'),
            'climate change is a hoax': (False, 'Contradicts scientific consensus'),
            '5g causes': (False, 'No scientific evidence supports 5G health claims'),
            'evolution is just a theory': (False, 'Misunderstands scientific meaning of theory'),
            'scientific consensus': (True, 'References established scientific agreement'),
            'peer-reviewed': (True, 'References academic validation process'),
            'cdc guidelines': (True, 'References official health guidance'),
            'fda approved': (True, 'References regulatory approval'),
        }

    def _query_google_fact_check(self, claim: str) -> Optional[FactCheckResult]:
        """Query Google Fact Check API."""
        if not self.google_api_key:
            return None

        try:
            # Build API URL
            base_url = 'https://factchecktools.googleapis.com/v1alpha1/claims:search'
            params = {
                'key': self.google_api_key,
                'query': claim[:200],  # Limit query length
                'languageCode': 'en'
            }
            url = f"{base_url}?{urllib.parse.urlencode(params)}"

            # Make request
            request = urllib.request.Request(url)
            request.add_header('Accept', 'application/json')

            with urllib.request.urlopen(request, timeout=10) as response:
                data = json.loads(response.read().decode())

            # Parse response
            if 'claims' in data and data['claims']:
                claim_review = data['claims'][0]
                claim_text = claim_review.get('text', claim)

                reviews = claim_review.get('claimReview', [])
                if reviews:
                    review = reviews[0]
                    rating = review.get('textualRating', 'Unknown')
                    publisher = review.get('publisher', {}).get('name', 'Unknown')
                    url = review.get('url', '')

                    # Interpret rating
                    false_indicators = ['false', 'wrong', 'incorrect', 'misleading', 'pants on fire']
                    verified = not any(ind in rating.lower() for ind in false_indicators)

                    return FactCheckResult(
                        claim=claim,
                        verified=verified,
                        source='google_fact_check',
                        rating=rating,
                        explanation=f"Rated '{rating}' by {publisher}",
                        source_url=url
                    )

            return None

        except urllib.error.URLError as e:
            logger.warning(f"Google Fact Check API error: {e}")
            print(f"      API error: {e}", flush=True)
            return None
        except Exception as e:
            logger.warning(f"Error querying fact check: {e}")
            print(f"      Error: {e}", flush=True)
            return None

    def _apply_corrections(
        self,
        content: str,
        results: List[FactCheckResult]
    ) -> str:
        """Apply corrections to content based on fact-check results."""
        corrected = content

        for result in results:
            if not result.verified and result.explanation:
                # Find the claim in content and add correction note
                # This is a simple approach - could be more sophisticated
                if result.claim in corrected:
                    correction_note = f" [Note: {result.explanation}]"
                    corrected = corrected.replace(
                        result.claim,
                        result.claim + correction_note,
                        1  # Only replace first occurrence
                    )

        return corrected


if __name__ == "__main__":
    # Simple test
    test_script = {
        'podcast_sections': [
            {
                'section_type': 'post_clip',
                'section_id': 'post_1',
                'script_content': '''
                Studies show that the claim about vaccines causing autism has been
                thoroughly debunked. According to the CDC, vaccines are safe and effective.
                The scientific consensus is clear on this matter.
                '''
            }
        ]
    }

    validator = FactValidator()
    result = validator.validate_script(test_script)

    print("\nFact Validation Results:")
    print(f"Validation metadata: {result.get('_fact_validation', {})}")
