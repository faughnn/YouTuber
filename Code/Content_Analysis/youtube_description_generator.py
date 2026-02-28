"""
YouTube Description Generator

Generates a formatted document with claims, verdicts, and source URLs
for use in YouTube video descriptions. Uses Gemini with Google Search
grounding to find real URLs for sources mentioned in rebuttals.

Author: Claude Code
Created: 2024-12-31
Pipeline: Stage 8 - Final Output Generation
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from google import genai
from google.genai import types

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Global client for Gemini API
_gemini_client = None


class YouTubeDescriptionGenerator:
    """
    Generates YouTube description documents with claims, verdicts, and sources.

    Extracts claim/rebuttal pairs from verified_unified_script.json and uses
    Gemini with Google Search grounding to generate concise summaries with
    real source URLs.
    """

    VERDICT_CATEGORIES = [
        "FALSE",
        "MISLEADING",
        "PARTIALLY TRUE",
        "UNSUBSTANTIATED",
        "OVERSIMPLIFIED"
    ]

    def __init__(self, config: Optional[Dict] = None):
        """Initialize the generator."""
        self.config = config or {}
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.model_name = "gemini-2.5-pro"
        self._configure_gemini()

    def _configure_gemini(self) -> bool:
        """Configure Gemini API connection."""
        global _gemini_client
        try:
            if self.api_key:
                _gemini_client = genai.Client(api_key=self.api_key)
                logger.info("Gemini API client configured for YouTube description generation")
                return True
            else:
                logger.error("No GEMINI_API_KEY found")
                return False
        except Exception as e:
            logger.error(f"Error configuring Gemini API: {e}")
            return False

    def _get_client(self):
        """Get the Gemini client."""
        global _gemini_client
        if _gemini_client is None:
            if not self._configure_gemini():
                raise Exception("Failed to configure Gemini API client")
        return _gemini_client

    def generate_description(self, script_path: str, output_dir: str) -> Dict:
        """
        Generate YouTube description document from verified script.

        Args:
            script_path: Path to verified_unified_script.json
            output_dir: Directory to save output file

        Returns:
            Dict with success status, output path, and metadata
        """
        logger.info(f"Generating YouTube description from: {script_path}")
        print(f"  Generating YouTube description document...", flush=True)

        try:
            # Load the verified script
            with open(script_path, 'r', encoding='utf-8') as f:
                script_data = json.load(f)

            # Extract claim/rebuttal pairs
            pairs = self._extract_claim_rebuttal_pairs(script_data)

            if not pairs:
                logger.warning("No claim/rebuttal pairs found in script")
                return {
                    'success': False,
                    'error': 'No claims found in script',
                    'output_path': None
                }

            print(f"  Found {len(pairs)} claims to process", flush=True)

            # Generate summaries with sources using Gemini
            summaries = self._generate_summaries_with_sources(pairs)

            # Format output document
            output_text = self._format_output_document(summaries, script_data)

            # Save to file
            output_path = Path(output_dir) / "youtube_description.txt"
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output_text)

            logger.info(f"YouTube description saved to: {output_path}")
            print(f"  Saved to: {output_path}", flush=True)

            return {
                'success': True,
                'output_path': str(output_path),
                'claims_processed': len(pairs),
                'summaries_generated': len(summaries)
            }

        except Exception as e:
            logger.error(f"Error generating YouTube description: {e}")
            return {
                'success': False,
                'error': str(e),
                'output_path': None
            }

    def _extract_claim_rebuttal_pairs(self, script_data: Dict) -> List[Dict]:
        """Extract video_clip and corresponding post_clip pairs."""
        pairs = []
        sections = script_data.get('podcast_sections', [])

        # Build a map of clip_id to post_clip content
        post_clips = {}
        for section in sections:
            if section.get('section_type') == 'post_clip':
                clip_ref = section.get('clip_reference')
                if clip_ref:
                    post_clips[clip_ref] = section.get('script_content', '')

        # Extract video clips with their rebuttals
        for section in sections:
            if section.get('section_type') in ['video_clip', 'hook_clip']:
                clip_id = section.get('clip_id')
                pair = {
                    'title': section.get('title', 'Unknown Claim'),
                    'key_claims': section.get('key_claims', []),
                    'severity_level': section.get('severity_level', 'MEDIUM'),
                    'rebuttal': post_clips.get(clip_id, ''),
                    'clip_id': clip_id
                }
                pairs.append(pair)

        return pairs

    def _generate_summaries_with_sources(self, pairs: List[Dict]) -> List[Dict]:
        """Generate concise summaries with verdicts and source URLs using Gemini."""

        # Build the prompt
        claims_text = ""
        for i, pair in enumerate(pairs, 1):
            claims_text += f"""
CLAIM {i}: {pair['title']}
Key assertions: {json.dumps(pair['key_claims'])}
Severity: {pair['severity_level']}
Rebuttal content:
{pair['rebuttal'][:2000]}...

---
"""

        prompt = f"""You are generating a YouTube video description that fact-checks claims from a podcast.

For each claim below, generate a concise summary in this EXACT format:

"[Short Claim Title]" - [VERDICT]
[1-2 sentence explanation of why the claim is problematic]
Sources: [URL1] | [URL2]

VERDICT must be one of: FALSE, MISLEADING, PARTIALLY TRUE, UNSUBSTANTIATED, OVERSIMPLIFIED

IMPORTANT INSTRUCTIONS:
1. Use Google Search to find REAL, WORKING URLs for credible sources that support the rebuttal
2. Prefer official sources: .gov, .edu, peer-reviewed journals, major news outlets, fact-checkers
3. Keep explanations brief but informative (1-2 sentences max)
4. The claim title should be short and quotable (3-6 words)
5. Include 1-3 source URLs per claim
6. Make sure URLs are real and accessible

CLAIMS TO PROCESS:
{claims_text}

OUTPUT FORMAT:
Return ONLY the formatted claim summaries, one per claim, separated by blank lines. No introduction or conclusion text.
"""

        try:
            client = self._get_client()

            print(f"  Searching for source URLs with Google Search...", flush=True)

            # Use Google Search grounding to find real URLs
            config = types.GenerateContentConfig(
                temperature=0.3,
                top_p=0.9,
                candidate_count=1,
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )

            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )

            if not response.text:
                raise ValueError("Empty response from Gemini")

            # Parse the response into individual summaries
            summaries = self._parse_summaries(response.text, pairs)
            return summaries

        except Exception as e:
            logger.error(f"Error generating summaries: {e}")
            print(f"  Error: {e}", flush=True)
            # Return basic summaries without URLs on failure
            return self._generate_fallback_summaries(pairs)

    def _parse_summaries(self, response_text: str, pairs: List[Dict]) -> List[Dict]:
        """Parse Gemini response into structured summaries."""
        summaries = []

        # Split by double newlines to separate claims
        blocks = response_text.strip().split('\n\n')

        for i, block in enumerate(blocks):
            if not block.strip():
                continue

            lines = block.strip().split('\n')

            summary = {
                'raw_text': block.strip(),
                'claim_index': i
            }

            # Try to extract structured data
            if lines:
                # First line should be "Title" - VERDICT
                first_line = lines[0]
                if ' - ' in first_line:
                    parts = first_line.split(' - ', 1)
                    summary['title'] = parts[0].strip().strip('"')
                    summary['verdict'] = parts[1].strip() if len(parts) > 1 else 'UNVERIFIED'

                # Look for Sources line
                for line in lines:
                    if line.startswith('Sources:') or line.startswith('Source:'):
                        summary['sources_line'] = line

            summaries.append(summary)

        return summaries

    def _generate_fallback_summaries(self, pairs: List[Dict]) -> List[Dict]:
        """Generate basic summaries without API if Gemini fails."""
        summaries = []

        for pair in pairs:
            # Determine verdict from severity
            severity = pair.get('severity_level', 'MEDIUM')
            if severity == 'CRITICAL':
                verdict = 'FALSE'
            elif severity == 'HIGH':
                verdict = 'MISLEADING'
            else:
                verdict = 'UNSUBSTANTIATED'

            summary = {
                'title': pair['title'][:50],
                'verdict': verdict,
                'raw_text': f'"{pair["title"][:50]}" - {verdict}\nSee video for detailed fact-check.',
                'sources_line': 'Sources: See video description'
            }
            summaries.append(summary)

        return summaries

    def _format_output_document(self, summaries: List[Dict], script_data: Dict) -> str:
        """Format the final output document."""

        # Header
        theme = script_data.get('narrative_theme', 'Fact-Check Summary')
        timestamp = datetime.now().strftime('%Y-%m-%d')

        output = f"""FACT-CHECK SUMMARY
{theme}
Generated: {timestamp}

{'=' * 60}
CLAIMS AND SOURCES
{'=' * 60}

"""

        # Add each summary
        for summary in summaries:
            output += summary.get('raw_text', '') + '\n\n'

        # Footer
        output += f"""
{'=' * 60}
This fact-check was generated by Alternative Media Literacy.
All sources should be independently verified.
"""

        return output


def generate_youtube_description(script_path: str, output_dir: str, config: Optional[Dict] = None) -> Dict:
    """
    Convenience function for pipeline integration.

    Args:
        script_path: Path to verified_unified_script.json
        output_dir: Directory to save output
        config: Optional configuration

    Returns:
        Result dictionary with success status and output path
    """
    generator = YouTubeDescriptionGenerator(config)
    return generator.generate_description(script_path, output_dir)


if __name__ == "__main__":
    # CLI test
    if len(sys.argv) < 3:
        print("Usage: python youtube_description_generator.py <script_path> <output_dir>")
        sys.exit(1)

    script_path = sys.argv[1]
    output_dir = sys.argv[2]

    result = generate_youtube_description(script_path, output_dir)

    if result['success']:
        print(f"\nSuccess! Output saved to: {result['output_path']}")
    else:
        print(f"\nError: {result.get('error', 'Unknown error')}")
        sys.exit(1)
