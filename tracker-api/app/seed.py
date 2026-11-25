"""First-run defaults: your goals and starter topics. Edit them later in the app."""

import json

from app.db import connection

DEFAULT_GOALS = """\
I want general updates on AI and what it is being used for, especially LLMs and computer vision.
My career is focused on using AI applications for health care, so news that combines AI and
health is especially valuable. My research targets sexual health, HIV, AIDS and other STIs.
I plan to use this information to develop applications and/or AI algorithms that help solve
these problems, so summaries should point toward how a finding could be built on or applied."""

DEFAULT_TOPICS: list[dict[str, object]] = [
    {
        "name": "AI for HIV & sexual health",
        "description": "AI, LLMs, chatbots or computer vision applied to HIV, PrEP and STIs.",
        "queries": [
            "artificial intelligence HIV",
            "large language model sexual health",
            "machine learning PrEP",
            "AI sexually transmitted infections",
        ],
        "sources": ["pubmed", "news", "arxiv"],
    },
    {
        "name": "HIV, AIDS & STI news",
        "description": "Prevention, treatment, policy and epidemiology updates.",
        "queries": ["HIV prevention", "PrEP", "syphilis gonorrhea chlamydia", "HIV treatment"],
        "sources": ["news", "pubmed"],
    },
    {
        "name": "LLMs in healthcare",
        "description": "Clinical LLMs, health chatbots, evaluation and safety.",
        "queries": [
            "large language models healthcare",
            "clinical LLM evaluation",
            "health chatbot",
        ],
        "sources": ["arxiv", "pubmed", "news"],
    },
    {
        "name": "Computer vision in medicine",
        "description": "Medical imaging, diagnostics and vision models in health.",
        "queries": ["computer vision medical diagnosis", "medical image deep learning"],
        "sources": ["arxiv", "pubmed"],
    },
    {
        "name": "General AI updates",
        "description": "Major model releases, research breakthroughs and AI industry news.",
        "queries": ["large language model release", "AI research breakthrough"],
        "sources": ["news", "arxiv"],
    },
]


def seed_if_empty() -> None:
    with connection() as conn:
        if conn.execute("SELECT 1 FROM profile").fetchone() is None:
            conn.execute("INSERT INTO profile (id, goals) VALUES (1, ?)", (DEFAULT_GOALS,))
        if conn.execute("SELECT 1 FROM topics").fetchone() is None:
            for topic in DEFAULT_TOPICS:
                conn.execute(
                    "INSERT INTO topics (name, description, queries, sources) VALUES (?, ?, ?, ?)",
                    (
                        topic["name"],
                        topic["description"],
                        json.dumps(topic["queries"]),
                        json.dumps(topic["sources"]),
                    ),
                )
