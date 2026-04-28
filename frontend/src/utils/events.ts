/**
 * Event name constants for bridge communication.
 * Must match core/events.py in the Python backend.
 */

export const EVENT_TASK_STATE_CHANGED = "task_state_changed"
export const EVENT_TASK_PROGRESS = "task_progress"
export const EVENT_TASK_LOG = "task_log"
export const EVENT_TASK_REMOVED = "task_removed"
export const EVENT_TASK_INFO_UPDATED = "task_info_updated"
export const EVENT_QUEUE_CHANGED = "queue_changed"
export const EVENT_AUTO_EDITOR_VERSION_CHANGED = "auto_editor_version_changed"
export const EVENT_AUTO_EDITOR_DOWNLOAD_PROGRESS = "auto_editor_download_progress"
export const EVENT_LOG_LINE = "log_line"
