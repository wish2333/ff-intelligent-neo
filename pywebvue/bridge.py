"""Bridge base class and @expose decorator."""

from __future__ import annotations

import functools
import queue
import threading
from typing import Any, Callable

_EVENT_QUEUE_TIMEOUT = 0.05  # seconds


def expose(func: Callable[..., Any]) -> Callable[..., Any]:
    """Wrap a bridge method with try/except error handling.

    Exposed methods should return ``{"success": True, "data": ...}``.
    On unhandled exception, the decorator returns
    ``{"success": False, "error": "..."}`` instead of crashing.
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> dict[str, Any]:
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    return wrapper


class Bridge:
    """Base class for Python APIs exposed to the frontend.

    Subclass this and decorate public methods with ``@expose``.
    Use ``self._emit(event_name, data)`` to push events to the frontend.

    Thread safety
    -------------
    ``_emit`` is thread-safe: events are queued and flushed on the main
    thread by ``_tick``, which is driven by a repeating JS timer set up
    by :class:`~pywebvue.app.App`.

    ``run_on_main_thread`` lets background threads schedule work on the
    main thread via registered handlers.
    """

    def __init__(self) -> None:
        self._window = None
        self._drop_lock = threading.Lock()
        self._dropped_paths: list[str] = []
        self._event_queue: queue.Queue[tuple[str, Any]] = queue.Queue()
        self._task_queue: queue.Queue[tuple[str, Any, queue.Queue]] = queue.Queue()
        self._handlers: dict[str, Callable[..., Any]] = {}
        self._cancelled_tasks: set[str] = set()
        self._task_id_counter = 0
        self._task_counter_lock = threading.Lock()

    # ------------------------------------------------------------------
    # Event emission (thread-safe, queue-based)
    # ------------------------------------------------------------------

    def _emit(self, event: str, data: Any = None) -> None:
        """Enqueue an event for main-thread dispatch.

        Events arrive at the frontend with at most ``tick_interval`` ms
        of delay (set in :class:`~pywebvue.app.App`).
        """
        self._event_queue.put((event, data))

    @expose
    def tick(self) -> None:
        """Flush queued events and run main-thread tasks.

        Called periodically by a JS timer set up in :class:`~pywebvue.app.App`.
        Exposed so the JS timer can reach it.
        """
        self._tick_internal()

    def _tick_internal(self) -> None:
        """Flush queued events.  Called on the main thread by a JS timer."""
        import json

        if self._window is None:
            return

        # --- flush events ---
        events: list[str] = []
        while True:
            try:
                event, data = self._event_queue.get_nowait()
            except queue.Empty:
                break
            payload = json.dumps(data, ensure_ascii=False) if data is not None else "null"
            events.append(
                f"document.dispatchEvent(new CustomEvent('pywebvue:{event}',"
                f"{{detail: {payload}, bubbles: true}}))"
            )

        if events:
            js = ";".join(events)
            try:
                self._window.evaluate_js(js)
            except Exception:
                pass

        # --- execute main-thread tasks ---
        while True:
            try:
                task_id, args, result_q = self._task_queue.get_nowait()
            except queue.Empty:
                break

            if task_id in self._cancelled_tasks:
                self._cancelled_tasks.discard(task_id)
                if not result_q.empty():
                    try:
                        result_q.get_nowait()
                    except queue.Empty:
                        pass
                result_q.put(("cancelled", None))
                continue

            handler = self._handlers.get(task_id)
            if handler is None:
                result_q.put(("error", RuntimeError(f"Handler '{task_id}' not registered")))
                continue

            try:
                result = handler(args)
                result_q.put(("ok", result))
            except Exception as exc:
                result_q.put(("error", exc))

    # ------------------------------------------------------------------
    # Main-thread task execution
    # ------------------------------------------------------------------

    def register_handler(self, name: str, fn: Callable[[Any], Any]) -> None:
        """Register a named handler for ``run_on_main_thread``.

        Args:
            name: Unique identifier for the handler.
            fn: Callable that receives the task payload and returns a result.
        """
        self._handlers[name] = fn

    def unregister_handler(self, name: str) -> None:
        """Remove a previously registered handler."""
        self._handlers.pop(name, None)

    def run_on_main_thread(
        self,
        name: str,
        args: Any = None,
        *,
        timeout: float = 10.0,
    ) -> Any:
        """Schedule a handler on the main thread and wait for the result.

        Args:
            name: Handler name (must be registered via ``register_handler``).
            args: Payload passed to the handler.
            timeout: Maximum seconds to wait for the result.

        Returns:
            The handler's return value.

        Raises:
            RuntimeError: If the handler is not registered.
            TimeoutError: If the main thread does not process the task in time.
        """
        if name not in self._handlers:
            raise RuntimeError(f"Handler '{name}' is not registered")

        result_q: queue.Queue[tuple[str, Any]] = queue.Queue()
        self._task_queue.put((name, args, result_q))

        try:
            status, value = result_q.get(timeout=timeout)
        except Exception:
            with self._task_counter_lock:
                self._cancelled_tasks.add(name)
            raise TimeoutError(f"Main-thread task '{name}' timed out after {timeout}s")

        if status == "error":
            raise value
        if status == "cancelled":
            raise TimeoutError(f"Main-thread task '{name}' was cancelled")
        return value

    # ------------------------------------------------------------------
    # Native file drag-and-drop
    # ------------------------------------------------------------------

    def _on_drop(self, event: dict) -> None:
        """Handle native file drag-and-drop events from pywebview."""
        files = event.get("dataTransfer", {}).get("files", [])
        paths = [
            f.get("pywebviewFullPath")
            for f in files
            if f.get("pywebviewFullPath")
        ]
        if paths:
            with self._drop_lock:
                self._dropped_paths.extend(paths)

    @expose
    def get_dropped_files(self) -> dict[str, Any]:
        """Return file paths from the most recent drop event and clear the buffer."""
        with self._drop_lock:
            paths = list(self._dropped_paths)
            self._dropped_paths.clear()
        return {"success": True, "data": paths}
