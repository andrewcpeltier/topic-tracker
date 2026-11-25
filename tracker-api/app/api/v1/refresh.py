from typing import Any

from fastapi import APIRouter, HTTPException

from app.pipeline import start_refresh, status

router = APIRouter(tags=["refresh"])


@router.post("/refresh", status_code=202)
async def refresh(topic_id: int | None = None, fetch: bool = True) -> dict[str, Any]:
    """Start fetching (unless fetch=false) and summarizing in the background.

    Async on purpose: the job must be started on the server's event loop. Poll GET /status.
    """
    if not start_refresh(topic_id, fetch):
        raise HTTPException(409, "A refresh is already running")
    return status()


@router.get("/status")
def get_status() -> dict[str, Any]:
    return status()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
