# Problem Statement
YouTube channels have different formats for the title of their videos. Sometimes the host's or guest's name is in the title, sometimes it isn't. This plan devises a robust strategy to correctly identify the host and guest(s) to create a standardized folder structure.

## Current State Analysis

**Existing Components (Already Built):**
- ✅ `NameExtractor` module with hierarchical extraction logic
- ✅ `ConfigManager` and `name_extractor_rules.json` configuration
- ✅ `get_video_metadata()` function in `youtube_video_downloader.py`
- ✅ `FileOrganizer` with `get_episode_paths()` method
- ✅ User verification system in `user_verification.py`

**The Actual Problem:**
Stage 1 in `master_processor_v2.py` doesn't use any of these existing components. It follows the old pattern:
1. Download video/audio to temporary locations
2. *Then* try to figure out proper paths
3. Move files around afterward

This causes the name extraction issues because paths are determined after download, not before.

---

## The Solution: Stage 1 Integration Refactor

### New Stage 1 Workflow: "Setup Environment and Download Media"

The `_stage_1_media_extraction` method in `master_processor_v2.py` will be refactored to properly integrate existing components:

1. **Metadata-First Fetch:** Use existing `get_video_metadata(url)` to fetch title and uploader without downloading
2. **Name Extraction:** Use existing `NameExtractor` to determine Host and Guest from metadata
3. **Conditional User Verification:** If `prompt_for_verification` config is true OR no guest is found, trigger verification using existing `user_verification.py`
4. **Directory Setup:** Use existing `FileOrganizer.get_episode_paths()` to create standardized directory structure
5. **Direct Download:** Download video and audio files directly to the correct target paths (no moving/copying)

### Error Handling Strategy

- **Metadata fetch fails:** Fail immediately with clear error message
- **Name extraction produces no guest:** Trigger user verification regardless of config
- **User cancels verification:** Stop pipeline execution gracefully
- **Directory creation fails:** Fail with detailed error message for debugging
- **Download fails:** Standard error handling as currently implemented

### Integration Points

**Stage 1 Method Signature Changes:**
- Remove backward compatibility constraints
- Accept additional parameters for verification preferences
- Return structured episode information for downstream stages

**Download Function Usage:**
- Stage 1 calculates all paths using `FileOrganizer.get_episode_paths()`
- Pass calculated paths to unchanged download functions
- No modifications needed to `youtube_video_downloader.py` or `youtube_audio_extractor.py`

**Configuration Integration:**
- Use existing `ConfigManager` to load `name_extractor_rules.json`
- Respect `prompt_for_verification` setting
- Apply uploader-specific rules through existing `NameExtractor`

---

## Design Decisions & Requirements

### Name Extraction Logic
- **Host Identification**: Always use `uploader` from metadata as canonical host name
- **Guest Extraction**: Extract guest from `title` only, ignoring any host mentions in title
- **Conflict Resolution**: If title suggests different host than uploader, ignore title host and use uploader

### User Experience Enhancements
- **Preview at Verification**: Show extracted names and proposed folder structure before user confirmation
- **Rule Learning Mode**: When user makes corrections during verification, offer to save as new uploader-specific rule
- **Simple Success/Failure Logging**: Track extraction outcomes with rule types used

### Logging Strategy
```python
# Success logging
self.enhanced_logger.info(f"Name extraction: Host='{host}' Guest='{guest}' (Rule: {rule_used})")

# Failure/verification logging  
self.enhanced_logger.warning(f"Name extraction failed, triggered verification")
self.enhanced_logger.info(f"User correction: Host='{old_host}' -> '{new_host}', Guest='{old_guest}' -> '{new_guest}'")
```

### Rule Evolution System
When verification is triggered and user provides corrections:
1. Analyze user's correction pattern
2. Offer to save as new uploader-specific rule: "Save this pattern for future videos from '{uploader}'? (y/n)"
3. If accepted, update `name_extractor_rules.json` automatically
4. Log rule creation for future reference

---

## Implementation Status: ✅ COMPLETED

### Phase 1: Core Integration ✅ 
1. **✅ Refactored `master_processor_v2._stage_1_media_extraction()`**
   - ✅ Implemented new workflow using existing components
   - ✅ Added proper error handling for each step
   - ✅ Ensures clean pipeline termination on errors

2. **✅ Enhanced User Verification System**
   - ✅ Added preview mode showing extracted names and folder structure
   - ✅ Implemented rule learning functionality
   - ✅ Added automatic rule saving capability

### Phase 2: Name Extraction Improvements ✅
1. **✅ Updated NameExtractor Logic**
   - ✅ Enforced uploader-as-host principle
   - ✅ Improved guest-only extraction from titles
   - ✅ Added simple success/failure logging with rule tracking

2. **✅ Enhanced Configuration Management**
   - ✅ Added methods for automatic rule updates
   - ✅ Implemented rule suggestion system
   - ✅ Added validation for new rules

### Implementation Summary

**✅ Complete New Stage 1 Workflow:**
1. **Metadata-First Fetch** → Uses `get_video_metadata()` to fetch title and uploader
2. **Name Extraction** → Uses enhanced `NameExtractor` with uploader-as-host principle
3. **Conditional User Verification** → Shows preview + rule learning when needed
4. **Directory Setup** → Uses `FileOrganizer.get_episode_paths()` for structure
5. **Direct Download** → Downloads to correct target paths (no moving/copying)

**✅ Enhanced User Experience:**
- **Preview Mode**: Shows proposed folder structure before confirmation
- **Rule Learning**: Automatically suggests new rules from user corrections
- **Smart Verification**: Only triggers when needed (no guest found or config enabled)

**✅ Improved Logging:**
- Success/failure tracking with rule types used
- User correction logging for future improvements
- Clear error messages for debugging

**✅ All Requirements Met:**
- ✅ Uploader always used as canonical host
- ✅ Guest-only extraction from titles
- ✅ No live stream processing needed
- ✅ Simple logging strategy implemented
- ✅ Rule learning mode implemented
- ✅ Preview mode at verification decision

## Testing Results

**✅ Core Components Tested:**
- ✅ NameExtractor with rule tracking (`uploader_rule_split`, `generic_rule`, `fallback`)
- ✅ FileOrganizer path generation (host/guest combinations)
- ✅ UserVerification preview mode and rule analysis
- ✅ Complete Stage 1 workflow (mocked downloads)
- ✅ Verification trigger logic (correct scenarios)

**✅ Integration Tests Passed:**
- ✅ All imports work correctly
- ✅ Components integrate seamlessly
- ✅ Error handling works as expected
- ✅ Workflow produces correct results

## Next Steps (Optional Future Enhancements)

### Phase 3: Testing and Validation (Optional)
1. **Real-world Testing with YouTube Channels**
   - Test with channels having clear naming patterns
   - Test with channels having inconsistent titles  
   - Test channels requiring uploader-specific rules
2. **Error Scenario Validation**
   - Test network failures during metadata fetch
   - Test user cancellation scenarios
   - Test invalid URLs and edge cases

### Phase 4: Documentation and Optimization (Optional)
1. **Documentation Updates**
   - Update configuration documentation
   - Provide examples of uploader-specific rules
   - Document rule learning system usage
2. **Performance Optimization**
   - Monitor metadata fetch performance
   - Optimize directory creation for batch scenarios
