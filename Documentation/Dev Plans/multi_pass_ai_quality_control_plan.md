# Multi-Pass AI Quality Control System - Implementation Plan

## Overview
Implement an automated 3-pass AI quality control system to improve segment selection quality by ignoring unreliable initial severity ratings and applying rigorous evidence-based filtering.

## Problem Statement
Current content analysis produces 20 segments with inconsistent severity ratings that don't reliably indicate actual harm potential:
- **MEDIUM** rated segments sometimes more impactful than **HIGH** rated ones
- Initial AI pass casts too wide a net with permissive criteria
- Severity ratings not trustworthy for filtering decisions
- Need automated quality control to reduce manual review burden

## Solution: Multi-Pass AI Analysis

### **Pass 1: Broad Analysis** (Current System - Keep As Is)
- **Purpose**: Wide net to capture all potential harmful content
- **Criteria**: Permissive to avoid missing anything important
- **Output**: `original_audio_analysis_results.json` (up to 20 segments)
- **Status**: ✅ Already implemented and working

### **Pass 2: Evidence-Based Quality Assessment**
- **Purpose**: Rigorous evaluation ignoring original severity ratings
- **Focus**: Evidence strength, factual accuracy, potential impact
- **Output**: `quality_assessed_analysis_results.json` (filtered with quality scores)

### **Pass 3: Final Ranking & Selection**
- **Purpose**: Select best segments for script generation
- **Focus**: Impact potential, uniqueness, narrative variety
- **Output**: `final_filtered_analysis_results.json` (8-12 high-quality segments)

---

## Pass 2: Quality Assessment Implementation

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

### Filtering Rules for Pass 2

**Automatic Removal Criteria**:
- Quote Strength < 6/10 (weak evidence in quotes)
- Factual Accuracy < 5/10 (mostly accurate statements)
- Content Specificity < 5/10 (too vague to be harmful)

**Flag for Review**:
- Context Appropriateness < 6/10 (may be legitimate debate)
- Any score showing high variance (conflicting assessments)

**Quality Score Calculation**:
```
Quality Score = (Quote Strength × 0.3) + (Factual Accuracy × 0.25) + 
                (Potential Impact × 0.25) + (Content Specificity × 0.1) + 
                (Context Appropriateness × 0.1)
```

---

## Pass 3: Final Selection Implementation

### Ranking Factors

1. **Quality Score** (from Pass 2) - 40% weight
2. **Harm Category Distribution** - 20% weight
   - Ensure variety: Misinformation, Conspiracy Theory, Pseudoscience, Societal Damage
   - Avoid over-representation of any single category
3. **Uniqueness Score** - 20% weight
   - Penalize repetitive content (similar topics/claims)
   - Reward novel harmful patterns
4. **Narrative Impact** - 15% weight
   - Compelling for viewers (clear, dramatic examples)
   - Good for educational purposes
5. **Duration Balance** - 5% weight
   - Mix of segment lengths (some short punchy clips, some longer explanations)

### Selection Logic

**Step 1: Filter by Quality Threshold**
- Keep only segments with Quality Score ≥ 6.5/10
- If this yields < 8 segments, lower threshold to 6.0

**Step 2: Ensure Critical Content**
- Auto-include segments with Quality Score ≥ 8.5 (genuinely harmful)
- Guarantee at least 2-3 truly problematic segments

**Step 3: Category Distribution**
- Target: 25% each of major harm categories
- Allow flexibility but avoid 70%+ of any single category

**Step 4: Remove Redundancy**
- Group similar topics (e.g., multiple trans-related segments)
- Keep only the highest-quality example from each group

**Step 5: Final Selection**
- Rank remaining segments by composite score
- Select top 8-12 segments
- Ensure minimum of 8, maximum of 12

**Output Target**: 8-12 segments (down from 20)

---

## Technical Implementation

### File Structure
```
Content_Analysis/
├── transcript_analyzer.py (Pass 1 - existing)
├── quality_assessor.py (Pass 2 - new)
├── segment_selector.py (Pass 3 - new)
├── multi_pass_controller.py (orchestrates all passes)
└── Quality_Control/
    ├── pass_2_prompt.txt
    ├── pass_3_prompt.txt
    └── scoring_rubrics.json
```

### Integration with Existing Pipeline

**Current Flow**:
```
Transcript → transcript_analyzer.py → original_audio_analysis_results.json → Script Generation
```

**New Flow**:
```
Transcript → transcript_analyzer.py → original_audio_analysis_results.json
    ↓
quality_assessor.py → quality_assessed_analysis_results.json
    ↓
segment_selector.py → final_filtered_analysis_results.json → Script Generation
```

### Prompt Engineering Strategy

**Pass 2 Prompt Key Elements**:
- "IGNORE all existing severityRating fields - they are unreliable"
- "Evaluate based ONLY on the actual quotes provided"
- "Score each dimension independently on 1-10 scale"
- "Be conservative - err on side of exclusion for weak evidence"
- "Focus on explicit harmful content, not implied meanings"

**Pass 3 Prompt Key Elements**:
- "Select 8-12 highest quality segments for maximum impact"
- "Prioritize variety across harm types"
- "Avoid repetitive topics - choose best example of each type"
- "Consider narrative flow and viewer engagement"

---

## Implementation Phases

### Phase 1: Core Quality Assessment (Days 1-3)
- [ ] Create `quality_assessor.py`
- [ ] Design Pass 2 prompt with scoring rubrics
- [ ] Implement 5-dimension scoring system
- [ ] Test with current Joe Rogan / Mike Baker episode
- [ ] Validate scoring accuracy on known good/bad segments

### Phase 2: Selection Algorithm (Days 4-5)
- [ ] Create `segment_selector.py`
- [ ] Implement ranking algorithm with weighted factors
- [ ] Add category distribution logic
- [ ] Add uniqueness detection (topic similarity)
- [ ] Test selection quality with multiple episodes

### Phase 3: Pipeline Integration (Days 6-7)
- [ ] Create `multi_pass_controller.py` orchestrator
- [ ] Modify `master_processor_v2.py` to use new system
- [ ] Add configuration options (target segment count, thresholds)
- [ ] Ensure backward compatibility (fallback to original system)

### Phase 4: Testing & Refinement (Days 8-10)
- [ ] Test on Gary Stevenson episode (known problematic ratings)
- [ ] Compare output quality vs. original 20-segment approach
- [ ] Fine-tune scoring weights and thresholds
- [ ] Add logging and diagnostics for transparency

---

## Success Metrics

### Quantitative Measures
- **Segment Count**: Reduce from 20 to 8-12 segments
- **Quality Consistency**: ≥80% of final segments should have Quality Score ≥7.0
- **Category Distribution**: No single harm category >50% of final segments
- **Processing Time**: Additional QC should add <5 minutes to pipeline

### Qualitative Measures
- **Relevance**: Final segments should be clearly problematic (no obvious false positives)
- **Impact**: Selected segments should have genuine potential for harm/misinformation
- **Variety**: Good mix of harm types, topics, and segment lengths
- **Narrative Quality**: Segments should work well together in final video

---

## Risk Mitigation

### Edge Cases
1. **Too Few Segments After Filtering**
   - Fallback: Lower quality thresholds gradually
   - Minimum: Always output at least 6 segments
   - Alerting: Log when falling back to lower standards

2. **Category Imbalance**
   - Strategy: Prefer variety over perfect scores
   - Ensure at least 2 different harm categories in final selection

3. **All Segments Similar Topics**
   - Detection: Compare segment titles and topics
   - Resolution: Force selection across diverse topics

### Quality Assurance
- **Manual Spot Checks**: Review 20% of filtered results manually
- **A/B Testing**: Compare engagement of multi-pass vs. original segments
- **Feedback Loop**: Track which segments perform well in final videos

---

## Configuration Options

### Tunable Parameters
```json
{
  "target_segment_count": 10,
  "min_segment_count": 8,
  "max_segment_count": 12,
  "quality_threshold": 6.5,
  "quality_fallback_threshold": 6.0,
  "auto_include_threshold": 8.5,
  "max_category_percentage": 50,
  "uniqueness_similarity_threshold": 0.7
}
```

### Processing Modes
- **Conservative**: Higher thresholds, prefer quality over quantity
- **Balanced**: Default settings as specified above
- **Comprehensive**: Lower thresholds, closer to original 20-segment approach

---

## Future Enhancements

### Advanced Features (Post-MVP)
1. **Machine Learning Integration**: Train model on manual quality assessments
2. **Viewer Engagement Prediction**: Factor in predicted audience response
3. **Dynamic Thresholds**: Adjust based on episode-specific context
4. **Cross-Episode Learning**: Improve scoring based on past episode performance

### Analytics Dashboard
- Track quality score distributions over time
- Monitor category balance across episodes
- Identify scoring patterns for continuous improvement

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
