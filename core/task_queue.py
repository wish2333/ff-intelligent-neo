"""Task queue: CRUD, state machine, ordering, and JSON persistence."""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Callable

from core.models import Task, TaskState, VALID_TRANSITIONS
from core.paths import get_data_dir

_SAVE_DEBOUNCE_SECONDS = 0.5


def _queue_path() -> Path:
    return get_data_dir() / "queue_state.json"


class TaskQueue:
    """In-memory task queue with optional JSON persistence."""

    def __init__(self) -> None:
        self._tasks: list[Task] = []
        self._lock = threading.RLock()
        self._save_timer: threading.Timer | None = None
        self._on_change: Callable[[dict], None] | None = None

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def set_on_change(self, fn: Callable[[dict], None]) -> None:
        """Register a callback fired on any queue mutation.

        The callback receives a ``summary`` dict (counts by state).
        """
        self._on_change = fn

    def _notify(self) -> None:
        if self._on_change:
            self._on_change(self.get_summary())

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def add_task(self, task: Task) -> Task:
        with self._lock:
            self._tasks.append(task)
            self._notify()
            return task

    def add_tasks(self, tasks: list[Task]) -> list[Task]:
        with self._lock:
            self._tasks.extend(tasks)
            self._notify()
            return tasks

    def remove_tasks(self, task_ids: list[str]) -> int:
        with self._lock:
            before = len(self._tasks)
            self._tasks = [t for t in self._tasks if t.id not in task_ids]
            removed = before - len(self._tasks)
            if removed:
                self._notify()
            return removed

    def get_task(self, task_id: str) -> Task | None:
        with self._lock:
            for t in self._tasks:
                if t.id == task_id:
                    return t
        return None

    def get_all_tasks(self) -> list[dict]:
        """Return serialised copies of all tasks (queue order)."""
        with self._lock:
            return [t.to_dict() for t in self._tasks]

    def get_all_tasks_objects(self) -> list[Task]:
        """Return references to all task objects (queue order).

        Caller must hold ``_lock`` or accept a point-in-time snapshot.
        """
        with self._lock:
            return list(self._tasks)

    # ------------------------------------------------------------------
    # State machine
    # ------------------------------------------------------------------

    def transition_task(self, task_id: str, new_state: TaskState) -> str | None:
        """Transition a task to *new_state*.

        Returns the previous state, or ``None`` if the task was not found.
        Raises ``ValueError`` on invalid transitions.
        """
        with self._lock:
            task = self._get_by_id_unlocked(task_id)
            if task is None:
                return None
            old = task.transition(new_state)
            self._notify()
            self._schedule_save()
            return old

    # ------------------------------------------------------------------
    # Ordering
    # ------------------------------------------------------------------

    def reorder_tasks(self, task_ids: list[str]) -> None:
        """Reorder the queue to match *task_ids* (first = top).

        Task IDs not present in the current queue are ignored.
        Tasks present in the queue but missing from *task_ids* keep their
        relative order and are appended at the end.
        """
        with self._lock:
            existing = {t.id: t for t in self._tasks}
            ordered: list[Task] = []
            for tid in task_ids:
                if tid in existing:
                    ordered.append(existing.pop(tid))
            # append leftovers
            ordered.extend(existing.values())
            self._tasks = ordered
            self._schedule_save()

    # ------------------------------------------------------------------
    # Bulk operations
    # ------------------------------------------------------------------

    def clear_completed(self) -> int:
        with self._lock:
            before = len(self._tasks)
            self._tasks = [
                t for t in self._tasks if t.state != "completed"
            ]
            removed = before - len(self._tasks)
            if removed:
                self._notify()
                self._schedule_save()
            return removed

    def clear_all(self) -> int:
        with self._lock:
            removed = len(self._tasks)
            self._tasks.clear()
            if removed:
                self._notify()
                self._schedule_save()
            return removed

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def get_summary(self) -> dict[str, int]:
        with self._lock:
            summary: dict[str, int] = {
                "pending": 0,
                "running": 0,
                "paused": 0,
                "completed": 0,
                "failed": 0,
                "cancelled": 0,
            }
            for t in self._tasks:
                summary[t.state] += 1
            return summary

    # ------------------------------------------------------------------
    # Persistence (Phase 5 will flesh this out; stubs here)
    # ------------------------------------------------------------------

    def save_state(self) -> None:
        """Persist current queue to JSON (debounced in normal flow).

        Saves all non-terminal tasks plus the most recent 50 terminal tasks
        (completed/failed/cancelled) to keep the file manageable.
        """
        from core.logging import get_logger
        _logger = get_logger()

        with self._lock:
            non_terminal = [t for t in self._tasks if t.state not in ("completed", "failed", "cancelled")]
            terminal = [t for t in self._tasks if t.state in ("completed", "failed", "cancelled")]
            # Keep most recent 50 terminal tasks (newest first by completed_at)
            terminal.sort(key=lambda t: t.completed_at or "", reverse=True)
            terminal = terminal[:50]
            # Restore original queue order and snapshot under lock
            saved_ids = {t.id for t in non_terminal + terminal}
            ordered = [t for t in self._tasks if t.id in saved_ids]
            to_save = [t.to_dict() for t in ordered]

        path = _queue_path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "version": "2.0.0",
                "saved_at": datetime.now().isoformat(),
                "tasks": to_save,
            }
            # Atomic write: temp file + os.replace (prevents corruption on crash)
            import tempfile as _tempfile
            fd, tmp_path = _tempfile.mkstemp(
                dir=path.parent, suffix=".tmp", prefix="queue_"
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    f.write("\n")
                os.replace(tmp_path, str(path))
            except Exception:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                raise
        except OSError as exc:
            _logger.error("Failed to save queue state: {}", exc)

    def load_state(self) -> None:
        """Load queue from JSON on startup with state recovery.

        Per PRD 10.3:
        - running -> failed (process no longer exists after restart)
        - paused -> pending (process no longer exists after restart)
        - pending -> kept as-is
        - completed/failed/cancelled -> kept for history

        Note: State is set directly rather than via Task.transition() because
        loaded tasks may not have valid transition paths from their persisted
        state (e.g. "running" was valid at save time but the process is gone).
        Both running and paused tasks are marked as failed -- user can retry.
        """
        from core.logging import get_logger
        _logger = get_logger()

        path = _queue_path()
        if not path.exists():
            return
        try:
            text = path.read_text(encoding="utf-8")
            data = json.loads(text)
            tasks = [Task.from_dict(d) for d in data.get("tasks", [])]

            recovered = 0
            for task in tasks:
                if task.state in ("running", "paused"):
                    task.state = "failed"
                    task.error = "Process interrupted by app close"
                    task.completed_at = datetime.now().isoformat()
                    recovered += 1

            if recovered:
                _logger.info(
                    "Queue recovery: {} tasks reset to failed (app was closed)",
                    recovered,
                )

            with self._lock:
                self._tasks = tasks
        except (json.JSONDecodeError, OSError) as exc:
            _logger.error("Failed to load queue state: {}", exc)

    def _schedule_save(self) -> None:
        """Debounced save -- avoids hammering disk on rapid state changes."""
        if self._save_timer is not None:
            self._save_timer.cancel()

        def _do_save() -> None:
            self._save_timer = None
            self.save_state()

        self._save_timer = threading.Timer(_SAVE_DEBOUNCE_SECONDS, _do_save)
        self._save_timer.daemon = True
        self._save_timer.start()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_by_id_unlocked(self, task_id: str) -> Task | None:
        for t in self._tasks:
            if t.id == task_id:
                return t
        return None
