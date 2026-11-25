"""arXiv API: newest preprints matching the query."""

import feedparser

from app.sources.base import RawItem, http_client, strip_html

ARXIV_URL = "https://export.arxiv.org/api/query"


async def fetch_arxiv(query: str, limit: int) -> list[RawItem]:
    params = {
        # Every word must appear somewhere; exact phrases are too strict for short queries.
        "search_query": " AND ".join(f"all:{word}" for word in query.split()),
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": str(limit),
    }
    async with http_client() as client:
        resp = await client.get(ARXIV_URL, params=params)
        resp.raise_for_status()
    feed = feedparser.parse(resp.text)
    return [
        RawItem(
            source="arxiv",
            url=entry.get("link", ""),
            title=" ".join(entry.get("title", "").split()),
            snippet=strip_html(entry.get("summary", "")),
            published=entry.get("published"),
        )
        for entry in feed.entries
        if entry.get("link")
    ]
