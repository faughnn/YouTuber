# Quality Improvement Plan

Identified bottlenecks in the multi-pass content analysis pipeline, ranked by expected impact on final output quality.

---

## Priority 1: Critical Quality Killers

### 1.1 Narrative Prompt Overloaded (Single Call Doing Too Much)
**File:** `Generation_Templates/tts_podcast_narrative_prompt.txt`
**Impact:** High — the biggest quality bottleneck

The narrative generation prompt asks Gemini to simultaneously:
- Adopt a complex persona (Jon Stewart-like snarky commentator)
- Select and reorder clips (choose the hook)
- Research guest credibility via internet search
- Write factual rebuttals for every claim
- Apply 15+ TTS formatting rules
- Structure output as strict JSON with many nested fields
- Calibrate timing for each section

The model's attention is split so thin that everything comes out mediocre.

**Fix:** Split into 2 calls — structure/clip selection first, then creative script writing.

### 1.2 Rich Upstream Analysis Thrown Away Before Script Generation
**Files:** `multi_pass_controller.py`, `podcast_narrative_generator.py`

Pass 1 (`transcript_analyzer.py`) identifies `rhetorical_strategies`, `societal_impacts`, `harm_category` for each segment. The narrative prompt never tells the model to use any of it. The most expensive analysis stage produces insights the scriptwriter never sees.

**Fix:** Make narrative prompt explicitly reference and use `identified_rhetorical_strategies`, `potential_societal_impacts`, and `harm_category` from the upstream analysis.

### 1.3 Failed Rebuttals Silently Pass as "Passed With Warning"
**File:** `binary_rebuttal_verifier.py:303`

After 3 failed self-correction iterations, the verifier marks the result as `passed=True` with a warning field. No downstream code checks the warning. Rebuttals that never passed verification end up in the final output.

```python
# Current (line 303):
passed=True,  # Still use the content, but with warning
```

**Fix:** Either genuinely fail these (remove from output), or add a human review flag that blocks pipeline completion.

---

## Priority 2: Significant Design Issues

### 2.1 Binary Gates Lose Context by Running as Separate Calls
**File:** `binary_segment_filter.py`

Each of the 5 segment filter gates is a standalone API call. Gate 3 (accuracy) doesn't know Gate 1 already confirmed a factual claim exists. Gate 5 (rebuttability) doesn't know what Gate 3 concluded about accuracy.

**Fix:** Consolidate 5 binary gates into a single structured prompt evaluating all dimensions at once. Cuts ~80 API calls/video and produces more coherent judgments.

### 2.2 Gate 1 Kills "Societal Damage" Content by Design
**Files:** `binary_segment_filter.py` (gate 1), `Analysis_Guidelines/Joe_Rogan_selective_analysis_rules.txt`

The analysis rules define Societal Damage (dehumanizing rhetoric, institutional erosion) as a key category. Gate 1 asks "is this a specific factual claim?" and immediately rejects anything that isn't a factual claim. The pipeline hunts for societal damage content, then the first filter rejects it.

**Fix:** Rework Gate 1 to ask "Does this segment contain content worth rebutting?" rather than requiring a specific factual claim.

### 2.3 Confirmed-True Claims Still Reach Final Output
**File:** `multi_pass_controller.py` (recent events verifier integration)

The Recent Events Verifier can discover a claim is actually true (not misinformation), setting `_correction_needed=True`. No downstream stage checks this flag. The pipeline can end up "rebutting" something that's correct.

**Fix:** Filter out or correct segments with `_correction_needed=True` before script generation.

### 2.4 "Use ALL Provided Segments" Forces Weak Material In
**File:** `Generation_Templates/tts_podcast_narrative_prompt.txt` (line 23)

The prompt says "Use ALL provided segments — incorporate every analyzed clip into your script." If 2 out of 10 survivors are marginal, the AI must build commentary around weak material, dragging down the whole script.

**Fix:** Allow the narrative generator to minimize or skip weak segments. Or add a pre-generation quality cut.

### 2.5 TTS Rules Mixed Into Creative Writing Prompt
**File:** `Generation_Templates/tts_podcast_narrative_prompt.txt` (section 6)

20+ TTS formatting rules are embedded in the creative prompt, acting as constant cognitive tax on the creative writing.

**Fix:** Remove TTS rules from the narrative prompt. Add a separate TTS post-processing step that reformats the generated script.

---

## Priority 3: Moderate Issues

### 3.1 Diversity Selector Ignores Quality
**File:** `diversity_selector.py`

Round-robin selection picks the first segment per topic group regardless of quality score. Topic assignment uses keyword matching where common words ("million", "government", "school") match nearly everything.

**Fix:** Sort each topic group by quality signal before selecting. Consider LLM-based topic classification instead of keyword matching.

### 3.2 Fixed 20-Segment Output Cap
**File:** `Analysis_Guidelines/Joe_Rogan_selective_analysis_rules.txt`

Rules demand exactly 20 segments regardless of podcast length. A 45-minute podcast gets padded with weak segments; a 4-hour podcast gets artificially truncated.

**Fix:** Make segment count proportional to transcript duration (e.g., 5-8 per hour).

### 3.3 Rebuttal Clip Context Truncated to 3 Quotes
**File:** `binary_rebuttal_verifier.py:363`

Only the first 3 quotes from a clip are passed to verification. If the harmful claim is in quotes 4+, the verifier can't properly assess the rebuttal.

**Fix:** Pass all quotes, or at minimum the ones the rebuttal references.

### 3.4 False Negative Scanner Is Mostly a No-Op
**File:** `false_negative_scanner.py`

Re-runs the exact same 5-gate system that already rejected the segment. At temperature 0.3, the LLM gives near-identical answers. Recovery is effectively a coin flip, capped at 2 segments max.

**Fix:** Use relaxed gate thresholds for recovery, or a separate "second opinion" prompt rather than re-running identical gates.

### 3.5 120-Second Clip Cap Truncates Complex Arguments
**File:** `Analysis_Guidelines/Joe_Rogan_selective_analysis_rules.txt`

Many conspiracy arguments take 3-5 minutes to unfold. The 2-minute cap captures partial arguments, making rebuttals look like straw-man attacks.

**Fix:** Allow longer clips for segments flagged as multi-part arguments, or explicitly note when a clip is truncated.

---

## Priority 4: Cleanup and Maintenance

### 4.1 Persona Definition Duplicated 4+ Times With Drift
The "Alternative Media Literacy" character profile is copy-pasted in:
- `Generation_Templates/tts_podcast_narrative_prompt.txt`
- `Generation_Templates/tts_podcast_narrative_prompt_WITHOUT_HOOK.txt`
- `Quality_Control/rebuttal_rewriting_prompt.txt`
- `binary_rebuttal_verifier.py:493`

Each copy has subtle differences (e.g., "Jon Stewart-inspired tone" vs "Think Jon Stewart at his most pointed").

**Fix:** Single canonical persona file imported/included everywhere.

### 4.2 Narrative Prompt Has Internal Duplication
**File:** `Generation_Templates/tts_podcast_narrative_prompt.txt`

The "Post-Clip Deconstruction" section (lines 62-111) is repeated almost verbatim in the "Remaining Clips" section (lines 88-111), wasting tokens and confusing the model.

**Fix:** Deduplicate the prompt.

### 4.3 WITHOUT_HOOK Variant Is a Separate File With Drift Risk
Two nearly identical 260+ line prompt files that must be manually kept in sync.

**Fix:** Single template with a conditional hook section.

### 4.4 Analysis Rules Hardcoded to "Joe Rogan"
**File:** `multi_pass_controller.py:306-309`

The rules file path is hardcoded to `Joe_Rogan_selective_analysis_rules.txt`. Non-JRE podcasts either get JRE rules or no rules.

**Fix:** Generic rules file, or host-specific rules with a fallback.

### 4.5 Old Numeric Scoring System Still in Codebase
`quality_assessor.py` (1058 lines), `two_pass_controller.py` (547 lines), and `pass_2_prompt.txt` represent the old numeric scoring system replaced by binary gates. Still imported as fallbacks.

**Fix:** Remove or archive these files once binary system is fully validated.

### 4.6 Duplicate Analysis Rules File
`Joe_Rogan_selective_analysis_rules copy.txt` exists with minor differences ("Dangerous Misinformation" vs "Misinformation"). Editing the wrong file causes silent failures.

**Fix:** Delete the copy.

---

## Changes Already Made (This Session)

- **Model upgrade:** All Gemini API calls switched from `gemini-2.5-flash` / `gemini-2.0-flash` to `gemini-2.5-pro`
- **Temperature tuning:** Per-stage temperatures adjusted:
  - Transcript analysis: 0.1 (unchanged — factual extraction)
  - Binary segment filter gates: 0.1 → 0.3
  - Quality assessment: 0.1 → 0.2
  - Narrative generation: 0.1 → 0.6
  - Rebuttal verification gates: 0.1 → 0.3
  - Rebuttal rewrites: base 0.2 → 0.4, cap 0.4 → 0.7
  - Rebuttal assessment: 0.1 → 0.2
  - Rebuttal voice rewriting: 0.2 → 0.5
  - Recent events verification: 0.1 (unchanged — factual checking)
  - YouTube description: 0.3 (unchanged)
