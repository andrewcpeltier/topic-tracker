"""The Claude Code backend, with the `claude` process replaced by a fake (no network, no login)."""

import json
import subprocess
import sys

import pytest

from app.config import settings
from app.pipeline import pending_count, run_fetch, summarize_pending
from app.sources import RawItem
from app.summarizer import claude_code


async def two_items(query: str, limit: int) -> list[RawItem]:
    return [
        RawItem(
            source="pubmed",
            url="https://example.org/1",
            title="LLM chatbot for PrEP",
            snippet="...",
        ),
        RawItem(
            source="pubmed",
            url="https://example.org/2",
            title="Knee surgery outcomes",
            snippet="...",
        ),
    ]


@pytest.fixture
def use_claude_code(monkeypatch) -> list[list[str]]:
    monkeypatch.setattr(settings, "llm_stub", False)
    monkeypatch.setattr(settings, "summarizer", "claude_code")
    monkeypatch.setattr(settings, "claude_cli", sys.executable)  # any real executable
    return []


def fake_claude(calls: list[list[str]], entries_for):  # type: ignore[no-untyped-def]
    def run(cmd: list[str], prompt: str) -> subprocess.CompletedProcess[str]:
        calls.append(cmd)
        ids = [
            int(line.split()[-1]) for line in prompt.splitlines() if line.startswith("### Resource")
        ]
        envelope = {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "structured_output": {"items": entries_for(ids)},
        }
        return subprocess.CompletedProcess(cmd, 0, json.dumps(envelope), "")

    return run


async def test_claude_code_summaries_are_stored_with_their_scores(
    client, use_claude_code, monkeypatch
) -> None:
    def entries(ids: list[int]) -> list[dict[str, object]]:
        return [
            {
                "id": i,
                "summary": f"S{i}",
                "relevance": "R",
                "application_ideas": ["idea"],
                "relevance_score": 5 if i == min(ids) else 1,
            }
            for i in ids
        ]

    monkeypatch.setattr(claude_code, "_run", fake_claude(use_claude_code, entries))
    await run_fetch(topic_id=1, sources={"pubmed": two_items})

    result = await summarize_pending()

    assert result.summarized == 2 and pending_count() == 0
    assert len(use_claude_code) == 1, "both items go to Claude Code in one call"
    cmd = use_claude_code[0]
    assert "--bare" not in cmd, "--bare would skip your subscription login"
    assert cmd[cmd.index("--tools") + 1] == ""
    scores = sorted(i["relevance_score"] for i in client.get("/api/v1/items?min_score=1").json())
    assert scores == [1, 5]


async def test_items_stay_pending_when_claude_code_fails(
    client, use_claude_code, monkeypatch
) -> None:
    def failing(cmd: list[str], prompt: str) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(cmd, 1, "", "Please run /login")

    monkeypatch.setattr(claude_code, "_run", failing)
    await run_fetch(topic_id=1, sources={"pubmed": two_items})

    result = await summarize_pending()

    assert result.summarized == 0
    assert pending_count() == 2
    assert any("sign in" in e for e in result.errors)


def test_entries_for_unknown_ids_are_ignored() -> None:
    envelope = {
        "subtype": "success",
        "is_error": False,
        "structured_output": {
            "items": [
                {
                    "id": 7,
                    "summary": "s",
                    "relevance": "r",
                    "application_ideas": [],
                    "relevance_score": 3,
                },
                {
                    "id": 99,
                    "summary": "s",
                    "relevance": "r",
                    "application_ideas": [],
                    "relevance_score": 3,
                },
            ]
        },
    }
    assert set(claude_code.parse_output(json.dumps(envelope), {7})) == {7}
