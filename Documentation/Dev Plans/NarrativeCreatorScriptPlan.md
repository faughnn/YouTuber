# Narrative Creator Script - Single Call Implementation Plan

## Overview
Single Gemini API call that uploads analysis JSON and generates unified script-timeline structure. Replaces existing two-call system completely.

## Architecture
- **Input**: `{episode}/Processing/original_audio_full_transcript_analysis_results.json` (uploaded to Gemini)
- **Prompt**: Existing `tts_podcast_narrative_prompt.txt` 
- **Output**: `{episode}/Output/Scripts/unified_podcast_script.json`
- **Integration**: Direct replacement in `master_processor.py` Stage 6

### Expected Output Format
```json
{
  "narrative_theme": "chosen theme name",
  "podcast_sections": [
    {
      "section_type": "intro|pre_clip|video_clip|post_clip|outro",
      "section_id": "unique_identifier",
      "script_content": "complete script text",
      "estimated_duration": "duration",
      "audio_tone": "voice style",
      "clip_reference": "segment_id (for clip-related sections)"
    }
  ],
  "script_metadata": {
    "total_estimated_duration": "total minutes",
    "target_audience": "description",
    "key_themes": ["themes"],
    "tts_segments_count": "number",
    "timeline_ready": true
  }
}
```

### Benefits
- **Simplified Architecture**: One call, one output, one failure point
- **Unified Context**: LLM sees all clips and makes holistic decisions
- **Better Optimization**: Clip selection and narrative generation optimized together
- **Easier Debugging**: All logic contained in single operation

## Implementation Structure
```python
class NarrativeCreatorGenerator:
    def __init__(self, config_path=None)
    def generate_unified_narrative(self, analysis_json_path, episode_title) -> Dict
    def save_unified_script(self, script_data, output_path) -> Path
```

---

## Design Decisions (Confirmed)

### Integration & Architecture
- Complete replacement of two-call system (no fallbacks)
- Single method only - default and only approach
- Output filename: `unified_podcast_script.json`
- Output location: Episode-specific Scripts folder
- Standard error handling: 3 API retries, clear failures

### Implementation Pattern (from transcript_analyzer.py)
```python
# Upload analysis file to Gemini
uploaded_file = genai.upload_file(
    path=analysis_json_path,
    display_name=f"Analysis Results - {episode_title}"
)

# Wait for processing
while uploaded_file.state.name == "PROCESSING":
    time.sleep(2)
    uploaded_file = genai.get_file(uploaded_file.name)

# Generate with file reference
response = model.generate_content([prompt_content, uploaded_file])
```

### File Locations
- **Prompt**: `Code/Content_Analysis/Prompts/tts_podcast_narrative_prompt.txt` (no changes needed)
- **Input**: `{episode}/Processing/original_audio_full_transcript_analysis_results.json`
- **Output**: `{episode}/Output/Scripts/unified_podcast_script.json`
- **Integration**: `master_processor.py` Stage 6 replacement