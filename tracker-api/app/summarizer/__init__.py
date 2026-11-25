"""Summarize resources and explain their relevance to the user's goals.

Three backends, chosen by the SUMMARIZER setting (see app.config):
- claude_code: runs the Claude Code CLI on this computer (`claude -p`), signed in with your
  Claude subscription. Several items go in one call.
- openai: OpenAI or Azure OpenAI API key, one item per call.
- stub: placeholder text, used by tests and when nothing else is available.
"""

import re
import shutil
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field

from app.config import settings

PROMPTS_DIR = Path(__file__).parent / "prompts"


@dataclass
class PendingItem:
    id: int
    source: str
    title: str
    url: str
    published: str | None
    snippet: str


class Summary(BaseModel):
    summary: str
    relevance: str
    application_ideas: list[str] = Field(default_factory=list)
    relevance_score: int = Field(ge=1, le=5)


@lru_cache
def load_prompt(name: str) -> str:
    text = (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")
    return re.sub(r"<!--.*?-->\s*", "", text, flags=re.DOTALL).strip()


def system_prompt(topic: str, goals: str) -> str:
    return load_prompt("summarize").format(goals=goals, topic=topic)


def item_text(item: PendingItem) -> str:
    return (
        f"Source: {item.source}\nTitle: {item.title}\nPublished: {item.published or 'unknown'}\n"
        f"URL: {item.url}\n\nText:\n{item.snippet or '(headline only)'}"
    )


def active_backend() -> str:
    """Which backend will run. 'auto' prefers OpenAI if a key is set, then Claude Code."""
    if settings.llm_stub:
        return "stub"
    if settings.summarizer != "auto":
        return settings.summarizer
    if settings.openai_api_key or settings.azure_openai_endpoint:
        return "openai"
    if shutil.which(settings.claude_cli):
        return "claude_code"
    return "stub"


def stub_summary(item: PendingItem, topic: str) -> Summary:
    return Summary(
        summary=f"[stub] {item.title}",
        relevance=f"[stub] Matched the topic '{topic}'. Set SUMMARIZER to get real summaries.",
        application_ideas=[],
        relevance_score=3,
    )


async def summarize_batch(items: list[PendingItem], topic: str, goals: str) -> dict[int, Summary]:
    """Summaries keyed by item id. Items the backend could not handle are simply missing."""
    backend = active_backend()
    if backend == "claude_code":
        from app.summarizer.claude_code import summarize_with_claude_code

        return await summarize_with_claude_code(items, topic, goals)
    if backend == "openai":
        from app.summarizer.openai_api import summarize_with_openai

        return await summarize_with_openai(items, topic, goals)
    return {item.id: stub_summary(item, topic) for item in items}
