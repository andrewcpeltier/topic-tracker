from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup

USER_AGENT = "topic-tracker/0.1 (personal research feed)"


@dataclass
class RawItem:
    source: str
    url: str
    title: str
    snippet: str
    published: str | None = None


def http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=20, follow_redirects=True, headers={"User-Agent": USER_AGENT})


def strip_html(text: str, limit: int = 2000) -> str:
    plain = BeautifulSoup(text or "", "html.parser").get_text(" ", strip=True)
    return " ".join(plain.split())[:limit]
