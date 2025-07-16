# ElevenLabs TTS Integration Plan

## Overview
This plan outlines the integration of ElevenLabs Text-to-Speech API as an optional alternative to the existing Chatterbox TTS system. Since ElevenLabs is a paid service, users should be prompted to choose between the two TTS options when Stage 5 (Audio Generation) is selected in the pipeline.

## Current State Analysis

### Existing TTS Implementation
- **Current System**: Chatterbox SimpleTTSEngine (`Code/Chatterbox/simple_tts_engine.py`)
- **Pipeline Integration**: Stage 5 in `master_processor_v2.py` calls `_stage_5_audio_generation()`
- **Menu Integration**: `run_pipeline_menu.py` triggers Stage 5 via user selection
- **Functionality**: Processes episode scripts, generates audio sections sequentially

### ElevenLabs Implementation Status
- **Existing Code**: Basic functionality in `Code/ElevenLabs/simple_tts.py`
- **Features**: Text-to-speech conversion with voice settings, file saving
- **API Integration**: Using `elevenlabs` Python client
- **Current Limitations**: Single text input, not integrated with pipeline

## Integration Strategy

### Phase 1: Core ElevenLabs Engine Development

#### Task 1.1: Create ElevenLabs TTS Engine
**Objective**: Develop a pipeline-compatible ElevenLabs TTS engine

**Files to Create/Modify**:
- `Code/ElevenLabs/elevenlabs_tts_engine.py` (new)
- `Code/ElevenLabs/config_elevenlabs.py` (new)
- `Code/ElevenLabs/__init__.py` (new)

**Key Components**:
1. **ElevenLabsTTSEngine Class**:
   - Mirror the interface of `SimpleTTSEngine` for compatibility
   - Implement `process_episode_script()` method
   - Return `SimpleProcessingReport` compatible results
   - Handle API rate limiting and error recovery

2. **Configuration Management**:
   - API key management (environment variable)
   - Hardcoded voice ID (no user selection needed)
   - Audio quality settings (Speed: 1.00, Stability: 50%, Similarity: 75%)
   - Output format: MP3 (matching Chatterbox output)

3. **Audio Processing Pipeline**:
   - Parse JSON script files (same format as Chatterbox)
   - Process audio sections sequentially
   - Generate MP3 files with identical naming convention to Chatterbox
   - Implement progress tracking and logging

#### Task 1.2: Enhanced Error Handling & Rate Limiting
**Objective**: Ensure robust API usage and graceful handling

**Features**:
- Rate limiting compliance (fail immediately on rate limit - no retry logic initially)
- Clear error messages displaying raw ElevenLabs API errors
- Robust API failure handling

### Phase 2: Pipeline Integration

#### Task 2.1: Modify Master Processor
**File**: `Code/master_processor_v2.py`

**Changes Required**:
1. **Update `_stage_5_audio_generation()` method**:
   - Add `tts_provider` parameter (default: "chatterbox")
   - Implement provider selection logic
   - Maintain existing interface for backward compatibility

2. **Provider Factory Pattern**:
   ```python
   def _get_tts_engine(self, provider: str):
       if provider.lower() == "elevenlabs":
           return ElevenLabsTTSEngine(self.config_path)
       else:
           return SimpleTTSEngine(self.config_path)
   ```

3. **Enhanced Logging**:
   - Log selected TTS provider
   - Provider-specific configuration logging

#### Task 2.2: Update Pipeline Menu System
**File**: `Code/run_pipeline_menu.py`

**Changes Required**:
1. **TTS Provider Selection Function**:
   ```python
   def get_tts_provider_choice():
       """Prompt user to select TTS provider."""
       print("\n🎤 TTS Provider Selection")
       print("1. Chatterbox TTS (Free)")
       print("2. ElevenLabs TTS (Paid - Higher Quality)")
       choice = input("Select TTS provider (1-2): ").strip()
       return "elevenlabs" if choice == "2" else "chatterbox"
   ```

2. **Integration Points**:
   - `run_pipeline_start_from()`: Add TTS provider prompt immediately at start if Stage 5 is included
   - `run_pipeline_one_stage()`: Add TTS provider prompt immediately at start when Stage 5 selected
   - `run_pipeline_full()`: Add TTS provider prompt immediately at start (before any pipeline processing)

3. **Method Signature Updates**:
   - Update all calls to `_stage_5_audio_generation()` to include provider parameter
   - Maintain backward compatibility with default parameter

### Phase 3: Configuration & Setup

#### Task 3.1: Configuration Management
**Files**:
- `Code/ElevenLabs/config_elevenlabs.py` (new)
- `Code/Config/` updates (if applicable)

**Configuration Elements**:
1. **API Configuration**:
   - API key storage (environment variable)
   - Hardcoded voice ID
   - Default settings: Speed 1.00, Stability 50%, Similarity 75%

2. **Output Configuration**:
   - MP3 audio format
   - Identical file naming convention to Chatterbox (for seamless pipeline integration)

#### Task 3.2: Dependencies & Requirements
**File**: `requirements.txt`

**New Dependencies**:
```
elevenlabs>=0.2.0
```

**Verification**:
- Test import compatibility
- Verify API client functionality
- Check version compatibility with existing dependencies

### Phase 4: Basic Testing

#### Task 4.1: Simple Integration Testing
**Objective**: Verify basic functionality works

**Test Scenarios**:
1. **Basic Pipeline Test**:
   - Run pipeline with ElevenLabs selection
   - Verify MP3 files are generated with identical naming to Chatterbox
   - Test pipeline failure with raw API error message when ElevenLabs fails

2. **Menu System Test**:
   - Test TTS provider selection at very start
   - Verify prompt appears before any processing begins

### Phase 5: Basic Documentation

#### Task 5.1: Setup Guide
**Files to Create**:
- `Code/ElevenLabs/README.md`

**Content**:
- API key setup instructions
- Basic usage guide

## Implementation Priority

### High Priority (Core Functionality)
1. ElevenLabs engine development (Task 1.1)
2. Pipeline integration (Task 2.1, 2.2)
3. Basic configuration (Task 3.1)

### Medium Priority (Polish)
1. Basic error handling (Task 1.2)
2. Simple testing (Task 4.1)
3. Setup documentation (Task 5.1)

## Technical Considerations

### API Integration
- **Error Handling**: Fail with clear error message showing raw ElevenLabs API error (no fallback to Chatterbox)
- **Rate Limiting**: Fail immediately on rate limits (no retry logic initially)

### Compatibility
- **Interface Consistency**: Maintain same return types and error patterns
- **File Structure**: Identical output directory and naming conventions to Chatterbox
- **Audio Format**: MP3 output matching Chatterbox format

### Security
- **API Key Management**: Environment variable storage

## Success Criteria

### Functional Requirements
- [ ] Users can select between Chatterbox and ElevenLabs TTS at the very start of pipeline
- [ ] ElevenLabs integration produces compatible audio files
- [ ] Pipeline fails clearly with error message if ElevenLabs API fails (no fallback)
- [ ] Voice selection handled via config file (no runtime prompts for voice)

### Non-Functional Requirements
- [ ] No breaking changes to existing Chatterbox functionality
- [ ] Performance comparable to existing TTS system
- [ ] Clear user feedback during processing
- [ ] Comprehensive error messages and recovery guidance

## Risk Mitigation

### Technical Risks
- **API Failures**: Pipeline fails with clear error message (no fallback mechanism)

### User Experience Risks
- **Complexity**: Keep selection process simple and clear

## Next Steps

1. **Immediate**: Begin Task 1.1 (ElevenLabs engine development)
2. **Week 1**: Complete core engine and basic integration
3. **Week 2**: Implement menu system and user prompts
4. **Week 3**: Basic testing and setup documentation

This lean plan focuses on the core functionality needed to integrate ElevenLabs TTS as an option while keeping complexity minimal.
