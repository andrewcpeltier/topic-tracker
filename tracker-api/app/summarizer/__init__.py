"""Summarize a resource and explain its relevance to the user's goals."""

import json
import re
from functools import lru_cache
from pathlib import Path

from openai import AsyncAzureOpenAI, AsyncOpenAI
from pydantic import BaseModel, Field, ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.sources.base import RawItem

PROMPTS_DIR = Path(__file__).parent / "prompts"


class Summary(BaseModel):
    summary: str
    relevance: str
    application_ideas: list[str] = Field(default_factory=list)
    relevance_score: int = Field(ge=1, le=5)


@lru_cache
def load_prompt(name: str) -> str:
    text = (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")
    return re.sub(r"<!--.*?-->\s*", "", text, flags=re.DOTALL).strip()


@lru_cache
def _client() -> AsyncOpenAI:
    if settings.azure_openai_endpoint:
        return AsyncAzureOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key or settings.openai_api_key,
            api_version=settings.azure_openai_api_version,
        )
    return AsyncOpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)


def stub_summary(item: RawItem, topic: str) -> Summary:
    """Deterministic stand-in used in tests and when no API key is configured."""
    return Summary(
        summary=f"[stub] {item.title}",
        relevance=f"[stub] Matched the topic '{topic}'. Add OPENAI_API_KEY for real summaries.",
        application_ideas=[],
        relevance_score=3,
    )


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10), reraise=True)
async def summarize(item: RawItem, topic: str, goals: str) -> Summary:
    if settings.use_stub:
        return stub_summary(item, topic)

    system = load_prompt("summarize").format(goals=goals, topic=topic)
    user = (
        f"Source: {item.source}\nTitle: {item.title}\nPublished: {item.published or 'unknown'}\n"
        f"URL: {item.url}\n\nText:\n{item.snippet or '(headline only)'}"
    )
    model = settings.azure_summary_deployment or settings.summary_model
    resp = await _client().chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        response_format={"type": "json_object"},
    )
    content = resp.choices[0].message.content or "{}"
    try:
        return Summary.model_validate(json.loads(content))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ValueError(f"Model returned an unusable summary: {content[:200]}") from exc
