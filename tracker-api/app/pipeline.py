"""Fetch new resources for each topic, store them, then summarize whatever is still pending.

Storing first means a failed or interrupted summary is never lost: the item stays pending
(summary IS NULL) and is picked up by the next run.
"""

import asyncio
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

import structlog

from app.config import settings
from app.db import connection
from app.sources import POLITE_DELAY, SOURCES, Fetcher, RawItem
from app.summarizer import PendingItem, active_backend, summarize_batch

log = structlog.get_logger()


@dataclass
class RunResult:
    fetched: int = 0
    added: int = 0
    summarized: int = 0
    errors: list[str] = field(default_factory=list)


async def _query_source(
    name: str, fetch: Fetcher, queries: list[str], topic: str
) -> tuple[list[RawItem], list[str]]:
    items: list[RawItem] = []
    errors: list[str] = []
    for i, query in enumerate(queries):
        if i:
            await asyncio.sleep(POLITE_DELAY.get(name, 0.0))
        try:
            items += await fetch(query, settings.items_per_query)
        except Exception as exc:
            msg = f"{topic} / {name} / {query}: {exc}"
            log.warning("source_failed", error=msg)
            errors.append(msg)
    return items, errors


async def run_fetch(
    topic_id: int | None = None,
    sources: dict[str, Fetcher] | None = None,
    result: RunResult | None = None,
) -> RunResult:
    """Fetch every enabled topic and store new items, unsummarized."""
    sources = sources or SOURCES
    result = result or RunResult()
    with connection() as conn:
        sql = "SELECT * FROM topics WHERE enabled = 1"
        params: tuple[int, ...] = ()
        if topic_id is not None:
            sql += " AND id = ?"
            params = (topic_id,)
        topics = conn.execute(sql, params).fetchall()

    for topic in topics:
        queries = json.loads(topic["queries"])
        names = [s for s in json.loads(topic["sources"]) if s in sources]
        # Sources run in parallel; queries to one source run in order, with a polite delay.
        per_source = await asyncio.gather(
            *(_query_source(name, sources[name], queries, topic["name"]) for name in names)
        )
        raw: dict[str, RawItem] = {}
        for batch, errors in per_source:
            result.errors.extend(errors)
            for item in batch:
                raw.setdefault(item.url, item)
        result.fetched += len(raw)

        with connection() as conn:
            for item in raw.values():
                cur = conn.execute(
                    """INSERT OR IGNORE INTO items
                       (topic_id, source, url, title, published, snippet)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (topic["id"], item.source, item.url, item.title, item.published, item.snippet),
                )
                result.added += cur.rowcount
    log.info("fetch_done", fetched=result.fetched, added=result.added)
    return result


def pending_count() -> int:
    with connection() as conn:
        return int(conn.execute("SELECT COUNT(*) FROM items WHERE summary IS NULL").fetchone()[0])


async def summarize_pending(
    topic_id: int | None = None, limit: int | None = None, result: RunResult | None = None
) -> RunResult:
    """Summarize stored items that have no summary yet, newest first, batched per topic."""
    result = result or RunResult()
    limit = limit or settings.summaries_per_run
    with connection() as conn:
        goals = conn.execute("SELECT goals FROM profile WHERE id = 1").fetchone()["goals"]
        sql = """SELECT items.*, topics.name AS topic_name FROM items
                 JOIN topics ON topics.id = items.topic_id WHERE summary IS NULL"""
        params: list[Any] = []
        if topic_id is not None:
            sql += " AND topic_id = ?"
            params.append(topic_id)
        sql += " ORDER BY items.id DESC LIMIT ?"
        rows = conn.execute(sql, [*params, limit]).fetchall()

    by_topic: dict[str, list[PendingItem]] = {}
    for r in rows:
        by_topic.setdefault(r["topic_name"], []).append(
            PendingItem(r["id"], r["source"], r["title"], r["url"], r["published"], r["snippet"])
        )

    size = settings.summary_batch_size
    for topic, items in by_topic.items():
        for start in range(0, len(items), size):
            batch = items[start : start + size]
            try:
                summaries = await summarize_batch(batch, topic, goals)
            except Exception as exc:  # leave the batch pending; the next run retries it
                msg = f"summarize {topic} ({len(batch)} items): {exc}"
                log.warning("summarize_failed", error=msg)
                result.errors.append(msg)
                continue
            with connection() as conn:
                for item_id, s in summaries.items():
                    conn.execute(
                        """UPDATE items SET summary = ?, relevance = ?, application_ideas = ?,
                           relevance_score = ? WHERE id = ?""",
                        (
                            s.summary,
                            s.relevance,
                            json.dumps(s.application_ideas),
                            s.relevance_score,
                            item_id,
                        ),
                    )
            result.summarized += len(summaries)
    log.info("summarize_done", summarized=result.summarized, backend=active_backend())
    return result


# ---- background refresh job ---------------------------------------------------------------


@dataclass
class JobState:
    running: bool = False
    phase: str = "idle"  # idle | fetching | summarizing
    started_at: str | None = None
    finished_at: str | None = None
    last_result: RunResult | None = None


job = JobState()
_task: asyncio.Task[None] | None = None


async def _refresh(topic_id: int | None, fetch: bool) -> None:
    result = RunResult()
    try:
        if fetch:
            job.phase = "fetching"
            await run_fetch(topic_id, result=result)
        job.phase = "summarizing"
        job.last_result = result  # visible while summarizing
        await summarize_pending(topic_id, result=result)
    except Exception as exc:
        log.exception("refresh_failed")
        result.errors.append(f"refresh failed: {exc}")
    finally:
        job.running, job.phase = False, "idle"
        job.finished_at = datetime.now(UTC).isoformat()
        job.last_result = result


def start_refresh(topic_id: int | None = None, fetch: bool = True) -> bool:
    """Start a background refresh. Returns False if one is already running."""
    global _task
    if job.running:
        return False
    _task = asyncio.create_task(_refresh(topic_id, fetch))  # raises if there's no event loop
    job.running, job.phase = True, "starting"
    job.started_at, job.finished_at = datetime.now(UTC).isoformat(), None
    return True


def status() -> dict[str, Any]:
    return {
        "running": job.running,
        "phase": job.phase,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
        "last_result": asdict(job.last_result) if job.last_result else None,
        "pending": pending_count(),
        "summarizer": active_backend(),
    }


async def fetch_loop() -> None:
    """Scheduled refresh, like CHIA's heartbeat service: a simple asyncio loop."""
    while True:
        if start_refresh() and _task is not None:
            await asyncio.shield(_task)
        await asyncio.sleep(settings.fetch_interval_minutes * 60)
