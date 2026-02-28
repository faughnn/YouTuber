"""
Output Quality Gate - Script Structure Validation

This module validates generated scripts for structural issues before downstream
processing. Uses binary checks to catch problems like missing clip references,
invalid timestamps, and structural inconsistencies.

Binary Checks:
1. Do all clip references in the script exist in the source?
2. Are all timestamps valid and non-overlapping?
3. Does the intro accurately preview the content?
4. Does each rebuttal reference the correct clip?

Author: Claude Code
Created: 2024-12-28
Pipeline: Multi-Pass Quality Control System
"""

import os
import sys
import json
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


@dataclass
class QualityIssue:
    """A quality issue found in the script."""
    check_name: str
    severity: str  # 'CRITICAL', 'WARNING', 'INFO'
    description: str
    location: Optional[str] = None
    auto_fixable: bool = False


@dataclass
class GateResult:
    """Result of running all quality gate checks."""
    passed: bool
    issues: List[QualityIssue] = field(default_factory=list)
    critical_count: int = 0
    warning_count: int = 0

    def to_dict(self) -> Dict:
        return {
            'passed': self.passed,
            'critical_count': self.critical_count,
            'warning_count': self.warning_count,
            'issues': [
                {
                    'check': i.check_name,
                    'severity': i.severity,
                    'description': i.description,
                    'location': i.location
                }
                for i in self.issues
            ]
        }


class OutputQualityGate:
    """
    Validates script structure and consistency before downstream processing.

    Performs binary pass/fail checks on structural elements of the generated
    script to catch issues that would cause problems in TTS or video compilation.
    """

    # Common filler phrases to exclude from repetition detection
    REPETITION_STOPLIST = {
        'in the first place', 'at the end of the day', 'the fact that',
        'on the other hand', 'at the same time', 'in other words',
        'for the record', 'the bottom line', 'the thing is',
        'when it comes to', 'the point is', 'what we know',
        'a lot of people', 'for a long time', 'at this point',
        'as a matter of', 'in the middle of', 'one of the most',
        'some of the most', 'this is the kind', 'that is the kind',
        'this is what happens', 'but here is the', 'and here is the',
        'and this is where', 'but this is where', 'and that is the',
        'but that is the', 'the kind of thing',
    }

    def __init__(self, config: Optional[Dict] = None, verified_names: Optional[Dict] = None):
        """
        Initialize the OutputQualityGate.

        Args:
            config: Optional configuration dictionary
            verified_names: Optional dict with 'host' and 'guest' canonical names
        """
        self.config = config or {}
        self.verified_names = verified_names or {}
        qc_config = self.config.get('quality_control', {}).get('output_gate', {})
        self.max_regeneration_attempts = qc_config.get('max_regeneration_attempts', 2)

    def validate_script(self, script_data: Dict) -> GateResult:
        """
        Run all quality gate checks on a script.

        Args:
            script_data: Unified podcast script dictionary

        Returns:
            GateResult with pass/fail status and issues
        """
        issues = []

        # Check 1: Clip reference consistency
        issues.extend(self._check_clip_references(script_data))

        # Check 2: Timestamp validity
        issues.extend(self._check_timestamps(script_data))

        # Check 3: Section structure
        issues.extend(self._check_section_structure(script_data))

        # Check 4: Content consistency
        issues.extend(self._check_content_consistency(script_data))

        # Check 5: TTS readiness
        issues.extend(self._check_tts_readiness(script_data))

        # Check 6: Rebuttal proportionality
        issues.extend(self._check_rebuttal_proportionality(script_data))

        # Check 7: Name consistency
        issues.extend(self._check_name_consistency(script_data))

        # Check 8: Repetitive phrases
        issues.extend(self._check_phrase_repetition(script_data))

        # Count by severity
        critical_count = sum(1 for i in issues if i.severity == 'CRITICAL')
        warning_count = sum(1 for i in issues if i.severity == 'WARNING')

        # Pass if no critical issues
        passed = critical_count == 0

        result = GateResult(
            passed=passed,
            issues=issues,
            critical_count=critical_count,
            warning_count=warning_count
        )

        logger.info(f"Quality gate: {'PASSED' if passed else 'FAILED'} "
                    f"({critical_count} critical, {warning_count} warnings)")

        return result

    def _check_clip_references(self, script_data: Dict) -> List[QualityIssue]:
        """Check that all clip references in script match actual clips."""
        issues = []

        sections = script_data.get('podcast_sections', [])

        # Find all video_clip IDs
        video_clip_ids = set()
        for section in sections:
            if section.get('section_type') == 'video_clip':
                clip_id = section.get('clip_id')
                if clip_id:
                    video_clip_ids.add(clip_id)

        # Check all pre_clip and post_clip references
        for section in sections:
            section_type = section.get('section_type')
            section_id = section.get('section_id', 'unknown')

            if section_type in ['pre_clip', 'post_clip']:
                clip_ref = section.get('clip_reference')
                if clip_ref and clip_ref not in video_clip_ids:
                    issues.append(QualityIssue(
                        check_name='clip_reference',
                        severity='CRITICAL',
                        description=f"Clip reference '{clip_ref}' not found in video clips",
                        location=section_id
                    ))

        return issues

    def _check_timestamps(self, script_data: Dict) -> List[QualityIssue]:
        """Check timestamp validity and ordering."""
        issues = []

        sections = script_data.get('podcast_sections', [])
        previous_end = None

        for section in sections:
            if section.get('section_type') == 'video_clip':
                section_id = section.get('section_id', 'unknown')

                try:
                    start_time = float(section.get('start_time', 0))
                    end_time = float(section.get('end_time', 0))

                    # Check start < end
                    if start_time >= end_time:
                        issues.append(QualityIssue(
                            check_name='timestamp_order',
                            severity='CRITICAL',
                            description=f"Start time ({start_time}) >= end time ({end_time})",
                            location=section_id,
                            auto_fixable=True
                        ))

                    # Check for very short clips
                    duration = end_time - start_time
                    clip_config = self.config.get('quality_control', {}).get('clip_duration', {})
                    min_duration = clip_config.get('min_seconds', 25)
                    if duration < min_duration:
                        issues.append(QualityIssue(
                            check_name='clip_duration_short',
                            severity='WARNING',
                            description=f"Clip duration ({duration:.0f}s) below minimum of {min_duration}s",
                            location=section_id
                        ))

                    # Check for very long clips
                    is_extended = section.get('extended_clip', False)
                    max_duration = (
                        clip_config.get('extended_max_seconds', 180) if is_extended
                        else clip_config.get('max_seconds', 120)
                    )
                    if duration > max_duration:
                        issues.append(QualityIssue(
                            check_name='clip_duration',
                            severity='WARNING',
                            description=f"Clip duration ({duration:.0f}s) exceeds {'extended ' if is_extended else ''}max of {max_duration}s",
                            location=section_id
                        ))

                    # Check for overlapping clips
                    if previous_end is not None and start_time < previous_end:
                        issues.append(QualityIssue(
                            check_name='timestamp_overlap',
                            severity='WARNING',
                            description=f"Clip overlaps with previous (starts at {start_time}, previous ends at {previous_end})",
                            location=section_id
                        ))

                    previous_end = end_time

                except (ValueError, TypeError) as e:
                    issues.append(QualityIssue(
                        check_name='timestamp_format',
                        severity='CRITICAL',
                        description=f"Invalid timestamp format: {e}",
                        location=section_id
                    ))

        return issues

    def _check_section_structure(self, script_data: Dict) -> List[QualityIssue]:
        """Check that script has required sections in correct order."""
        issues = []

        sections = script_data.get('podcast_sections', [])

        if not sections:
            issues.append(QualityIssue(
                check_name='empty_sections',
                severity='CRITICAL',
                description="Script has no podcast_sections"
            ))
            return issues

        section_types = [s.get('section_type') for s in sections]

        # Check for intro
        if 'intro' not in section_types and 'intro_plus_hook_analysis' not in section_types:
            issues.append(QualityIssue(
                check_name='missing_intro',
                severity='WARNING',
                description="Script is missing an intro section"
            ))

        # Check for outro
        if 'outro' not in section_types:
            issues.append(QualityIssue(
                check_name='missing_outro',
                severity='WARNING',
                description="Script is missing an outro section"
            ))

        # Check for at least one video_clip
        if 'video_clip' not in section_types:
            issues.append(QualityIssue(
                check_name='no_clips',
                severity='CRITICAL',
                description="Script has no video_clip sections"
            ))

        # Check that each video_clip has a post_clip
        video_clip_refs = set()
        post_clip_refs = set()

        for section in sections:
            if section.get('section_type') == 'video_clip':
                video_clip_refs.add(section.get('clip_id'))
            elif section.get('section_type') == 'post_clip':
                post_clip_refs.add(section.get('clip_reference'))

        missing_rebuttals = video_clip_refs - post_clip_refs
        for clip_id in missing_rebuttals:
            issues.append(QualityIssue(
                check_name='missing_rebuttal',
                severity='WARNING',
                description=f"Video clip '{clip_id}' has no corresponding post_clip rebuttal"
            ))

        return issues

    def _check_content_consistency(self, script_data: Dict) -> List[QualityIssue]:
        """Check content consistency between sections."""
        issues = []

        sections = script_data.get('podcast_sections', [])

        for section in sections:
            section_type = section.get('section_type')
            section_id = section.get('section_id', 'unknown')

            # Check that script sections have content
            if section_type in ['intro', 'pre_clip', 'post_clip', 'outro', 'intro_plus_hook_analysis']:
                content = section.get('script_content', '')
                if not content or len(content.strip()) < 50:
                    issues.append(QualityIssue(
                        check_name='empty_content',
                        severity='CRITICAL' if section_type in ['intro', 'post_clip'] else 'WARNING',
                        description=f"Section has insufficient content ({len(content)} chars)",
                        location=section_id
                    ))

            # Check that video clips have required fields
            if section_type == 'video_clip':
                required_fields = ['clip_id', 'start_time', 'end_time', 'title']
                for field in required_fields:
                    if not section.get(field):
                        issues.append(QualityIssue(
                            check_name='missing_field',
                            severity='CRITICAL',
                            description=f"Video clip missing required field: {field}",
                            location=section_id
                        ))

        return issues

    def _check_tts_readiness(self, script_data: Dict) -> List[QualityIssue]:
        """Check that script content is TTS-ready."""
        issues = []

        sections = script_data.get('podcast_sections', [])

        # Patterns that should be avoided for TTS
        problematic_patterns = [
            (r'\b[A-Z]{2,}\b', 'Uppercase abbreviation'),  # Matches "CIA", "FBI", etc.
            (r'\d+%', 'Percentage symbol'),  # Should be "fifty percent"
            (r'\$\d+', 'Dollar sign'),  # Should be "one hundred dollars"
            (r'#\d+', 'Hashtag number'),  # Should be "number one"
            (r'&', 'Ampersand'),  # Should be "and"
        ]

        # Stage direction keywords to check for
        stage_keywords = [
            'sound', 'pause', 'beat', 'laughing', 'laughter', 'sighs',
            'sigh', 'clears throat', 'music', 'sfx', 'record scratch',
            'transition', 'silence', 'dramatic', 'whispers', 'yelling',
        ]
        stage_pattern = re.compile(
            r'\([^)]*\b(?:' + '|'.join(stage_keywords) + r')[^)]*\)',
            re.IGNORECASE
        )
        generic_stage_pattern = re.compile(
            r'\((SFX|NOTE|CUE|FX|MUSIC|SOUND)[^)]*\)',
            re.IGNORECASE
        )

        for section in sections:
            section_type = section.get('section_type')
            section_id = section.get('section_id', 'unknown')

            if section_type in ['intro', 'pre_clip', 'post_clip', 'outro', 'intro_plus_hook_analysis']:
                content = section.get('script_content', '')

                for pattern, description in problematic_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        # Only report first few matches
                        sample = matches[:3]
                        issues.append(QualityIssue(
                            check_name='tts_formatting',
                            severity='INFO',
                            description=f"{description} found: {sample}",
                            location=section_id,
                            auto_fixable=True
                        ))

                # Check for remaining stage directions
                stage_matches = stage_pattern.findall(content)
                stage_matches.extend(generic_stage_pattern.findall(content))
                if stage_matches:
                    issues.append(QualityIssue(
                        check_name='stage_directions',
                        severity='WARNING',
                        description=f"Stage directions found that TTS would read aloud: {stage_matches[:3]}",
                        location=section_id,
                        auto_fixable=True
                    ))

        return issues

    def _check_rebuttal_proportionality(self, script_data: Dict) -> List[QualityIssue]:
        """Check that post_clip rebuttals are proportional to their clip duration."""
        issues = []

        proportionality = self.config.get('quality_control', {}).get('rebuttal_proportionality', {})
        if not proportionality.get('enabled', False):
            return issues

        tiers = proportionality.get('tiers', [])
        if not tiers:
            return issues

        sections = script_data.get('podcast_sections', [])

        # Build map of clip_id -> duration
        clip_durations = {}
        for section in sections:
            if section.get('section_type') == 'video_clip':
                clip_id = section.get('clip_id')
                try:
                    start = float(section.get('start_time', 0))
                    end = float(section.get('end_time', 0))
                    if end > start:
                        clip_durations[clip_id] = end - start
                except (ValueError, TypeError):
                    pass

        # Check each post_clip against its tier limit
        for section in sections:
            if section.get('section_type') != 'post_clip':
                continue

            section_id = section.get('section_id', 'unknown')
            clip_ref = section.get('clip_reference')
            content = section.get('script_content', '')
            word_count = len(content.split())

            duration = clip_durations.get(clip_ref)
            if duration is None:
                continue

            # Find applicable tier
            tier_limit = None
            tier_label = None
            for tier in tiers:
                if duration <= tier.get('max_clip_seconds', 999):
                    tier_limit = tier.get('max_words', 500)
                    tier_label = tier.get('label', 'unknown')
                    break
            if tier_limit is None and tiers:
                tier_limit = tiers[-1].get('max_words', 600)
                tier_label = tiers[-1].get('label', 'extended')

            if tier_limit and word_count > tier_limit * 1.2:
                issues.append(QualityIssue(
                    check_name='rebuttal_proportionality',
                    severity='WARNING',
                    description=(
                        f"Rebuttal ({word_count} words) exceeds {tier_label} tier limit "
                        f"({tier_limit} words) by {((word_count / tier_limit) - 1) * 100:.0f}% "
                        f"for {duration:.0f}s clip"
                    ),
                    location=section_id,
                ))

        return issues

    def _check_name_consistency(self, script_data: Dict) -> List[QualityIssue]:
        """Check that host/guest names appear correctly in script content."""
        issues = []

        if not self.verified_names:
            return issues

        sections = script_data.get('podcast_sections', [])
        narration_types = ['intro', 'pre_clip', 'post_clip', 'outro', 'intro_plus_hook_analysis']

        for role in ['host', 'guest']:
            canonical = self.verified_names.get(role, '')
            if not canonical:
                continue

            # Build TTS-formatted canonical (periods removed, Jr->Junior)
            tts_canonical = canonical
            tts_canonical = re.sub(r'\b([A-Z])\.\s', r'\1 ', tts_canonical)
            tts_canonical = tts_canonical.replace('Jr.', 'Junior').replace('Sr.', 'Senior')

            tokens = tts_canonical.split()
            if len(tokens) < 2:
                continue

            # Check each narration section for correct name usage
            canonical_found_anywhere = False
            for section in sections:
                if section.get('section_type') not in narration_types:
                    continue
                content = section.get('script_content', '')
                section_id = section.get('section_id', 'unknown')

                # Check if the canonical name (or last-name-only) appears
                last_name = tokens[-1] if tokens[-1] not in ('Junior', 'Senior') else tokens[-2]
                if tts_canonical in content or canonical in content:
                    canonical_found_anywhere = True
                elif last_name.lower() in content.lower():
                    # Last name found but not full name — acceptable for subsequent mentions
                    canonical_found_anywhere = True

                # Check for partial/garbled variants
                # Look for name fragments in wrong order or missing parts
                if len(tokens) >= 3:
                    # Check for partial match without first name
                    partial = ' '.join(tokens[1:])
                    if partial in content and tts_canonical not in content:
                        issues.append(QualityIssue(
                            check_name='name_consistency',
                            severity='WARNING',
                            description=f"{role.title()} name appears garbled: '{partial}' without '{tokens[0]}' prefix",
                            location=section_id,
                            auto_fixable=True
                        ))

            if not canonical_found_anywhere:
                issues.append(QualityIssue(
                    check_name='name_consistency',
                    severity='CRITICAL',
                    description=f"{role.title()} name '{canonical}' never appears correctly in any narration section",
                    auto_fixable=True
                ))

        return issues

    def _check_phrase_repetition(self, script_data: Dict) -> List[QualityIssue]:
        """Detect phrases repeated across multiple script sections."""
        issues = []

        sections = script_data.get('podcast_sections', [])
        narration_types = ['intro', 'pre_clip', 'post_clip', 'outro', 'intro_plus_hook_analysis']

        # Collect text by section
        section_texts = []
        for section in sections:
            if section.get('section_type') in narration_types:
                content = section.get('script_content', '')
                if content:
                    section_texts.append(content.lower())

        if len(section_texts) < 2:
            return issues

        # Extract n-grams (3 to 6 words) from each section and track which sections they appear in
        phrase_sections = {}  # phrase -> set of section indices

        for section_idx, text in enumerate(section_texts):
            # Tokenize: split on whitespace, strip punctuation
            words = re.findall(r"[a-z']+", text)

            seen_in_section = set()
            for n in range(3, 7):
                for i in range(len(words) - n + 1):
                    phrase = ' '.join(words[i:i + n])
                    if phrase in seen_in_section:
                        continue
                    if phrase in self.REPETITION_STOPLIST:
                        continue
                    seen_in_section.add(phrase)
                    if phrase not in phrase_sections:
                        phrase_sections[phrase] = set()
                    phrase_sections[phrase].add(section_idx)

        # Flag phrases appearing in 3+ different sections
        flagged = set()  # avoid flagging substrings of already-flagged phrases
        # Sort by length descending so longer phrases take priority
        sorted_phrases = sorted(
            ((p, secs) for p, secs in phrase_sections.items() if len(secs) >= 3),
            key=lambda x: len(x[0]),
            reverse=True
        )

        for phrase, section_indices in sorted_phrases:
            # Skip if this phrase is a substring of an already-flagged phrase
            is_substring = False
            for flagged_phrase in flagged:
                if phrase in flagged_phrase:
                    is_substring = True
                    break
            if is_substring:
                continue

            flagged.add(phrase)
            issues.append(QualityIssue(
                check_name='phrase_repetition',
                severity='WARNING',
                description=f"Phrase \"{phrase}\" repeated across {len(section_indices)} sections",
            ))

        return issues

    def auto_correct(
        self,
        script_data: Dict,
        issues: List[QualityIssue]
    ) -> Dict:
        """
        Attempt to auto-correct fixable issues.

        Args:
            script_data: Original script data
            issues: List of issues to fix

        Returns:
            Corrected script data
        """
        corrected = json.loads(json.dumps(script_data))  # Deep copy

        for issue in issues:
            if not issue.auto_fixable:
                continue

            if issue.check_name == 'tts_formatting':
                corrected = self._fix_tts_formatting(corrected)

            elif issue.check_name == 'timestamp_order':
                corrected = self._fix_timestamp_order(corrected, issue.location)

            elif issue.check_name == 'name_consistency':
                corrected = self._fix_name_consistency(corrected)

            elif issue.check_name == 'stage_directions':
                corrected = self._fix_stage_directions(corrected)

        return corrected

    def _fix_tts_formatting(self, script_data: Dict) -> Dict:
        """Fix TTS formatting issues in script content."""
        sections = script_data.get('podcast_sections', [])

        for section in sections:
            if 'script_content' in section:
                content = section['script_content']

                # Replace common TTS issues
                content = re.sub(r'\$(\d+)', r'\1 dollars', content)
                content = re.sub(r'(\d+)%', r'\1 percent', content)
                content = content.replace('&', 'and')
                content = re.sub(r'#(\d+)', r'number \1', content)

                section['script_content'] = content

        return script_data

    def _fix_timestamp_order(self, script_data: Dict, section_id: str) -> Dict:
        """Fix timestamp order issue by swapping start and end."""
        sections = script_data.get('podcast_sections', [])

        for section in sections:
            if section.get('section_id') == section_id:
                start = section.get('start_time')
                end = section.get('end_time')
                if start and end:
                    section['start_time'] = end
                    section['end_time'] = start

        return script_data

    def _fix_name_consistency(self, script_data: Dict) -> Dict:
        """Fix garbled names using verified canonical forms."""
        if not self.verified_names:
            return script_data

        # Use TTSFormatter's name-fix logic
        try:
            from .tts_formatter import TTSFormatter
        except ImportError:
            try:
                from tts_formatter import TTSFormatter
            except ImportError:
                return script_data

        formatter = TTSFormatter(verified_names=self.verified_names)
        sections = script_data.get('podcast_sections', [])

        for section in sections:
            if 'script_content' in section:
                section['script_content'] = formatter._fix_names(section['script_content'])

        return script_data

    def _fix_stage_directions(self, script_data: Dict) -> Dict:
        """Strip stage directions from script content."""
        try:
            from .tts_formatter import TTSFormatter
        except ImportError:
            try:
                from tts_formatter import TTSFormatter
            except ImportError:
                return script_data

        formatter = TTSFormatter()
        sections = script_data.get('podcast_sections', [])

        for section in sections:
            if 'script_content' in section:
                section['script_content'] = formatter._strip_stage_directions(section['script_content'])

        return script_data


if __name__ == "__main__":
    # Simple test
    test_script = {
        'podcast_sections': [
            {'section_type': 'intro', 'section_id': 'intro_1', 'script_content': 'Welcome to the show...'},
            {'section_type': 'video_clip', 'section_id': 'clip_1', 'clip_id': 'Harmful_Segment_01',
             'start_time': '10.5', 'end_time': '45.0', 'title': 'Test clip'},
            {'section_type': 'post_clip', 'section_id': 'post_1', 'clip_reference': 'Harmful_Segment_01',
             'script_content': 'This is a rebuttal with 50% wrong claims and $100 million in losses.'},
            {'section_type': 'outro', 'section_id': 'outro_1', 'script_content': 'Thanks for watching...'}
        ]
    }

    gate = OutputQualityGate()
    result = gate.validate_script(test_script)

    print(f"\nQuality Gate Result: {'PASSED' if result.passed else 'FAILED'}")
    print(f"Critical issues: {result.critical_count}")
    print(f"Warnings: {result.warning_count}")

    for issue in result.issues:
        print(f"  [{issue.severity}] {issue.check_name}: {issue.description}")
