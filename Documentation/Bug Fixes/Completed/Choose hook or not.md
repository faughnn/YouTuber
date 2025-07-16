# Plan: Implement User Choice for Narrative Format

## Problem
The current narrative generation stage (`_stage_4_narrative_generation`) in `master_processor_v2.py` implicitly uses a single prompt file. The user requires a choice between two prompt files: `tts_podcast_narrative_prompt.txt` (with hook) and `tts_podcast_narrative_prompt_WITHOUT_HOOK.txt` (without hook). This choice needs to be presented to the user via the `run_pipeline_menu.py` script.

## Proposed Solution

### 1. Modify `run_pipeline_menu.py`
Integrate a user prompt for narrative format selection within the `run_pipeline_menu.py` script.

*   **Location:** The prompt should appear before the call to `processor._stage_4_narrative_generation` in both `run_pipeline_start_from` and `run_pipeline_one_stage` functions.
*   **Prompt:** Ask the user to choose between "with hook" and "without hook" (e.g., by entering '1' or '2').
*   **Validation:** Implement basic input validation to ensure the user enters a valid choice.
*   **Pass Argument:** The selected format (e.g., a string like "with_hook" or "without_hook") will be passed as a new argument to the `_stage_4_narrative_generation` method of the `MasterProcessorV2` instance.

### 2. Modify `master_processor_v2.py`
Update the `_stage_4_narrative_generation` method to accept and utilize the new argument.

*   **Method Signature:** Add a new parameter (e.g., `narrative_format`) to the `_stage_4_narrative_generation` method.
*   **Conditional Logic:** Inside this method, use an `if/else` statement or a dictionary lookup to construct the correct absolute path to the prompt file based on the `narrative_format` argument.
    *   If `narrative_format` is "with_hook", use `tts_podcast_narrative_prompt.txt`.
    *   If `narrative_format` is "without_hook", use `tts_podcast_narrative_prompt_WITHOUT_HOOK.txt`.
*   **File Loading:** Load the content of the chosen prompt file for narrative generation.

## Implementation Steps

1.  **Read `run_pipeline_menu.py`**: Re-read the file to confirm the exact locations for modification.
2.  **Read `master_processor_v2.py`**: Read the file to understand the `_stage_4_narrative_generation` method and its dependencies.
3.  **Apply Changes to `run_pipeline_menu.py`**:
    *   Add the user prompt and input validation.
    *   Pass the `narrative_format` to `_stage_4_narrative_generation`.
4.  **Apply Changes to `master_processor_v2.py`**:
    *   Update the method signature.
    *   Implement the conditional logic for prompt file selection.
5.  **Testing (Manual)**: After implementation, manually test the pipeline by running `run_pipeline_menu.py` and selecting Stage 4 (either directly or by starting from it) to ensure the prompt appears and the correct file is used.
