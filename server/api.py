BIND_TO_ALL = True

from log_stream import LogStream
import asyncio
import rootutils
import json

root = rootutils.setup_root(__file__, pythonpath=True)

from fastapi import (
    FastAPI,
    HTTPException,
    status,
    Header,
    WebSocket,
    WebSocketDisconnect,
    WebSocketException,
)
from fastapi import status as ws_status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse


from orchestrator import run_externally
from settings.settings import settings

from typing import Annotated

app = FastAPI()

from pathlib import Path

from pathlib import Path

FRONTEND_DIR = Path(__file__).parent / "frontend"  # server/frontend

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
def serve_app():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/settings/")
def get_settings():
    return settings.data


@app.post("/settings/")
def post_settings(settings_json: Annotated[str, Header(convert_underscores=False)]):
    try:
        parse_settings = json.loads(settings_json)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Settings are invalid"
        )

    settings.load_custom_settings(data=parse_settings)

    return {"success": True, "detail": "Loaded custom settings"}


@app.websocket("/run/")
async def run(websocket: WebSocket, task: str, mode_override: str | None = None):

    if not task:
        raise WebSocketException(
            code=ws_status.WS_1008_POLICY_VIOLATION,
            reason="Task is a required parameter",
        )

    if mode_override and mode_override not in ["planner", "autonomy"]:
        raise WebSocketException(
            code=ws_status.WS_1008_POLICY_VIOLATION,
            reason="Mode Overrides can only be 'planner' or 'autonomy'",
        )

    await websocket.accept()

    loop = asyncio.get_running_loop()
    stream = LogStream(loop)

    future = loop.run_in_executor(
        None,
        _run_with_stream,
        task,
        mode_override,
        stream,
    )

    try:
        async for record in stream.stream():
            try:
                await websocket.send_text(json.dumps(record))
            except WebSocketDisconnect:
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
        pass
    finally:
        await websocket.close(code=1000)


def _run_with_stream(task, mode_override, stream):
    stream.attach()
    try:
        run_externally(task=task, mode_override=mode_override)
    finally:
        stream.detach()


if __name__ == "__main__":
    import uvicorn

    if BIND_TO_ALL:
        host = "0.0.0.0"
    else:
        host = "127.0.0.1"

    uvicorn.run("api:app", host=host, port=8000, reload=True)
