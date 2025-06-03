# Podcast Narrative Automation Plan

## Overview
Automate the creation of critique podcast scripts for Joe Rogan Experience episodes using Gemini AI to analyze content and generate humorous, sarcastic, fact-checking narratives.

## System Architecture

### Current Infrastructure ✅
- **Master Processor Pipeline**: `Scripts/master_processor.py`
- **Gemini API Integration**: Via `Scripts/config/default_config.yaml`
- **Analysis System**: Generates structured JSON with severity ratings
- **Video Clipping**: Automated clip extraction from analysis

### New Component: Podcast Narrative Generator

#### Core Functionality
```
Analysis JSON → Gemini Processing → Podcast Script (JSON + TXT)
```

#### Key Features
- **Full Automation**: Gemini makes all narrative decisions
- **Voice Style**: Humorous, slightly sarcastic, slightly snarky (Jon Stewart meets fact-checker)
- **Complete JSON Ingestion**: Feed entire analysis segments to Gemini for context-aware decisions

## Implementation Plan

### Phase 1: Core Generator Class
Create `Scripts/Content Analysis/podcast_narrative_generator.py`:

```python
class PodcastNarrativeGenerator:
    - Load analysis JSON
    - Generate comprehensive Gemini prompt
    - Parse and structure response
    - Save dual format output (JSON + readable script)
```

### Phase 2: Gemini Decision Framework

#### Clip Selection Criteria (Gemini Determines):
- **Factual Inaccuracy Level**: How wrong is the claim?
- **Real-World Harm Potential**: Could this hurt people?
- **Audience Reach/Virality**: Will this spread?
- **Misinformation Pattern**: Representative of broader issues?

#### Narrative Theme Options (Gemini Chooses):
- **"Escalating Absurdity"**: Mild → extreme claims progression
- **"Theme Deep-Dives"**: Medical, conspiracy, political focus
- **"Rhetorical Techniques Exposed"**: How persuasion works
- **"Harm Demonstration"**: Real-world consequences focus

#### Clip Ordering Strategy (Gemini Decides):
- Maximum narrative impact
- Logical flow between topics
- Building to climactic moments
- Effective opening/closing

### Phase 3: Script Structure

#### Generated Script Format:
```
INTRO (3-4 min)
├── Hook with most compelling clip preview
├── Context setting
└── Theme preview

CLIP ANALYSIS SEGMENTS
├── PRE-CLIP SETUP
│   └── What listeners should notice
├── [CLIP_MARKER: timestamp, title]
├── POST-CLIP ANALYSIS
│   ├── Fact-checking
│   ├── Rhetorical technique breakdown
│   └── Real-world implications

CONCLUSION (5-7 min)
├── Theme synthesis
├── Media literacy lesson
└── Call to action
```

### Phase 4: Integration with Master Processor

#### New Command Line Options:
```powershell
# Generate podcast script from existing analysis
python Scripts/master_processor.py --generate-podcast --analysis-only "path/to/analysis.json"

# Full pipeline with podcast generation
python Scripts/master_processor.py "URL" --generate-podcast

# All stages including podcast
python Scripts/master_processor.py "URL" --all
```

#### Pipeline Extension:
```
Stage 1: Video Download ✅
Stage 2: Audio Extraction ✅  
Stage 3: Transcript Generation ✅
Stage 4: Content Analysis ✅
Stage 5: Video Clipping ✅
Stage 6: Podcast Script Generation (NEW)
```

## Technical Specifications

### Input Format
- **Primary Input**: `*_analysis_analysis.json` from existing pipeline
- **Structure**: Complete segments array with severity ratings, claims, evidence

### Output Format
- **JSON Structure**: `{episode_name}_podcast_script.json`
  ```json
  {
    "narrative_theme": "chosen theme",
    "selected_clips": [clip objects with reasoning],
    "clip_order": [ordered clip IDs],
    "full_script": "complete podcast script",
    "generation_metadata": {...}
  }
  ```
- **Readable Script**: `{episode_name}_podcast_script.txt`

### Gemini Prompt Strategy

#### Core Prompt Structure:
```
ROLE: Podcast script creator for Joe Rogan critique
VOICE: Humorous, sarcastic, snarky fact-checker
INPUT: Complete analysis JSON
TASKS: 
  1. Select podcast-worthy clips
  2. Choose narrative theme
  3. Order clips for impact
  4. Write complete script
OUTPUT: Structured JSON response
```

#### Quality Control:
- **Iterative Prompt Refinement**: Trial and error approach
- **Voice Consistency**: Maintain humor while being factual
- **Educational Focus**: Media literacy over pure entertainment

## File Structure

### New Files:
```
Scripts/
├── Content Analysis/
│   ├── podcast_narrative_generator.py (NEW)
│   └── ...existing files...
└── master_processor.py (MODIFIED)

Transcripts/
└── Joe_Rogan_Experience/
    └── {Episode}/
        ├── {episode}_podcast_script.json (NEW)
        ├── {episode}_podcast_script.txt (NEW)
        └── ...existing files...
```

## Development Workflow

### Step 1: Create Generator Class
- Implement core `PodcastNarrativeGenerator` class
- Test with existing Joe Rogan 2325 analysis JSON
- Refine Gemini prompt for desired voice/output

### Step 2: Integrate with Master Processor  
- Add `--generate-podcast` argument
- Implement Stage 6 in pipeline
- Test end-to-end automation

### Step 3: Prompt Optimization
- Test multiple JRE episodes
- Refine prompt for consistency
- Adjust voice/tone based on output quality

### Step 4: Quality Assurance
- Validate fact-checking accuracy
- Ensure clip selection logic is sound
- Test narrative flow effectiveness

## Success Metrics

### Technical Success:
- [ ] Generates complete podcast scripts automatically
- [ ] Integrates seamlessly with existing pipeline
- [ ] Produces both structured and readable outputs
- [ ] Maintains consistent voice across episodes

### Content Success:
- [ ] Selects most impactful clips from analysis
- [ ] Creates engaging narrative flow
- [ ] Maintains factual accuracy in corrections
- [ ] Balances humor with educational content

## Future Enhancements

### Template System:
- Guest-type specific templates (politicians, comedians, scientists)
- Episode format variations (single vs multi-topic)
- Seasonal/topical content adaptation

### Multi-Episode Features:
- Cross-episode theme tracking
- Recurring misinformation pattern analysis
- Guest behavior pattern documentation

### Quality Improvements:
- A/B testing different prompt approaches
- User feedback integration
- Voice style fine-tuning based on audience response

## Implementation Timeline

### Week 1: Core Development
- Create `podcast_narrative_generator.py`
- Initial Gemini prompt development
- Basic integration with master processor

### Week 2: Testing & Refinement  
- Test with Joe Rogan 2325 analysis
- Refine prompt for voice consistency
- Improve output formatting

### Week 3: Full Integration
- Complete master processor integration
- End-to-end pipeline testing
- Documentation and error handling

### Week 4: Optimization
- Prompt optimization based on results
- Quality assurance testing
- Performance improvements

## Risk Mitigation

### Technical Risks:
- **Gemini API Rate Limits**: Implement retry logic and caching
- **JSON Parsing Failures**: Robust error handling and fallback formats
- **Large Input Handling**: Chunking strategy for very long episodes

### Content Risks:
- **Factual Accuracy**: Cross-reference generated claims with reliable sources
- **Voice Consistency**: Regular prompt testing and refinement
- **Legal Considerations**: Ensure fair use compliance in clip selection

## Notes
- Focus on automation over perfection initially
- Iterate based on actual output quality
- Maintain flexibility for manual overrides when needed
- Consider community feedback for voice/style adjustments
