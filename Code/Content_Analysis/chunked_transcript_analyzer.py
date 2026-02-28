"""
Chunked Transcript Analyzer - Splits long transcripts for better Gemini analysis.

Long transcripts (e.g., 3-hour podcasts) overwhelm Gemini's attention when analyzed
in a single API call, producing thin, short clips. This module splits transcripts
into ~25-minute time windows with overlap, analyzes each chunk independently, then
merges and deduplicates results.

Wraps existing transcript_analyzer.py functions — no modifications to working
analysis code.

Author: Claude Code
Created: 2026-02-28
Pipeline: Multi-Pass Quality Control System
"""

import os
import sys
import json
import time
import math
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

# Add paths for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
utils_dir = os.path.join(current_dir, '..', 'Utils')
code_dir = os.path.join(current_dir, '..')

for path in [utils_dir, current_dir, code_dir]:
    if path not in sys.path:
        sys.path.append(path)

# Import existing transcript analysis functions
try:
    from .transcript_analyzer import (
        upload_transcript_to_gemini,
        analyze_with_gemini_file_upload,
        load_episode_metadata_from_path,
    )
except ImportError:
    try:
        from Content_Analysis.transcript_analyzer import (
            upload_transcript_to_gemini,
            analyze_with_gemini_file_upload,
            load_episode_metadata_from_path,
        )
    except ImportError:
        from transcript_analyzer import (
            upload_transcript_to_gemini,
            analyze_with_gemini_file_upload,
            load_episode_metadata_from_path,
        )

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


class ChunkedTranscriptAnalyzer:
    """
    Splits long transcripts into time-windowed chunks, analyzes each with
    existing Gemini analysis functions, then merges and deduplicates results.
    """

    def __init__(self, config: Dict[str, Any], enhanced_logger=None):
        self.config = config
        self.enhanced_logger = enhanced_logger or self._create_fallback_logger()

        # Chunked analysis config
        chunk_config = config.get('chunked_analysis', {})
        self.chunk_duration_minutes = chunk_config.get('chunk_duration_minutes', 25)
        self.chunk_overlap_minutes = chunk_config.get('chunk_overlap_minutes', 3)
        self.max_chunks = chunk_config.get('max_chunks', 12)
        self.segments_per_chunk = chunk_config.get('segments_per_chunk', 5)
        self.dedup_overlap_threshold = chunk_config.get('dedup_overlap_threshold', 0.5)
        self.delay_between_chunks = chunk_config.get('delay_between_chunks', 5)

    def _create_fallback_logger(self):
        class FallbackLogger:
            def info(self, msg): logger.info(msg)
            def error(self, msg): logger.error(msg)
            def warning(self, msg): logger.warning(msg)
            def success(self, msg): logger.info(f"SUCCESS: {msg}")
        return FallbackLogger()

    def analyze_transcript(
        self,
        transcript_path: str,
        analysis_rules: str,
        processing_dir: str,
        total_target_segments: int = 20,
    ) -> Optional[str]:
        """
        Main entry point: chunk, analyze, merge, return JSON string.

        Args:
            transcript_path: Path to the transcript JSON file
            analysis_rules: Full analysis rules text (including guest profile)
            processing_dir: Directory for intermediate files
            total_target_segments: Target number of segments in final output

        Returns:
            JSON string of merged analysis results, or None on failure
        """
        # Load transcript to determine duration
        with open(transcript_path, 'r', encoding='utf-8') as f:
            transcript_data = json.load(f)

        segments = transcript_data.get('segments', [])
        if not segments:
            logger.error("No segments found in transcript")
            return None

        # Calculate total duration
        total_duration_seconds = self._get_total_duration(segments)
        total_duration_minutes = total_duration_seconds / 60

        self.enhanced_logger.info(
            f"  Transcript duration: {total_duration_minutes:.1f} minutes"
        )

        # If short enough, skip chunking
        if total_duration_minutes <= 30:
            self.enhanced_logger.info("  Transcript under 30 min — using single-call analysis")
            return self._single_call_analysis(
                transcript_path, analysis_rules, processing_dir
            )

        # Chunk the transcript
        chunks = self._chunk_transcript(transcript_data, segments)
        num_chunks = len(chunks)

        self.enhanced_logger.info(
            f"  Split into {num_chunks} chunks "
            f"(~{self.chunk_duration_minutes} min each, "
            f"{self.chunk_overlap_minutes} min overlap)"
        )

        # Calculate per-chunk segment target
        per_chunk_target = math.ceil(total_target_segments / num_chunks) + 1

        # Create chunks directory
        chunks_dir = os.path.join(processing_dir, 'chunks')
        os.makedirs(chunks_dir, exist_ok=True)

        # Analyze each chunk
        all_chunk_results = []
        for i, chunk in enumerate(chunks):
            chunk_num = i + 1
            self.enhanced_logger.info(
                f"  Analyzing chunk {chunk_num}/{num_chunks} "
                f"({chunk['start_min']:.1f}-{chunk['end_min']:.1f} min, "
                f"{len(chunk['segments'])} segments)..."
            )

            # Check for cached chunk result
            chunk_result_path = os.path.join(
                chunks_dir, f'chunk_{chunk_num:03d}_results.json'
            )
            if os.path.exists(chunk_result_path):
                self.enhanced_logger.info(f"    Using cached result for chunk {chunk_num}")
                with open(chunk_result_path, 'r', encoding='utf-8') as f:
                    chunk_results = json.load(f)
                all_chunk_results.extend(chunk_results)
                continue

            # Write chunk transcript to temp file
            chunk_transcript_path = os.path.join(
                chunks_dir, f'chunk_{chunk_num:03d}_transcript.json'
            )
            chunk_transcript_data = {
                'metadata': transcript_data.get('metadata', {}),
                'segments': chunk['segments'],
                '_chunk_info': {
                    'chunk_number': chunk_num,
                    'total_chunks': num_chunks,
                    'start_seconds': chunk['start_sec'],
                    'end_seconds': chunk['end_sec'],
                }
            }
            with open(chunk_transcript_path, 'w', encoding='utf-8') as f:
                json.dump(chunk_transcript_data, f, indent=2, ensure_ascii=False)

            # Build chunk-specific rules with header
            chunk_rules = self._build_chunk_rules(
                analysis_rules, chunk_num, num_chunks, per_chunk_target,
                chunk['start_min'], chunk['end_min']
            )

            # Analyze this chunk using existing functions
            result = self._analyze_chunk(
                chunk_transcript_path, chunk_rules, chunks_dir
            )

            if result:
                try:
                    chunk_results = json.loads(result)
                    if isinstance(chunk_results, list):
                        # Tag each segment with chunk info
                        for seg in chunk_results:
                            seg['_source_chunk'] = chunk_num

                        # Cache chunk result
                        with open(chunk_result_path, 'w', encoding='utf-8') as f:
                            json.dump(chunk_results, f, indent=2, ensure_ascii=False)

                        all_chunk_results.extend(chunk_results)
                        self.enhanced_logger.info(
                            f"    Chunk {chunk_num}: found {len(chunk_results)} segments"
                        )
                    else:
                        self.enhanced_logger.warning(
                            f"    Chunk {chunk_num}: unexpected result format"
                        )
                except json.JSONDecodeError as e:
                    self.enhanced_logger.warning(
                        f"    Chunk {chunk_num}: JSON parse error - {e}"
                    )
            else:
                self.enhanced_logger.warning(
                    f"    Chunk {chunk_num}: analysis returned no results"
                )

            # Rate limiting between chunks
            if i < num_chunks - 1:
                self.enhanced_logger.info(
                    f"    Waiting {self.delay_between_chunks}s before next chunk..."
                )
                time.sleep(self.delay_between_chunks)

        if not all_chunk_results:
            self.enhanced_logger.error("  No results from any chunk")
            return None

        self.enhanced_logger.info(
            f"  Total segments before dedup: {len(all_chunk_results)}"
        )

        # Merge and deduplicate
        merged = self._merge_results(all_chunk_results)

        self.enhanced_logger.info(
            f"  Total segments after dedup: {len(merged)}"
        )

        # Re-number segment IDs sequentially
        for i, seg in enumerate(merged):
            seg['segment_id'] = f'Harmful_Segment_{i+1:02d}'

        return json.dumps(merged, indent=2, ensure_ascii=False)

    def _get_total_duration(self, segments: List[Dict]) -> float:
        """Get total transcript duration in seconds from segment list."""
        if not segments:
            return 0
        last_seg = segments[-1]
        return float(last_seg.get('end_time', last_seg.get('end', 0)))

    def _chunk_transcript(
        self,
        transcript_data: Dict,
        segments: List[Dict]
    ) -> List[Dict]:
        """Split transcript segments into time-windowed chunks with overlap."""
        chunk_duration_sec = self.chunk_duration_minutes * 60
        overlap_sec = self.chunk_overlap_minutes * 60
        total_duration = self._get_total_duration(segments)

        chunks = []
        chunk_start = 0.0

        while chunk_start < total_duration and len(chunks) < self.max_chunks:
            chunk_end = min(chunk_start + chunk_duration_sec, total_duration)

            # Collect segments that fall within this time window
            chunk_segments = []
            for seg in segments:
                seg_start = float(seg.get('start_time', seg.get('start', 0)))
                seg_end = float(seg.get('end_time', seg.get('end', 0)))

                # Include segment if it overlaps with the chunk window
                if seg_start < chunk_end and seg_end > chunk_start:
                    chunk_segments.append(seg)

            if chunk_segments:
                chunks.append({
                    'start_sec': chunk_start,
                    'end_sec': chunk_end,
                    'start_min': chunk_start / 60,
                    'end_min': chunk_end / 60,
                    'segments': chunk_segments,
                })

            # If we've reached the end of the transcript, stop
            if chunk_end >= total_duration:
                break

            # Move to next chunk with overlap
            chunk_start = chunk_end - overlap_sec

        return chunks

    def _build_chunk_rules(
        self,
        base_rules: str,
        chunk_num: int,
        total_chunks: int,
        per_chunk_target: int,
        start_min: float,
        end_min: float,
    ) -> str:
        """Prepend chunking context header to analysis rules."""
        header = f"""## CHUNKING CONTEXT

**IMPORTANT:** This is chunk {chunk_num} of {total_chunks} from a long podcast transcript.
You are analyzing the portion from {start_min:.1f} to {end_min:.1f} minutes.

**Your target:** Find {per_chunk_target} harmful segments in THIS chunk.
Focus on the strongest, most impactful content within this time window.
Each segment MUST have timestamps that fall within this chunk's time range.

Maintain the same JSON output format and quality standards as described below.

---

"""
        return header + base_rules

    def _analyze_chunk(
        self,
        chunk_transcript_path: str,
        chunk_rules: str,
        output_dir: str,
    ) -> Optional[str]:
        """Analyze a single chunk using existing transcript_analyzer functions."""
        try:
            display_name = f"chunk_{os.path.basename(chunk_transcript_path)}"
            file_object = upload_transcript_to_gemini(
                chunk_transcript_path, display_name
            )

            if not file_object:
                logger.error(f"Failed to upload chunk: {chunk_transcript_path}")
                return None

            result = analyze_with_gemini_file_upload(
                file_object=file_object,
                analysis_rules=chunk_rules,
                output_dir=output_dir,
                file_path=chunk_transcript_path,
            )

            return result

        except Exception as e:
            logger.error(f"Chunk analysis failed: {e}")
            return None

    def _merge_results(self, all_results: List[Dict]) -> List[Dict]:
        """Deduplicate segments from overlapping chunks.

        When two segments have >50% timestamp overlap, keep the one with
        higher severity or longer duration.
        """
        if not all_results:
            return []

        # Sort by start time
        def get_start(seg):
            ts = seg.get('fullerContextTimestamps', {})
            try:
                return float(ts.get('start', 0))
            except (ValueError, TypeError):
                return 0
        all_results.sort(key=get_start)

        # Severity ordering for tie-breaking
        severity_order = {'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}

        merged = []
        for seg in all_results:
            ts = seg.get('fullerContextTimestamps', {})
            try:
                seg_start = float(ts.get('start', 0))
                seg_end = float(ts.get('end', 0))
            except (ValueError, TypeError):
                merged.append(seg)
                continue

            seg_duration = seg_end - seg_start
            if seg_duration <= 0:
                merged.append(seg)
                continue

            # Check for overlap with already-merged segments
            is_duplicate = False
            for i, existing in enumerate(merged):
                ex_ts = existing.get('fullerContextTimestamps', {})
                try:
                    ex_start = float(ex_ts.get('start', 0))
                    ex_end = float(ex_ts.get('end', 0))
                except (ValueError, TypeError):
                    continue

                # Calculate overlap
                overlap_start = max(seg_start, ex_start)
                overlap_end = min(seg_end, ex_end)
                overlap = max(0, overlap_end - overlap_start)

                # Check if overlap exceeds threshold relative to shorter segment
                shorter_duration = min(seg_duration, ex_end - ex_start)
                if shorter_duration > 0 and overlap / shorter_duration > self.dedup_overlap_threshold:
                    # Keep the better one
                    seg_severity = severity_order.get(
                        seg.get('severityRating', ''), 0
                    )
                    ex_severity = severity_order.get(
                        existing.get('severityRating', ''), 0
                    )

                    if seg_severity > ex_severity or (
                        seg_severity == ex_severity and seg_duration > (ex_end - ex_start)
                    ):
                        # Replace existing with new (better) segment
                        merged[i] = seg

                    is_duplicate = True
                    break

            if not is_duplicate:
                merged.append(seg)

        return merged

    def _single_call_analysis(
        self,
        transcript_path: str,
        analysis_rules: str,
        processing_dir: str,
    ) -> Optional[str]:
        """Fallback: analyze entire transcript in one call (short podcasts)."""
        try:
            display_name = f"transcript_{os.path.basename(transcript_path)}"
            file_object = upload_transcript_to_gemini(
                transcript_path, display_name
            )

            if not file_object:
                return None

            result = analyze_with_gemini_file_upload(
                file_object=file_object,
                analysis_rules=analysis_rules,
                output_dir=processing_dir,
                file_path=transcript_path,
            )

            return result

        except Exception as e:
            logger.error(f"Single-call analysis failed: {e}")
            return None
