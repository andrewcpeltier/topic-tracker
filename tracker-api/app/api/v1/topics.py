import json
import sqlite3
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.db import connection, row_to_dict
from app.sources import SOURCES

router = APIRouter(prefix="/topics", tags=["topics"])
JSON_FIELDS = ("queries", "sources")


class TopicIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = ""
    queries: list[str] = Field(min_length=1)
    sources: list[str] = Field(min_length=1)
    enabled: bool = True

    @field_validator("sources")
    @classmethod
    def known_sources(cls, value: list[str]) -> list[str]:
        unknown = set(value) - set(SOURCES)
        if unknown:
            raise ValueError(f"Unknown sources: {sorted(unknown)}. Use {sorted(SOURCES)}.")
        return value


@router.get("/sources")
def list_sources() -> list[str]:
    return sorted(SOURCES)


@router.get("")
def list_topics() -> list[dict[str, Any]]:
    with connection() as conn:
        rows = conn.execute("""SELECT topics.*, COUNT(items.id) AS item_count FROM topics
               LEFT JOIN items ON items.topic_id = topics.id
               GROUP BY topics.id ORDER BY topics.id""").fetchall()
    return [row_to_dict(r, JSON_FIELDS) for r in rows]


def _values(body: TopicIn) -> tuple[Any, ...]:
    return (
        body.name,
        body.description,
        json.dumps(body.queries),
        json.dumps(body.sources),
        int(body.enabled),
    )


@router.post("", status_code=201)
def create_topic(body: TopicIn) -> dict[str, Any]:
    try:
        with connection() as conn:
            cur = conn.execute(
                "INSERT INTO topics (name, description, queries, sources, enabled) "
                "VALUES (?, ?, ?, ?, ?)",
                _values(body),
            )
            row = conn.execute("SELECT * FROM topics WHERE id = ?", (cur.lastrowid,)).fetchone()
    except sqlite3.IntegrityError as exc:
        raise HTTPException(409, "A topic with that name already exists") from exc
    return row_to_dict(row, JSON_FIELDS)


@router.put("/{topic_id}")
def update_topic(topic_id: int, body: TopicIn) -> dict[str, Any]:
    with connection() as conn:
        conn.execute(
            "UPDATE topics SET name=?, description=?, queries=?, sources=?, enabled=? WHERE id=?",
            (*_values(body), topic_id),
        )
        row = conn.execute("SELECT * FROM topics WHERE id = ?", (topic_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "Topic not found")
    return row_to_dict(row, JSON_FIELDS)


@router.delete("/{topic_id}", status_code=204)
def delete_topic(topic_id: int) -> None:
    with connection() as conn:
        conn.execute("DELETE FROM topics WHERE id = ?", (topic_id,))
