from app.pipeline import run_fetch, summarize_pending
from app.sources import RawItem


async def fake_source(query: str, limit: int) -> list[RawItem]:
    return [
        RawItem(
            source="news",
            url="https://example.org/a",
            title="AI predicts PrEP uptake",
            snippet="A model...",
        )
    ]


async def broken_source(query: str, limit: int) -> list[RawItem]:
    raise RuntimeError("feed down")


async def test_new_items_are_stored_once_then_summarized(client) -> None:
    sources = {"news": fake_source, "arxiv": fake_source, "pubmed": fake_source}

    first = await run_fetch(topic_id=1, sources=sources)
    second = await run_fetch(topic_id=1, sources=sources)
    summarized = await summarize_pending()

    assert (first.added, second.added, summarized.summarized) == (1, 0, 1)
    items = client.get("/api/v1/items").json()
    assert len(items) == 1
    assert items[0]["summary"].startswith("[stub]")


async def test_a_failing_source_is_reported_without_stopping_the_run(client) -> None:
    sources = {"news": broken_source, "pubmed": fake_source, "arxiv": fake_source}

    result = await run_fetch(topic_id=1, sources=sources)

    assert result.added == 1
    assert any("feed down" in e for e in result.errors)
