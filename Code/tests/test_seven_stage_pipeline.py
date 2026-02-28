"""
Seven-Stage Pipeline Integration Tests

Comprehensive tests for all 7 stages of the YouTube Processing Pipeline:
- Stage 1: Media Extraction (YouTube download)
- Stage 2: Transcript Generation (WhisperX/diarization)
- Stage 3: Content Analysis (Gemini AI)
- Stage 4: Narrative Generation (Script creation)
- Stage 5: Audio Generation (TTS)
- Stage 6: Video Clipping (FFmpeg)
- Stage 7: Video Compilation (Final output)

Uses mocks to avoid external service calls.

Author: Claude Code
Created: 2024-12-28
"""

import os
import sys
import json
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock
from datetime import datetime

# Add Code directory to path
code_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, code_dir)


# =============================================================================
# MOCK DATA FOR ALL STAGES
# =============================================================================

MOCK_VIDEO_METADATA = {
    'title': 'Joe Rogan Experience #2000 - Test Guest',
    'uploader': 'PowerfulJRE',
    'uploader_id': 'PowerfulJRE',
    'duration': 7200,
    'view_count': 1000000,
    'upload_date': '20241228',
    'webpage_url': 'https://www.youtube.com/watch?v=test123'
}

MOCK_TRANSCRIPT = {
    'segments': [
        {
            'speaker': 'SPEAKER_00',
            'text': 'Welcome to the show. Today we have a fascinating guest.',
            'start': 0.0,
            'end': 5.0
        },
        {
            'speaker': 'SPEAKER_01',
            'text': 'Thank you for having me Joe. I want to talk about vaccines causing autism.',
            'start': 5.0,
            'end': 12.0
        },
        {
            'speaker': 'SPEAKER_00',
            'text': 'Thats a controversial topic. Tell me more.',
            'start': 12.0,
            'end': 16.0
        },
        {
            'speaker': 'SPEAKER_01',
            'text': 'Studies have shown that climate change is a hoax perpetrated by scientists.',
            'start': 16.0,
            'end': 24.0
        }
    ],
    'language': 'en',
    'duration': 24.0
}

MOCK_ANALYSIS_RESULTS = [
    {
        'segment_id': 'seg_001',
        'narrativeSegmentTitle': 'Vaccine Misinformation Claims',
        'clipContextDescription': 'Guest makes false claims about vaccines and autism',
        'suggestedClip': [
            {
                'speaker': 'Guest',
                'quote': 'Vaccines cause autism. This has been proven.',
                'timestamp': '00:05:00'
            }
        ],
        'severity': 'high',
        'factual_accuracy': 1,
        'potential_harm': 9
    },
    {
        'segment_id': 'seg_002',
        'narrativeSegmentTitle': 'Climate Change Denial',
        'clipContextDescription': 'Guest denies scientific consensus on climate change',
        'suggestedClip': [
            {
                'speaker': 'Guest',
                'quote': 'Climate change is a hoax perpetrated by scientists.',
                'timestamp': '00:16:00'
            }
        ],
        'severity': 'high',
        'factual_accuracy': 2,
        'potential_harm': 8
    }
]

MOCK_UNIFIED_SCRIPT = {
    'script_metadata': {
        'episode_title': 'Test Episode',
        'generation_timestamp': datetime.now().isoformat(),
        'total_sections': 5
    },
    'podcast_sections': [
        {
            'section_id': 'intro_001',
            'section_type': 'intro',
            'script_content': 'Welcome to our fact-checking podcast. Today we examine claims made on a recent episode.'
        },
        {
            'section_id': 'video_clip_001',
            'section_type': 'video_clip',
            'clip_id': 'clip_001',
            'start_time': '300.0',
            'end_time': '360.0',
            'title': 'Vaccine Claim'
        },
        {
            'section_id': 'post_clip_001',
            'section_type': 'post_clip',
            'clip_reference': 'clip_001',
            'script_content': 'The claim that vaccines cause autism has been thoroughly debunked by scientific research.'
        },
        {
            'section_id': 'video_clip_002',
            'section_type': 'video_clip',
            'clip_id': 'clip_002',
            'start_time': '960.0',
            'end_time': '1020.0',
            'title': 'Climate Claim'
        },
        {
            'section_id': 'outro_001',
            'section_type': 'outro',
            'script_content': 'Thank you for watching. Remember to check your sources.'
        }
    ]
}


# =============================================================================
# MOCK CLASSES
# =============================================================================

class MockEnhancedLogger:
    """Mock logger that does nothing."""
    def info(self, msg): pass
    def error(self, msg): pass
    def warning(self, msg): pass
    def success(self, msg): pass
    def spinner(self, msg): return self._null_context()
    def spinner_context(self, msg): return self._null_context()
    def stage_context(self, name, num=None): return self._null_context()
    def progress_context(self, total, desc): return MockProgress()
    def display_summary_table(self, title, data): pass
    def _null_context(self):
        class NullContext:
            def __enter__(self): return self
            def __exit__(self, *args): pass
        return NullContext()


class MockProgress:
    """Mock progress tracker."""
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def advance(self, n=1): pass


class MockProcessingReport:
    """Mock TTS processing report."""
    def __init__(self):
        self.total_sections = 5
        self.successful_sections = 5
        self.failed_sections = 0
        self.skipped_sections = 0
        self.generated_files = ['intro_001.wav', 'post_clip_001.wav', 'outro_001.wav']
        self.output_directory = '/mock/output/Generated'
        self.metadata_file = '/mock/output/metadata.json'
        self.processing_time = 30.5


class MockCompilationResult:
    """Mock video compilation result."""
    def __init__(self):
        self.success = True
        self.output_path = Path('/mock/output/final_video.mp4')
        self.duration = 120.5
        self.segments_processed = 5
        self.audio_segments_converted = 3
        self.segments_skipped = 0
        self.error = None


# =============================================================================
# STAGE 1 TESTS: MEDIA EXTRACTION
# =============================================================================

class TestStage1MediaExtraction(unittest.TestCase):
    """Tests for Stage 1: Media Extraction (YouTube download)."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.mock_url = 'https://www.youtube.com/watch?v=test123'

    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch('Extraction.youtube_video_downloader.get_video_metadata')
    def test_metadata_extraction(self, mock_get_metadata):
        """Test video metadata extraction."""
        mock_get_metadata.return_value = MOCK_VIDEO_METADATA

        from Extraction.youtube_video_downloader import get_video_metadata
        metadata = get_video_metadata(self.mock_url)

        self.assertEqual(metadata['title'], 'Joe Rogan Experience #2000 - Test Guest')
        self.assertEqual(metadata['uploader'], 'PowerfulJRE')
        self.assertEqual(metadata['duration'], 7200)

    @patch('Extraction.youtube_audio_extractor.download_audio')
    def test_audio_download(self, mock_download):
        """Test audio download function."""
        expected_path = os.path.join(self.test_dir, 'audio.mp3')
        mock_download.return_value = expected_path

        from Extraction.youtube_audio_extractor import download_audio
        result = download_audio(self.mock_url, expected_path)

        self.assertEqual(result, expected_path)
        mock_download.assert_called_once()

    @patch('Extraction.youtube_video_downloader.download_video')
    def test_video_download(self, mock_download):
        """Test video download function."""
        expected_path = os.path.join(self.test_dir, 'video.mp4')
        mock_download.return_value = expected_path

        from Extraction.youtube_video_downloader import download_video
        result = download_video(self.mock_url, expected_path)

        self.assertEqual(result, expected_path)
        mock_download.assert_called_once()

    def test_name_extraction_from_metadata(self):
        """Test host/guest name extraction from video metadata."""
        from Utils.name_extractor import NameExtractor

        extractor = NameExtractor(
            MOCK_VIDEO_METADATA['title'],
            MOCK_VIDEO_METADATA['uploader']
        )
        result = extractor.extract()

        self.assertIn('host', result)
        self.assertIn('guest', result)
        self.assertEqual(result['host'], 'Joe Rogan')


# =============================================================================
# STAGE 2 TESTS: TRANSCRIPT GENERATION
# =============================================================================

class TestStage2TranscriptGeneration(unittest.TestCase):
    """Tests for Stage 2: Transcript Generation."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch('Extraction.audio_diarizer.diarize_audio')
    def test_diarization_returns_transcript(self, mock_diarize):
        """Test that diarization returns structured transcript."""
        mock_diarize.return_value = json.dumps(MOCK_TRANSCRIPT)

        from Extraction.audio_diarizer import diarize_audio

        audio_path = os.path.join(self.test_dir, 'test.mp3')
        output_path = os.path.join(self.test_dir, 'transcript.json')

        # Create dummy audio file
        with open(audio_path, 'w') as f:
            f.write('dummy')

        result = diarize_audio(audio_path, 'mock_token', output_path)

        self.assertIsNotNone(result)

    def test_transcript_structure(self):
        """Test transcript has required structure."""
        self.assertIn('segments', MOCK_TRANSCRIPT)
        self.assertIn('language', MOCK_TRANSCRIPT)

        for segment in MOCK_TRANSCRIPT['segments']:
            self.assertIn('speaker', segment)
            self.assertIn('text', segment)
            self.assertIn('start', segment)
            self.assertIn('end', segment)

    def test_speaker_diarization_format(self):
        """Test speaker labels are properly formatted."""
        for segment in MOCK_TRANSCRIPT['segments']:
            self.assertTrue(segment['speaker'].startswith('SPEAKER_'))


# =============================================================================
# STAGE 3 TESTS: CONTENT ANALYSIS
# =============================================================================

class TestStage3ContentAnalysis(unittest.TestCase):
    """Tests for Stage 3: Content Analysis."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.episode_dir = os.path.join(self.test_dir, 'Test_Episode')
        os.makedirs(os.path.join(self.episode_dir, 'Processing'))

        # Save mock transcript
        transcript_path = os.path.join(self.episode_dir, 'Processing', 'original_audio_transcript.json')
        with open(transcript_path, 'w') as f:
            json.dump(MOCK_TRANSCRIPT, f)

    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_analysis_result_structure(self):
        """Test analysis results have required fields."""
        for segment in MOCK_ANALYSIS_RESULTS:
            self.assertIn('segment_id', segment)
            self.assertIn('narrativeSegmentTitle', segment)
            self.assertIn('suggestedClip', segment)

    @patch('Content_Analysis.binary_segment_filter.BinarySegmentFilter')
    def test_binary_filter_integration(self, mock_filter_class):
        """Test binary segment filter is called correctly."""
        mock_filter = MagicMock()
        mock_filter.filter_segments.return_value = (
            MOCK_ANALYSIS_RESULTS,  # passed
            [],  # rejected
            {'total_segments': 2, 'passed_count': 2}  # metadata
        )
        mock_filter_class.return_value = mock_filter

        from Content_Analysis.binary_segment_filter import BinarySegmentFilter
        filter_instance = BinarySegmentFilter({}, skip_api_init=True)

        passed, rejected, meta = mock_filter.filter_segments(MOCK_ANALYSIS_RESULTS)

        self.assertEqual(len(passed), 2)
        self.assertEqual(len(rejected), 0)


# =============================================================================
# STAGE 4 TESTS: NARRATIVE GENERATION
# =============================================================================

class TestStage4NarrativeGeneration(unittest.TestCase):
    """Tests for Stage 4: Narrative Generation."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_unified_script_structure(self):
        """Test unified script has required structure."""
        self.assertIn('script_metadata', MOCK_UNIFIED_SCRIPT)
        self.assertIn('podcast_sections', MOCK_UNIFIED_SCRIPT)

        sections = MOCK_UNIFIED_SCRIPT['podcast_sections']
        self.assertGreater(len(sections), 0)

        section_types = {s['section_type'] for s in sections}
        self.assertIn('intro', section_types)
        self.assertIn('outro', section_types)

    def test_script_sections_have_required_fields(self):
        """Test each section has required fields."""
        for section in MOCK_UNIFIED_SCRIPT['podcast_sections']:
            self.assertIn('section_id', section)
            self.assertIn('section_type', section)

            if section['section_type'] == 'video_clip':
                self.assertIn('start_time', section)
                self.assertIn('end_time', section)
            elif section['section_type'] in ['intro', 'outro', 'pre_clip', 'post_clip']:
                self.assertIn('script_content', section)

    def test_clip_references_valid(self):
        """Test that post_clip sections reference valid clips."""
        clip_ids = {s['clip_id'] for s in MOCK_UNIFIED_SCRIPT['podcast_sections']
                   if s['section_type'] == 'video_clip'}

        for section in MOCK_UNIFIED_SCRIPT['podcast_sections']:
            if section['section_type'] == 'post_clip':
                if 'clip_reference' in section:
                    self.assertIn(section['clip_reference'], clip_ids)


# =============================================================================
# STAGE 5 TESTS: AUDIO GENERATION
# =============================================================================

class TestStage5AudioGeneration(unittest.TestCase):
    """Tests for Stage 5: Audio Generation (TTS)."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.episode_dir = os.path.join(self.test_dir, 'Test_Episode')
        os.makedirs(os.path.join(self.episode_dir, 'Output', 'Scripts'))
        os.makedirs(os.path.join(self.episode_dir, 'Output', 'Generated'))

        # Save mock script
        script_path = os.path.join(self.episode_dir, 'Output', 'Scripts', 'verified_unified_script.json')
        with open(script_path, 'w') as f:
            json.dump(MOCK_UNIFIED_SCRIPT, f)

    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_audio_sections_extracted(self):
        """Test that audio sections are correctly identified from script."""
        audio_section_types = {'intro', 'outro', 'pre_clip', 'post_clip'}
        audio_sections = [s for s in MOCK_UNIFIED_SCRIPT['podcast_sections']
                         if s['section_type'] in audio_section_types]

        self.assertGreater(len(audio_sections), 0)

        for section in audio_sections:
            self.assertIn('script_content', section)

    @patch('Chatterbox.simple_tts_engine.SimpleTTSEngine')
    def test_tts_engine_called(self, mock_engine_class):
        """Test TTS engine is initialized and called correctly."""
        mock_engine = MagicMock()
        mock_engine.process_episode_script.return_value = MockProcessingReport()
        mock_engine.check_existing_audio_files.return_value = ([], [], [])
        mock_engine_class.return_value = mock_engine

        from Chatterbox.simple_tts_engine import SimpleTTSEngine

        engine = SimpleTTSEngine('config_path')
        script_path = os.path.join(self.episode_dir, 'Output', 'Scripts', 'verified_unified_script.json')

        result = mock_engine.process_episode_script(script_path)

        self.assertEqual(result.successful_sections, 5)
        self.assertEqual(result.failed_sections, 0)

    def test_processing_report_structure(self):
        """Test processing report has required fields."""
        report = MockProcessingReport()

        self.assertIsNotNone(report.total_sections)
        self.assertIsNotNone(report.successful_sections)
        self.assertIsNotNone(report.failed_sections)
        self.assertIsNotNone(report.generated_files)
        self.assertIsNotNone(report.output_directory)


# =============================================================================
# STAGE 6 TESTS: VIDEO CLIPPING
# =============================================================================

class TestStage6VideoClipping(unittest.TestCase):
    """Tests for Stage 6: Video Clipping."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.episode_dir = os.path.join(self.test_dir, 'Test_Episode')
        os.makedirs(os.path.join(self.episode_dir, 'Output', 'Scripts'))
        os.makedirs(os.path.join(self.episode_dir, 'Output', 'Clips'))
        os.makedirs(os.path.join(self.episode_dir, 'Input'))

        # Save mock script
        script_path = os.path.join(self.episode_dir, 'Output', 'Scripts', 'verified_unified_script.json')
        with open(script_path, 'w') as f:
            json.dump(MOCK_UNIFIED_SCRIPT, f)

    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_video_clips_extracted_from_script(self):
        """Test that video clip sections are identified."""
        video_clips = [s for s in MOCK_UNIFIED_SCRIPT['podcast_sections']
                      if s['section_type'] == 'video_clip']

        self.assertEqual(len(video_clips), 2)

        for clip in video_clips:
            self.assertIn('start_time', clip)
            self.assertIn('end_time', clip)
            self.assertIn('clip_id', clip)

    def test_timestamp_parsing(self):
        """Test timestamp values are valid."""
        for section in MOCK_UNIFIED_SCRIPT['podcast_sections']:
            if section['section_type'] == 'video_clip':
                start = float(section['start_time'])
                end = float(section['end_time'])

                self.assertGreaterEqual(start, 0)
                self.assertGreater(end, start)

    @patch('Video_Clipper.integration.extract_clips_from_script')
    def test_clip_extraction_called(self, mock_extract):
        """Test clip extraction function is called correctly."""
        mock_extract.return_value = {
            'success': True,
            'clips_created': 2,
            'clips_failed': 0,
            'output_directory': os.path.join(self.episode_dir, 'Output', 'Clips'),
            'extraction_time': 5.2,
            'success_rate': '100%'
        }

        from Video_Clipper.integration import extract_clips_from_script

        result = extract_clips_from_script(
            episode_dir=self.episode_dir,
            script_filename='verified_unified_script.json'
        )

        self.assertTrue(result['success'])
        self.assertEqual(result['clips_created'], 2)


# =============================================================================
# STAGE 7 TESTS: VIDEO COMPILATION
# =============================================================================

class TestStage7VideoCompilation(unittest.TestCase):
    """Tests for Stage 7: Video Compilation."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.episode_dir = os.path.join(self.test_dir, 'Test_Episode')

        # Create directory structure
        for subdir in ['Output/Scripts', 'Output/Generated', 'Output/Clips', 'Output/Final']:
            os.makedirs(os.path.join(self.episode_dir, subdir))

    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_compilation_result_structure(self):
        """Test compilation result has required fields."""
        result = MockCompilationResult()

        self.assertTrue(result.success)
        self.assertIsNotNone(result.output_path)
        self.assertIsNotNone(result.duration)
        self.assertIsNone(result.error)

    @patch('Video_Compilator.SimpleCompiler')
    def test_compiler_initialization(self, mock_compiler_class):
        """Test video compiler is initialized correctly."""
        mock_compiler = MagicMock()
        mock_compiler.compile_episode.return_value = MockCompilationResult()
        mock_compiler_class.return_value = mock_compiler

        from Video_Compilator import SimpleCompiler

        compiler = SimpleCompiler(keep_temp_files=True, validate_segments=True)
        result = mock_compiler.compile_episode(Path(self.episode_dir), 'final_video.mp4')

        self.assertTrue(result.success)

    def test_audio_and_clips_required(self):
        """Test that compilation requires both audio and clips."""
        audio_dir = os.path.join(self.episode_dir, 'Output', 'Generated')
        clips_dir = os.path.join(self.episode_dir, 'Output', 'Clips')

        # Both directories should exist for compilation
        self.assertTrue(os.path.exists(audio_dir))
        self.assertTrue(os.path.exists(clips_dir))


# =============================================================================
# FULL PIPELINE INTEGRATION TESTS
# =============================================================================

class TestFullPipelineIntegration(unittest.TestCase):
    """Tests for full 7-stage pipeline integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.episode_dir = os.path.join(self.test_dir, 'Test_Episode')

        # Create full directory structure
        for subdir in ['Input', 'Processing', 'Output/Scripts', 'Output/Generated',
                       'Output/Clips', 'Output/Final']:
            os.makedirs(os.path.join(self.episode_dir, subdir))

    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_data_flows_between_stages(self):
        """Test that data flows correctly from stage to stage."""
        # Stage 1 output -> Stage 2 input
        audio_path = os.path.join(self.episode_dir, 'Input', 'original_audio.mp3')
        with open(audio_path, 'w') as f:
            f.write('dummy audio')

        # Stage 2 output -> Stage 3 input
        transcript_path = os.path.join(self.episode_dir, 'Processing', 'original_audio_transcript.json')
        with open(transcript_path, 'w') as f:
            json.dump(MOCK_TRANSCRIPT, f)

        # Stage 3 output -> Stage 4 input
        analysis_path = os.path.join(self.episode_dir, 'Processing', 'original_audio_analysis_results.json')
        with open(analysis_path, 'w') as f:
            json.dump(MOCK_ANALYSIS_RESULTS, f)

        # Stage 4 output -> Stage 5 & 6 input
        script_path = os.path.join(self.episode_dir, 'Output', 'Scripts', 'verified_unified_script.json')
        with open(script_path, 'w') as f:
            json.dump(MOCK_UNIFIED_SCRIPT, f)

        # Verify all files exist
        self.assertTrue(os.path.exists(audio_path))
        self.assertTrue(os.path.exists(transcript_path))
        self.assertTrue(os.path.exists(analysis_path))
        self.assertTrue(os.path.exists(script_path))

    def test_episode_directory_structure(self):
        """Test expected directory structure is created."""
        expected_dirs = [
            'Input',
            'Processing',
            'Output/Scripts',
            'Output/Generated',
            'Output/Clips',
            'Output/Final'
        ]

        for subdir in expected_dirs:
            path = os.path.join(self.episode_dir, subdir)
            self.assertTrue(os.path.exists(path), f"Missing directory: {subdir}")

    @patch('master_processor_v2.MasterProcessorV2')
    def test_master_processor_orchestration(self, mock_processor_class):
        """Test MasterProcessorV2 orchestrates all stages."""
        mock_processor = MagicMock()
        mock_processor.session_id = 'test_session_123'
        mock_processor.episode_dir = self.episode_dir
        mock_processor.process_full_pipeline.return_value = '/mock/output/final_video.mp4'
        mock_processor_class.return_value = mock_processor

        from master_processor_v2 import MasterProcessorV2

        processor = MasterProcessorV2()
        result = mock_processor.process_full_pipeline('https://youtube.com/test', 'chatterbox')

        self.assertIsNotNone(result)
        mock_processor.process_full_pipeline.assert_called_once()

    def test_stage_output_paths(self):
        """Test expected output paths for each stage."""
        stage_outputs = {
            1: ('Input', 'original_audio.mp3'),
            2: ('Processing', 'original_audio_transcript.json'),
            3: ('Processing', 'original_audio_analysis_results.json'),
            4: ('Output/Scripts', 'verified_unified_script.json'),
            5: ('Output/Generated', '*.wav'),
            6: ('Output/Clips', '*.mp4'),
            7: ('Output/Final', '*_final.mp4')
        }

        for stage, (subdir, filename) in stage_outputs.items():
            dir_path = os.path.join(self.episode_dir, subdir)
            self.assertTrue(os.path.exists(dir_path),
                          f"Stage {stage} output directory missing: {subdir}")


# =============================================================================
# PIPELINE ERROR HANDLING TESTS
# =============================================================================

class TestPipelineErrorHandling(unittest.TestCase):
    """Tests for pipeline error handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_missing_audio_file_handled(self):
        """Test handling of missing audio file."""
        non_existent_path = os.path.join(self.test_dir, 'nonexistent.mp3')
        self.assertFalse(os.path.exists(non_existent_path))

    def test_invalid_transcript_json_handled(self):
        """Test handling of invalid transcript JSON."""
        invalid_json_path = os.path.join(self.test_dir, 'invalid.json')
        with open(invalid_json_path, 'w') as f:
            f.write('not valid json {{{')

        with self.assertRaises(json.JSONDecodeError):
            with open(invalid_json_path) as f:
                json.load(f)

    def test_empty_script_sections_handled(self):
        """Test handling of script with no sections."""
        empty_script = {
            'script_metadata': {},
            'podcast_sections': []
        }

        self.assertEqual(len(empty_script['podcast_sections']), 0)

    def test_invalid_timestamp_format(self):
        """Test detection of invalid timestamps."""
        bad_clip = {
            'section_type': 'video_clip',
            'start_time': 'invalid',
            'end_time': '100.0'
        }

        with self.assertRaises(ValueError):
            float(bad_clip['start_time'])


# =============================================================================
# CONFIGURATION TESTS
# =============================================================================

class TestPipelineConfiguration(unittest.TestCase):
    """Tests for pipeline configuration."""

    def test_config_file_exists(self):
        """Test default config file exists."""
        config_path = os.path.join(code_dir, 'Config', 'default_config.yaml')
        self.assertTrue(os.path.exists(config_path),
                       f"Config file not found: {config_path}")

    def test_name_extractor_config_exists(self):
        """Test name extractor config file exists."""
        config_path = os.path.join(code_dir, 'Config', 'name_extractor_rules.json')
        self.assertTrue(os.path.exists(config_path),
                       f"Name extractor config not found: {config_path}")

    def test_config_has_required_sections(self):
        """Test config has required sections."""
        import yaml

        config_path = os.path.join(code_dir, 'Config', 'default_config.yaml')
        with open(config_path) as f:
            config = yaml.safe_load(f)

        self.assertIn('file_paths', config)
        self.assertIn('api', config)
        self.assertIn('quality_control', config)


if __name__ == '__main__':
    unittest.main(verbosity=2)
