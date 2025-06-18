# Implementation Plan: TTS API Integration Project

**Project:** Simple TTS API Integration - Replace Chatterbox TTS System  
**Manager Agent:** APM Manager Agent  
**Created:** June 16, 2025  
**Status:** Active  
**Priority:** High  

## Project Overview

### Objective
Replace the current complex Chatterbox TTS system with a simplified API-based approach while maintaining all existing functionality, file organization, and pipeline compatibility.

### Success Criteria
- Sequential API calls work correctly (one request at a time)
- All API interactions logged for debugging
- JSON parsing works with existing `unified_podcast_script.json` format
- Episode directory discovery and file organization maintained
- Master processor Stage 5 integration complete
- Legacy batch processing components removed
- System fails fast on errors (no complex fallbacks)

### Key Constraints
- API server at `localhost:4123` handles only one request at a time
- Must maintain existing directory structure (`Content/Episode/Output/Audio/`)
- Must preserve compatibility with existing JSON format and file organization
- Fail fast approach - no complex error handling or retry mechanisms

## Implementation Phases

### Phase 1: Core Component Development
**Duration:** Week 1 (Days 1-5)  
**Agent Type:** Implementation Agent  

#### Task 1.1: Create SimpleTTSEngine Class
**Assigned to:** Implementation Agent  
**Dependencies:** None  
**Deliverables:**
- `Code/Chatterbox/simple_tts_engine.py` with complete implementation
- API integration with `localhost:4123/v1/audio/speech`
- Sequential processing pipeline (one request at a time)
- Comprehensive API call logging system

**Technical Requirements:**
```python
class SimpleTTSEngine:
    def __init__(self, config_path=None)
    def process_episode_script(self, script_path: str) -> SimpleProcessingReport
    def generate_speech(self, text: str, output_path: str) -> bool
    def log_api_call(self, section_id: str, text_length: int, response_data: dict) -> None
```

**Key Implementation Points:**
- Use existing `config_tts_api.py` for API configuration
- Implement `SimpleProcessingReport` dataclass compatible with master processor expectations
- Process audio sections: `intro`, `pre_clip`, `post_clip`, `outro`
- Skip `video_clip` sections automatically
- Generate filenames from `section_id`: `intro_001.wav`, `pre_clip_001.wav`

#### Task 1.2: Adapt ChatterboxAudioFileManager
**Assigned to:** Implementation Agent  
**Dependencies:** Task 1.1 completion  
**Deliverables:**
- Modified `Code/Chatterbox/audio_file_manager.py`
- Remove complex dependencies (`TTSResult`, `ChatterboxTTSConfig`)
- Maintain file organization and directory structure logic
- Keep episode directory discovery functionality

**Specific Changes:**
- Remove imports: `from .tts_engine import TTSResult`, `from .config import ChatterboxTTSConfig`
- Adapt `organize_audio_file()` method for simple metadata structure
- Maintain `create_episode_structure()` and `discover_episode_from_script()` methods
- Simplify metadata generation for API-based processing

#### Task 1.3: Integrate JSON Parser
**Assigned to:** Implementation Agent  
**Dependencies:** Task 1.1, Task 1.2 completion  
**Deliverables:**
- Integration with existing `ChatterboxResponseParser`
- Validation of `unified_podcast_script.json` format compatibility
- Audio section extraction pipeline

**Implementation Notes:**
- Reuse existing `ChatterboxResponseParser.parse_response_file()`
- Use `ChatterboxResponseParser.extract_audio_sections()` for section filtering
- Maintain compatibility with existing JSON structure and validation

### Phase 2: Master Processor Integration
**Duration:** Week 1-2 (Days 4-8)  
**Agent Type:** Implementation Agent  

#### Task 2.1: Replace Stage 5 in Master Processor
**Assigned to:** Implementation Agent  
**Dependencies:** Phase 1 complete  
**Deliverables:**
- Modified `Code/master_processor_v2.py` Stage 5 method
- Direct integration with `SimpleTTSEngine`
- Compatible return format for pipeline continuation

**Specific Changes:**
```python
# Replace in _stage_5_audio_generation():
# OLD: processor = ChatterboxBatchProcessor(self.config_path)
# NEW: processor = SimpleTTSEngine(self.config_path)

# Maintain return structure:
results_dict = {
    'status': 'success',
    'total_sections': audio_results.total_sections,
    'successful_sections': audio_results.successful_sections,
    'failed_sections': audio_results.failed_sections,
    'generated_files': audio_results.generated_files,
    'output_directory': audio_results.output_directory,
    'processing_time': audio_results.processing_time
}
```

#### Task 2.2: End-to-End Pipeline Testing
**Assigned to:** Implementation Agent  
**Dependencies:** Task 2.1 completion  
**Deliverables:**
- Full pipeline test with sample `unified_podcast_script.json`
- Validation of file organization and output structure
- API call logging verification
- Master processor compatibility confirmation

### Phase 3: Legacy Code Removal & Validation
**Duration:** Week 2 (Days 8-10)  
**Agent Type:** Implementation Agent  

#### Task 3.1: Remove Legacy Components
**Assigned to:** Implementation Agent  
**Dependencies:** Phase 2 complete and validated  
**Deliverables:**
- Remove `Code/Chatterbox/tts_engine.py`
- Remove `Code/Chatterbox/batch_processor.py`
- Remove `Code/Chatterbox/config.py`
- Clean up unused imports and dependencies
- Update `Code/Chatterbox/__init__.py` exports

#### Task 3.2: Final System Validation
**Assigned to:** Implementation Agent  
**Dependencies:** Task 3.1 completion  
**Deliverables:**
- Comprehensive testing of all success criteria
- Performance validation (sequential processing)
- Error handling validation (fail fast behavior)
- API logging system verification
- Documentation of final system state

## Dependencies and Resources

### External Dependencies
- Chatterbox TTS API server running on `localhost:4123`
- Python `requests` library
- Existing episode directory structure

### Internal Dependencies
- `Code/Chatterbox/config_tts_api.py` (existing configuration)
- `Code/Chatterbox/json_parser.py` (existing JSON parser)
- `Code/Chatterbox/audio_file_manager.py` (to be adapted)
- `Code/master_processor_v2.py` (Stage 5 integration point)

### File System Requirements
- Input: `Content/Episode/Output/Scripts/unified_podcast_script.json`
- Output: `Content/Episode/Output/Audio/{section_id}.wav`
- Metadata: `Content/Episode/Output/Chatterbox/generation_metadata.json`

## Risk Assessment

### Technical Risks
- **API Server Dependency:** System depends on `localhost:4123` availability
  - Mitigation: User manages API server (per project constraints)
- **Sequential Performance:** May be slower than batch processing
  - Mitigation: Acceptable per project requirements (simplicity over performance)

### Implementation Risks
- **Master Processor Compatibility:** Return format must match existing expectations
  - Mitigation: Careful interface matching and testing in Task 2.1
- **File Organization Compatibility:** Must maintain existing directory structure
  - Mitigation: Reuse existing audio file manager logic (Task 1.2)

## Success Metrics

### Functional Metrics
- [ ] All audio sections processed successfully (intro, pre_clip, post_clip, outro)
- [ ] Files organized in correct directory structure
- [ ] Master processor pipeline completes without errors
- [ ] API calls logged with required details
- [ ] Legacy components removed cleanly

### Performance Metrics
- [ ] Sequential processing completes within acceptable timeframes
- [ ] Memory usage reduced (no local model loading)
- [ ] System startup time improved (no complex initialization)

### Quality Metrics
- [ ] Code maintainability improved (simplified architecture)
- [ ] Error handling clear and immediate (fail fast)
- [ ] Logging provides adequate debugging information

## Memory Bank Configuration

**Structure:** Single `Memory_Bank.md` file  
**Justification:** This project has a clear, linear progression through defined phases with a manageable scope and 2-week timeline. A single file provides easy tracking of implementation progress and agent activities without the complexity of multi-file organization.

**Location:** `C:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Memory_Bank.md`

## Communication Protocol

All Implementation Agents must:
1. Log all significant actions, decisions, and outcomes to the Memory Bank
2. Report completion of each task with deliverables summary
3. Escalate any blocking issues or scope changes to Manager Agent
4. Follow the standardized Memory Bank log format for all entries

## Timeline Summary

| Week | Phase | Key Deliverables |
|------|-------|------------------|
| Week 1 | Phase 1 & 2 Start | SimpleTTSEngine, adapted AudioFileManager, Master Processor integration |
| Week 2 | Phase 2 Complete & Phase 3 | End-to-end testing, legacy code removal, final validation |

**Project Completion Target:** End of Week 2 (June 30, 2025)

---

**Next Steps:** Manager Agent will now create detailed task assignment prompts for Implementation Agents based on this plan, starting with Phase 1, Task 1.1.
