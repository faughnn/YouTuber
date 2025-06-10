# APM Project Memory Bank Directory

This directory houses the detailed log files for the Master Processor Architectural Refactoring project.

## Structure:

Logs are organized into subdirectories corresponding to each Phase in the `Implementation_Plan.md`:

- `Phase_1_Discovery_Architecture_Analysis/` - Analysis of current implementation and architecture design
- `Phase_2_Core_Orchestrator_Implementation/` - New master_processor_v2.py development
- `Phase_3_Video_Processing_Implementation/` - Video clipping and compilation stages
- `Phase_4_Testing_Validation/` - Testing suite and validation work
- `Phase_5_Deployment_Optimization/` - Final integration and deployment preparation

## Individual Log Files:

Within each phase directory, individual `.md` files capture logs for specific tasks:
- `Task_[Phase.Task]_[Description]_Log.md` (e.g., `Task_1.1_Current_Implementation_Analysis_Log.md`)

All log entries within these files adhere to the format defined in `APM/prompts/02_Utility_Prompts_And_Format_Definitions/Memory_Bank_Log_Format.md`.

## Usage:

Implementation Agents must log their activities, outputs, and results to the appropriate task log file upon completing work or reaching significant milestones, after receiving confirmation from the User. This ensures the Manager Agent and User can track progress accurately across the multi-phase refactoring project.
