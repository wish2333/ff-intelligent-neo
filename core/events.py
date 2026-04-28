"""Event name constants for bridge communication.

Both the Python backend and TypeScript frontend reference these names.
For the frontend, the TS constants are defined in frontend/src/utils/events.ts.
"""

# Task lifecycle events
TASK_STATE_CHANGED = "task_state_changed"
TASK_PROGRESS = "task_progress"
TASK_LOG = "task_log"
TASK_REMOVED = "task_removed"
TASK_INFO_UPDATED = "task_info_updated"

# Queue events
QUEUE_CHANGED = "queue_changed"

# Auto-editor events
AUTO_EDITOR_VERSION_CHANGED = "auto_editor_version_changed"
AUTO_EDITOR_DOWNLOAD_PROGRESS = "auto_editor_download_progress"

# Log forwarding
LOG_LINE = "log_line"
