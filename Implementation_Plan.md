# Implementation Plan

Project Goal: Implement a Two-Pass AI Quality Control System for the existing YouTube video processing pipeline to improve segment selection quality through evidence-based filtering and automated rebuttal verification.

## Phase 1: Core Infrastructure & Schema Foundation - Agent Group Alpha (Agent_Schema_Architect, Agent_Quality_Assessor)

### Task 1.1 - Agent_Schema_Architect: JSON Schema Definition & Validation Framework
Objective: Create comprehensive JSON schema definitions and validation framework for all pipeline data structures to ensure format consistency across Pass 1, Pass 2, and rebuttal verification stages.

1. Extract and formalize existing JSON schemas from codebase.
   - Analyze `original_audio_analysis_results.json` structure from Joe Rogan/Mike Baker episode.
   - Document `unified_podcast_script.json` schema from existing pipeline outputs.
   - Create formal JSON schema files for validation.
     * Guidance: Use JSON Schema Draft 2020-12 standard for compatibility with Python jsonschema library.
2. Design new schema structures for Pass 2 and verification outputs.
   - Create `final_filtered_analysis_results.json` schema with quality assessment fields.
   - Design `verified_unified_script.json` schema with verification metadata.
   - Define Quality Control Results schema for test result preservation.
     * Guidance: Extend existing schemas to maintain backward compatibility for downstream processes.
3. Implement comprehensive validation framework.
   - Create validation utility module with schema checking functions.
   - Implement strict input/output validation for each processing stage.
   - Add detailed error reporting for schema violations.
     * Guidance: Use Python jsonschema library, halt pipeline on validation failures.

### Task 1.2 - Agent_Quality_Assessor: Pass 2 Quality Assessment Implementation
Objective: Implement the core quality assessment module with 5-dimension scoring system and evidence-based filtering logic.

1. Create `quality_assessor.py` module with strict I/O validation.
   - Implement module structure following existing codebase patterns.
   - Add comprehensive input validation against Pass 1 schema.
   - Implement output validation against Pass 2 schema.
     * Guidance: Follow existing module patterns from `transcript_analyzer.py`.
2. Implement 5-dimension scoring system.
   - Create scoring functions for Quote Strength (1-10 scale).
   - Implement Factual Accuracy assessment logic.
   - Add Potential Impact evaluation framework.
   - Create Content Specificity scoring mechanism.
   - Implement Context Appropriateness evaluation.
     * Guidance: Each dimension should be independently scored with clear criteria documentation.
3. Design and implement automatic filtering rules.
   - Apply removal criteria (Quote Strength < 6, Factual Accuracy < 5, etc.).
   - Implement quality score calculation with weighted formula.
   - Create final selection logic (sort by score, select top 8-12).
   - Add minimum segment count enforcement (reject if < 6 segments).
     * Guidance: Use weighted formula: (Quote Strength × 0.3) + (Factual Accuracy × 0.25) + (Potential Impact × 0.25) + (Content Specificity × 0.1) + (Context Appropriateness × 0.1).
4. Implement Gemini API integration for Pass 2 analysis.
   - Adapt existing API patterns from `transcript_analyzer.py`.
   - Create Pass 2 prompt with rigorous evaluation criteria.
   - Implement error handling and retry logic consistent with existing code.
     * Guidance: Reuse API configuration from existing codebase, maintain same authentication and rate limiting patterns.

## Phase 2: Rebuttal Verification & Rewriting System - Agent Group Beta (Agent_Fact_Checker, Agent_Content_Rewriter)

### Task 2.1 - Agent_Fact_Checker: Rebuttal Verification Framework
Objective: Create comprehensive fact-checking system for generated rebuttals with accuracy scoring and verification metadata tracking.

1. Create `rebuttal_verifier_rewriter.py` module with schema validation.
   - Implement module structure following existing patterns.
   - Add input validation against unified script schema.
   - Design output validation for verified script format.
     * Guidance: Follow same architectural patterns as other processing modules.
2. Implement 3-dimension rebuttal assessment system.
   - Create Accuracy scoring function (1-10 scale) for factual correctness.
   - Implement Completeness evaluation for argument coverage.
   - Add Effectiveness assessment for counter-argument strength.
     * Guidance: Each dimension independently scored with detailed criteria.
3. Design verification triggers and thresholds.
   - Implement rewriting triggers (Accuracy < 7, Completeness < 6, Effectiveness < 6).
   - Create verification decision logic.
   - Add metadata tracking for assessment scores.
     * Guidance: Clear threshold-based triggers to ensure consistent quality standards.

### Task 2.2 - Agent_Content_Rewriter: Automated Rebuttal Rewriting System
Objective: Implement intelligent rewriting system that improves inadequate rebuttals while maintaining voice consistency and factual accuracy.

1. Design rewriting action framework.
   - Implement fact correction logic for inaccurate statements.
   - Create source enhancement system for credible citations.
   - Add argument expansion for missing counter-points.
   - Design clarity improvement mechanisms.
     * Guidance: Maintain the humorous, sarcastic, and snarky commentary style with factual entertainment and pointed wit.
2. Implement Gemini API integration for rewriting.
   - Create fact-checking prompts for post_clip sections.
   - Design rewriting prompts with voice consistency requirements.
   - Implement source verification and citation enhancement logic.
     * Guidance: Use existing Gemini API patterns, ensure prompts maintain character voice.
3. Create rewriting validation and output generation.
   - Implement before/after comparison tracking.
   - Add rewriting action logging for transparency.
   - Generate final verified script with improvement metadata.
     * Guidance: Preserve original content alongside improvements for auditing.

## Phase 3: Pipeline Integration & Orchestration - Agent Group Gamma (Agent_Pipeline_Integrator, Agent_Downstream_Updater)

### Task 3.1 - Agent_Pipeline_Integrator: Two-Pass Controller Implementation
Objective: Create central orchestration module that coordinates Pass 1, Pass 2, and rebuttal verification in seamless pipeline flow.

1. Create `two_pass_controller.py` orchestrator module.
   - Design controller class with stage management.
   - Implement error handling between stages.
   - Add progress tracking and logging integration.
     * Guidance: Follow existing orchestration patterns from `master_processor_v2.py`.
2. Implement stage coordination logic.
   - Create Pass 1 → Pass 2 data flow management.
   - Add Pass 2 → Script Generation coordination.
   - Implement Script → Verification pipeline stage.
   - Design rollback mechanisms for stage failures.
     * Guidance: Ensure atomic operations between stages with proper error recovery.
3. Integrate with existing master processor.
   - Modify `master_processor_v2.py` to use two-pass system.
   - Update pipeline flow to include new stages.
   - Maintain existing logging and progress reporting.
     * Guidance: Preserve existing pipeline behavior while adding new stages.

### Task 3.2 - Agent_Downstream_Updater: Downstream Process Updates
Objective: Update all downstream processes to consume verified_unified_script.json instead of unified_podcast_script.json with comprehensive compatibility testing.

1. Audit and update script consumer modules.
   - Update `Video_Clipper/script_parser.py` to use verified script.
   - Modify `Video_Compilator/simple_compiler.py` for new format.
   - Update TTS processing modules in Chatterbox and ElevenLabs.
   - Modify any other hardcoded script references.
     * Guidance: Change all references from unified_podcast_script.json to verified_unified_script.json.
2. Implement compatibility validation.
   - Test JSON format compatibility across all consumers.
   - Validate that verified script maintains required structure.
   - Add error handling for missing verified scripts.
     * Guidance: Ensure verified_unified_script.json maintains exact same structure as original for compatibility.
3. Update configuration and file paths.
   - Modify hardcoded paths in config files.
   - Update any documentation referencing old script format.
   - Add configuration options for new system parameters.
     * Guidance: Update default_config.yaml and any other configuration references.

## Phase 4: Quality Control Results & Test Infrastructure - Agent Group Delta (Agent_QC_Infrastructure, Agent_Testing_Specialist)

### Task 4.1 - Agent_QC_Infrastructure: Quality Control Results Framework
Objective: Implement comprehensive test result preservation system for Pass 2 evaluations and rebuttal verification outcomes.

1. Create Quality Control Results directory structure.
   - Design file organization for `Content/{podcast_name}/{episode_name}/Quality_Control_Results/`.
   - Implement `pass_2_evaluation/` subdirectory with result files.
   - Create `rebuttal_verification/` subdirectory structure.
     * Guidance: Follow existing Content directory organization patterns.
2. Implement result preservation logic.
   - Create quality scores tracking for individual segments.
   - Add filtering decisions logging with rationale.
   - Implement selection logic documentation.
   - Design rebuttal assessment tracking system.
     * Guidance: Save detailed JSON files for each evaluation step for debugging and analysis.
3. Add result analysis and reporting capabilities.
   - Create summary reporting for quality assessments.
   - Implement trend analysis for score distributions.
   - Add diagnostic capabilities for filtering decisions.
     * Guidance: Enable comprehensive analysis of quality control effectiveness.

### Task 4.2 - Agent_Testing_Specialist: Integration Testing & Validation
Objective: Comprehensive testing framework to validate entire two-pass system with existing episode data and ensure pipeline integrity.

1. Create comprehensive test suite for new modules.
   - Implement unit tests for quality_assessor.py functionality.
   - Create integration tests for rebuttal_verifier_rewriter.py.
   - Add end-to-end pipeline testing with real episode data.
     * Guidance: Use existing episode data from Joe Rogan/Mike Baker and Gary Stevenson episodes.
2. Validate JSON format consistency across pipeline.
   - Test schema validation at each stage.
   - Verify downstream process compatibility.
   - Validate error handling and recovery mechanisms.
     * Guidance: Ensure 100% format consistency between all pipeline stages.
3. Performance optimization and monitoring.
   - Implement performance benchmarking for new stages.
   - Add monitoring for API usage and rate limiting.
   - Optimize processing time for additional quality control steps.
     * Guidance: Additional QC should add <5 minutes to pipeline processing time.

## General Project Notes

### Memory Bank System
Memory Bank System: Directory `/Memory/` with log files per phase, organized as `Memory/Phase_X_Title_From_Plan/Task_[Phase.Task]_Description_Log.md`, as detailed in `Memory/README.md`. This multi-file structure supports the complex, phased nature of this integration project with multiple specialized agents and distinct technical domains.

### Quality Control Configuration
The implementation includes configurable parameters for quality thresholds, target segment counts, and processing modes (Conservative, Balanced, Comprehensive) as specified in the original plan document.

### API Integration Standards
All new Gemini API integrations must follow existing patterns from `transcript_analyzer.py` and `podcast_narrative_generator.py` for consistency in authentication, error handling, and rate limiting.

---

## Note on Handover Protocol

For long-running projects or situations requiring context transfer (e.g., exceeding LLM context limits, changing specialized agents), the APM Handover Protocol should be initiated. This ensures smooth transitions and preserves project knowledge. Detailed procedures are outlined in the framework guide:

`prompts/01_Manager_Agent_Core_Guides/05_Handover_Protocol_Guide.md`

The current Manager Agent or the User should initiate this protocol as needed.