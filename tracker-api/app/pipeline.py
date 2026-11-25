"""Fetch new resources for each topic, summarize them, and store them."""

import asyncio
import json
from dataclasses import dataclass, field

import structlog

from app.config import settings
from app.db import connection
from app.sources import POLITE_DELAY, SOURCES, Fetcher, RawItem
from app.summarizer import summarize

log = structlog.get_logger()


@dataclass
class RunResult:
    fetched: int = 0
    added: int = 0
    errors: list[str] = field(default_factory=list)


def _known_urls(urls: list[str]) -> set[str]:
    if not urls:
        return set()
    with connection() as conn:
        marks = ",".join("?" * len(urls))
        rows = conn.execute(f"SELECT url FROM items WHERE url IN ({marks})", urls).fetchall()
    return {r["url"] for r in rows}


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
    topic_id: int | None = None, sources: dict[str, Fetcher] | None = None
) -> RunResult:
    sources = sources or SOURCES
    result = RunResult()
    with connection() as conn:
        goals = conn.execute("SELECT goals FROM profile WHERE id = 1").fetchone()["goals"]
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

        known = _known_urls(list(raw))
        new_items = [i for url, i in raw.items() if url not in known]
        for item in new_items:
            try:
                s = await summarize(item, topic["name"], goals)
            except Exception as exc:  # keep going; one bad item shouldn't stop the run
                result.errors.append(f"summarize {item.url}: {exc}")
                continue
            with connection() as conn:
                conn.execute(
                    """INSERT OR IGNORE INTO items (topic_id, source, url, title, published,
                       snippet, summary, relevance, application_ideas, relevance_score)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        topic["id"], item.source, item.url, item.title, item.published,
                        item.snippet, s.summary, s.relevance, json.dumps(s.application_ideas),
                        s.relevance_score,
                    ),
                )
            result.added += 1
    log.info("fetch_done", fetched=result.fetched, added=result.added, errors=len(result.errors))
    return result


async def fetch_loop() -> None:
    """Background refresh, like CHIA's heartbeat service: a simple asyncio loop."""
    while True:
        try:
            await run_fetch()
        except Exception:
            log.exception("fetch_loop_failed")
        await asyncio.sleep(settings.fetch_interval_minutes * 60)
