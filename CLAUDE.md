# Topic Tracker

A personal web app that fetches news and research on topics I follow, summarizes each item with an
LLM, and explains how it relates to my career goals (AI for health, especially HIV, AIDS, STIs and
sexual health). Built with the same stack and conventions as CHIA (`A:\Code\CHIA-enhanced`).

## Layout
- `tracker-api/`: Python 3.11, FastAPI, pydantic-settings, OpenAI SDK (Azure switch like CHIA), SQLite.
  - `app/sources/`: one adapter per source (`arxiv`, `pubmed`, `news`). Register new ones in `app/sources/__init__.py`.
  - `app/summarizer/prompts/*.md`: prompts live in markdown, outside the code (CHIA convention). HTML comments are stripped.
  - `app/pipeline.py`: fetch → dedupe by URL → summarize → store. Also the background asyncio loop.
  - `app/api/v1/`: versioned REST routes.
- `tracker-frontend/`: Angular 20 standalone components, signals, custom SCSS, Karma/Jasmine.
- SQLite file at `data/tracker.db` (git-ignored).

## Commands
- API: `cd tracker-api; .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000`
- API tests: `.\.venv\Scripts\python.exe -m pytest` (tests use the stub LLM and fake sources, no network)
- Lint/format: `ruff check app tests`, `black app tests`, `mypy app` (line length 100)
- Frontend: `cd tracker-frontend; npm start` (proxies `/api` to :8000), `npm test`, `npx ng build`
- Both at once: `.\start-all.ps1`. Docker: `docker compose up --build` (app on :8080)

## Conventions
- Test names describe behaviour (e.g. `test_fetch_stores_new_items_once.py`).
- Without `OPENAI_API_KEY`, or with `LLM_STUB=true`, summaries come from a stub. Keep tests off the network.
- Secrets go in the root `.env` only (see `.env.example`). Never commit `.env`.
- Workflow skills in `.claude/skills/` were copied from CHIA (`/tdd`, `/to-spec`, `/to-tickets`,
  `/implement`, `/diagnosing-bugs`, `/grilling` and others). Ignore CHIA-only rules inside them:
  participant Click-through lines, clinical/PI sign-off, and the no-sub-agents note.
