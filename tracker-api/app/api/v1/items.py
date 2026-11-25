from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.db import connection, row_to_dict

router = APIRouter(prefix="/items", tags=["items"])


class ItemUpdate(BaseModel):
    saved: bool | None = None
    is_read: bool | None = None


@router.get("")
def list_items(
    topic_id: int | None = None,
    min_score: int = Query(1, ge=1, le=5),
    saved: bool | None = None,
    unread: bool | None = None,
    q: str | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
) -> list[dict[str, Any]]:
    sql = """SELECT items.*, topics.name AS topic_name FROM items
             JOIN topics ON topics.id = items.topic_id
             WHERE COALESCE(relevance_score, 1) >= ?"""
    params: list[Any] = [min_score]
    if topic_id is not None:
        sql += " AND topic_id = ?"
        params.append(topic_id)
    if saved is not None:
        sql += " AND saved = ?"
        params.append(int(saved))
    if unread:
        sql += " AND is_read = 0"
    if q:
        sql += " AND (title LIKE ? OR summary LIKE ?)"
        params += [f"%{q}%", f"%{q}%"]
    sql += " ORDER BY items.created_at DESC, relevance_score DESC LIMIT ? OFFSET ?"
    params += [limit, offset]
    with connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [row_to_dict(r, ("application_ideas",)) for r in rows]


@router.patch("/{item_id}")
def update_item(item_id: int, body: ItemUpdate) -> dict[str, Any]:
    changes = body.model_dump(exclude_none=True)
    with connection() as conn:
        for field, value in changes.items():
            conn.execute(f"UPDATE items SET {field} = ? WHERE id = ?", (int(value), item_id))
        row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "Item not found")
    return row_to_dict(row, ("application_ideas",))
