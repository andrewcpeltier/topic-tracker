"""Summaries from the OpenAI or Azure OpenAI API, one item per request."""

import asyncio
import json
from functools import lru_cache

import structlog
from openai import AsyncAzureOpenAI, AsyncOpenAI
from pydantic import ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.summarizer import PendingItem, Summary, item_text, system_prompt

log = structlog.get_logger()

JSON_INSTRUCTIONS = """

Return a JSON object with exactly the keys "summary", "relevance", "application_ideas" and
"relevance_score"."""


@lru_cache
def _client() -> AsyncOpenAI:
    if settings.azure_openai_endpoint:
        return AsyncAzureOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key or settings.openai_api_key,
            api_version=settings.azure_openai_api_version,
        )
    return AsyncOpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10), reraise=True)
async def _summarize_one(item: PendingItem, topic: str, goals: str) -> Summary:
    resp = await _client().chat.completions.create(
        model=settings.azure_summary_deployment or settings.summary_model,
        messages=[
            {"role": "system", "content": system_prompt(topic, goals) + JSON_INSTRUCTIONS},
            {"role": "user", "content": item_text(item)},
        ],
        response_format={"type": "json_object"},
    )
    content = resp.choices[0].message.content or "{}"
    try:
        return Summary.model_validate(json.loads(content))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ValueError(f"Model returned an unusable summary: {content[:200]}") from exc


async def summarize_with_openai(
    items: list[PendingItem], topic: str, goals: str
) -> dict[int, Summary]:
    limit = asyncio.Semaphore(4)

    async def one(item: PendingItem) -> tuple[int, Summary | None]:
        async with limit:
            try:
                return item.id, await _summarize_one(item, topic, goals)
            except Exception as exc:
                log.warning("openai_summary_failed", url=item.url, error=str(exc))
                return item.id, None

    results = await asyncio.gather(*(one(i) for i in items))
    return {item_id: s for item_id, s in results if s is not None}
