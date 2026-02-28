"""
TTS Formatter - Post-Processing for Text-to-Speech Readiness

Replaces in-prompt TTS rules with deterministic code-based formatting.
Applied after script generation and before quality gate checks.

Rules:
- Abbreviations & titles expansion
- Symbol replacement
- Number/currency/percentage spelling
- Name period removal
- Hyphen cleanup for compound words

Author: Claude Code
Created: 2025-02-27
Pipeline: Multi-Pass Quality Control System
"""

import re
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class TTSFormatter:
    """Deterministic TTS formatting applied after script generation."""

    # Stage direction keywords that should be stripped before TTS
    STAGE_DIRECTION_KEYWORDS = [
        'sound', 'pause', 'beat', 'laughing', 'laughter', 'sighs',
        'sigh', 'clears throat', 'music', 'sfx', 'record scratch',
        'transition', 'silence', 'dramatic', 'whispers', 'yelling',
    ]

    # Abbreviation expansions
    ABBREVIATIONS = {
        'Dr.': 'Doctor',
        'Mr.': 'Mister',
        'Mrs.': 'Missus',
        'Ms.': 'Miss',
        'Prof.': 'Professor',
        'Jr.': 'Junior',
        'Sr.': 'Senior',
        'etc.': 'and so on',
        'vs.': 'versus',
        'approx.': 'approximately',
        'govt.': 'government',
        'dept.': 'department',
    }

    # Symbol replacements
    SYMBOLS = {
        '&': 'and',
        '@': 'at',
        '...': ',',
    }

    # Hyphenated words to join (TTS creates unwanted pauses)
    HYPHEN_JOIN = [
        'co-author', 'co-founder', 'co-host', 'co-worker',
        'pre-existing', 'post-pandemic', 'anti-vaccine', 'anti-vax',
        'well-known', 'so-called', 'self-correcting',
    ]

    def __init__(self, verified_names: Dict = None):
        """
        Initialize TTSFormatter.

        Args:
            verified_names: Optional dict with 'host' and 'guest' canonical names
                            from episode_metadata.json. Used for name consistency fixes.
        """
        self.verified_names = verified_names or {}
        self._name_patterns = self._build_name_patterns()

    def _build_name_patterns(self) -> List[tuple]:
        """Build regex patterns to detect and fix garbled names.

        Returns list of (compiled_regex, replacement_string) tuples.
        """
        patterns = []
        for role in ['host', 'guest']:
            canonical = self.verified_names.get(role, '')
            if not canonical:
                continue

            # After TTS formatting, periods are removed from initials
            # e.g. "Robert F. Kennedy Jr." -> "Robert F Kennedy Junior"
            # Build the canonical TTS-formatted version
            tts_canonical = canonical
            # Remove periods from initials
            tts_canonical = re.sub(r'\b([A-Z])\.\s', r'\1 ', tts_canonical)
            # Expand Jr./Sr.
            tts_canonical = tts_canonical.replace('Jr.', 'Junior').replace('Sr.', 'Senior')

            tokens = tts_canonical.split()
            if len(tokens) < 2:
                continue

            # Significant tokens: non-initial tokens (length > 1)
            significant = [t for t in tokens if len(t) > 1]
            if len(significant) < 2:
                continue

            # Pattern 1: Name parts in wrong order
            # e.g. "Kennedy Junior Robert" or "F Kennedy Junior" without "Robert"
            # We detect when significant surname tokens appear without the first name nearby

            # Pattern 2: Missing first name - e.g. "F Kennedy Junior" -> full name
            # Only for names with 3+ tokens (has middle initial or suffix)
            if len(tokens) >= 3:
                # Match the name minus the first token
                partial = ' '.join(tokens[1:])
                # Ensure partial doesn't match inside the full canonical name
                # Only fix when partial appears NOT preceded by the first token
                first_token = re.escape(tokens[0])
                partial_escaped = re.escape(partial)
                # Negative lookbehind for first name + space
                pattern = re.compile(
                    r'(?<!' + first_token + r'\s)' + partial_escaped,
                    re.IGNORECASE
                )
                patterns.append((pattern, tts_canonical))

            # Pattern 3: "Name1 and Name2 Surname" split errors
            # e.g. "Joe Rogan Robert and F Kennedy" — harder to catch generically
            # We look for host_first + guest_first + "and" + rest_of_guest in wrong order
            host_name = self.verified_names.get('host', '')
            guest_name = self.verified_names.get('guest', '')
            if host_name and guest_name and role == 'guest':
                host_first = host_name.split()[0] if host_name else ''
                guest_tokens = tts_canonical.split()
                if host_first and len(guest_tokens) >= 2:
                    # Pattern: "Host_First Guest_First and Rest_Of_Guest"
                    # e.g. "Joe Rogan Robert and F Kennedy Junior"
                    mangled = (
                        re.escape(host_first) + r'\s+' +
                        re.escape(guest_tokens[0]) + r'\s+and\s+' +
                        re.escape(' '.join(guest_tokens[1:]))
                    )
                    # Replace with "Host_First and Guest_Full"
                    host_tts = host_name
                    host_tts = re.sub(r'\b([A-Z])\.\s', r'\1 ', host_tts)
                    replacement = f"{host_tts} and {tts_canonical}"
                    patterns.append((re.compile(mangled, re.IGNORECASE), replacement))

        return patterns

    def format_script(self, script_data: Dict) -> Dict:
        """
        Apply TTS formatting to all script_content fields.

        Args:
            script_data: Unified podcast script dictionary

        Returns:
            Script data with TTS-formatted content
        """
        sections = script_data.get('podcast_sections', [])
        formatted_count = 0

        for section in sections:
            if 'script_content' in section:
                original = section['script_content']
                section['script_content'] = self.format_text(original)
                if section['script_content'] != original:
                    formatted_count += 1

        if formatted_count > 0:
            logger.info(f"TTS formatting applied to {formatted_count} sections")

        return script_data

    def format_text(self, text: str) -> str:
        """Apply all TTS formatting rules to a text string."""
        text = self._strip_stage_directions(text)
        text = self._collapse_spaced_acronyms(text)
        text = self._expand_abbreviations(text)
        text = self._replace_symbols(text)
        text = self._spell_numbers(text)
        text = self._remove_name_periods(text)
        text = self._fix_hyphens(text)
        text = self._clean_ellipses(text)
        text = self._fix_names(text)
        return text

    def _collapse_spaced_acronyms(self, text: str) -> str:
        """Collapse spaced-out acronyms like 'C O V I D' back to 'COVID'.

        LLMs sometimes spell out acronyms letter-by-letter when told to make
        text TTS-ready. This sounds terrible when spoken aloud.
        """
        def collapse_match(m):
            return m.group(0).replace(' ', '')
        # Match 3+ single uppercase letters separated by single spaces
        # e.g. "C O V I D" -> "COVID", "V A E R S" -> "VAERS"
        text = re.sub(r'\b[A-Z](?:\s[A-Z]){2,}\b', collapse_match, text)
        return text

    def _expand_abbreviations(self, text: str) -> str:
        """Expand abbreviations to full words."""
        for abbr, expansion in self.ABBREVIATIONS.items():
            # Use word boundary to avoid partial matches
            text = text.replace(abbr, expansion)
        return text

    def _replace_symbols(self, text: str) -> str:
        """Replace symbols with spoken equivalents."""
        # Handle & (but not in HTML entities)
        text = re.sub(r'(?<!\w)&(?!\w{2,};)', 'and', text)
        text = text.replace('@', 'at')
        return text

    def _spell_numbers(self, text: str) -> str:
        """Convert numbers, percentages, currency to spoken form."""
        # Percentages: "50%" -> "fifty percent"
        def replace_percent(match):
            num = match.group(1)
            return f"{num} percent"
        text = re.sub(r'(\d+(?:\.\d+)?)%', replace_percent, text)

        # Currency: "$100" -> "100 dollars", "$100 million" -> "100 million dollars"
        def replace_dollar(match):
            num = match.group(1)
            magnitude = match.group(2) or ''
            if magnitude:
                return f"{num} {magnitude} dollars"
            return f"{num} dollars"
        text = re.sub(r'\$(\d[\d,]*(?:\.\d+)?)\s*(million|billion|trillion|thousand)?', replace_dollar, text)

        # Hashtag numbers: "#2334" -> "number 2334"
        text = re.sub(r'#(\d+)', r'number \1', text)

        return text

    def _remove_name_periods(self, text: str) -> str:
        """Remove periods from names like 'Robert F. Kennedy' -> 'Robert F Kennedy'."""
        # Match single capital letter followed by period and space (middle initials)
        text = re.sub(r'\b([A-Z])\.\s', r'\1 ', text)
        return text

    def _fix_hyphens(self, text: str) -> str:
        """Remove hyphens from compound words that cause TTS pauses."""
        for word in self.HYPHEN_JOIN:
            replacement = word.replace('-', '')
            text = re.sub(re.escape(word), replacement, text, flags=re.IGNORECASE)

        # Also handle hyphenated personal names: "Mary-Jane" -> "Mary Jane"
        text = re.sub(r'([A-Z][a-z]+)-([A-Z][a-z]+)', r'\1 \2', text)

        return text

    def _clean_ellipses(self, text: str) -> str:
        """Replace ellipses with commas for natural pauses."""
        text = re.sub(r'\.{3,}', ',', text)
        return text

    def _strip_stage_directions(self, text: str) -> str:
        """Remove parenthetical stage directions that TTS would read aloud.

        Preserves parenthetical citations like (according to the WHO)
        or factual asides like (that's 40 percent of the population).
        Only strips parentheticals containing stage-direction keywords.
        """
        # Match parenthetical containing a stage-direction keyword
        pattern = r'\([^)]*\b(?:' + '|'.join(self.STAGE_DIRECTION_KEYWORDS) + r')[^)]*\)'
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        # Also catch generic stage directions: (SFX: ...), (NOTE: ...), (CUE: ...)
        text = re.sub(r'\((SFX|NOTE|CUE|FX|MUSIC|SOUND)[^)]*\)', '', text, flags=re.IGNORECASE)

        # Clean up double spaces left behind
        text = re.sub(r'  +', ' ', text)
        return text

    def _fix_names(self, text: str) -> str:
        """Fix garbled names using verified canonical forms.

        Applies patterns built from verified_names to catch common
        Gemini name-mangling errors (missing first names, wrong order,
        split names with 'and' inserted).
        """
        for pattern, replacement in self._name_patterns:
            text = pattern.sub(replacement, text)
        return text
