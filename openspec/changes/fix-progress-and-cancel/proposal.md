## Why

Two critical bugs in the batch FFmpeg processing workflow:

1. **FFmpeg progress data is dumped to loguru console instead of the frontend UI.** The `on_log` callback in `ffmpeg_runner.py` forwards every stderr line to the frontend via `log_line` events, and the loguru frontend sink also forwards all Python log lines (including DEBUG-level ffmpeg runner internals). The result is the frontend log panel is flooded with raw ffmpeg output while the actual progress panel only shows a percentage bar. Users want to see: speed, elapsed time / total time, and status at a glance.

2. **Cancel functionality is broken.** When the user clicks "Cancel", the cancel event is set in `BatchRunner.cancel()`, but the thread pool does not properly await cancellation. Specifically: the `_run_all` function iterates `futures` and calls `f.result()` which blocks until each task completes -- even cancelled tasks run to completion because `proc.kill()` only fires after the cancel event is detected in the polling loop. Meanwhile the frontend never receives a `batch_complete` with cancellation status, so `processing` stays `true` and buttons remain in the wrong state.

## What Changes

- Stop forwarding raw ffmpeg stderr lines to the frontend log panel. Keep loguru console logging at DEBUG level only for Python-side debugging.
- Send enriched progress events to frontend: include `current_time_seconds`, `total_duration_seconds`, `speed`, `fps`, and `status` in a single structured payload.
- Update frontend `ProgressPanel.vue` to display: progress percentage, speed, elapsed time / total duration, status badge -- replacing the raw log dump.
- Fix cancel: after setting the cancel event, actively kill all running subprocesses and wait for thread termination with timeout. Emit `batch_cancelled` event so the frontend can correctly reset state.
- Fix frontend button state: add a `cancelled` event listener that sets `processing = false`, matching the `batch_complete` behavior.
- Remove the `log_line` event emission from `on_log` callback in batch_runner.py to stop flooding the frontend.

## Capabilities

### New Capabilities
- `progress-display`: Structured progress data display (speed, elapsed/total time, status) in the frontend UI replacing raw ffmpeg log output
- `cancel-reliability`: Robust subprocess cancellation that kills running ffmpeg processes, properly cleans up threads, and resets frontend state

### Modified Capabilities
<!-- No existing specs to modify -->

## Impact

- `core/ffmpeg_runner.py`: Remove `on_log` callback usage for line-by-line forwarding; enrich `on_progress` callback with `current_seconds` and `total_duration`
- `core/batch_runner.py`: Remove `on_log` callback wiring; fix `cancel()` to track and kill running processes; emit `batch_cancelled` event
- `core/models.py`: Add `current_seconds` and `total_duration` fields to `TaskProgress`
- `core/logging.py`: Remove or silence the frontend sink for DEBUG-level messages (or raise log level to WARNING for the frontend sink)
- `frontend/src/composables/useBatchProcess.ts`: Add `batch_cancelled` event listener; remove `log_line` listener; update `TaskProgressData` interface
- `frontend/src/components/ProgressPanel.vue`: Replace raw log section with structured progress display (speed, time, status)
- `frontend/src/App.vue`: Remove global `log_line` event listener
- `frontend/src/components/LogViewer.vue`: Can be removed or kept for future use (no longer auto-populated with ffmpeg output)
