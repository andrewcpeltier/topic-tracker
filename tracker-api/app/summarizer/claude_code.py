"""Summaries from the Claude Code CLI, using the Claude subscription you are signed in with.

Requires `claude` on this computer and a one-time `claude` login. It does not work inside the
Docker image, which has no Claude Code install or login.
"""

import asyncio
import json
import shutil
import subprocess
import tempfile
from typing import Any

import structlog
from pydantic import ValidationError

from app.config import settings
from app.summarizer import PendingItem, Summary, item_text, system_prompt

log = structlog.get_logger()

BATCH_INSTRUCTIONS = """

You will receive several resources, each starting with a line `### Resource <id>`.
Return one entry in "items" per resource, with its id."""

OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "summary": {"type": "string"},
                    "relevance": {"type": "string"},
                    "application_ideas": {"type": "array", "items": {"type": "string"}},
                    "relevance_score": {"type": "integer", "minimum": 1, "maximum": 5},
                },
                "required": ["id", "summary", "relevance", "application_ideas", "relevance_score"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["items"],
    "additionalProperties": False,
}


class ClaudeCodeError(RuntimeError):
    pass


def build_command(topic: str, goals: str) -> list[str]:
    exe = shutil.which(settings.claude_cli)
    if not exe:
        raise ClaudeCodeError(
            f"'{settings.claude_cli}' was not found. Install Claude Code and sign in with `claude`."
        )
    cmd = [
        exe,
        "-p",
        "--output-format",
        "json",
        "--json-schema",
        json.dumps(OUTPUT_SCHEMA),
        "--system-prompt",
        system_prompt(topic, goals) + BATCH_INSTRUCTIONS,
        "--tools",
        "",  # summarize only: no file, shell or web access
        "--strict-mcp-config",  # don't start your MCP servers for each call
        "--no-session-persistence",  # keep these runs out of your session history
    ]
    if settings.claude_code_model:
        cmd += ["--model", settings.claude_code_model]
    return cmd


def build_input(items: list[PendingItem]) -> str:
    return "\n\n".join(f"### Resource {item.id}\n{item_text(item)}" for item in items)


def parse_output(stdout: str, wanted: set[int]) -> dict[int, Summary]:
    try:
        envelope = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise ClaudeCodeError(f"Claude Code returned non-JSON output: {stdout[:300]}") from exc
    if envelope.get("is_error") or envelope.get("subtype") != "success":
        raise ClaudeCodeError(f"Claude Code failed: {str(envelope.get('result'))[:300]}")
    out: dict[int, Summary] = {}
    for entry in (envelope.get("structured_output") or {}).get("items", []):
        try:
            item_id = int(entry.pop("id"))
            if item_id in wanted:
                out[item_id] = Summary.model_validate(entry)
        except (KeyError, TypeError, ValueError, ValidationError):
            log.warning("claude_code_bad_entry", entry=str(entry)[:200])
    return out


def _run(cmd: list[str], prompt: str) -> subprocess.CompletedProcess[str]:
    # Run outside the project so this repo's CLAUDE.md and skills aren't loaded into each call.
    return subprocess.run(
        cmd,
        input=prompt,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=settings.claude_code_timeout_seconds,
        cwd=tempfile.gettempdir(),
    )


async def summarize_with_claude_code(
    items: list[PendingItem], topic: str, goals: str
) -> dict[int, Summary]:
    cmd = build_command(topic, goals)
    # A thread, not asyncio subprocesses: those aren't supported on every Windows event loop.
    proc = await asyncio.to_thread(_run, cmd, build_input(items))
    if proc.returncode != 0 and not proc.stdout.strip():
        hint = " Run `claude` once to sign in." if "login" in proc.stderr.lower() else ""
        raise ClaudeCodeError(f"claude exited with {proc.returncode}: {proc.stderr[:300]}{hint}")
    return parse_output(proc.stdout, {item.id for item in items})
