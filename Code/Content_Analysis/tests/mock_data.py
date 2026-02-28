"""
Mock Data for Quality Control System Testing

Provides mock data and fixtures for testing the binary filtering pipeline
without making actual API calls to Gemini.

Author: Claude Code
Created: 2024-12-28
"""

import json
from typing import Dict, List, Any
from datetime import datetime


# =============================================================================
# MOCK PASS 1 ANALYSIS RESULTS (Transcript Analysis Output)
# =============================================================================

MOCK_PASS1_SEGMENTS = [
    {
        "segment_id": "Harmful_Segment_01",
        "narrativeSegmentTitle": "Vaccine Safety Misinformation",
        "clipContextDescription": "Guest makes false claims about vaccine safety, citing debunked studies and conspiracy theories about pharmaceutical companies hiding data.",
        "suggestedClip": [
            {
                "timestamp": "[12:34]",
                "speaker": "Guest",
                "quote": "The vaccines were never properly tested. They skipped all the safety trials and the data shows thousands of deaths."
            },
            {
                "timestamp": "[12:45]",
                "speaker": "Guest",
                "quote": "Big pharma is hiding the real numbers. My friend who works at the FDA told me they're covering up adverse events."
            }
        ],
        "startTime": 754.0,
        "endTime": 812.5,
        "severityRating": "HIGH"
    },
    {
        "segment_id": "Harmful_Segment_02",
        "narrativeSegmentTitle": "Election Fraud Claims",
        "clipContextDescription": "Guest alleges widespread election fraud without evidence, repeating debunked claims about voting machines.",
        "suggestedClip": [
            {
                "timestamp": "[25:10]",
                "speaker": "Guest",
                "quote": "The machines were programmed to flip votes. We have mathematical proof that the numbers don't add up."
            },
            {
                "timestamp": "[25:30]",
                "speaker": "Guest",
                "quote": "Dead people voted in every swing state. The evidence is overwhelming."
            }
        ],
        "startTime": 1510.0,
        "endTime": 1590.0,
        "severityRating": "HIGH"
    },
    {
        "segment_id": "Harmful_Segment_03",
        "narrativeSegmentTitle": "Climate Change Denial",
        "clipContextDescription": "Guest denies scientific consensus on climate change, claiming it's a hoax for government control.",
        "suggestedClip": [
            {
                "timestamp": "[38:20]",
                "speaker": "Guest",
                "quote": "Climate change is the biggest scam in history. The scientists are paid to lie."
            }
        ],
        "startTime": 2300.0,
        "endTime": 2380.0,
        "severityRating": "MEDIUM"
    },
    {
        "segment_id": "Harmful_Segment_04",
        "narrativeSegmentTitle": "Media Criticism (Opinion)",
        "clipContextDescription": "Guest shares opinion about media bias without making specific false claims.",
        "suggestedClip": [
            {
                "timestamp": "[45:00]",
                "speaker": "Guest",
                "quote": "I think the media has a bias problem. They don't cover both sides equally."
            }
        ],
        "startTime": 2700.0,
        "endTime": 2750.0,
        "severityRating": "LOW"
    },
    {
        "segment_id": "Harmful_Segment_05",
        "narrativeSegmentTitle": "5G Health Claims",
        "clipContextDescription": "Guest makes false claims about 5G technology causing health problems.",
        "suggestedClip": [
            {
                "timestamp": "[52:15]",
                "speaker": "Guest",
                "quote": "5G radiation is causing cancer clusters. Look at the data from Wuhan - 5G rollout coincided with the pandemic."
            }
        ],
        "startTime": 3135.0,
        "endTime": 3200.0,
        "severityRating": "HIGH"
    },
    {
        "segment_id": "Harmful_Segment_06",
        "narrativeSegmentTitle": "Personal Anecdote",
        "clipContextDescription": "Guest shares personal story about a family member's health without making verifiable claims.",
        "suggestedClip": [
            {
                "timestamp": "[58:30]",
                "speaker": "Guest",
                "quote": "My uncle got really sick after his shot. I'm not saying it was the vaccine, but the timing was suspicious."
            }
        ],
        "startTime": 3510.0,
        "endTime": 3560.0,
        "severityRating": "LOW"
    },
    {
        "segment_id": "Harmful_Segment_07",
        "narrativeSegmentTitle": "Government Control Conspiracy",
        "clipContextDescription": "Guest claims government is using various crises for population control.",
        "suggestedClip": [
            {
                "timestamp": "[65:00]",
                "speaker": "Guest",
                "quote": "This is all about control. They want to track everyone with digital IDs and control your money."
            }
        ],
        "startTime": 3900.0,
        "endTime": 3980.0,
        "severityRating": "MEDIUM"
    },
    {
        "segment_id": "Harmful_Segment_08",
        "narrativeSegmentTitle": "Medical Treatment Misinformation",
        "clipContextDescription": "Guest promotes unproven treatments and discourages evidence-based medicine.",
        "suggestedClip": [
            {
                "timestamp": "[72:40]",
                "speaker": "Guest",
                "quote": "Ivermectin cures COVID. The studies are clear but the establishment won't admit it because there's no money in it."
            }
        ],
        "startTime": 4360.0,
        "endTime": 4420.0,
        "severityRating": "HIGH"
    }
]


# =============================================================================
# MOCK UNIFIED PODCAST SCRIPT (For Rebuttal Verification Testing)
# =============================================================================

MOCK_UNIFIED_SCRIPT = {
    "narrative_theme": "Examining misinformation spread on popular podcasts",
    "podcast_sections": [
        {
            "section_type": "intro",
            "section_id": "intro_1",
            "estimated_duration": "60s",
            "script_content": "Welcome to Alternative Media Literacy. Today we're diving into some wild claims from a recent podcast episode. Buckle up, because we've got vaccines, elections, and yes, even 5G conspiracies. Let's break down the misinformation."
        },
        {
            "section_type": "video_clip",
            "section_id": "clip_1",
            "clip_id": "Harmful_Segment_01",
            "start_time": "754.0",
            "end_time": "812.5",
            "title": "Vaccine Safety Misinformation",
            "selection_reason": "Clear false claims about vaccine testing",
            "severity_level": "HIGH",
            "key_claims": ["Vaccines weren't tested", "Deaths being hidden"],
            "suggestedClip": [
                {
                    "timestamp": "[12:34]",
                    "speaker": "Guest",
                    "quote": "The vaccines were never properly tested."
                }
            ]
        },
        {
            "section_type": "post_clip",
            "section_id": "post_clip_1",
            "clip_reference": "Harmful_Segment_01",
            "estimated_duration": "90s",
            "script_content": "Okay, let's fact-check this. The COVID vaccines went through all standard clinical trial phases. Phase 1, 2, and 3 trials involved over 70,000 participants. The FDA's VAERS system tracks adverse events and the data is publicly available. Studies show the vaccines are safe and effective."
        },
        {
            "section_type": "video_clip",
            "section_id": "clip_2",
            "clip_id": "Harmful_Segment_02",
            "start_time": "1510.0",
            "end_time": "1590.0",
            "title": "Election Fraud Claims",
            "selection_reason": "Debunked election conspiracy theories",
            "severity_level": "HIGH",
            "key_claims": ["Voting machines flipped votes", "Dead people voted"],
            "suggestedClip": [
                {
                    "timestamp": "[25:10]",
                    "speaker": "Guest",
                    "quote": "The machines were programmed to flip votes."
                }
            ]
        },
        {
            "section_type": "post_clip",
            "section_id": "post_clip_2",
            "clip_reference": "Harmful_Segment_02",
            "estimated_duration": "90s",
            "script_content": "This has been thoroughly debunked. Over 60 court cases found no evidence of widespread fraud. The Cybersecurity and Infrastructure Security Agency called it the most secure election in American history. Dominion voting machines were audited multiple times with no irregularities found."
        },
        {
            "section_type": "video_clip",
            "section_id": "clip_3",
            "clip_id": "Harmful_Segment_05",
            "start_time": "3135.0",
            "end_time": "3200.0",
            "title": "5G Health Claims",
            "selection_reason": "False health claims about technology",
            "severity_level": "HIGH",
            "key_claims": ["5G causes cancer", "5G linked to COVID"],
            "suggestedClip": [
                {
                    "timestamp": "[52:15]",
                    "speaker": "Guest",
                    "quote": "5G radiation is causing cancer clusters."
                }
            ]
        },
        {
            "section_type": "post_clip",
            "section_id": "post_clip_3",
            "clip_reference": "Harmful_Segment_05",
            "estimated_duration": "90s",
            "script_content": "5G uses non-ionizing radiation, which doesn't have enough energy to damage DNA. The WHO and FDA have both confirmed 5G is safe. The pandemic started in Wuhan before 5G was widely deployed there. This conspiracy theory has been debunked by scientists worldwide."
        },
        {
            "section_type": "outro",
            "section_id": "outro_1",
            "estimated_duration": "45s",
            "script_content": "And that's today's breakdown. Remember, always check your sources and look for evidence before sharing claims. Misinformation spreads fast, but so can the truth. Thanks for watching Alternative Media Literacy."
        }
    ],
    "script_metadata": {
        "total_estimated_duration": "8 minutes",
        "target_audience": "General public interested in media literacy",
        "key_themes": ["vaccine safety", "election integrity", "technology health claims"],
        "total_clips_analyzed": "3",
        "tts_segments_count": "7",
        "timeline_ready": True
    }
}


# =============================================================================
# MOCK GEMINI API RESPONSES
# =============================================================================

class MockGeminiResponse:
    """Mock Gemini API response object."""

    def __init__(self, text: str):
        self.text = text


def create_mock_gate_response(gate_name: str, passed: bool, segment_id: str = "test") -> str:
    """Create a mock gate evaluation response."""
    if passed:
        return f"""ANSWER: YES
JUSTIFICATION: The segment contains a specific factual claim that can be evaluated for accuracy. The content makes verifiable assertions about real-world events or data.
EVIDENCE: "{segment_id}" contains specific claims that can be fact-checked against established sources."""
    else:
        return f"""ANSWER: NO
JUSTIFICATION: The segment does not meet the criteria for this gate. The content is primarily opinion-based or does not contain verifiable factual claims.
EVIDENCE: No specific evidence of factual claims found in the segment content."""


def create_mock_rebuttal_gate_response(gate_name: str, passed: bool) -> str:
    """Create a mock rebuttal gate evaluation response."""
    if passed:
        return f"""ANSWER: YES
JUSTIFICATION: The rebuttal content meets the {gate_name} criteria. The counter-arguments are well-supported and effectively address the false claims.
SPECIFIC_ISSUES: None"""
    else:
        issues = {
            "accuracy": "Claim about '70,000 participants' needs citation",
            "completeness": "Missing counter to 'deaths being hidden' claim",
            "sources": "No specific sources cited for FDA data",
            "clarity": "Some technical jargon may confuse general audience"
        }
        return f"""ANSWER: NO
JUSTIFICATION: The rebuttal has issues with {gate_name}. Specific improvements are needed.
SPECIFIC_ISSUES: {issues.get(gate_name, 'General improvements needed')}"""


def create_mock_rewrite_response(original_content: str, failed_gate: str) -> str:
    """Create a mock rebuttal rewrite response."""
    improvements = {
        "accuracy": "According to FDA clinical trial data, the COVID-19 vaccines underwent rigorous Phase 1, 2, and 3 trials involving over 70,000 participants before emergency authorization.",
        "completeness": "Let's address both claims. First, the vaccines were thoroughly tested - Phase 3 trials ran for months with tens of thousands of participants. Second, adverse event data isn't hidden - it's publicly available through VAERS and regularly analyzed by the CDC.",
        "sources": "The FDA's public database shows the Pfizer trial included 43,000 participants (source: FDA.gov BLA approval documents). The CDC's VAERS system has recorded all reported adverse events, which are analyzed weekly.",
        "clarity": "Here's the simple truth: before any vaccine reaches your arm, it goes through three testing phases with thousands of volunteers. These tests check for both effectiveness and side effects. The results are publicly available - anyone can look them up."
    }
    return improvements.get(failed_gate, original_content)


# =============================================================================
# MOCK CLASSES FOR TESTING
# =============================================================================

class MockBinarySegmentFilter:
    """Mock segment filter that doesn't call Gemini API."""

    def __init__(self, config=None):
        self.config = config or {}
        # Define which segments should pass (based on segment_id)
        self.passing_segments = {
            "Harmful_Segment_01",  # Vaccine - clear misinformation
            "Harmful_Segment_02",  # Election - clear misinformation
            "Harmful_Segment_05",  # 5G - clear misinformation
            "Harmful_Segment_08",  # Medical treatment - clear misinformation
        }
        self.failing_segments = {
            "Harmful_Segment_03": "harm_assessment",  # Climate - less immediate harm
            "Harmful_Segment_04": "claim_detection",  # Opinion only
            "Harmful_Segment_06": "claim_detection",  # Personal anecdote
            "Harmful_Segment_07": "verifiability",    # Vague conspiracy
        }

    def filter_segments(self, segments, output_path=None):
        """Mock filter that returns predetermined results."""
        passed = []
        rejected = []

        for segment in segments:
            seg_id = segment.get('segment_id', '')

            if seg_id in self.passing_segments:
                segment_copy = segment.copy()
                segment_copy['binary_filter_results'] = {
                    'segment_id': seg_id,
                    'passed': True,
                    'gate_results': {
                        'claim_detection': {'passed': True, 'justification': 'Contains factual claim'},
                        'verifiability': {'passed': True, 'justification': 'Claim is verifiable'},
                        'accuracy_check': {'passed': True, 'justification': 'Claim is false'},
                        'harm_assessment': {'passed': True, 'justification': 'Could cause harm'},
                        'rebuttability': {'passed': True, 'justification': 'Can be rebutted'},
                    }
                }
                passed.append(segment_copy)
            else:
                failed_gate = self.failing_segments.get(seg_id, 'claim_detection')
                segment_copy = segment.copy()
                segment_copy['binary_filter_results'] = {
                    'segment_id': seg_id,
                    'passed': False,
                    'failed_at': failed_gate,
                    'rejection_reason': f'Failed {failed_gate} gate',
                    'gate_results': {}
                }
                rejected.append(segment_copy)

        metadata = {
            'filtering_timestamp': datetime.now().isoformat(),
            'total_segments': len(segments),
            'passed_count': len(passed),
            'rejected_count': len(rejected),
            'pass_rate': len(passed) / len(segments) if segments else 0
        }

        return passed, rejected, metadata

    def filter_segment(self, segment):
        """Mock single segment filter."""
        from binary_segment_filter import FilterResult

        seg_id = segment.get('segment_id', '')

        if seg_id in self.passing_segments:
            return FilterResult(
                segment_id=seg_id,
                passed=True,
                gate_results={
                    'claim_detection': {'passed': True, 'justification': 'OK'},
                    'verifiability': {'passed': True, 'justification': 'OK'},
                    'accuracy_check': {'passed': True, 'justification': 'OK'},
                    'harm_assessment': {'passed': True, 'justification': 'OK'},
                    'rebuttability': {'passed': True, 'justification': 'OK'},
                }
            )
        else:
            failed_gate = self.failing_segments.get(seg_id, 'claim_detection')
            return FilterResult(
                segment_id=seg_id,
                passed=False,
                failed_at=failed_gate,
                rejection_reason=f'Failed {failed_gate}',
                gate_results={}
            )


class MockBinaryRebuttalVerifier:
    """Mock rebuttal verifier that doesn't call Gemini API."""

    def __init__(self, config=None):
        self.config = config or {}
        self.max_iterations = 3

    def verify_script_rebuttals(self, script_data, output_path=None):
        """Mock verification that passes all rebuttals after 1-2 iterations."""
        sections = script_data.get('podcast_sections', [])

        total_rebuttals = 0
        total_rewrites = 0

        for section in sections:
            if section.get('section_type') == 'post_clip':
                total_rebuttals += 1
                # Simulate one rewrite needed for some rebuttals
                if 'citation' not in section.get('script_content', '').lower():
                    total_rewrites += 1
                    # Add mock improvement
                    section['script_content'] = section.get('script_content', '') + " (Source: FDA.gov)"

        metadata = {
            'verification_timestamp': datetime.now().isoformat(),
            'rebuttals_verified': total_rebuttals,
            'total_rewrites': total_rewrites,
            'fully_passed': total_rebuttals,
            'passed_with_warnings': 0
        }

        return script_data, metadata


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_mock_pass1_data() -> List[Dict]:
    """Get mock Pass 1 analysis data."""
    return MOCK_PASS1_SEGMENTS.copy()


def get_mock_script_data() -> Dict:
    """Get mock unified script data."""
    return json.loads(json.dumps(MOCK_UNIFIED_SCRIPT))  # Deep copy


def save_mock_data_to_file(data: Any, filepath: str) -> None:
    """Save mock data to a JSON file."""
    import os
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    # Test mock data generation
    print("Mock Pass 1 Segments:")
    print(f"  Total: {len(MOCK_PASS1_SEGMENTS)}")
    for seg in MOCK_PASS1_SEGMENTS:
        print(f"  - {seg['segment_id']}: {seg['narrativeSegmentTitle']}")

    print("\nMock Script Sections:")
    for section in MOCK_UNIFIED_SCRIPT['podcast_sections']:
        print(f"  - {section['section_type']}: {section['section_id']}")

    print("\nMock filter test:")
    mock_filter = MockBinarySegmentFilter()
    passed, rejected, meta = mock_filter.filter_segments(MOCK_PASS1_SEGMENTS)
    print(f"  Passed: {len(passed)}")
    print(f"  Rejected: {len(rejected)}")
