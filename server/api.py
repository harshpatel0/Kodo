import rootutils
import json

root = rootutils.setup_root(__file__, pythonpath=True)

from fastapi import FastAPI, HTTPException, status, Header
from orchestrator import run_externally
from settings.settings import settings

from typing import Annotated

app = FastAPI()


@app.get("/")
def health():
    return {"status": "API Running"}


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


@app.get("/run/")
def run(task: str, mode_override: str | None = None):
    if not task:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task is a required parameter",
        )

    if mode_override:
        if mode_override not in ["planner", "autonomy"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mode Overrides can only be 'planner' or 'autonomy'",
            )

    run_externally(task=task, mode_override=mode_override)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
