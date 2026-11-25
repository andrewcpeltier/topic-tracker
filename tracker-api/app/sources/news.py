"""News via the Google News RSS search feed (headline + short blurb per story)."""

import feedparser

from app.sources.base import RawItem, http_client, strip_html

NEWS_RSS = "https://news.google.com/rss/search"


async def fetch_news(query: str, limit: int) -> list[RawItem]:
    params = {"q": f"{query} when:30d", "hl": "en-US", "gl": "US", "ceid": "US:en"}
    async with http_client() as client:
        resp = await client.get(NEWS_RSS, params=params)
        resp.raise_for_status()
    feed = feedparser.parse(resp.text)
    return [
        RawItem(
            source="news",
            url=entry.get("link", ""),
            title=entry.get("title", ""),
            snippet=strip_html(entry.get("summary", "")),
            published=entry.get("published"),
        )
        for entry in feed.entries[:limit]
        if entry.get("link")
    ]
