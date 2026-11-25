# Topic Tracker

Follows the topics you care about (AI updates, LLMs and computer vision, AI in healthcare, HIV/AIDS
and STI news), pulls new items from **PubMed**, **arXiv** and **Google News**, and has an LLM
write, for each one:

- a short **summary**,
- **why it matters to you**, based on the goals you write on the *My goals* page,
- **ideas to build on**: apps, models, datasets or studies you could develop from it,
- a **relevance score** from 1 to 5, which you can filter the feed by.

## Stack (same as CHIA)
| Part | Tech |
|---|---|
| Frontend | Angular 20, TypeScript, SCSS, Karma/Jasmine |
| API | Python 3.11, FastAPI, pydantic-settings, httpx, feedparser |
| Summaries | Claude Code CLI with your subscription (default), or OpenAI / Azure OpenAI |
| Storage | SQLite (single user) |
| Deploy | Docker Compose, nginx |

## Summaries with your Claude subscription
By default the summaries are written by **Claude Code running on your own computer**, signed in
with your Claude subscription, so no API key is needed. The API calls `claude -p` with a batch of
items, no tools, and a JSON schema for the answer.

- Install Claude Code and run `claude` once to sign in.
- Run the API on the same computer (`start-all.ps1`). This doesn't work in Docker, which has no
  Claude Code login.
- Summaries count toward your plan's usage limits. Set `CLAUDE_CODE_MODEL=haiku` in `.env` to use
  less, and lower `SUMMARIES_PER_RUN` to cap each refresh.
- Items are saved before they're summarized. If Claude Code fails or you hit a limit, items stay
  "waiting" and the next refresh, or **Summarize N waiting**, picks them up.

To use an API key instead, set `SUMMARIZER=openai` and `OPENAI_API_KEY`.

## Getting started
1. Copy `.env.example` to `.env`. It is set up for Claude Code summaries (see above).
2. Set up the API (first time only):
   ```powershell
   cd tracker-api
   A:\Code\chia-venv\Scripts\python.exe -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -e ".[dev]"
   ```
3. Set up the frontend (first time only): `cd tracker-frontend; npm install`
4. Run both: `.\start-all.ps1`, then open http://localhost:4200 and click **Fetch new**.

API docs are at http://localhost:8000/docs.

## Next ideas
- Daily or weekly email or push digest of the 4–5 scored items
- More sources: WHO/CDC/HIV.gov feeds, medRxiv, conference proceedings, specific journals
- Embeddings to group related items and avoid near-duplicates across sources
- Feedback buttons ("more like this") that feed back into the relevance prompt
