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
async def run(websocket: WebSocket, task: str, mode_override: str | None = None):

    if not task:
        raise WebSocketException(
            code=ws_status.WS_1008_POLICY_VIOLATION,
            reason="Task is a required parameter",
        )

    if mode_override and mode_override not in ["planner-actor", "autonomy"]:
        raise WebSocketException(
            code=ws_status.WS_1008_POLICY_VIOLATION,
            reason="Mode Overrides can only be 'planner-actor' or 'autonomy'",
        )

    await websocket.accept()

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

    try:
        async for record in stream.stream():
            try:
                await websocket.send_text(json.dumps(record))
            except WebSocketDisconnect:
                if thread_id_holder:
                    _kill_thread(thread_id_holder[0])
                future.cancel()
                return

        try:
            await future
            await websocket.send_text(json.dumps({"type": "status", "status": "done"}))
        except Exception as exc:
            await websocket.send_text(
                json.dumps({"type": "status", "status": "error", "message": str(exc)})
            )

    except WebSocketDisconnect:
        if thread_id_holder:
            _kill_thread(thread_id_holder[0])
    finally:
        await websocket.close(code=1000)


def capture_desktop():
    monitor = pc_screen.monitors[1]

    while True:
        screenshot = pc_screen.grab(monitor)
        img = np.array(screenshot)

        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        success, jpeg_img = cv2.imencode(
            ".jpg",
            img,
            [cv2.IMWRITE_JPEG_QUALITY, API_DESKTOP_STREAMING_PICTURE_QUALITY],
        )

        if not success:
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + jpeg_img.tobytes() + b"\r\n"
        )

        time.sleep(1 / API_DESKTOP_STREAMING_FRAME_RATE)


@app.get("/desktop-feed")
async def desktop_feed():
    return StreamingResponse(
        capture_desktop(), media_type="multipart/x-mixed-replace; boundary=frame"
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
