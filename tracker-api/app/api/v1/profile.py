from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.db import connection

router = APIRouter(prefix="/profile", tags=["profile"])


class Profile(BaseModel):
    goals: str = Field(min_length=1, max_length=5000)


@router.get("")
def get_profile() -> Profile:
    with connection() as conn:
        row = conn.execute("SELECT goals FROM profile WHERE id = 1").fetchone()
    return Profile(goals=row["goals"])


@router.put("")
def update_profile(body: Profile) -> Profile:
    with connection() as conn:
        conn.execute("UPDATE profile SET goals = ? WHERE id = 1", (body.goals,))
    return body
