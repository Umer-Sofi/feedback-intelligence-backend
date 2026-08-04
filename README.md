# Feedback Intelligence Backend

An AI-powered backend that automatically **categorizes** customer feedback
(reviews, support tickets, survey responses), **scores sentiment**, groups
feedback into recurring **themes**, generates a weekly narrative **summary**,
and exposes a **RAG chatbot** for natural-language questions over the dataset.

Backend-only (FastAPI). No frontend in this repository.

---

## Features

- **Classification** — every feedback item gets a category (9 types),
  sentiment (positive/neutral/negative), a continuous sentiment score
  (−1.0 → 1.0), and a confidence value. Low-confidence items are flagged.
- **Theme grouping without clustering** — themes emerge via vector similarity
  (embeddings + nearest-neighbor search), not k-means/HDBSCAN. New themes are
  named by an LLM only when nothing similar exists.
- **Analytics** — category counts, sentiment distribution, and week-over-week
  theme trends.
- **Weekly summary** — a narrative grounded in retrieved feedback (RAG).
- **RAG chatbot** — reformulates follow-ups, retrieves relevant feedback, and
  answers with cited sources.

---

## Tech stack

| Concern | Choice |
|---|---|
| Web framework | FastAPI + Uvicorn |
| ORM | SQLAlchemy 2.0 |
| Config / validation | Pydantic v2 + pydantic-settings |
| Database **and** vector store | **PostgreSQL + pgvector** (one server) |
| LLM + embeddings | OpenAI API |
| Retry / backoff | tenacity |
| Data / eval | pandas |

---

## Architecture / data flow

```
data/feedback.csv
   │  scripts/load_dataset.py   (insert rows as UNPROCESSED + embeddings)
   ▼
PostgreSQL + pgvector   (structured columns AND embedding vectors)
   │  services/pipeline.py   (run manually / cron — NOT a scheduler)
   ├── classifier.py        → category + sentiment (1 LLM call/item)
   └── theme_aggregator.py  → nearest-theme vector search, else name new theme
   ▼
services/analytics.py + summarizer.py   (stats + RAG weekly narrative)
   ▼
FastAPI routers (src/main.py)
   ├── GET  /feedback            list/filter processed records (GET only)
   ├── GET  /analytics/overview  dashboard stats
   ├── GET  /analytics/summary   weekly narrative summary (RAG)
   ├── POST /chat                ask the RAG chatbot
   └── GET  /chat/{session_id}   conversation history
```

All OpenAI calls route through `services/openai_client.py`, which uses
`utils/retry.py` (tenacity) for backoff and JSON-validation retries.

---

## Setup

### Prerequisites
- Python 3.9+
- Docker Desktop (for PostgreSQL + pgvector)
- An OpenAI API key

### 1. Virtual environment + dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment variables
Create a `.env` file in `backend/`:
```
OPENAI_API_KEY=sk-your-real-key-here
OPENAI_CLASSIFIER_MODEL=gpt-4o-mini
OPENAI_SUMMARY_MODEL=gpt-4o-mini
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
DATABASE_URL=postgresql+psycopg://feedback:feedback@localhost:5432/feedback
EMBEDDING_DIM=1536
THEME_SIMILARITY_THRESHOLD=0.58
LOW_CONFIDENCE_THRESHOLD=0.6
RETRY_MAX_ATTEMPTS=4
LOG_LEVEL=INFO
```

### 3. Start PostgreSQL + pgvector
```bash
docker compose up -d          # starts the feedback_pg container
```

### 4. Create the schema
```bash
python -m src.database.init_db
```

---

## Running

### Load the dataset
```bash
python -m scripts.load_dataset            # inserts rows + embeddings
# or, without an API key (rows only, no embeddings):
python -m scripts.load_dataset --skip-embeddings
```

### Run the processing pipeline
Classifies + themes all unprocessed feedback. Triggered manually or by cron —
never on API startup.
```bash
python -m src.services.pipeline
```

### Start the API server
```bash
python -m uvicorn src.main:app --reload
```
Open the interactive docs at http://127.0.0.1:8000/docs

---

## Design constraints honored

- **No ML clustering** — theme grouping is vector similarity + an LLM naming
  call, never k-means/HDBSCAN.
- **No feedback submission via API** — `/feedback` is GET-only; data enters
  only through `scripts/load_dataset.py`.
- **One retry path** — all OpenAI calls go through `openai_client.py` +
  `utils/retry.py`; retry logic is never duplicated.
- **Pipeline is a plain callable** — no in-process scheduler, nothing runs on
  app startup.
- **Single source of truth** — the taxonomy lives in `src/constants.py`; every
  prompt and schema references it.

---

## Project structure

```
backend/
├── docker-compose.yml        # Postgres + pgvector
├── requirements.txt
├── data/feedback.csv         # dataset (synthetic)
├── scripts/load_dataset.py   # ingestion (the only data entry point)
├── tests/eval/               # accuracy eval (run_eval.py + labeled_samples.csv)
└── src/
    ├── main.py               # FastAPI app
    ├── constants.py          # taxonomy (single source of truth)
    ├── core/config.py        # typed settings from .env
    ├── database/             # engine, session, init
    ├── models/               # SQLAlchemy tables (incl. vector columns)
    ├── schemas/              # Pydantic request/response models
    ├── routers/              # feedback (GET), analytics, chat
    ├── services/             # classifier, vector_store, theme_aggregator,
    │                         #   analytics, retrieval, summarizer,
    │                         #   chat_service, pipeline, openai_client
    ├── prompts/              # one prompt file per LLM generation task
    └── utils/                # retry, logger
```

---

## Testing & accuracy

Accuracy is measured by `tests/eval/run_eval.py`, which runs the classifier
over a labeled sample set (`tests/eval/labeled_samples.csv`) and writes the
results to [`ACCURACY.md`](ACCURACY.md).

Latest run (50 labeled samples):

| Metric | Score |
|---|---|
| Category accuracy | **80.0%** |
| Sentiment accuracy | **96.0%** |

Regenerate anytime (requires an OpenAI key):
```bash
python -m tests.eval.run_eval
```

Most categories score 100%; `praise` is lower because it overlaps with topic
categories (e.g. "love how fast reports load" is both `praise` and
`performance`) — a taxonomy ambiguity, not a hard error.

Unit tests (pytest/httpx) are not yet implemented; the accuracy eval is the
current automated check.

---

## Notes

- The dataset in `data/feedback.csv` is **synthetic** (150 rows), generated to
  cover all categories/sentiments/sources with dates spread over recent weeks.
