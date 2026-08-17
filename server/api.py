from utils.globals import (
    API_DESKTOP_STREAMING_FRAME_RATE,
    API_DESKTOP_STREAMING_PICTURE_QUALITY,
    API_PORT,
)


from server.log_stream import LogStream, web_emitter
import asyncio
import rootutils
import json

root = rootutils.setup_root(__file__, pythonpath=True)

from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    WebSocketException,
)
from fastapi import status as ws_status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.websockets import WebSocketState

from fastapi.middleware.cors import CORSMiddleware


from orchestrator import run_externally
from settings.settings import settings

import time
from fastapi.responses import StreamingResponse
from mss import mss
import cv2
import numpy as np

import ctypes
import threading

from utils.loading_text import get_loading_text

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from pathlib import Path

FRONTEND_DIR = Path(__file__).parent / "frontend"  # server/frontend

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

pc_screen = mss()

_TASK_LOCK = threading.Lock()

_RUN_STATE = {"running": False, "task": None}
_subscribers: set = set()


@app.get("/")
def serve_app():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/settings/")
def get_settings():
    return settings.data


@app.post("/settings/")
def post_settings(settings_json: dict):
    settings.load_custom_settings(data=settings_json)
    return {"success": True, "detail": "Loaded custom settings"}


@app.get("/run/status")
async def run_status():
    return dict(_RUN_STATE)


async def _broadcast(record: dict):
    """Fan a record out to every connected WebSocket."""
    text = json.dumps(record)
    for ws in list(_subscribers):
        try:
            await ws.send_text(text)
        except Exception:
            _subscribers.discard(ws)


def _kill_thread(thread_id: int):
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


@app.websocket("/run/")
async def run(
    websocket: WebSocket,
    task: str = "",
    mode_override: str | None = None,
    observe: bool = False,
):

    if not task and not observe:
        raise WebSocketException(
            code=ws_status.WS_1008_POLICY_VIOLATION,
            reason="Task is a required parameter",
        )

    if mode_override and mode_override not in ["planner-actor", "autonomy"]:
        raise WebSocketException(
            code=ws_status.WS_1008_POLICY_VIOLATION,
            reason="Mode Overrides can only be 'planner-actor' or 'autonomy'",
        )

    if task:
        if not _TASK_LOCK.acquire(blocking=False):
            raise WebSocketException(
                code=ws_status.WS_1008_POLICY_VIOLATION,
                reason="Another task is already running. Stop it first.",
            )
    elif not _RUN_STATE["running"]:
        raise WebSocketException(
            code=ws_status.WS_1008_POLICY_VIOLATION,
            reason="No task is currently running.",
        )

    await websocket.accept()
    _subscribers.add(websocket)

    try:
        if task:
            await _run_task(websocket, task, mode_override)
        else:
            # Observer: just relay the running task's records until it ends.
            while _RUN_STATE["running"]:
                await asyncio.sleep(0.5)
            if websocket.client_state != WebSocketState.DISCONNECTED:
                await websocket.close(code=1000)
    finally:
        _subscribers.discard(websocket)
        if task:
            _TASK_LOCK.release()
            _RUN_STATE["running"] = False
            _RUN_STATE["task"] = None


async def _run_task(websocket: WebSocket, task: str, mode_override: str | None):
    _RUN_STATE["running"] = True
    _RUN_STATE["task"] = task

    loop = asyncio.get_running_loop()
    stream = LogStream(loop)

    # We need the thread ID from inside the thread itself
    thread_id_holder: list[int] = []
    thread_id_ready = asyncio.Event()

    def _run_with_stream_and_id(task, mode_override, stream):
        # Capture the OS thread ID before doing any work
        thread_id_holder.append(threading.current_thread().ident)
        loop.call_soon_threadsafe(thread_id_ready.set)

        stream.attach()
        web_emitter.attach(stream)

        try:
            run_externally(task=task, mode_override=mode_override)
        except SystemExit:
            pass  # clean exit from _kill_thread
        finally:
            stream.detach()
            web_emitter.detach()

    future = loop.run_in_executor(
        None, _run_with_stream_and_id, task, mode_override, stream
    )

    # Wait until the thread has registered its ID before we start streaming
    await thread_id_ready.wait()

    # The starter socket is the Stop control: if it goes away, request a stop.
    # The task itself keeps running and its records keep streaming to everyone
    # until the worker thread actually ends (or the kill request takes effect).
    disconnected = asyncio.Event()

    async def watch_starter():
        try:
            while True:
                await websocket.receive()
        except Exception:
            _kill_thread(thread_id_holder[0])
            disconnected.set()

    watcher = asyncio.create_task(watch_starter())

    try:
        async for record in stream.stream():
            await _broadcast(record)

        try:
            await future
            await _broadcast({"type": "status", "status": "done"})
        except Exception as exc:
            await _broadcast({"type": "status", "status": "error", "message": str(exc)})
    finally:
        watcher.cancel()
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.close(code=1000)


def capture_desktop(
    streaming_quality: int = API_DESKTOP_STREAMING_PICTURE_QUALITY,
    streaming_frame_rate: int = API_DESKTOP_STREAMING_FRAME_RATE,
):
    monitor = pc_screen.monitors[1]

    while True:
        try:
            screenshot = pc_screen.grab(monitor)
            img = np.array(screenshot)

            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            success, jpeg_img = cv2.imencode(
                ".jpg",
                img,
                [cv2.IMWRITE_JPEG_QUALITY, streaming_quality],
            )
        except Exception:
            time.sleep(0.1)
            continue

        if not success:
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + jpeg_img.tobytes() + b"\r\n"
        )

        time.sleep(1 / streaming_frame_rate)


@app.get("/desktop-feed")
async def desktop_feed():
    return StreamingResponse(
        capture_desktop(), media_type="multipart/x-mixed-replace; boundary=frame"
    )


@app.get("/bg-desktop-feed")
async def bg_desktop_feed():
    return StreamingResponse(
        capture_desktop(
            streaming_quality=5,
            streaming_frame_rate=75,
        ),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.get("/loading-text")
async def return_loading_text():
    return get_loading_text()


def main():
    import uvicorn

    if settings.web_ui.expose_web_ui_to_all_devices_on_the_network:
        host = "0.0.0.0"
    else:
        host = "127.0.0.1"

    uvicorn.run(
        "api:app",
        host=host,
        port=API_PORT,
        reload=True,
        reload_excludes=[".kodo_venv/*", ".lmcontrol_venv/*"],
    )


if __name__ == "__main__":
    main()
