"""Thread pool-based task runner with per-task cancellation.

Phase 2a: start / stop only.
Phase 4: pause / resume / retry via OS-level process suspension.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable

from core.command_builder import build_command, build_output_path
from core.ffmpeg_runner import run_single
from core.ffmpeg_setup import get_ffmpeg_path, get_ffprobe_path
from core.logging import get_logger
from core.events import TASK_STATE_CHANGED, QUEUE_CHANGED, TASK_PROGRESS, TASK_LOG
from core.models import Task, TaskProgress, TaskState
from core.process_control import resume_process, suspend_process, kill_process_tree
from core.task_queue import TaskQueue

logger = get_logger()


class TaskRunner:
    """Manages concurrent FFmpeg task execution."""

    def __init__(
        self,
        queue: TaskQueue,
        emit: Callable,
    ) -> None:
        self._queue = queue
        self._emit = emit
        self._cancel_events: dict[str, threading.Event] = {}
        self._running_procs: dict[str, subprocess.Popen] = {}
        self._procs_lock = threading.Lock()
        self._executor: ThreadPoolExecutor | None = None
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self, max_workers: int = 2) -> None:
        if self._executor is not None:
            return
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        logger.info("TaskRunner started (max_workers={})", max_workers)

    def shutdown(self, wait: bool = False) -> None:
        """Stop all running tasks and shut down the thread pool."""
        self.stop_all()
        if self._executor is not None:
            self._executor.shutdown(wait=wait)
            self._executor = None
            logger.info("TaskRunner shut down")

    def force_kill_all(self) -> None:
        """Kill all running FFmpeg processes without state transitions.

        Used during app shutdown where we just need processes dead.
        """
        with self._procs_lock:
            for proc in self._running_procs.values():
                if proc.poll() is None:
                    kill_process_tree(proc.pid)
            self._running_procs.clear()
        for evt in self._cancel_events.values():
            evt.set()
        self._cancel_events.clear()
        if self._executor is not None:
            self._executor.shutdown(wait=False)

    # ------------------------------------------------------------------
    # Single-task control
    # ------------------------------------------------------------------

    def start_task(self, task_id: str, config: dict | None = None) -> bool:
        """Submit a pending task for execution.

        If *config* is provided, it updates ``task.config`` before building
        the command so the latest UI settings are always used.

        Returns ``True`` if the task was submitted, ``False`` otherwise
        (e.g. wrong state, not found).
        """
        from core.models import TaskConfig

        task = self._queue.get_task(task_id)
        if task is None:
            logger.warning("start_task: task {} not found", task_id)
            return False
        if not task.can_transition("running"):
            logger.warning(
                "start_task: invalid transition {} -> running", task.state
            )
            return False

        # Apply latest config from frontend if provided
        if config is not None:
            incoming = TaskConfig.from_dict(config)
            current = task.config
            # Preserve the task's sub-configs (merge, avsmix, clip, custom_command)
            # so that a merge task added from MergePage keeps its own merge config
            # rather than being overwritten by the global config (which may only
            # have intro/outro from the Config page).
            task.config = TaskConfig(
                transcode=incoming.transcode,
                filters=incoming.filters,
                clip=incoming.clip or current.clip,
                merge=current.merge or incoming.merge,
                avsmix=current.avsmix or incoming.avsmix,
                custom_command=current.custom_command or incoming.custom_command,
                output_dir=incoming.output_dir or current.output_dir,
            )

        ffmpeg_path = get_ffmpeg_path()
        ffprobe_path = get_ffprobe_path()
        if not ffmpeg_path:
            task.error = "FFmpeg binary not found"
            self._queue.transition_task(task_id, "failed")
            self._emit(TASK_STATE_CHANGED, {
                "task_id": task_id,
                "old_state": "pending",
                "new_state": "failed",
            })
            self._emit(QUEUE_CHANGED, self._queue.get_summary())
            return False

        # Create cancel event for this task
        cancel_event = threading.Event()
        with self._lock:
            self._cancel_events[task_id] = cancel_event

        old_state = self._queue.transition_task(task_id, "running")
        self._emit(TASK_STATE_CHANGED, {
            "task_id": task_id,
            "old_state": old_state or "pending",
            "new_state": "running",
        })
        self._emit(QUEUE_CHANGED, self._queue.get_summary())

        # Build output path
        output_path = build_output_path(
            task.file_path, task.config, task.config.output_dir
        )
        task.output_path = output_path

        # Build FFmpeg args
        args = build_command(task.config, task.file_path, output_path, task.duration_seconds)

        # For concat_protocol and ts_concat merge modes, create a temp list file
        temp_list_path: str | None = None
        try:
            if task.config.merge and task.config.merge.merge_mode in ("concat_protocol", "ts_concat"):
                def _escape_concat_path(p: str) -> str:
                    escaped = p.replace("\\", "/").replace("'", "'\\''")
                    return f"'{escaped}'"
                list_content = "\n".join(
                    f"file {_escape_concat_path(path)}" for path in task.config.merge.file_list
                )
                tmp = tempfile.NamedTemporaryFile(
                    mode="w", suffix=".txt", delete=False, encoding="utf-8"
                )
                tmp.write(list_content)
                tmp.close()
                temp_list_path = tmp.name
                args = [temp_list_path if a == "list.txt" else a for a in args]

            # Submit to thread pool (pass temp_list_path for cleanup)
            assert self._executor is not None
            self._executor.submit(
                self._run_task, task, ffmpeg_path, ffprobe_path, args, cancel_event,
                temp_list_path,
            )
        except Exception:
            # Clean up temp file if submission fails
            if temp_list_path:
                try:
                    os.unlink(temp_list_path)
                except OSError:
                    pass
            raise
        return True

    def stop_task(self, task_id: str) -> bool:
        """Cancel / stop a single task."""
        task = self._queue.get_task(task_id)
        if task is None:
            return False

        # Set cancel event
        cancel_event = self._cancel_events.get(task_id)
        if cancel_event:
            cancel_event.set()

        # Kill the process tree
        with self._procs_lock:
            proc = self._running_procs.pop(task_id, None)
            if proc and proc.poll() is None:
                kill_process_tree(proc.pid)

        # Transition state
        if task.state in ("pending", "running", "paused"):
            old_state = self._queue.transition_task(task_id, "cancelled")
            self._emit(TASK_STATE_CHANGED, {
                "task_id": task_id,
                "old_state": old_state or task.state,
                "new_state": "cancelled",
            })
            self._emit(QUEUE_CHANGED, self._queue.get_summary())

        # Cleanup
        with self._lock:
            self._cancel_events.pop(task_id, None)

        return True

    def pause_task(self, task_id: str) -> bool:
        """Suspend a running task's FFmpeg process.

        If OS-level suspension fails (e.g. permission denied), falls back
        to killing the process and marking the task as failed with the
        current progress preserved so the user can retry.
        """
        task = self._queue.get_task(task_id)
        if task is None or task.state != "running":
            return False

        with self._procs_lock:
            proc = self._running_procs.get(task_id)
            if proc is None:
                return False

            # Check if process already exited
            if proc.poll() is not None:
                # Process finished on its own - let _run_task handle the
                # terminal transition, don't mark as paused
                logger.info(
                    "pause_task: process already exited (task {})", task_id
                )
                return False

            try:
                suspend_process(proc.pid)
            except OSError as exc:
                logger.warning(
                    "pause_task: suspend failed (task {}): {}, "
                    "falling back to kill + preserve progress",
                    task_id, exc,
                )
                # Degradation: kill the process and mark as failed
                # Progress is preserved in the task for potential retry
                kill_process_tree(proc.pid)
                try:
                    proc.wait(timeout=5)
                except Exception:
                    pass
                self._running_procs.pop(task_id, None)
                cancel_event = self._cancel_events.get(task_id)
                if cancel_event:
                    cancel_event.set()
                with self._lock:
                    self._cancel_events.pop(task_id, None)

                old_state = self._queue.transition_task(task_id, "failed")
                task.error = f"Suspend failed: {exc}"
                self._emit(TASK_STATE_CHANGED, {
                    "task_id": task_id,
                    "old_state": old_state or "running",
                    "new_state": "failed",
                })
                self._emit(QUEUE_CHANGED, self._queue.get_summary())
                return False

        old_state = self._queue.transition_task(task_id, "paused")
        self._emit(TASK_STATE_CHANGED, {
            "task_id": task_id,
            "old_state": old_state or "running",
            "new_state": "paused",
        })
        self._emit(QUEUE_CHANGED, self._queue.get_summary())
        logger.info("Task {} paused", task_id)
        return True

    def resume_task(self, task_id: str) -> bool:
        """Resume a paused task's FFmpeg process."""
        task = self._queue.get_task(task_id)
        if task is None or task.state != "paused":
            return False

        with self._procs_lock:
            proc = self._running_procs.get(task_id)
            if proc is None:
                return False

            if proc.poll() is not None:
                logger.warning(
                    "resume_task: process already exited (task {})", task_id
                )
                # Mark as failed since process died while paused
                old_state = self._queue.transition_task(task_id, "failed")
                task.error = "Process exited while paused"
                self._emit(TASK_STATE_CHANGED, {
                    "task_id": task_id,
                    "old_state": old_state or "paused",
                    "new_state": "failed",
                })
                self._emit(QUEUE_CHANGED, self._queue.get_summary())
                return False

            try:
                resume_process(proc.pid)
            except OSError as exc:
                logger.warning(
                    "resume_task: resume failed (task {}): {}", task_id, exc
                )
                return False

        old_state = self._queue.transition_task(task_id, "running")
        self._emit(TASK_STATE_CHANGED, {
            "task_id": task_id,
            "old_state": old_state or "paused",
            "new_state": "running",
        })
        self._emit(QUEUE_CHANGED, self._queue.get_summary())
        logger.info("Task {} resumed", task_id)
        return True

    def retry_task(self, task_id: str, config: dict | None = None) -> bool:
        """Reset a failed task to pending and re-execute it.

        Keeps log_lines intact so the user can review previous failure logs.
        """
        task = self._queue.get_task(task_id)
        if task is None or task.state != "failed":
            return False

        # Clear error and reset progress but keep log_lines
        with task.lock:
            task.error = ""
            task.progress = TaskProgress()
            task.output_path = ""
            task.started_at = ""
            task.completed_at = ""

        old_state = self._queue.transition_task(task_id, "pending")
        self._emit(TASK_STATE_CHANGED, {
            "task_id": task_id,
            "old_state": old_state or "failed",
            "new_state": "pending",
        })
        self._emit(QUEUE_CHANGED, self._queue.get_summary())

        # Re-submit for execution with latest config
        return self.start_task(task_id, config=config)

    def reset_task(self, task_id: str) -> bool:
        """Reset a completed or cancelled task to pending for re-execution.

        Clears log_lines, output_path, error, progress, and timestamps.
        Does NOT auto-start the task.
        """
        task = self._queue.get_task(task_id)
        if task is None or task.state not in ("completed", "cancelled"):
            return False

        # Clear all runtime data
        with task.lock:
            task.error = ""
            task.progress = TaskProgress()
            task.output_path = ""
            task.log_lines = []
            task.started_at = ""
            task.completed_at = ""

        old_state = self._queue.transition_task(task_id, "pending")
        self._emit(TASK_STATE_CHANGED, {
            "task_id": task_id,
            "old_state": old_state or task.state,
            "new_state": "pending",
        })
        self._emit(QUEUE_CHANGED, self._queue.get_summary())
        return True

    # ------------------------------------------------------------------
    # Bulk control
    # ------------------------------------------------------------------

    def stop_all(self) -> int:
        """Stop all non-terminal tasks. Returns count stopped."""
        stopped = 0
        task_ids = [
            t.id for t in self._queue.get_all_tasks_objects()
            if t.state in ("pending", "running", "paused")
        ]
        for tid in task_ids:
            if self.stop_task(tid):
                stopped += 1
        return stopped

    def pause_all(self) -> int:
        """Pause all running tasks. Returns count paused."""
        paused = 0
        task_ids = [
            t.id for t in self._queue.get_all_tasks_objects()
            if t.state == "running"
        ]
        for tid in task_ids:
            if self.pause_task(tid):
                paused += 1
        return paused

    def resume_all(self) -> int:
        """Resume all paused tasks. Returns count resumed."""
        resumed = 0
        task_ids = [
            t.id for t in self._queue.get_all_tasks_objects()
            if t.state == "paused"
        ]
        for tid in task_ids:
            if self.resume_task(tid):
                resumed += 1
        return resumed

    # ------------------------------------------------------------------
    # Internal: task execution
    # ------------------------------------------------------------------

    def start_auto_editor_task(
        self,
        task_id: str,
        args: list[str],
        input_file: str = "",
        output_path: str = "",
    ) -> bool:
        """Submit a pending auto-editor task for execution.

        Args:
            task_id: Task identifier.
            args: auto-editor CLI arguments (including binary).
            input_file: Input file path (for metadata).
            output_path: Expected output path (for cleanup on cancel).

        Returns:
            True if the task was submitted, False otherwise.
        """
        task = self._queue.get_task(task_id)
        if task is None:
            logger.warning("start_auto_editor_task: task {} not found", task_id)
            return False
        if not task.can_transition("running"):
            logger.warning(
                "start_auto_editor_task: invalid transition {} -> running",
                task.state,
            )
            return False

        task.output_path = output_path

        cancel_event = threading.Event()
        with self._lock:
            self._cancel_events[task_id] = cancel_event

        old_state = self._queue.transition_task(task_id, "running")
        self._emit(TASK_STATE_CHANGED, {
            "task_id": task_id,
            "old_state": old_state or "pending",
            "new_state": "running",
        })
        self._emit(QUEUE_CHANGED, self._queue.get_summary())

        assert self._executor is not None
        self._executor.submit(
            self._run_auto_editor_task,
            task,
            args,
            cancel_event,
            input_file,
        )
        return True

    def _run_auto_editor_task(
        self,
        task: Task,
        args: list[str],
        cancel_event: threading.Event,
        input_file: str,
    ) -> None:
        """Execute a single auto-editor task in a worker thread."""
        from core.auto_editor_runner import read_auto_editor_output
        from core.process_control import kill_process_tree

        task_id = task.id

        def _on_progress(progress: TaskProgress) -> None:
            self._emit(TASK_PROGRESS, {
                "task_id": task_id,
                "progress": progress.to_dict(),
            })

        def _on_log(line: str) -> None:
            self._emit(TASK_LOG, {
                "task_id": task_id,
                "line": line,
            })

        env = os.environ.copy()
        env["NO_COLOR"] = "1"

        popen_kw: dict = {
            "stdout": subprocess.PIPE,
            "stderr": subprocess.STDOUT,
            "text": False,
            "env": env,
        }
        if sys.platform == "win32":
            popen_kw["creationflags"] = (
                subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            popen_kw["start_new_session"] = True

        try:
            proc = subprocess.Popen(args, **popen_kw)
        except OSError as e:
            logger.error("Failed to start auto-editor: {}", e)
            with self._lock:
                self._cancel_events.pop(task_id, None)
            task.error = str(e)
            self._queue.transition_task(task_id, "failed")
            self._emit(TASK_STATE_CHANGED, {
                "task_id": task_id,
                "old_state": "running",
                "new_state": "failed",
            })
            self._emit(QUEUE_CHANGED, self._queue.get_summary())
            return

        with self._procs_lock:
            self._running_procs[task_id] = proc

        logger.debug("Running auto-editor: {}", " ".join(args))

        # Read output and parse progress
        try:
            for segment in read_auto_editor_output(proc):
                if cancel_event.is_set():
                    break

                if segment.get("type") == "progress":
                    progress = TaskProgress(
                        percent=segment["progress"],
                        current_seconds=segment["current"],
                        total_seconds=segment["total"],
                    )
                    task.update_progress(progress)
                    _on_progress(progress)
                else:
                    log_line = segment.get("message", "")
                    if log_line:
                        task.append_log(log_line)
                        _on_log(log_line)
        except Exception:
            logger.exception("Error reading auto-editor output (task {})", task_id)

        # Wait for process to finish
        returncode = 0
        try:
            while True:
                if cancel_event.is_set():
                    kill_process_tree(proc.pid)
                    try:
                        proc.wait(timeout=5)
                    except Exception:
                        pass
                    returncode = -1
                    break

                returncode = proc.poll()
                if returncode is not None:
                    break

                time.sleep(0.1)
        except Exception as e:
            logger.error("Exception during auto-editor proc wait: {}", e)
            kill_process_tree(proc.pid)
            returncode = -1

        # Cleanup
        with self._procs_lock:
            self._running_procs.pop(task_id, None)
        with self._lock:
            self._cancel_events.pop(task_id, None)

        if cancel_event.is_set():
            # Already cancelled via stop_task -- cleanup partial output
            if task.output_path:
                try:
                    Path(task.output_path).unlink(missing_ok=True)
                except OSError:
                    pass
            return

        if returncode == 0:
            progress = TaskProgress(percent=100.0)
            task.update_progress(progress)
            _on_progress(progress)
            logger.info("auto-editor completed (task {})", task_id)
            new_state: TaskState = "completed"
            task.error = ""
        else:
            logger.error("auto-editor exited with code {} (task {})", returncode, task_id)
            new_state = "failed"
            task.error = f"auto-editor exited with code {returncode}"

        try:
            old_state = self._queue.transition_task(task_id, new_state)
        except ValueError:
            logger.debug("Task {} race: skip {} transition", task_id, new_state)
            return

        self._emit(TASK_STATE_CHANGED, {
            "task_id": task_id,
            "old_state": old_state,
            "new_state": new_state,
        })
        self._emit(QUEUE_CHANGED, self._queue.get_summary())

    def _run_task(
        self,
        task: Task,
        ffmpeg_path: str,
        ffprobe_path: str,
        args: list[str],
        cancel_event: threading.Event,
        temp_list_path: str | None = None,
    ) -> None:
        """Execute a single task in a worker thread."""
        task_id = task.id

        try:
            self._run_task_inner(
                task, ffmpeg_path, ffprobe_path, args, cancel_event,
            )
        finally:
            # Clean up temp list file for ts_concat
            if temp_list_path:
                try:
                    os.unlink(temp_list_path)
                except OSError:
                    pass

    def _run_task_inner(
        self,
        task: Task,
        ffmpeg_path: str,
        ffprobe_path: str,
        args: list[str],
        cancel_event: threading.Event,
    ) -> None:
        """Inner task execution (separated for cleanup)."""
        task_id = task.id

        def _on_progress(progress: TaskProgress) -> None:
            self._emit(TASK_PROGRESS, {
                "task_id": task_id,
                "progress": progress.to_dict(),
            })

        def _on_log(line: str) -> None:
            self._emit(TASK_LOG, {
                "task_id": task_id,
                "line": line,
            })

        def _on_proc_start(proc: subprocess.Popen) -> None:
            with self._procs_lock:
                self._running_procs[task_id] = proc

        success, error = run_single(
            task=task,
            ffmpeg_path=ffmpeg_path,
            ffprobe_path=ffprobe_path,
            args=args,
            cancel_event=cancel_event,
            on_progress=_on_progress,
            on_log=_on_log,
            on_proc_start=_on_proc_start,
        )

        # Cleanup process tracking
        with self._procs_lock:
            self._running_procs.pop(task_id, None)
        with self._lock:
            self._cancel_events.pop(task_id, None)

        # Transition to terminal state
        if cancel_event.is_set():
            # Already cancelled via stop_task -- skip double transition
            return

        if success:
            new_state: TaskState = "completed"
            task.error = ""
        else:
            new_state = "failed"
            task.error = error

        try:
            old_state = self._queue.transition_task(task_id, new_state)
        except ValueError:
            # Task was already cancelled by stop_task while we were finishing
            logger.debug("Task {} race: skip {} transition", task_id, new_state)
            return

        self._emit(TASK_STATE_CHANGED, {
            "task_id": task_id,
            "old_state": old_state,
            "new_state": new_state,
        })
        self._emit(QUEUE_CHANGED, self._queue.get_summary())
