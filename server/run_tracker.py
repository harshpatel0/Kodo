"""Single home for all teardown logic.

server/api.py's websocket handler (the stop button) and trayapp.py's exit handlers both
need to tear things down -- this is the one place that logic lives so neither duplicates
it, and so the two tiers (agent-only vs. everything) stay obviously distinct:

    teardown_agent()  Kills the orchestrator's thread and any subprocess a skill/python
                       action spawned. Leaves the REST API and tray app running -- this
                       is what the stop button calls.
    teardown_all()     teardown_agent() plus disconnecting MCP servers and hard-exiting
                       the process -- this is a full app exit.
"""

import ctypes
import os
import threading

_active_thread_id: int | None = None


def register_thread(thread_id: int) -> None:
    global _active_thread_id
    _active_thread_id = thread_id


def clear_thread() -> None:
    global _active_thread_id
    _active_thread_id = None


def _kill_thread(thread_id: int) -> None:
    """Raise SystemExit in a running thread by its OS thread ID.
    Uses a safer two-call pattern to avoid corrupting thread state.
    """
    if thread_id == threading.current_thread().ident:
        return

    ctypes.pythonapi.PyThreadState_SetAsyncExc(
        ctypes.c_ulong(thread_id),
        ctypes.py_object(SystemExit),
    )
    ctypes.pythonapi.PyThreadState_SetAsyncExc(
        ctypes.c_ulong(thread_id),
        ctypes.c_long(0),
    )


def teardown_agent() -> None:
    """Best-effort teardown of whatever the orchestrator is currently doing: kill any
    subprocess a skill/python action spawned (a blocking subprocess.communicate() won't
    notice the thread-kill below until it returns on its own), then interrupt the
    orchestrator's own thread. Safe to call even when nothing is running.
    """
    from interactions.python.run_python_code import PythonRunner

    PythonRunner.kill_all_running()

    if _active_thread_id is not None:
        _kill_thread(_active_thread_id)


def teardown_all() -> None:
    """Full app exit: teardown_agent(), then disconnect MCP servers so their subprocesses
    don't end up orphaned, then hard-exit the process.

    A hard os._exit() is necessary, not just cleanup: uvicorn.run() blocks the non-daemon
    thread pywebview spawns to run it, so the interpreter would otherwise never actually
    quit once the window is gone -- nothing tells that thread to stop.
    """
    try:
        teardown_agent()
    except Exception:
        pass

    try:
        from interactions.mcps.mcp_registry import mcp_registry

        mcp_registry.disconnect_all()
    except Exception:
        pass

    os._exit(0)
