"""Source adapters. Each one turns a search query into a list of RawItem."""

from collections.abc import Awaitable, Callable

from app.sources.arxiv import fetch_arxiv
from app.sources.base import RawItem
from app.sources.news import fetch_news
from app.sources.pubmed import fetch_pubmed

Fetcher = Callable[[str, int], Awaitable[list[RawItem]]]

SOURCES: dict[str, Fetcher] = {
    "arxiv": fetch_arxiv,
    "pubmed": fetch_pubmed,
    "news": fetch_news,
}

# Seconds to wait between queries to the same source (PubMed allows 3/s without an API key;
# arXiv asks for 3 s between calls).
POLITE_DELAY: dict[str, float] = {"arxiv": 3.0, "pubmed": 0.5, "news": 0.0}

__all__ = ["POLITE_DELAY", "SOURCES", "Fetcher", "RawItem"]
