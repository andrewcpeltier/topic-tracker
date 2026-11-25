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
| API | Python 3.11, FastAPI, pydantic-settings, OpenAI SDK (or Azure OpenAI), httpx, feedparser |
| Storage | SQLite (single user) |
| Deploy | Docker Compose, nginx |

## Getting started
1. Copy `.env.example` to `.env` and set `OPENAI_API_KEY`. Without a key the app still runs, but
   summaries are placeholder text.
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
