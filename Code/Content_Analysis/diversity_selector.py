"""
Diversity Selector - Topic-Aware Segment Selection

This module ensures topic diversity in selected segments, preventing all segments
from clustering around the same topic. Uses keyword extraction and topic grouping
to select a balanced mix of content.

Author: Claude Code
Created: 2024-12-28
Pipeline: Multi-Pass Quality Control System
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


class DiversitySelector:
    """
    Ensures topic diversity in segment selection.

    After binary filtering, segments may cluster around popular topics.
    This module ensures variety by:
    1. Extracting topics from each segment
    2. Grouping segments by topic similarity
    3. Selecting round-robin from each topic group
    4. Ensuring minimum topic coverage
    """

    # Common topic keywords for clustering
    TOPIC_KEYWORDS = {
        'health': ['vaccine', 'health', 'medical', 'doctor', 'treatment', 'disease', 'covid', 'virus', 'drug', 'pharma'],
        'politics': ['election', 'vote', 'democrat', 'republican', 'government', 'policy', 'political', 'president', 'congress'],
        'media': ['media', 'news', 'journalist', 'cnn', 'fox', 'mainstream', 'propaganda', 'coverage', 'narrative'],
        'science': ['science', 'research', 'study', 'scientist', 'data', 'evidence', 'climate', 'evolution'],
        'conspiracy': ['conspiracy', 'hidden', 'secret', 'cover-up', 'truth', 'control', 'agenda', 'deep state'],
        'economics': ['economy', 'money', 'inflation', 'taxes', 'bank', 'financial', 'market', 'wealth'],
        'technology': ['tech', 'ai', 'social media', 'facebook', 'google', 'censorship', 'algorithm', 'platform'],
        'society': ['culture', 'society', 'education', 'children', 'family', 'community', 'values'],
    }

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the DiversitySelector.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        qc_config = self.config.get('quality_control', {}).get('diversity', {})

        self.min_segments = qc_config.get('min_segments', 6)
        self.max_segments = qc_config.get('max_segments', 12)
        self.max_per_topic = qc_config.get('max_per_topic', 3)

    def select_diverse(
        self,
        segments: List[Dict],
        min_count: Optional[int] = None,
        max_count: Optional[int] = None
    ) -> List[Dict]:
        """
        Select a diverse set of segments ensuring topic variety.

        Args:
            segments: List of segments that passed filtering
            min_count: Minimum segments to select
            max_count: Maximum segments to select

        Returns:
            List of selected segments with topic diversity
        """
        min_count = min_count or self.min_segments
        max_count = max_count or self.max_segments

        if len(segments) <= min_count:
            logger.info(f"Only {len(segments)} segments available, returning all")
            return segments

        logger.info(f"Selecting diverse segments from {len(segments)} candidates")

        # Extract topics for each segment
        segment_topics = []
        for segment in segments:
            topics = self._extract_topics(segment)
            segment_topics.append({
                'segment': segment,
                'topics': topics,
                'primary_topic': topics[0] if topics else 'general'
            })

        # Group by primary topic
        topic_groups = defaultdict(list)
        for item in segment_topics:
            topic_groups[item['primary_topic']].append(item['segment'])

        # Sort each topic group by quality signals (best first)
        for topic in topic_groups:
            topic_groups[topic] = sorted(
                topic_groups[topic],
                key=lambda s: self._quality_score(s),
                reverse=True
            )

        logger.info(f"Found {len(topic_groups)} topic groups: {list(topic_groups.keys())}")

        # Round-robin selection from each topic group
        selected = []
        topic_counts = defaultdict(int)

        # First pass: take the best from each topic
        for topic, group_segments in topic_groups.items():
            if group_segments and len(selected) < max_count:
                selected.append(group_segments[0])
                topic_counts[topic] = 1

        # Second pass: round-robin until max reached
        iteration = 0
        max_iterations = max_count * 2  # Safety limit

        while len(selected) < max_count and iteration < max_iterations:
            added_this_round = False

            for topic, group_segments in topic_groups.items():
                if len(selected) >= max_count:
                    break

                # Check if we can add more from this topic
                if topic_counts[topic] < self.max_per_topic:
                    # Find next unselected segment from this topic
                    for seg in group_segments:
                        if seg not in selected:
                            selected.append(seg)
                            topic_counts[topic] += 1
                            added_this_round = True
                            break

            if not added_this_round:
                break

            iteration += 1

        # Log selection summary
        logger.info(f"Selected {len(selected)} segments with topic distribution:")
        for topic, count in sorted(topic_counts.items(), key=lambda x: -x[1]):
            logger.info(f"  {topic}: {count} segments")

        return selected

    def _quality_score(self, segment: Dict) -> float:
        """
        Compute a quality score for sorting within topic groups.
        Higher is better. Uses severity, gate results, and confidence.
        """
        score = 0.0

        # Severity rating
        severity_map = {'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1, 'HOOK': 5}
        severity = segment.get('severity_rating', segment.get('severity_level', ''))
        if isinstance(severity, str):
            score += severity_map.get(severity.upper(), 0)

        # Gate results: count passed gates
        filter_results = segment.get('binary_filter_results', {})
        gate_results = filter_results.get('gate_results', {})
        if gate_results:
            passed = sum(1 for g in gate_results.values() if g.get('passed'))
            score += passed

        # Confidence level
        confidence_map = {'high': 3, 'medium': 2, 'low': 1}
        confidence = segment.get('confidence_level', '')
        if isinstance(confidence, str):
            score += confidence_map.get(confidence.lower(), 0)

        return score

    def _extract_topics(self, segment: Dict) -> List[str]:
        """
        Extract topic labels from a segment based on content keywords.

        Args:
            segment: Segment dictionary

        Returns:
            List of topic labels, most relevant first
        """
        # Combine all text content for analysis
        text_parts = []

        if 'narrativeSegmentTitle' in segment:
            text_parts.append(segment['narrativeSegmentTitle'])

        if 'clipContextDescription' in segment:
            text_parts.append(segment['clipContextDescription'])

        if 'suggestedClip' in segment:
            for clip in segment['suggestedClip']:
                if 'quote' in clip:
                    text_parts.append(clip['quote'])

        combined_text = ' '.join(text_parts).lower()

        # Score each topic
        topic_scores = {}
        for topic, keywords in self.TOPIC_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                # Count keyword occurrences
                score += len(re.findall(r'\b' + re.escape(keyword) + r'\b', combined_text))
            if score > 0:
                topic_scores[topic] = score

        # Sort by score
        sorted_topics = sorted(topic_scores.items(), key=lambda x: -x[1])

        if sorted_topics:
            return [t[0] for t in sorted_topics]
        else:
            return ['general']

    def get_topic_distribution(self, segments: List[Dict]) -> Dict[str, int]:
        """
        Get the topic distribution for a set of segments.

        Args:
            segments: List of segments

        Returns:
            Dictionary mapping topics to counts
        """
        distribution = defaultdict(int)

        for segment in segments:
            topics = self._extract_topics(segment)
            primary_topic = topics[0] if topics else 'general'
            distribution[primary_topic] += 1

        return dict(distribution)


if __name__ == "__main__":
    # Simple test
    test_segments = [
        {'segment_id': '1', 'narrativeSegmentTitle': 'Vaccine claims about safety'},
        {'segment_id': '2', 'narrativeSegmentTitle': 'Election fraud allegations'},
        {'segment_id': '3', 'narrativeSegmentTitle': 'Media bias in coverage'},
        {'segment_id': '4', 'narrativeSegmentTitle': 'More vaccine misinformation'},
        {'segment_id': '5', 'narrativeSegmentTitle': 'Climate science denial'},
    ]

    selector = DiversitySelector()
    selected = selector.select_diverse(test_segments, min_count=3, max_count=4)

    print(f"\nSelected {len(selected)} diverse segments:")
    for seg in selected:
        print(f"  - {seg['segment_id']}: {seg['narrativeSegmentTitle']}")
