"""OS-level process suspend, resume, and tree termination.

Windows: NtSuspendProcess / NtResumeProcess via ntdll, taskkill for tree kill.
Linux/macOS: SIGSTOP / SIGCONT, SIGKILL via process group.

Phase 3.5 verified that NtSuspendProcess works correctly and stderr
reader threads do NOT need to be paused (readline naturally blocks).
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys

from core.logging import get_logger

logger = get_logger()


# ---------------------------------------------------------------------------
# Process tree termination (shared helper)
# ---------------------------------------------------------------------------

def kill_process_tree(pid: int) -> None:
    """Kill a process and all its children.

    On Windows: uses ``taskkill /F /T /PID`` for reliable tree termination.
    On Unix: tries to get the process group ID via ``os.getpgid`` (since
    ``start_new_session=True`` puts the child in its own session/group),
    then sends SIGKILL to the entire group.  Falls back to direct kill.
    """
    try:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                capture_output=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        else:
            try:
                # When start_new_session=True was used, the child's
                # PGID equals its own PID, so getpgid(pid) == pid.
                pgid = os.getpgid(pid)
                os.killpg(pgid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError, OSError):
                try:
                    os.kill(pid, signal.SIGKILL)
                except (ProcessLookupError, PermissionError, OSError):
                    pass
    except Exception as exc:
        logger.debug("kill_process_tree pid={}: {}", pid, exc)

# ---------------------------------------------------------------------------
# Windows implementation (ntdll)
# ---------------------------------------------------------------------------

if sys.platform == "win32":
    import ctypes

    PROCESS_SUSPEND_RESUME = 0x0800
    NTSTATUS_SUCCESS = 0x00000000

    _kernel32 = ctypes.windll.kernel32
    _ntdll = ctypes.windll.ntdll

    # NtSuspendProcess(HANDLE ProcessHandle) -> NTSTATUS
    _ntdll.NtSuspendProcess.argtypes = [ctypes.c_void_p]
    _ntdll.NtSuspendProcess.restype = ctypes.c_ulong

    # NtResumeProcess(HANDLE ProcessHandle) -> NTSTATUS
    _ntdll.NtResumeProcess.argtypes = [ctypes.c_void_p]
    _ntdll.NtResumeProcess.restype = ctypes.c_ulong

    def _open_process(pid: int) -> int:
        """Open a process handle with SUSPEND_RESUME access.

        Returns the Windows HANDLE (int). Raises OSError on failure.
        """
        handle = _kernel32.OpenProcess(PROCESS_SUSPEND_RESUME, False, pid)
        if not handle:
            err = ctypes.get_last_error()
            raise OSError(
                f"OpenProcess failed for pid {pid} (error {err})"
            )
        return handle  # type: ignore[return-value]

    def suspend_process(pid: int) -> None:
        """Suspend a process by PID.

        Raises OSError if the process cannot be opened or suspended.
        """
        handle = _ntdll_handle = 0
        try:
            handle = _open_process(pid)
            _ntdll_handle = handle
            status = _ntdll.NtSuspendProcess(handle)
            if status != NTSTATUS_SUCCESS:
                raise OSError(
                    f"NtSuspendProcess failed for pid {pid} "
                    f"(NTSTATUS=0x{status:08X})"
                )
            logger.debug("Suspended process pid={}", pid)
        finally:
            if handle:
                _kernel32.CloseHandle(handle)

    def resume_process(pid: int) -> None:
        """Resume a suspended process by PID.

        Raises OSError if the process cannot be opened or resumed.
        """
        handle = _ntdll_handle = 0
        try:
            handle = _open_process(pid)
            _ntdll_handle = handle
            status = _ntdll.NtResumeProcess(handle)
            if status != NTSTATUS_SUCCESS:
                raise OSError(
                    f"NtResumeProcess failed for pid {pid} "
                    f"(NTSTATUS=0x{status:08X})"
                )
            logger.debug("Resumed process pid={}", pid)
        finally:
            if handle:
                _kernel32.CloseHandle(handle)

# ---------------------------------------------------------------------------
# Linux / macOS implementation (signals)
# ---------------------------------------------------------------------------

else:

    def suspend_process(pid: int) -> None:
        """Suspend a process group via SIGSTOP.

        Sends SIGSTOP to the entire process group (PGID) so that child
        processes spawned by FFmpeg (e.g. multi-pass workers) are also
        frozen.  ``start_new_session=True`` in the Popen call ensures
        the child is the leader of its own group.

        Raises OSError if the process cannot be suspended.
        """
        try:
            pgid = os.getpgid(pid)
            os.killpg(pgid, signal.SIGSTOP)
            logger.debug("Suspended process group pgid={} (SIGSTOP)", pgid)
        except (PermissionError, ProcessLookupError, OSError) as exc:
            raise OSError(
                f"Cannot suspend pid {pid}: {exc}"
            ) from exc

    def resume_process(pid: int) -> None:
        """Resume a suspended process group via SIGCONT.

        Raises OSError if the process cannot be resumed.
        """
        try:
            pgid = os.getpgid(pid)
            os.killpg(pgid, signal.SIGCONT)
            logger.debug("Resumed process group pgid={} (SIGCONT)", pgid)
        except (PermissionError, ProcessLookupError, OSError) as exc:
            raise OSError(
                f"Cannot resume pid {pid}: {exc}"
            ) from exc
