"""Thread pool-based task runner with per-task cancellation.

Phase 2a: start / stop only.
Phase 4: pause / resume / retry via OS-level process suspension.
"""

from __future__ import annotations

import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

from core.command_builder import build_command, build_output_path
from core.ffmpeg_runner import run_single
from core.ffmpeg_setup import get_ffmpeg_path, get_ffprobe_path
from core.logging import get_logger
from core.models import Task, TaskProgress, TaskState
from core.process_control import resume_process, suspend_process
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

    # ------------------------------------------------------------------
    # Single-task control
    # ------------------------------------------------------------------

    def start_task(self, task_id: str) -> bool:
        """Submit a pending task for execution.

        Returns ``True`` if the task was submitted, ``False`` otherwise
        (e.g. wrong state, not found).
        """
        task = self._queue.get_task(task_id)
        if task is None:
            logger.warning("start_task: task {} not found", task_id)
            return False
        if not task.can_transition("running"):
            logger.warning(
                "start_task: invalid transition {} -> running", task.state
            )
            return False

        ffmpeg_path = get_ffmpeg_path()
        ffprobe_path = get_ffprobe_path()
        if not ffmpeg_path:
            task.error = "FFmpeg binary not found"
            self._queue.transition_task(task_id, "failed")
            self._emit("task_state_changed", {
                "task_id": task_id,
                "old_state": "pending",
                "new_state": "failed",
            })
            self._emit("queue_changed", self._queue.get_summary())
            return False

        # Create cancel event for this task
        cancel_event = threading.Event()
        with self._lock:
            self._cancel_events[task_id] = cancel_event

        old_state = self._queue.transition_task(task_id, "running")
        self._emit("task_state_changed", {
            "task_id": task_id,
            "old_state": old_state or "pending",
            "new_state": "running",
        })
        self._emit("queue_changed", self._queue.get_summary())

        # Build output path
        output_path = build_output_path(
            task.file_path, task.config, task.config.output_dir
        )
        task.output_path = output_path

        # Build FFmpeg args
        args = build_command(task.config, task.file_path, output_path)

        # Submit to thread pool
        assert self._executor is not None
        self._executor.submit(
            self._run_task, task, ffmpeg_path, ffprobe_path, args, cancel_event
        )
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

        # Kill the process
        with self._procs_lock:
            proc = self._running_procs.pop(task_id, None)
            if proc and proc.poll() is None:
                try:
                    proc.kill()
                except OSError:
                    pass

        # Transition state
        if task.state in ("pending", "running", "paused"):
            old_state = self._queue.transition_task(task_id, "cancelled")
            self._emit("task_state_changed", {
                "task_id": task_id,
                "old_state": old_state or task.state,
                "new_state": "cancelled",
            })
            self._emit("queue_changed", self._queue.get_summary())

        # Cleanup
        with self._lock:
            self._cancel_events.pop(task_id, None)

        return True

    def pause_task(self, task_id: str) -> bool:
        """Suspend a running task's FFmpeg process."""
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
                    "pause_task: suspend failed (task {}): {}", task_id, exc
                )
                return False

        old_state = self._queue.transition_task(task_id, "paused")
        self._emit("task_state_changed", {
            "task_id": task_id,
            "old_state": old_state or "running",
            "new_state": "paused",
        })
        self._emit("queue_changed", self._queue.get_summary())
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
                self._emit("task_state_changed", {
                    "task_id": task_id,
                    "old_state": old_state or "paused",
                    "new_state": "failed",
                })
                self._emit("queue_changed", self._queue.get_summary())
                return False

            try:
                resume_process(proc.pid)
            except OSError as exc:
                logger.warning(
                    "resume_task: resume failed (task {}): {}", task_id, exc
                )
                return False

        old_state = self._queue.transition_task(task_id, "running")
        self._emit("task_state_changed", {
            "task_id": task_id,
            "old_state": old_state or "paused",
            "new_state": "running",
        })
        self._emit("queue_changed", self._queue.get_summary())
        logger.info("Task {} resumed", task_id)
        return True

    def retry_task(self, task_id: str) -> bool:
        """Reset a failed task to pending and re-execute it."""
        task = self._queue.get_task(task_id)
        if task is None or task.state != "failed":
            return False

        # Clear error and reset progress
        task.error = ""
        task.progress = TaskProgress()
        task.output_path = ""
        task.started_at = ""
        task.completed_at = ""

        old_state = self._queue.transition_task(task_id, "pending")
        self._emit("task_state_changed", {
            "task_id": task_id,
            "old_state": old_state or "failed",
            "new_state": "pending",
        })
        self._emit("queue_changed", self._queue.get_summary())

        # Re-submit for execution
        return self.start_task(task_id)

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

    def _run_task(
        self,
        task: Task,
        ffmpeg_path: str,
        ffprobe_path: str,
        args: list[str],
        cancel_event: threading.Event,
    ) -> None:
        """Execute a single task in a worker thread."""
        task_id = task.id

        def _on_progress(progress: TaskProgress) -> None:
            self._emit("task_progress", {
                "task_id": task_id,
                "progress": progress.to_dict(),
            })

        def _on_log(line: str) -> None:
            self._emit("task_log", {
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

        self._emit("task_state_changed", {
            "task_id": task_id,
            "old_state": old_state,
            "new_state": new_state,
        })
        self._emit("queue_changed", self._queue.get_summary())
