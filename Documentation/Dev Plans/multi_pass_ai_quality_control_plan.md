# Two-Pass AI Quality Control System - Implementation Plan

## Overview
Implement an automated 2-pass AI quality control system to improve segment selection quality by ignoring unreliable initial severity ratings and applying rigorous evidence-based filtering, followed by post-script rebuttal verification.

## Problem Statement
Current content analysis produces 20 segments with inconsistent severity ratings that don't reliably indicate actual harm potential:
- **MEDIUM** rated segments sometimes more impactful than **HIGH** rated ones
- Initial AI pass casts too wide a net with permissive criteria
- Severity ratings not trustworthy for filtering decisions
- Need automated quality control to reduce manual review burden
- Script rebuttals need fact-checking for accuracy

## Solution: Two-Pass AI Analysis + Post-Script Verification

### **Pass 1: Broad Analysis** (Current System - Keep As Is)
- **Purpose**: Wide net to capture all potential harmful content
- **Criteria**: Permissive to avoid missing anything important
- **Inputs**: Transcripts of entire chat plus prompt
- **Output**: `original_audio_analysis_results.json` (up to 20 segments)
- **Status**: ✅ Already implemented and working

### **Pass 2: Evidence-Based Quality Assessment & Selection**
- **Purpose**: Rigorous evaluation ignoring original severity ratings + final selection
- **Focus**: Evidence strength, factual accuracy, potential impact
- **Inputs**: `original_audio_analysis_results.json` plus prompt
- **Output**: `final_filtered_analysis_results.json` (8-12 high-quality segments)

### **Post-Script Pass: Rebuttal Verification & Rewriting**
- **Purpose**: Fact-check accuracy of generated rebuttals and rewrite inadequate sections
- **Focus**: Verify claims, correct inaccuracies, strengthen arguments, expand insufficient coverage
- **Inputs**: `unified_podcast_script.json` plus prompt
- **Output**: `verified_unified_script.json` (fact-checked and rewritten rebuttals)

**Note**: `verified_unified_script.json` becomes the new standard output for all downstream processes, replacing `unified_podcast_script.json` in the pipeline.

---

## Pass 2: Quality Assessment & Selection Implementation

### Evaluation Criteria (1-10 Scale)

1. **Quote Strength**: How explicitly harmful are the actual quotes?
   - 9-10: Direct false claims, explicit misinformation
   - 7-8: Strong implied harm, misleading statements
   - 5-6: Questionable but not clearly harmful
   - 1-4: Opinion, legitimate debate, weak evidence

2. **Factual Accuracy**: Are claims demonstrably false or misleading?
   - 9-10: Verifiably false statements
   - 7-8: Misleading but contains some truth
   - 5-6: Exaggerated but based on real events
   - 1-4: Opinion or subjective interpretation

3. **Potential Impact**: How likely to actually mislead/harm viewers?
   - 9-10: Could directly influence harmful behavior
   - 7-8: Likely to spread misinformation
   - 5-6: May confuse some viewers
   - 1-4: Limited real-world impact

4. **Content Specificity**: Are concrete false claims made vs. vague opinions?
   - 9-10: Specific false factual claims
   - 7-8: Concrete but debatable assertions
   - 5-6: General statements, some specifics
   - 1-4: Vague opinions, no specific claims

5. **Context Appropriateness**: Genuine misinformation vs. legitimate debate?
   - 9-10: Clear misinformation, no legitimate debate angle
   - 7-8: Mostly harmful but some legitimate concerns
   - 5-6: Mixed - some legitimate aspects
   - 1-4: Primarily legitimate discussion/inquiry

### Filtering & Selection Rules

**Automatic Removal Criteria**:
- Quote Strength < 6/10 (weak evidence in quotes)
- Factual Accuracy < 5/10 (mostly accurate statements)
- Potential Impact < 5/10 (limited real-world impact)
- Content Specificity < 5/10 (too vague to be harmful)
- Context Appropriateness < 5/10 (may be legitimate debate)

**Quality Score Calculation**:
```
Quality Score = (Quote Strength × 0.3) + (Factual Accuracy × 0.25) + 
                (Potential Impact × 0.25) + (Content Specificity × 0.1) + 
                (Context Appropriateness × 0.1)
```

**Final Selection Logic**:
1. Apply automatic removal criteria
2. Calculate quality scores for remaining segments
3. Sort by quality score (highest first)
4. Select top 8-12 segments
5. **Enforce minimum of 6 segments** - if fewer than 6 segments meet criteria:
   - **Reject the analysis** and flag for manual review
   - Do not lower quality thresholds to force 6 segments
   - **Quality over quantity**: Better to have no segments than poor quality segments

---

## Post-Script Rebuttal Verification & Rewriting

### Purpose
After the unified script is generated, verify the factual accuracy of the rebuttals and rewrite sections that are:
- Factually incorrect or misleading
- Insufficiently detailed or missing key counter-arguments
- Poorly sourced or lacking evidence
- Logically weak or ineffective at countering harmful content

### Verification & Rewriting Criteria

1. **Factual Accuracy**: Are the rebuttal claims verifiably true?
   - **Action**: Correct false statements, update outdated information
   
2. **Source Reliability**: Are cited studies/sources legitimate and correctly represented?
   - **Action**: Replace unreliable sources, add proper citations
   
3. **Logical Soundness**: Do the rebuttals logically address the harmful claims?
   - **Action**: Restructure arguments, add missing logical connections
   
4. **Completeness**: Are key counter-arguments covered?
   - **Action**: Expand rebuttals to include missing critical points
   
5. **Tone Appropriateness**: Is the response proportionate to the harm?
   - **Action**: Adjust tone to match severity, maintain credibility

### Rewriting Process

**Assessment Phase**:
- Score each `post_clip` section on accuracy (1-10)
- Score each `post_clip` section on completeness (1-10)
- Score each `post_clip` section on effectiveness (1-10)

**Rewriting Triggers**:
- Accuracy Score < 7/10: **Mandatory fact-checking and correction**
- Completeness Score < 6/10: **Expand with additional counter-arguments**
- Effectiveness Score < 6/10: **Restructure and strengthen rebuttal**

**Rewriting Actions**:
1. **Fact Correction**: Fix inaccurate statements with verified information
2. **Source Enhancement**: Add credible sources and proper citations
3. **Argument Expansion**: Include missing counter-arguments and context
4. **Clarity Improvement**: Simplify complex explanations, improve flow
5. **Evidence Strengthening**: Add specific examples, studies, or data points
6. **Voice Consistency**: Maintain the humorous, sarcastic, and snarky commentary style with factual entertainment and pointed wit when calling out misinformation

---

## Technical Implementation

### File Structure
```
Content_Analysis/
├── transcript_analyzer.py (Pass 1 - existing)
├── quality_assessor.py (Pass 2 - new)
├── rebuttal_verifier_rewriter.py (Post-script verification & rewriting - new)
├── two_pass_controller.py (orchestrates all passes)
├── Quality_Control/
│   ├── pass_2_prompt.txt
│   ├── rebuttal_verification_prompt.txt
│   ├── rebuttal_rewriting_prompt.txt
│   └── scoring_rubrics.json
└── JSON_Schemas/
    ├── pass_1_output_schema.json
    ├── pass_2_output_schema.json
    ├── unified_script_schema.json
    └── verified_script_schema.json

Content/{podcast_name}/{episode_name}/
└── Quality_Control_Results/
    ├── pass_2_evaluation/
    │   ├── quality_scores.json
    │   ├── filtering_decisions.json
    │   └── selection_rationale.json
    └── rebuttal_verification/
        ├── rebuttal_scores.json
        ├── rewriting_actions.json
        └── final_verification.json
```

### Integration with Existing Pipeline

**Current Flow**:
```
Transcript → transcript_analyzer.py → original_audio_analysis_results.json → Script Generation → unified_podcast_script.json
```

**New Flow**:
```
Transcript → transcript_analyzer.py → original_audio_analysis_results.json
    ↓
quality_assessor.py → final_filtered_analysis_results.json → Script Generation → unified_podcast_script.json
    ↓
rebuttal_verifier_rewriter.py → verified_unified_script.json
```

**Pipeline Integration Requirements**:
- All downstream processes must be updated to use `verified_unified_script.json` instead of `unified_podcast_script.json`
- `unified_podcast_script.json` becomes an intermediate file in the pipeline
- `verified_unified_script.json` becomes the final, production-ready script output
- Video production, TTS processing, and any other script consumers must point to the verified version

### Downstream Process Updates Required

**Files/Modules that need updating**:
- Any TTS processing scripts that currently read `unified_podcast_script.json`
- Video compilation modules that use script sections
- Timeline generation tools
- Audio processing pipelines
- Any manual review tools or interfaces

**Update Strategy**:
1. **Identify all script consumers**: Audit codebase for `unified_podcast_script.json` references
2. **Update file paths**: Change references to point to `verified_unified_script.json`
3. **Validate JSON compatibility**: Ensure `verified_unified_script.json` maintains same structure as original
4. **Add fallback logic**: If verified script doesn't exist, fall back to original unified script
5. **Update configuration**: Modify any hardcoded paths in config files

---

## JSON Format Consistency & Test Result Tracking

### Critical Data Flow Requirements

**Each stage MUST maintain exact JSON format compatibility:**

#### **Pass 1 Output Schema** (`original_audio_analysis_results.json`)
```json
{
  "segments": [
    {
      "segment_id": "string",
      "start_time": "float",
      "end_time": "float", 
      "harm_category": "string",
      "severityRating": "LOW|MEDIUM|HIGH|CRITICAL",
      "clipContextDescription": "string",
      "suggestedClip": [
        {
          "timestamp": "string",
          "speaker": "string", 
          "quote": "string"
        }
      ],
      "selectionReason": "string"
    }
  ],
  "episode_metadata": { "guest_name": "string", "episode_number": "string" }
}
```

#### **Pass 2 Output Schema** (`final_filtered_analysis_results.json`)
```json
{
  "segments": [
    {
      "segment_id": "string",
      "start_time": "float",
      "end_time": "float",
      "harm_category": "string", 
      "severityRating": "LOW|MEDIUM|HIGH|CRITICAL",
      "clipContextDescription": "string",
      "suggestedClip": [...],
      "selectionReason": "string",
      "quality_assessment": {
        "quote_strength": "float (1-10)",
        "factual_accuracy": "float (1-10)",
        "potential_impact": "float (1-10)", 
        "content_specificity": "float (1-10)",
        "context_appropriateness": "float (1-10)",
        "quality_score": "float",
        "selection_reason": "string"
      }
    }
  ],
  "filtering_summary": {
    "total_input_segments": "int",
    "segments_removed": "int", 
    "segments_selected": "int",
    "quality_threshold_used": "float",
    "min_threshold_met": "boolean"
  },
  "episode_metadata": { "guest_name": "string", "episode_number": "string" }
}
```

#### **Verified Script Schema** (`verified_unified_script.json`)
```json
{
  "narrative_theme": "string",
  "podcast_sections": [...],
  "script_metadata": {...},
  "verification_results": {
    "rebuttals_assessed": "int",
    "rebuttals_rewritten": "int", 
    "accuracy_improvements": "array",
    "completeness_improvements": "array",
    "effectiveness_improvements": "array"
  }
}
```

### Test Result Preservation

**Pass 2 Quality Assessment Results** (Saved to `Content/{podcast_name}/{episode_name}/Quality_Control_Results/pass_2_evaluation/`):
- `quality_scores.json`: Individual segment scores on all 5 dimensions
- `filtering_decisions.json`: Which segments removed and why
- `selection_rationale.json`: Final ranking and selection logic

**Rebuttal Verification Results** (Saved to `Content/{podcast_name}/{episode_name}/Quality_Control_Results/rebuttal_verification/`):
- `rebuttal_scores.json`: Accuracy/completeness/effectiveness scores per rebuttal
- `rewriting_actions.json`: What was rewritten and why
- `final_verification.json`: Before/after comparison of rebuttal quality

**Storage Path Examples**:
- `C:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Content\Joe_Rogan\Joe_Rogan_Mike_Baker\Quality_Control_Results\`
- `C:\Users\nfaug\OneDrive - LIR\Desktop\YouTuber\Content\Gary_Stevenson\Episode_Analysis\Quality_Control_Results\`

### Schema Validation Requirements

**Mandatory JSON Validation**:
- Each stage MUST validate input against expected schema before processing
- Each stage MUST validate output against target schema before saving
- Pipeline MUST halt if schema validation fails
- Error logs MUST specify exact schema violation details
   - 9-10: Direct false claims, explicit misinformation
   - 7-8: Strong implied harm, misleading statements
   - 5-6: Questionable but not clearly harmful
   - 1-4: Opinion, legitimate debate, weak evidence

2. **Factual Accuracy**: Are claims demonstrably false or misleading?
   - 9-10: Verifiably false statements
   - 7-8: Misleading but contains some truth
   - 5-6: Exaggerated but based on real events
   - 1-4: Opinion or subjective interpretation

3. **Potential Impact**: How likely to actually mislead/harm viewers?
   - 9-10: Could directly influence harmful behavior
   - 7-8: Likely to spread misinformation
   - 5-6: May confuse some viewers
   - 1-4: Limited real-world impact

4. **Content Specificity**: Are concrete false claims made vs. vague opinions?
   - 9-10: Specific false factual claims
   - 7-8: Concrete but debatable assertions
   - 5-6: General statements, some specifics
   - 1-4: Vague opinions, no specific claims

5. **Context Appropriateness**: Genuine misinformation vs. legitimate debate?
   - 9-10: Clear misinformation, no legitimate debate angle
   - 7-8: Mostly harmful but some legitimate concerns
   - 5-6: Mixed - some legitimate aspects
   - 1-4: Primarily legitimate discussion/inquiry

### Filtering Rules for Pass 2

**Automatic Removal Criteria**:
- Quote Strength < 6/10 (weak evidence in quotes)
- Factual Accuracy < 5/10 (mostly accurate statements)
- Potential Impact < 5/10 (limited real-world impact)
- Content Specificity < 5/10 (too vague to be harmful)
- Context Appropriateness < 5/10 (may be legitimate debate)
- Any score showing high variance (conflicting assessments)

**Quality Score Calculation**:
```
Quality Score = (Quote Strength × 0.3) + (Factual Accuracy × 0.25) + 
                (Potential Impact × 0.25) + (Content Specificity × 0.1) + 
                (Context Appropriateness × 0.1)
```

**Final Selection Logic**:
1. Apply automatic removal criteria
2. Calculate quality scores for remaining segments
3. Sort by quality score (highest first)
4. Select top 8-12 segments
5. Ensure minimum of 6 segments (lower threshold to 6.0 if needed)

---

### AI Implementation Details

**API Integration**:
- Both Pass 2 and Rebuttal Verification will use Google Gemini API calls
- Consistent with existing `transcript_analyzer.py` implementation
- Reuse existing API configuration and error handling
- Same authentication and rate limiting as Pass 1

### Prompt Engineering Strategy

**Pass 2 Prompt Key Elements**:
- "IGNORE all existing severityRating fields - they are unreliable"
- "Evaluate based ONLY on the actual quotes provided"
- "Score each dimension independently on 1-10 scale"
- "Be conservative - err on side of exclusion for weak evidence"
- "Focus on explicit harmful content, not implied meanings"
- "Automatically filter out segments not meeting minimum thresholds"
- "**Quality requirement**: MUST produce at least 6 high-quality segments or reject analysis"
- "Return final ranked list of 8-12 highest quality segments"

**Rebuttal Verification & Rewriting Prompt Key Elements**:
- "Fact-check each rebuttal claim for accuracy"
- "Score accuracy, completeness, and effectiveness on 1-10 scale"
- "Identify factual errors, missing arguments, weak evidence"
- "REWRITE sections scoring below thresholds (Accuracy<7, Completeness<6, Effectiveness<6)"
- "Expand rebuttals with additional counter-arguments when insufficient"
- "Correct inaccuracies with verified facts and reliable sources"
- "**MAINTAIN CHARACTER VOICE**: Humorous, slightly sarcastic, and unapologetically snarky. Think Jon Stewart at his most pointed, but with a sharper, more cynical edge. Be factual but relentlessly entertaining. Call out nonsense with biting wit, but allow moments of genuine anger and frustration when detailing real-world consequences"
- "Ensure rebuttals effectively counter the original harmful claims while preserving the commentator's clear point of view on misinformation dangers"

---

## Implementation Phases

### Phase 1: Core Quality Assessment (Days 1-4)
- [ ] **Create JSON schemas** for all input/output formats
- [ ] **Implement schema validation** functions with detailed error reporting
- [ ] Create `quality_assessor.py` with strict input/output validation
- [ ] Design Pass 2 prompt with scoring rubrics and filtering logic
- [ ] Implement 5-dimension scoring system with automatic filtering
- [ ] Add final selection logic (rank by score, take top 8-12)
- [ ] **Implement test result preservation** (quality scores, filtering decisions, selection rationale)
- [ ] Test with current Joe Rogan / Mike Baker episode
- [ ] Validate filtering and selection accuracy
- [ ] **Verify JSON format consistency** between Pass 1 → Pass 2 → Script Generation

### Phase 2: Rebuttal Verification & Rewriting System (Days 5-8)
- [ ] **Extend JSON schemas** for verification and rewriting results
- [ ] Create `rebuttal_verifier_rewriter.py` with strict schema validation
- [ ] Design fact-checking prompt for post_clip sections
- [ ] Implement 3-dimension scoring system (accuracy, completeness, effectiveness)
- [ ] Add rewriting triggers and logic for insufficient scores
- [ ] Implement rewriting prompts for fact correction and expansion
- [ ] Add source verification and citation enhancement
- [ ] **Implement test result preservation** (rebuttal scores, rewriting actions, verification results)
- [ ] Test with generated unified scripts
- [ ] Validate rewritten rebuttals for accuracy and effectiveness
- [ ] **Verify JSON format consistency** for verified script output

### Phase 3: Pipeline Integration (Days 9-10)
- [ ] Create `two_pass_controller.py` orchestrator
- [ ] Modify `master_processor_v2.py` to use new system
- [ ] **Update all downstream processes to use `verified_unified_script.json`**:
  - [ ] TTS processing modules
  - [ ] Video generation scripts  
  - [ ] Timeline creation tools
  - [ ] Any other script consumers
- [ ] Add configuration options (target segment count, thresholds)
- [ ] Ensure backward compatibility (fallback to original system)
- [ ] Add rebuttal verification and rewriting as final pipeline step
- [ ] Implement script versioning (original vs verified_unified_script)

### Phase 4: Testing & Refinement (Days 10-12)
- [ ] Test on Gary Stevenson episode (known problematic ratings)
- [ ] Compare output quality vs. original 20-segment approach
- [ ] Test rebuttal verification accuracy
- [ ] **Validate all downstream processes work with verified_unified_script.json**
- [ ] Fine-tune scoring weights and thresholds
- [ ] Add logging and diagnostics for transparency

---

## Success Metrics

### Quantitative Measures
- **Segment Count**: Reduce from 20 to 8-12 segments
- **Quality Consistency**: ≥80% of final segments should have Quality Score ≥7.0
- **Processing Time**: Additional QC should add <5 minutes to pipeline
- **Rebuttal Accuracy**: ≥95% of verified rebuttals should be factually correct
- **Rewriting Effectiveness**: ≥90% of rewritten rebuttals should score ≥7.0 on all dimensions
- **Schema Compliance**: 100% JSON format consistency between all pipeline stages
- **Test Result Preservation**: 100% of evaluation results saved for analysis and debugging

### Qualitative Measures
- **Relevance**: Final segments should be clearly problematic (no obvious false positives)
- **Impact**: Selected segments should have genuine potential for harm/misinformation
- **Narrative Quality**: Segments should work well together in final video
- **Rebuttal Strength**: Counter-arguments should be compelling and well-sourced

---

## Risk Mitigation

### Edge Cases
1. **Too Few Segments After Filtering**
   - **Primary Response**: Flag analysis for manual review if fewer than 6 segments meet criteria
   - **No Quality Degradation**: Do not automatically lower thresholds to force 6 segments
   - **Analysis Rejection**: Better to reject poor quality analysis than accept substandard segments
   - **Manual Override**: Allow manual selection if episode has genuine value despite low scores
   - **Alerting**: Log insufficient segment warnings for process improvement

2. **Poor Rebuttal Quality**
   - **Primary Response**: Automatically rewrite rebuttals scoring below thresholds
   - **Fact Correction**: Replace inaccurate information with verified facts
   - **Content Expansion**: Add missing counter-arguments and evidence
   - **Fallback**: Flag for manual review if rewriting fails to improve scores
   - **Quality Gate**: Don't proceed with unreliable rebuttals

### Quality Assurance
- **Manual Spot Checks**: Review 20% of filtered results manually
- **Rebuttal Fact-Checking**: Verify AI-generated fact-checks
- **Feedback Loop**: Track which segments perform well in final videos
- **Test Result Analysis**: Regular review of saved quality scores and filtering decisions to identify patterns
- **Schema Compliance Monitoring**: Automated alerts if JSON format violations occur
- **Performance Tracking**: Monitor quality score distributions over time to detect system drift

---

## Configuration Options

### Tunable Parameters
```json
{
  "target_segment_count": 10,
  "min_segment_count": 6,
  "max_segment_count": 12,
  "quality_threshold": 6.5,
  "strict_quality_enforcement": true,
  "reject_analysis_below_min": true,
  "auto_include_threshold": 8.5,
  "rebuttal_accuracy_threshold": 7.0
}
```

### Processing Modes
- **Conservative**: Higher thresholds, prefer quality over quantity
- **Balanced**: Default settings as specified above
- **Comprehensive**: Lower thresholds, closer to original 20-segment approach

---

## Implementation Timeline

**Week 1**: Core development (Phases 1-2)
**Week 2**: Integration and testing (Phases 3-4)
**Week 3**: Refinement and deployment
**Week 4**: Monitoring and optimization

**Go-Live Target**: 3-4 weeks from development start

---

## Next Steps

1. **Review and Approve Plan**: Finalize approach and parameters
2. **Create Development Environment**: Set up testing with existing episodes
3. **Begin Phase 1**: Start with quality_assessor.py implementation
4. **Design Pass 2 Prompt**: Create rigorous evaluation criteria
5. **Test with Known Data**: Validate approach on Joe Rogan/Mike Baker episode

**Ready to proceed with implementation?**
