"""App class - creates pywebview window and manages the bridge lifecycle."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable

import webview

from pywebvue.bridge import Bridge

_DEFAULT_TICK_INTERVAL = 50  # ms


def _resolve_frontend_path(frontend_dir: str) -> Path:
    """Resolve the absolute path to the frontend directory.

    Handles three environments:

    * **PyInstaller --onefile**: resources live in ``sys._MEIPASS``.
    * **PyInstaller --onedir**: resources live beside the executable.
    * **Development**: uses the given ``frontend_dir`` relative to CWD.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # --onefile bundle
        return Path(sys._MEIPASS) / frontend_dir
    if getattr(sys, "frozen", False):
        # --onedir bundle
        return Path(sys.executable).parent / frontend_dir
    return Path(frontend_dir)


class App:
    """Create a pywebview window wired to a :class:`Bridge` instance.

    Usage::

        from pywebvue import App, Bridge, expose

        class MyApi(Bridge):
            @expose
            def greet(self, name: str) -> dict:
                return {"success": True, "data": f"Hello, {name}!"}

        App(MyApi(), title="Demo", width=800, height=600,
            frontend_dir=".").run(dev=True)
    """

    def __init__(
        self,
        bridge: Bridge,
        *,
        title: str = "App",
        width: int = 800,
        height: int = 600,
        min_size: tuple[int, int] = (600, 400),
        frontend_dir: str = "frontend_dist",
        dev_url: str = "http://localhost:5173",
        tick_interval: int = _DEFAULT_TICK_INTERVAL,
        on_start: Callable[[], None] | None = None,
        on_closing: Callable[[], None] | None = None,
    ) -> None:
        self._bridge = bridge
        self._title = title
        self._width = width
        self._height = height
        self._min_size = min_size
        self._frontend_dir = frontend_dir
        self._dev_url = dev_url
        self._tick_interval = tick_interval
        self._on_start = on_start
        self._on_closing = on_closing

    @property
    def dev(self) -> bool:
        """True when running inside PyInstaller bundle."""
        return not getattr(sys, "frozen", False)

    def emit(self, event: str, data=None) -> None:
        """Push an event to the frontend. See :meth:`Bridge._emit`."""
        self._bridge._emit(event, data)

    def run(self, dev: bool | None = None, *, debug: bool | None = None) -> None:
        """Create the window and start the event loop.

        Args:
            dev:   URL source. ``True`` = Vite dev server, ``False`` = disk,
                   ``None`` = auto-detect (dev when not frozen).
            debug: Open developer tools. ``True`` / ``False`` / ``None``
                   (default: True when not frozen).
        """
        # on_start hook: runs BEFORE window creation.
        if self._on_start is not None:
            self._on_start()

        is_dev = dev if dev is not None else self.dev
        show_debug = debug if debug is not None else self.dev

        if is_dev:
            url = self._dev_url
        else:
            base = _resolve_frontend_path(self._frontend_dir)
            url = str(base / "index.html")

        window = webview.create_window(
            self._title,
            url,
            width=self._width,
            height=self._height,
            min_size=self._min_size,
            js_api=self._bridge,
        )

        self._bridge._window = window

        # on_closing hook: runs when the user closes the window.
        if self._on_closing is not None:
            window.events.closing += self._on_closing

        # Set up bridge infrastructure (drag-drop + tick timer).
        self._setup_bridge(window)

        webview.start(debug=show_debug)

    def _setup_bridge(self, window) -> None:
        """Register drag-drop handler and start the tick timer."""

        def on_loaded() -> None:
            # --- native file drag-and-drop ---
            from webview.dom import DOMEventHandler

            doc = window.dom.document
            handler = DOMEventHandler(self._bridge._on_drop, prevent_default=True)
            doc.on("drop", handler)

            # Prevent default browser behavior for drag events in JS
            # (using Python DOMEventHandler for high-freq events causes
            #  severe UI lag due to IPC overhead per event)
            window.evaluate_js(
                "document.addEventListener('dragover', function(e){e.preventDefault()});"
                "document.addEventListener('dragenter', function(e){e.preventDefault()});"
            )

            # --- periodic tick (event flush + main-thread tasks) ---
            interval_ms = self._tick_interval
            window.evaluate_js(
                f"setInterval(function(){{"
                f"  window.pywebview.api.tick();"
                f"}}, {interval_ms});"
            )

        window.events.loaded += on_loaded
