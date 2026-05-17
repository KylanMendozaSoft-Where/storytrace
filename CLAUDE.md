# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

**StoryTrace — "Git for News"**: A multi-agent system that takes a news article URL or topic, finds the original wire story, crawls 15 outlets, scores how much each outlet's coverage drifted from the original, and visualizes the mutation chain as a D3.js tree. See `STORYTRACE_FULL_CONTEXT.md` for the complete spec.

---

## Development Commands

### Backend (Python 3.14.3)
```bash
# Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Run FastAPI dev server
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Test GDELT API (no key needed)
curl "https://api.gdeltproject.org/api/v2/doc/doc?query=Iran&mode=artlist&format=json"
```

### Frontend (Next.js 14)
```bash
cd frontend
npm install
npm run dev       # http://localhost:3000
npm run build
npm run lint
```

### Docker (full stack)
```bash
docker-compose up -d        # start all services
docker-compose logs -f api  # stream backend logs
docker-compose down
```

### Database
```bash
# Run migrations (PostgreSQL must be up)
psql $DATABASE_URL -f backend/db/migrations.sql
```

---

## Architecture

### Agent Pipeline (sequential, via LangGraph `StateGraph`)

```
FastAPI POST /analyze
  └── LangGraph orchestrator
        ├── Agent 1: seed_agent      — GDELT → finds root story, extracts entities (spaCy)
        ├── Agent 2: crawler_agent   — feedparser, 15 RSS feeds, entity-matched headlines
        ├── Agent 3: translator      — Gemini Flash, fires only for non-English articles
        ├── Agent 4: dna_extractor   — Featherless API (Mistral-7B), structured JSON extraction
        ├── Agent 5: drift_scorer    — pure Python math, zero tokens
        ├── Agent 6: geo_builder     — builds D3-ready nested tree JSON
        └── Agent 7: alert_agent     — fires webhook when drift_score >= 70
```

Results stored in PostgreSQL (`stories` + `outlet_versions` tables). Redis caches repeat queries.

### Shared LangGraph State

Every agent receives and returns the same `state: dict`. The exact key names are a hard contract — a typo silently breaks downstream agents:

| Key | Written by | Read by |
|-----|-----------|---------|
| `state['job_id']` | FastAPI | alert_agent |
| `state['input']` | FastAPI | seed_agent |
| `state['entities']` | seed_agent | crawler_agent |
| `state['root']` | seed_agent | dna_extractor, drift_scorer, geo_builder |
| `state['articles']` | crawler_agent | translator (mutates in-place), dna_extractor |
| `state['dna_list']` | dna_extractor | drift_scorer |
| `state['scored_list']` | drift_scorer | geo_builder, alert_agent, update_story |
| `state['tree']` | geo_builder | FastAPI response |
| `state['alerts_fired']` | alert_agent | logging only |
| `state['error']` | seed_agent | FastAPI (check before saving) |

### Article dict shape (flows through `articles`, `dna_list`, `scored_list`)
```python
{
    'outlet':        str,   # e.g. "BBC"
    'country':       str,   # set by geo_builder before update_story
    'url':           str,
    'headline':      str,
    'text':          str,   # first 300 words; translator mutates in-place
    'language':      str,   # 'en' default; updated by translator
    'dna':           dict,  # added by dna_extractor
    'drift_score':   int,   # added by drift_scorer
    'parent_outlet': str,   # added by drift_scorer
}
```

### API Endpoints

- `POST /analyze` — accepts `{ url?, topic? }`, returns `{ job_id, status, poll_url }` (202)
- `GET /story/{job_id}` — poll for results; returns full tree JSON when `status == "complete"`
- `POST /forecast/{job_id}` — optional Gemini Pro world impact forecast
- `GET /health`

Full JSON shapes in `STORYTRACE_FULL_CONTEXT.md` section 8.

### Frontend

- `pages/index.jsx` — URL/topic input + Speechmatics voice input
- `pages/story/[id].jsx` — drift tree + diff panel, polls `GET /story/{id}`
- `components/DriftTree.jsx` — D3.js v7 tree, nodes colored green→amber→red by drift score
- `components/DiffPanel.jsx` — facts added/dropped on node click
- `components/VoiceInput.jsx` — Speechmatics WebSocket real-time transcription

---

## Environment Variables

Copy `.env.example` to `.env`. Required keys:

| Variable | Used by |
|---|---|
| `DATABASE_URL` | psycopg2 everywhere |
| `REDIS_URL` | cache layer |
| `NEWSAPI_KEY` | seed_agent fallback |
| `FEATHERLESS_API_KEY` | dna_extractor (Mistral-7B via OpenAI-compatible API) |
| `GEMINI_API_KEY` | translator + optional forecast |
| `WEBHOOK_URL` | alert_agent |
| `NEXT_PUBLIC_API_URL` | frontend → backend |
| `SPEECHMATICS_KEY` | server-side only — Next.js API route exchanges it for a short-lived JWT; never `NEXT_PUBLIC_` |

---

## Package Version Notes

`requirements.txt` has been updated to versions current as of May 2026. Two breaking changes from the spec code in `STORYTRACE_FULL_CONTEXT.md`:

1. **`google-generativeai` is deprecated — use `google-genai`.**
   The spec code uses `import google.generativeai as genai`. Replace with the new SDK:
   ```python
   from google import genai
   client = genai.Client()
   ```
   API surface changed; check the [google-genai migration guide](https://ai.google.dev/gemini-api/docs/migrate) when implementing PR-10 (Translator) and PR-20 (Forecast Agent).

2. **`openai` jumped from 1.x → 2.x.**
   The Featherless DNA Extractor usage (`openai.OpenAI(base_url=..., api_key=...)`) still works in 2.x — the custom base URL pattern is unchanged. No code change required for PR-09.

3. **`langgraph` 1.x and `langchain` 1.x have updated APIs** vs the 0.x code in the spec. The `StateGraph` / `add_node` / `add_edge` pattern in the spec is still valid in 1.x. Verify imports when implementing PR-04 (orchestrator).

4. **spaCy + Python 3.14.3**: spaCy 3.8.13 works correctly on Python 3.14.3 — `en_core_web_sm` loads without issue. If the model is missing, run `python -m spacy download en_core_web_sm`.

---

## Token Efficiency Rules

- spaCy NER runs locally — filters articles before any LLM call (zero tokens)
- RSS headline matching is local — zero tokens
- Only first 300 words per article sent to any LLM
- Featherless extracts structured JSON only (not open-ended summarization)
- Translator fires only when `langdetect` identifies non-English content
- Target: ~4,000–6,000 tokens per full pipeline run

---

## Branch Convention

```
main  ← protected, submission-only
  └── dev  ← all PRs target this
        ├── feature/backend-infra    (D1)
        ├── feature/core-agents      (D2)
        ├── feature/ai-agents        (D3)
        └── feature/frontend         (D4)
```

Commit prefix format: `[D1]`, `[D2]`, `[D3]`, `[D4]` matching which team wrote it.

---

## PR Plan

Full details for every PR are in [plan.md](plan.md). Summary:

| PR | Team | Branch | What | Depends on | Status |
|----|------|--------|------|------------|--------|
| **01** | D1 | `PR01-init-structure` | Scaffold — folders, .gitignore, .env.example, requirements.txt | — | ✅ done |
| **02** | D1 | `feature/database` | DB schema (migrations.sql) + connection.py | PR-01 | — |
| **03** | D1 | `feature/fastapi-skeleton` | **FastAPI skeleton — H4 API Contract Lock** | PR-02 | — |
| **04** | D1 | `feature/orchestrator` | LangGraph orchestrator + agent stubs | PR-03 | — |
| **05** | D1 | `feature/docker` | Docker Compose + Dockerfiles | PR-01 | — |
| **06** | D2 | `feature/agent-seed` | Agent 1 — Story Seed (GDELT + NewsAPI) | PR-04 | — |
| **07** | D2 | `feature/agent-crawler` | Agent 2 — Crawler (15 RSS feeds) | PR-06 | — |
| **08** | D2 | `feature/agent-alert` | Agent 7 — Alert Agent (webhook) | PR-04 | — |
| **09** | D3 | `feature/agent-dna` | Agent 3 — DNA Extractor (Featherless) | PR-04 | — |
| **10** | D3 | `feature/agent-translator` | Agent 4 — Translator (Gemini Flash) | PR-04 | — |
| **11** | D3 | `feature/agent-drift-scorer` | Agent 5 — Drift Scorer (pure Python) | PR-09 | — |
| **12** | D3 | `feature/agent-geo-builder` | Agent 6 — Geo-Branch Builder | PR-11 | — |
| **13** | All | `feature/e2e-pipeline` | **E2E integration test — H10 Pipeline Check** | PR-04–12 | — |
| **14** | D4 | `feature/frontend-setup` | Next.js setup + routing (starts at H0) | PR-01 | — |
| **15** | D4 | `feature/drift-tree` | DriftTree D3 component (static mock data) | PR-14 | — |
| **16** | D4 | `feature/diff-panel` | DiffPanel component | PR-15 | — |
| **17** | D4 | `feature/api-integration` | **API integration — H16 Frontend Lock** | PR-15, PR-03 | — |
| **18** | D4 | `feature/voice-input` | VoiceInput (Speechmatics WebSocket) | PR-17 | — |
| **19** | D4 | `feature/ui-polish` | UI polish + mobile responsive | PR-17, PR-18 | — |
| **20** | D3 | `feature/agent-forecast` | Forecast Agent — Gemini Pro (optional) | PR-13 | — |
| **21** | D1 | `feature/deployment` | Vultr deployment + Nginx | PR-13 | — |
| **22** | All | `feature/submission` | README + tag v1.0.0 + submit | All | — |

### Critical gates
- **H4** — PR-03 merged → API contract locked; D2 and D3 unblock
- **H10** — PR-13 passes → pipeline end-to-end confirmed
- **H16** — PR-17 merged → frontend wired to live API
- **H23** — code freeze, tag `v1.0.0`, submit

### Key implementation notes from plan.md
- **PR-03**: add `load_dotenv()` at top of `main.py`, CORS middleware for `localhost:3000`, run `run_pipeline` via `loop.run_in_executor` (it's synchronous and blocks the event loop)
- **PR-12**: geo_builder must write `art['country']` back into each `scored_list` dict before building the tree — otherwise `outlet_versions.country` is always `'Unknown'`
- **PR-18**: use `SPEECHMATICS_KEY` (no `NEXT_PUBLIC_` prefix); the Next.js API route at `/api/speechmatics-token` exchanges it for a short-lived JWT that the browser receives
