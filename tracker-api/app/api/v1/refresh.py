import asyncio
from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.pipeline import run_fetch

router = APIRouter(tags=["refresh"])
_lock = asyncio.Lock()


@router.post("/refresh")
async def refresh(topic_id: int | None = None) -> dict[str, Any]:
    """Fetch and summarize now. Waits for the run to finish (can take a minute or two)."""
    if _lock.locked():
        raise HTTPException(409, "A refresh is already running")
    async with _lock:
        result = await run_fetch(topic_id)
    return asdict(result)


@router.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "llm": "stub" if settings.use_stub else settings.summary_model}
