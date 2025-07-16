# APM Project Memory Bank Directory

This directory houses the detailed log files for the YouTube Pipeline UI project.

## Structure:

Logs are organized into subdirectories corresponding to each Phase in the `Implementation_Plan.md`. Within each phase directory, individual `.md` files capture logs for specific tasks.

### Phase Structure:
- `Phase_1_Flask_Foundation/` - Core Flask application setup and database models
- `Phase_2_Pipeline_Integration/` - Master processor integration and episode management
- `Phase_3_Segment_Selection/` - JSON parsing and segment selection interface
- `Phase_4_Realtime_System/` - SocketIO integration and JavaScript client
- `Phase_5_Preset_Audio/` - Workflow presets and audio integration
- `Phase_6_Polish_Testing/` - UI polish and integration testing

### File Naming Convention:
Individual task log files follow the pattern: `Task_[Phase.Task]_Short_Description_Log.md`

Example: `Task_1.1_Core_Flask_App_Setup_Log.md`

All log entries within these files adhere to the format defined in `prompts/02_Utility_Prompts_And_Format_Definitions/Memory_Bank_Log_Format.md`.
