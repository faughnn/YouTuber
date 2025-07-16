# Bug Fix Plan: Guest name and host name needs to be put into analysis prompts

## Problem Description

The content analysis system is not correctly identifying and using the actual guest and host names in the generated podcast scripts. Instead, it uses placeholder names like "Unknown Guest" even when the real names are available from the folder structure.

**Example from current output:**
```json
{
  "script_content": "Our guest today is the Unknown Guest. He is an environmental lawyer and activist..."
}
```

**Expected output:**
```json
{
  "script_content": "Our guest today is RFK Jr. He is an environmental lawyer and activist..."
}
```

## Updated Analysis: Two Prompts Need Fixing

**Investigation revealed this is actually a TWO-PROMPT issue:**

1. **First Prompt (Analysis)**: `transcript_analyzer.py` - Currently missing participant context
2. **Second Prompt (Narrative Generation)**: `podcast_narrative_generator.py` - Currently using flawed episode title parsing that defaults to "Unknown Guest" Fix Plan: Guest and Host Names in Analysis and Narrative Generation Prompts

## Problem Description

The content analysis system is not correctly identifying and using the actual guest and host names in the generated podcast scripts. Instead, it uses placeholder names like "Unknown Guest" even when the real names are available from the folder structure. **This issue affects both the first analysis prompt AND the second narrative generation prompt.**

**Example from current output:**
```json
{
  "script_content": "Our guest today is the Unknown Guest. He is an environmental lawyer and activist..."
}
```

**Expected output:**
```json
{
  "script_content": "Our guest today is RFK Jr. He is an environmental lawyer and activist..."
}
```

## Multi-Stage Problem Analysis

### Issue 1: First Analysis Prompt (transcript_analyzer.py)
- **Location**: `Code/Content_Analysis/transcript_analyzer.py`
- **Problem**: Analysis prompt doesn't include participant names
- **Impact**: Initial analysis lacks context about who is speaking

### Issue 2: Second Narrative Generation Prompt (podcast_narrative_generator.py)
- **Location**: `Code/Content_Analysis/podcast_narrative_generator.py`
- **Problem**: `_extract_guest_name_from_title()` function doesn't handle underscore-separated folder names
- **Current Logic**: Uses episode title `"Tucker_Carlson_RFK_Jr"` with regex patterns that expect dashes/colons
- **Impact**: Defaults to "Unknown Guest" when folder structure doesn't match expected patterns

## Root Cause Analysis

### Problem 1: Missing Context in First Analysis Prompt
1. **Missing Context in Analysis Prompt**: The analysis prompt in `create_file_based_prompt()` function doesn't include the actual host and guest names.
2. **Available Information**: The host and guest names are available from the folder structure:
   - Path: `Content/Tucker_Carlson/Tucker_Carlson_RFK_Jr/`
   - Host: Tucker Carlson (from `Tucker_Carlson` folder)
   - Guest: RFK Jr. (from `Tucker_Carlson_RFK_Jr` episode folder)
3. **Current Implementation Gap**: The `transcript_analyzer.py` creates analysis prompts without extracting or including the participant names.

### Problem 2: Regex Pattern Mismatch in Second Prompt
1. **Episode Title Source**: Episode title is set to folder name `"Tucker_Carlson_RFK_Jr"` in `master_processor_v2.py` line 690
2. **Pattern Mismatch**: `_extract_guest_name_from_title()` function expects formats like:
   - `"Host - Guest"` (with dashes)
   - `"Host with Guest"` (with "with")
   - `"Host: Guest"` (with colons)
3. **Underscore Format Not Supported**: The actual format `"Tucker_Carlson_RFK_Jr"` uses underscores, which isn't handled
4. **Fallback Behavior**: When no pattern matches, function returns "Unknown Guest"

### Flow Analysis
1. **master_processor_v2.py:690**: `episode_title = os.path.basename(self.episode_dir)` → `"Tucker_Carlson_RFK_Jr"`
2. **podcast_narrative_generator.py:233**: `guest_name = self._extract_guest_name_from_title(episode_title)`
3. **_extract_guest_name_from_title()**: Regex patterns fail to match underscore format
4. **Result**: Returns "Unknown Guest"
5. **_build_unified_prompt()**: Prepends incorrect name to second Gemini prompt

## Solution Strategy

### Approach: Extract Names from Folder Path and Prepend to Analysis Guidelines

The most effective solution is to:
1. Extract host and guest names from the folder structure
2. Prepend this information at the start of the analysis guidelines prompt
3. Ensure this information is available to the AI when generating script content

### Implementation Plan

#### Phase 1: Add Name Extraction Function - **MOST CRUCIAL PART**

**File**: `Code/Content_Analysis/transcript_analyzer.py`

**New Function**: `extract_host_and_guest_names(file_path)`
- Parse the file path to extract host and guest names
- **CRITICAL**: The folder format will ALWAYS be in this structure: `Content/{HOST}/{HOST}_{GUEST}/...`
- This is the definitive source for guest and host names
- Return formatted names for use in prompts

#### Phase 2: Modify Prompt Creation

**File**: `Code/Content_Analysis/transcript_analyzer.py`

**Function**: `create_file_based_prompt(analysis_rules, file_path=None)`
- Add optional `file_path` parameter
- Extract host and guest names if file_path is provided
- Prepend name information to the analysis rules

**Example Enhanced Prompt**:
```
PARTICIPANT INFORMATION:
Host: Tucker Carlson
Guest: RFK Jr.

ANALYSIS RULES:
{existing analysis_rules content}
```

#### Phase 3: Update Function Calls

**File**: `Code/Content_Analysis/transcript_analyzer.py`

**Function**: `analyze_with_gemini_file_upload()`
- Pass the transcript file path to `create_file_based_prompt()`
- Ensure the name information flows through the analysis pipeline

#### Phase 4: Test and Validate

**Validation Steps**:
1. Test with Tucker Carlson/RFK Jr. episode
2. Verify that generated scripts use actual names instead of "Unknown Guest"
3. Test with other host/guest combinations if available
4. Ensure backward compatibility with existing episodes

## Technical Implementation Details

### Code Changes Required

#### 1. Name Extraction Function
```python
def extract_host_and_guest_names(file_path):
    """
    Extract host and guest names from the episode folder structure.
    
    Expected structure: Content/{HOST}/{HOST}_{GUEST}/...
    
    Args:
        file_path: Path to transcript file or episode folder
        
    Returns:
        dict: {'host': str, 'guest': str} or None if cannot parse
    """
```

#### 2. Enhanced Prompt Creation
```python
def create_file_based_prompt(analysis_rules, file_path=None):
    """Create analysis prompt with participant information if available."""
    
    # Extract names if file path provided
    names = extract_host_and_guest_names(file_path) if file_path else None
    
    # Build prompt with participant info
    if names:
        prompt = f"""PARTICIPANT INFORMATION:
Host: {names['host']}
Guest: {names['guest']}

ANALYSIS RULES:
{analysis_rules}
...
"""
    else:
        # Fallback to existing behavior
        prompt = f"""ANALYSIS RULES:
{analysis_rules}
...
"""
```

#### 3. Update Function Call Sites
- Modify `analyze_with_gemini_file_upload()` to pass file path
- Update any other callers of `create_file_based_prompt()`

## Testing Strategy

### Test Cases

1. **Primary Test Case**:
   - File: `Content/Tucker_Carlson/Tucker_Carlson_RFK_Jr/...`
   - Expected: Host="Tucker Carlson", Guest="RFK Jr."

2. **Edge Cases**:
   - Single name guests (no underscore splitting needed)
   - Episodes with no guest (host-only)
   - Malformed folder structures

3. **Backward Compatibility**:
   - Episodes without clear host/guest structure should still work
   - Existing functionality should remain intact

## Benefits

1. **Accurate Script Generation**: Scripts will use actual participant names instead of placeholders
2. **Better User Experience**: Generated content will be more professional and accurate
3. **Automated Solution**: No manual intervention required for name identification
4. **Scalable**: Works for any host/guest combination following the folder structure convention

## Risk Assessment

### Low Risk
- Changes are additive (enhancing existing prompt)
- Fallback behavior maintains existing functionality
- No changes to core API or data structures

### Mitigation
- Thorough testing with existing episode data
- Gradual rollout if needed
- Clear logging for debugging name extraction

## Acceptance Criteria

- [ ] Guest and host names are correctly extracted from folder structure
- [ ] Analysis prompts include participant information when available
- [ ] Generated scripts use actual names instead of "Unknown Guest"
- [ ] Existing functionality remains intact for edge cases
- [ ] Solution works for Tucker Carlson/RFK Jr. episode specifically
- [ ] Code includes proper error handling and logging

## Files to Modify

1. `Code/Content_Analysis/transcript_analyzer.py`
   - Add `extract_host_and_guest_names()` function
   - Modify `create_file_based_prompt()` function
   - Update `analyze_with_gemini_file_upload()` function calls

## Implementation Priority

**Priority**: High
**Complexity**: Low-Medium
**Estimated Effort**: 2-4 hours

This is a straightforward enhancement that addresses a clear user experience issue with minimal risk to existing functionality.
