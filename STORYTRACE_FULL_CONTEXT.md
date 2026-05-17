# StoryTrace — Full Project Context
> **Hand this file to Claude Code or Cursor at the start of every session.**
> It contains the complete picture: idea, architecture, agent code, API contracts, database schema, team tasks, and deployment.

---

## Table of Contents
1. [What We Are Building](#1-what-we-are-building)
2. [The Two Use Cases](#2-the-two-use-cases)
3. [Hackathon Tracks We Target](#3-hackathon-tracks-we-target)
4. [Technology Partners](#4-technology-partners)
5. [System Architecture](#5-system-architecture)
6. [Tech Stack](#6-tech-stack)
7. [Folder Structure](#7-folder-structure)
8. [API Contract — Read This First](#8-api-contract--read-this-first)
9. [Database Schema](#9-database-schema)
10. [Agent 1 — Story Seed](#10-agent-1--story-seed-d2)
11. [Agent 2 — Crawler](#11-agent-2--crawler-d2)
12. [Agent 3 — DNA Extractor](#12-agent-3--dna-extractor-d3--featherless)
13. [Agent 4 — Translator](#13-agent-4--translator-d3--gemini-flash)
14. [Agent 5 — Drift Scorer](#14-agent-5--drift-scorer-d3)
15. [Agent 6 — Geo-Branch Builder](#15-agent-6--geo-branch-builder-d3)
16. [Agent 7 — Alert Agent](#16-agent-7--alert-agent-d2)
17. [LangGraph Orchestrator](#17-langgraph-orchestrator-d1)
18. [FastAPI Backend](#18-fastapi-backend-d1)
19. [Frontend Specification](#19-frontend-specification-d4)
20. [Optional — Forecast Agent](#20-optional--forecast-agent-d3)
21. [Environment Variables](#21-environment-variables)
22. [Docker & Deployment](#22-docker--deployment-d1)
23. [GitHub Workflow](#23-github-workflow)
24. [Team Task Breakdown](#24-team-task-breakdown)
25. [Sync Points](#25-sync-points)
26. [Research Papers](#26-research-papers)
27. [Why Not Claude or ChatGPT](#27-why-not-claude-or-chatgpt)

---

## 1. What We Are Building

**StoryTrace — Git for News**

> Paste any news article URL → StoryTrace finds the original wire story (AP/Reuters) → tracks how that story mutated, drifted, and branched differently across countries and outlets over time → visualized as a Git commit tree.

Just like Git tracks every change to code and shows who made it, StoryTrace tracks every change to a news narrative and shows which outlet caused each mutation, when it happened, and how far the story drifted from the original truth.

**The research gap we fill:**
- Fine-grained Narrative Classification in Biased News Articles (arXiv:2512.03582, Dec 2025) explicitly identifies that no temporal, cross-outlet, or cross-country tracking system exists.
- Media Bias Detector (arXiv:2502.06009, Feb 2025) analyzes one article at a time with no memory of how a story evolves. StoryTrace adds the temporal and relational dimension.

---

## 2. The Two Use Cases

### Use Case 1 — Narrative Drift Tracker (CORE — build this first)
- User pastes a URL or speaks a topic
- System finds the original wire story (root commit)
- Crawls 15 outlets every cycle
- Scores drift 0–100 per outlet
- Visualizes as a Git tree: root → country branches → outlet leaves
- Clickable nodes show exact facts added/dropped (like a code diff)
- Alert fires when drift > 70

### Use Case 2 — World Impact Forecast (OPTIONAL — only if time allows)
- On-demand button, not automatic
- Only for big geopolitical/economic events
- Tells you per country: what does this event actually mean?
- Example: Strait of Hormuz blocked → Pakistan (fuel crisis), USA (gas +$1.50), India (inflation spike)
- Flags which circulating media forecasts are panic-driven vs evidence-based
- Powered by Gemini Pro

---

## 3. Hackathon Tracks We Target

| Track | How StoryTrace Qualifies |
|---|---|
| 🔄 Agentic Workflows | 7 agents, each calling external tools, managing multi-step tasks over time |
| 🤝 Collaborative Systems | 7 specialized agents coordinating, passing structured JSON, achieving a goal no single LLM can |
| 🌍 Enterprise Utility | Newsrooms, intelligence teams, enterprise risk departments — real paying customers |
| 🧠 Intelligent Reasoning | Drift scoring, contagion chain detection, fallback logic without human intervention |

**Primary pitch to judges:** "Agentic Workflows + Collaborative Systems" — lead every conversation with this.

---

## 4. Technology Partners

| Partner | Prize | How We Use It |
|---|---|---|
| **Vultr** | $5,000 + $1K credits | Full backend on Vultr VM. Crawler, agents, DB, alert engine. |
| **Google Gemini** | $5,000 | Gemini Flash for translation. Gemini Pro for forecast. |
| **Featherless** | Credits + Claw Pro | Open-source narrative classification models via Featherless API. |
| **Speechmatics** | $1K cash + $1K credits | Real-time voice input — user speaks topic instead of typing. |

---

## 5. System Architecture

```
User (URL paste or Voice)
        │
        ├─ [Speechmatics]  voice → text  (D4)
        │
        ▼
FastAPI  POST /analyze  (D1 — Vultr VM)
        │
        ▼
LangGraph Orchestrator  (D1)
        │
        ├─ Agent 1: Story Seed      → GDELT API             (D2)
        ├─ Agent 2: Crawler         → 15 RSS feeds + spaCy  (D2)
        ├─ Agent 3: DNA Extractor   → Featherless API        (D3)
        ├─ Agent 4: Translator      → Gemini Flash           (D3)
        ├─ Agent 5: Drift Scorer    → internal Python math   (D3)
        ├─ Agent 6: Geo Builder     → PostgreSQL             (D3)
        └─ Agent 7: Alert Agent     → webhook / email        (D2)
        │
        ▼
PostgreSQL  (drift history, outlet_versions)
Redis       (cache — instant return on repeat queries)
        │
        ▼
Next.js Dashboard  (D4)
        ├─ D3.js Git Tree  ← HERO VISUAL
        ├─ Facts Diff Panel (click any node)
        └─ [Optional] Forecast Panel ← Gemini Pro
```

**Token efficiency strategy:**
- spaCy NER runs locally — zero tokens, filters articles before any LLM call
- RSS headlines matched locally — zero tokens
- Only first 300 words of each matched article sent to LLM
- Featherless does structured JSON extraction, not open-ended summarization
- Total cost: ~4,000–6,000 tokens per full pipeline run

---

## 6. Tech Stack

| Layer | Technology | Owner |
|---|---|---|
| Backend | Python 3.11 + FastAPI + Uvicorn | D1 |
| Agent Framework | LangGraph (StateGraph) | D1 |
| Database | PostgreSQL 15 + Redis 7 | D1 |
| Deployment | Vultr Ubuntu 22.04 + Nginx + Docker | D1 |
| Data Source | GDELT Project API + RSS feeds | D2 |
| NER Filter | spaCy en_core_web_sm (local, free) | D2 |
| AI — Extraction | Featherless API (Mistral-7B or similar) | D3 |
| AI — Translation | Gemini 1.5 Flash | D3 |
| AI — Forecast | Gemini 1.5 Pro (optional) | D3 |
| Frontend | Next.js 14 + Tailwind CSS | D4 |
| Visualization | D3.js v7 tree layout | D4 |
| Voice Input | Speechmatics real-time API | D4 |

---

## 7. Folder Structure

```
storytrace/
├── backend/
│   ├── main.py              ← FastAPI app, routes
│   ├── orchestrator.py      ← LangGraph graph definition
│   ├── models.py            ← Pydantic models
│   └── db/
│       ├── connection.py
│       └── migrations.sql
├── agents/
│   ├── seed_agent.py        ← Agent 1 (D2)
│   ├── crawler_agent.py     ← Agent 2 (D2)
│   ├── dna_extractor.py     ← Agent 3 (D3)
│   ├── translator.py        ← Agent 4 (D3)
│   ├── drift_scorer.py      ← Agent 5 (D3)
│   ├── geo_builder.py       ← Agent 6 (D3)
│   ├── alert_agent.py       ← Agent 7 (D2)
│   └── forecast_agent.py    ← Optional (D3)
├── frontend/
│   ├── pages/
│   │   ├── index.jsx        ← Home: input box + voice
│   │   ├── story/[id].jsx   ← Drift tree + diff panel
│   │   └── explore.jsx      ← Public cached dashboard
│   └── components/
│       ├── DriftTree.jsx    ← D3.js hero visual
│       ├── DiffPanel.jsx    ← Facts diff on node click
│       ├── VoiceInput.jsx   ← Speechmatics integration
│       └── ForecastPanel.jsx← Optional forecast output
├── docker-compose.yml
├── .env.example
├── requirements.txt
└── README.md
```

---

## 8. API Contract — Read This First

> D1 publishes this by Hour 4. No agent, no frontend, no test is written until everyone agrees on these JSON shapes.

### POST /analyze
**Trigger the full pipeline.**

Request:
```json
{
  "url":   "https://www.reuters.com/world/...",
  "topic": "Iran nuclear talks"
}
```
*(send either url or topic, not both required)*

Response (202 Accepted):
```json
{
  "job_id":   "550e8400-e29b-41d4-a716-446655440000",
  "status":   "processing",
  "poll_url": "/story/550e8400-e29b-41d4-a716-446655440000"
}
```

---

### GET /story/{job_id}
**Poll for results.**

Response while processing:
```json
{
  "job_id":   "uuid",
  "status":   "processing",
  "progress": 3,
  "message":  "Extracting narrative DNA..."
}
```

Response when complete:
```json
{
  "job_id": "uuid",
  "status": "complete",
  "root": {
    "outlet":    "Reuters",
    "country":   "US",
    "url":       "https://...",
    "headline":  "Iranian officials confirm partial withdrawal from Fordow facility",
    "published": "2026-05-13T09:00:00Z",
    "dna": {
      "facts_kept":    ["partial withdrawal", "Fordow facility", "IAEA inspection"],
      "facts_dropped": [],
      "tone":          "neutral",
      "framing":       "Diplomatic progress in nuclear negotiations",
      "political_lean":"center"
    }
  },
  "tree": [
    {
      "id":           "node-BBC",
      "outlet":       "BBC",
      "country":      "UK",
      "url":          "https://...",
      "headline":     "Iran steps back from nuclear site",
      "published":    "2026-05-13T10:30:00Z",
      "drift_score":  18,
      "parent_id":    "root",
      "parent_outlet":"Reuters",
      "dna": {
        "facts_kept":    ["withdrawal", "Fordow"],
        "facts_dropped": ["IAEA inspection"],
        "tone":          "neutral",
        "framing":       "Diplomatic de-escalation",
        "political_lean":"center"
      }
    }
  ]
}
```

---

### POST /forecast/{job_id}
**Optional — world impact forecast.**

Response:
```json
{
  "event_type": "geopolitical",
  "countries": [
    {
      "country":    "Pakistan",
      "dependency": "High Gulf oil reliance via Hormuz",
      "impact":     "Fuel prices spike, energy crisis within 2-3 weeks",
      "confidence": "high"
    },
    {
      "country":    "USA",
      "dependency": "Domestic production buffer, global ripple effect",
      "impact":     "Gas prices jump $1.20-1.80/gallon within 6 weeks",
      "confidence": "medium"
    }
  ],
  "panic_forecasts": [
    "Global economy collapses in 72 hours"
  ],
  "evidence_assessment": "Moderate disruption likely. Historical precedent from 2019 Abqaiq attack suggests 3-6 week disruption window."
}
```

---

## 9. Database Schema

```sql
-- Run this on Vultr PostgreSQL

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE stories (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  topic         TEXT,
  input_url     TEXT,
  root_outlet   TEXT,
  root_url      TEXT,
  root_headline TEXT,
  root_text     TEXT,
  root_dna      JSONB,
  status        TEXT DEFAULT 'processing',  -- processing | complete | failed
  created_at    TIMESTAMP DEFAULT NOW()
);

CREATE TABLE outlet_versions (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  story_id      UUID REFERENCES stories(id) ON DELETE CASCADE,
  outlet        TEXT NOT NULL,
  country       TEXT NOT NULL,
  url           TEXT,
  headline      TEXT,
  article_text  TEXT,
  dna           JSONB,
  drift_score   INTEGER CHECK (drift_score BETWEEN 0 AND 100),
  parent_outlet TEXT,       -- contagion chain: which outlet was copied
  language      TEXT DEFAULT 'en',
  crawled_at    TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_outlet_story    ON outlet_versions(story_id);
CREATE INDEX idx_outlet_country  ON outlet_versions(country);
CREATE INDEX idx_outlet_drift    ON outlet_versions(drift_score);
```

---

## 10. Agent 1 — Story Seed (D2)

**Input:** URL string or topic string from user
**Output:** `state['root']` — root story JSON, `state['entities']` — named entities
**Tool:** GDELT API
**Fallback:** If GDELT returns 0 results → NewsAPI

```python
# agents/seed_agent.py
import spacy
import requests
import os

nlp = spacy.load('en_core_web_sm')

GDELT_URL  = 'https://api.gdeltproject.org/api/v2/doc/doc'
NEWSAPI_URL= 'https://newsapi.org/v2/everything'

def query_gdelt(query: str) -> dict | None:
    try:
        r = requests.get(GDELT_URL, params={
            'query':      query,
            'mode':       'artlist',
            'maxrecords': 5,
            'sort':       'DateAsc',   # earliest = root story
            'format':     'json'
        }, timeout=10)
        articles = r.json().get('articles', [])
        return articles[0] if articles else None
    except Exception:
        return None

def query_newsapi(query: str) -> dict | None:
    """Fallback if GDELT returns nothing."""
    try:
        r = requests.get(NEWSAPI_URL, params={
            'q':        query,
            'sortBy':   'publishedAt',
            'pageSize': 1,
            'apiKey':   os.environ['NEWSAPI_KEY']
        }, timeout=10)
        articles = r.json().get('articles', [])
        return articles[0] if articles else None
    except Exception:
        return None

def run(state: dict) -> dict:
    user_input = state['input']

    # Step 1: extract entities — zero tokens, local spaCy
    doc = nlp(user_input)
    entities = [e.text for e in doc.ents if e.label_ in ('PERSON','ORG','GPE','EVENT','NORP')]
    query = ' '.join(entities[:3]) if entities else user_input
    state['entities'] = entities if entities else [user_input]

    # Step 2: find earliest story = root (GDELT first, NewsAPI fallback)
    root = query_gdelt(query) or query_newsapi(query)
    if not root:
        state['error'] = 'Could not find source story'
        return state

    state['root'] = {
        'outlet':    root.get('domain', root.get('source', {}).get('name', 'Unknown')),
        'country':   'US',
        'url':       root.get('url', root.get('url', '')),
        'headline':  root.get('title', ''),
        'text':      root.get('seendate', root.get('description', '')),
        'published': root.get('seendate', root.get('publishedAt', '')),
        'dna':       {}
    }
    return state
```

---

## 11. Agent 2 — Crawler (D2)

**Input:** `state['entities']`
**Output:** `state['articles']` — list of matched articles (first 300 words each)
**Tools:** feedparser + requests + spaCy NER
**Token cost:** ~200 tokens × 8 matches = ~1,600 tokens per cycle

```python
# agents/crawler_agent.py
import feedparser
import requests
import spacy

nlp = spacy.load('en_core_web_sm')

RSS_FEEDS = {
    'BBC':            'http://feeds.bbci.co.uk/news/rss.xml',
    'Al Jazeera':     'https://www.aljazeera.com/xml/rss/all.xml',
    'Dawn':           'https://www.dawn.com/feed',
    'CNN':            'http://rss.cnn.com/rss/edition.rss',
    'RT':             'https://www.rt.com/rss/news/',
    'Times of India': 'https://timesofindia.indiatimes.com/rssfeeds/296589292.cms',
    'Guardian':       'https://www.theguardian.com/world/rss',
    'Fox News':       'https://moxie.foxnews.com/google-publisher/world.xml',
    'DW':             'https://rss.dw.com/xml/rss-en-all',
    'France24':       'https://www.france24.com/en/rss',
    'NDTV':           'https://feeds.feedburner.com/ndtvnews-world-news',
    'Arab News':      'https://www.arabnews.com/rss.xml',
    'Sputnik':        'https://sputniknews.com/export/rss2/world/index.xml',
    'NHK':            'https://www3.nhk.or.jp/rss/news/cat6.xml',
    'TASS':           'https://tass.com/rss/v2.xml',
}

def entity_match(headline: str, entities: list[str]) -> bool:
    h = headline.lower()
    return any(e.lower() in h for e in entities)

def fetch_first_300_words(url: str) -> str | None:
    try:
        r = requests.get(url, timeout=5, headers={'User-Agent': 'StoryTrace/1.0'})
        words = r.text.split()[:300]
        return ' '.join(words)
    except Exception:
        return None

def run(state: dict) -> dict:
    entities = state.get('entities', [])
    matched  = []

    for outlet, feed_url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:20]:
                if entity_match(entry.get('title', ''), entities):
                    text = fetch_first_300_words(entry.link)
                    if text:
                        matched.append({
                            'outlet':   outlet,
                            'url':      entry.link,
                            'headline': entry.get('title', ''),
                            'text':     text,
                            'language': 'en'   # detected/updated by Translator agent
                        })
                    break  # one article per outlet
        except Exception:
            continue  # skip this outlet, never block the pipeline

    state['articles'] = matched
    return state
```

---

## 12. Agent 3 — DNA Extractor (D3) — Featherless

**Input:** `state['articles']`
**Output:** `state['dna_list']` — each article with structured DNA JSON attached
**Model:** Featherless API (OpenAI-compatible) — pick `mistralai/Mistral-7B-Instruct-v0.3` or best available news model
**Token cost:** ~300 tokens per article

```python
# agents/dna_extractor.py
from openai import OpenAI
import json
import os

client = OpenAI(
    base_url='https://api.featherless.ai/v1',
    api_key=os.environ['FEATHERLESS_API_KEY']
)

MODEL = 'mistralai/Mistral-7B-Instruct-v0.3'

PROMPT = """You are a journalism analyst. Extract the following from the article below.
Return ONLY valid JSON — no explanation, no markdown, just the JSON object.

{{
  "facts_kept":    ["list every key factual claim present in the article"],
  "facts_dropped": ["key facts from the ROOT STORY that are MISSING from this article"],
  "tone":          "neutral|alarming|dismissive|supportive",
  "framing":       "one sentence describing the narrative angle of this article",
  "political_lean":"left|center|right|unknown"
}}

ROOT STORY (ground truth):
{root_text}

THIS ARTICLE TO ANALYZE:
{article_text}
"""

def extract_dna(article_text: str, root_text: str) -> dict:
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{
                'role':    'user',
                'content': PROMPT.format(
                    root_text=root_text[:500],
                    article_text=article_text[:800]
                )
            }],
            temperature=0.1,
            max_tokens=400
        )
        raw = response.choices[0].message.content.strip()
        # strip markdown code fences if model adds them
        raw = raw.replace('```json', '').replace('```', '').strip()
        return json.loads(raw)
    except Exception as e:
        # safe fallback — empty DNA, pipeline continues
        return {
            'facts_kept':    [],
            'facts_dropped': [],
            'tone':          'unknown',
            'framing':       'Could not extract',
            'political_lean':'unknown'
        }

def run(state: dict) -> dict:
    root_text = state['root'].get('text', state['root'].get('headline', ''))
    dna_list  = []
    for art in state.get('articles', []):
        dna = extract_dna(art['text'], root_text)
        dna_list.append({**art, 'dna': dna})
    state['dna_list'] = dna_list
    return state
```

---

## 13. Agent 4 — Translator (D3) — Gemini Flash

**Input:** `state['articles']` — checks each for non-English content
**Output:** translated text written back into each article dict
**When it fires:** Only when `langdetect` identifies a non-English article
**Cost:** Only pays for non-English articles

```python
# agents/translator.py
import google.generativeai as genai
from langdetect import detect, LangDetectException
import os

genai.configure(api_key=os.environ['GEMINI_API_KEY'])
flash = genai.GenerativeModel('gemini-1.5-flash')

def translate_to_english(text: str) -> str:
    r = flash.generate_content(
        f'Translate this news article to English. Preserve the tone and framing exactly. '
        f'Do not add commentary. Return only the translated text.\n\n{text}'
    )
    return r.text

def run(state: dict) -> dict:
    for art in state.get('articles', []):
        try:
            lang = detect(art['text'])
            if lang != 'en':
                art['text']     = translate_to_english(art['text'])
                art['language'] = lang
        except LangDetectException:
            pass  # assume English if detection fails
    return state
```

---

## 14. Agent 5 — Drift Scorer (D3)

**Input:** `state['dna_list']` + `state['root']`
**Output:** `state['scored_list']` — each article with `drift_score` (0–100) and `parent_outlet`
**Cost:** Zero tokens — pure Python math

```python
# agents/drift_scorer.py

TONE_MAP = {
    'neutral':    0,
    'supportive': 20,
    'dismissive': 35,
    'alarming':   50,
    'unknown':    0
}

def compute_drift(root_dna: dict, outlet_dna: dict) -> int:
    root_facts   = set(f.lower() for f in root_dna.get('facts_kept', []))
    outlet_facts = set(f.lower() for f in outlet_dna.get('facts_kept', []))

    # Score 1: how many root facts were dropped (0–60 points)
    if root_facts:
        dropped_ratio = len(root_facts - outlet_facts) / len(root_facts)
    else:
        dropped_ratio = 0
    fact_score = dropped_ratio * 60

    # Score 2: tone shift from root (0–40 points)
    root_tone   = TONE_MAP.get(root_dna.get('tone', 'neutral'), 0)
    outlet_tone = TONE_MAP.get(outlet_dna.get('tone', 'neutral'), 0)
    tone_score  = min(abs(outlet_tone - root_tone), 40)

    return min(round(fact_score + tone_score), 100)

def find_parent_outlet(index: int, scored_so_far: list) -> str:
    """Simple contagion: parent is the most recently scored outlet with lowest drift."""
    if not scored_so_far:
        return 'root'
    # find the lowest-drift outlet scored so far = most likely copied from
    closest = min(scored_so_far, key=lambda x: x['drift_score'])
    return closest['outlet']

def run(state: dict) -> dict:
    root_dna = state['root'].get('dna', {})
    scored   = []

    for i, art in enumerate(state.get('dna_list', [])):
        score  = compute_drift(root_dna, art.get('dna', {}))
        parent = find_parent_outlet(i, scored)
        scored.append({
            **art,
            'drift_score':   score,
            'parent_outlet': parent
        })

    state['scored_list'] = sorted(scored, key=lambda x: x['drift_score'])
    return state
```

---

## 15. Agent 6 — Geo-Branch Builder (D3)

**Input:** `state['scored_list']`
**Output:** `state['tree']` — nested JSON ready for D3.js

```python
# agents/geo_builder.py

OUTLET_COUNTRY = {
    'BBC':            'UK',
    'Guardian':       'UK',
    'Reuters':        'US',
    'CNN':            'US',
    'Fox News':       'US',
    'Al Jazeera':     'Qatar',
    'Arab News':      'Saudi Arabia',
    'Dawn':           'Pakistan',
    'RT':             'Russia',
    'Sputnik':        'Russia',
    'TASS':           'Russia',
    'DW':             'Germany',
    'France24':       'France',
    'NDTV':           'India',
    'Times of India': 'India',
    'NHK':            'Japan',
}

def run(state: dict) -> dict:
    root = state['root']

    tree = {
        'id':          'root',
        'outlet':      root.get('outlet', 'Wire'),
        'country':     'US',
        'headline':    root.get('headline', ''),
        'drift_score': 0,
        'parent_id':   None,
        'type':        'root',
        'children':    []
    }

    # group articles by country
    by_country: dict[str, list] = {}
    for art in state.get('scored_list', []):
        country = OUTLET_COUNTRY.get(art['outlet'], 'Other')
        by_country.setdefault(country, []).append({
            'id':           f"node-{art['outlet'].replace(' ', '-')}",
            'outlet':       art['outlet'],
            'country':      country,
            'headline':     art['headline'],
            'url':          art['url'],
            'drift_score':  art['drift_score'],
            'parent_id':    art['parent_outlet'],
            'dna':          art.get('dna', {}),
            'type':         'outlet',
            'children':     []
        })

    # build country branch nodes
    for country, nodes in by_country.items():
        avg_drift = round(sum(n['drift_score'] for n in nodes) / len(nodes))
        branch = {
            'id':          f'branch-{country}',
            'country':     country,
            'type':        'country_branch',
            'drift_score': avg_drift,
            'children':    nodes
        }
        tree['children'].append(branch)

    # sort branches by average drift (lowest first)
    tree['children'].sort(key=lambda b: b['drift_score'])

    state['tree'] = tree
    return state
```

---

## 16. Agent 7 — Alert Agent (D2)

**Input:** `state['scored_list']`, `state['job_id']`
**Output:** fires webhook for any outlet with drift_score >= threshold

```python
# agents/alert_agent.py
import requests
import os

THRESHOLD = 70  # fire alert when drift score >= this

def send_alert(payload: dict) -> None:
    webhook = os.environ.get('WEBHOOK_URL', '')
    if webhook:
        try:
            requests.post(webhook, json=payload, timeout=5)
        except Exception:
            pass  # alerts are best-effort, never block pipeline

def run(state: dict) -> dict:
    alerts_fired = []
    for art in state.get('scored_list', []):
        if art['drift_score'] >= THRESHOLD:
            payload = {
                'job_id':      state.get('job_id'),
                'outlet':      art['outlet'],
                'country':     art.get('country', 'Unknown'),
                'drift_score': art['drift_score'],
                'headline':    art.get('headline', ''),
                'url':         art.get('url', ''),
                'alert':       f"DRIFT ALERT: {art['outlet']} scored {art['drift_score']}/100"
            }
            send_alert(payload)
            alerts_fired.append(art['outlet'])

    state['alerts_fired'] = alerts_fired
    return state
```

---

## 17. LangGraph Orchestrator (D1)

```python
# backend/orchestrator.py
from langgraph.graph import StateGraph, END
from agents import (
    seed_agent, crawler_agent, translator,
    dna_extractor, drift_scorer, geo_builder, alert_agent
)

def build_pipeline():
    g = StateGraph(dict)

    g.add_node('seed',       seed_agent.run)
    g.add_node('crawler',    crawler_agent.run)
    g.add_node('translator', translator.run)
    g.add_node('dna',        dna_extractor.run)
    g.add_node('scorer',     drift_scorer.run)
    g.add_node('geo',        geo_builder.run)
    g.add_node('alert',      alert_agent.run)

    g.set_entry_point('seed')
    g.add_edge('seed',       'crawler')
    g.add_edge('crawler',    'translator')   # translate before DNA extraction
    g.add_edge('translator', 'dna')
    g.add_edge('dna',        'scorer')
    g.add_edge('scorer',     'geo')
    g.add_edge('geo',        'alert')
    g.add_edge('alert',      END)

    return g.compile()

pipeline = build_pipeline()

def run_pipeline(job_id: str, user_input: str) -> dict:
    initial_state = {
        'job_id': job_id,
        'input':  user_input
    }
    return pipeline.invoke(initial_state)
```

---

## 18. FastAPI Backend (D1)

```python
# backend/main.py
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import uuid
import asyncio
from backend.orchestrator import run_pipeline
from backend.db.connection import save_story, update_story, get_story

app = FastAPI(title="StoryTrace API")

class AnalyzeRequest(BaseModel):
    url:   str | None = None
    topic: str | None = None

@app.post("/analyze", status_code=202)
async def analyze(req: AnalyzeRequest, background_tasks: BackgroundTasks):
    job_id    = str(uuid.uuid4())
    user_input= req.url or req.topic

    # save job as 'processing'
    save_story(job_id, user_input)

    # run pipeline in background
    background_tasks.add_task(run_and_save, job_id, user_input)

    return {
        "job_id":   job_id,
        "status":   "processing",
        "poll_url": f"/story/{job_id}"
    }

async def run_and_save(job_id: str, user_input: str):
    try:
        result = run_pipeline(job_id, user_input)
        update_story(job_id, result, status='complete')
    except Exception as e:
        update_story(job_id, {}, status='failed')

@app.get("/story/{job_id}")
async def get_story_result(job_id: str):
    story = get_story(job_id)
    if not story:
        return {"error": "Story not found"}, 404
    return story

@app.post("/forecast/{job_id}")
async def forecast(job_id: str):
    from agents.forecast_agent import run as run_forecast
    story = get_story(job_id)
    if not story or story['status'] != 'complete':
        return {"error": "Story not complete yet"}
    return run_forecast(story)

@app.get("/health")
async def health():
    return {"status": "ok"}
```

```python
# backend/db/connection.py
import psycopg2
import json
import os

def get_conn():
    return psycopg2.connect(os.environ['DATABASE_URL'])

def save_story(job_id: str, user_input: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO stories (id, topic, status) VALUES (%s, %s, 'processing')",
                (job_id, user_input)
            )

def update_story(job_id: str, result: dict, status: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE stories SET status=%s, root_dna=%s WHERE id=%s",
                (status, json.dumps(result.get('root', {})), job_id)
            )
            for art in result.get('scored_list', []):
                cur.execute("""
                    INSERT INTO outlet_versions
                      (story_id, outlet, country, url, headline, article_text, dna, drift_score, parent_outlet)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    job_id, art['outlet'], art.get('country','Unknown'),
                    art['url'], art['headline'], art['text'],
                    json.dumps(art.get('dna', {})),
                    art['drift_score'], art.get('parent_outlet','root')
                ))

def get_story(job_id: str) -> dict | None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM stories WHERE id=%s", (job_id,))
            row = cur.fetchone()
            if not row:
                return None
            # also fetch outlet versions
            cur.execute(
                "SELECT * FROM outlet_versions WHERE story_id=%s ORDER BY drift_score",
                (job_id,)
            )
            versions = cur.fetchall()
            return {'job_id': job_id, 'status': row[8], 'versions': versions}
```

---

## 19. Frontend Specification (D4)

### Setup
```bash
npx create-next-app@latest frontend --typescript --tailwind --app
cd frontend
npm install d3
```

### D3.js Drift Tree Component
```jsx
// frontend/components/DriftTree.jsx
import { useEffect, useRef } from 'react'
import * as d3 from 'd3'

const driftColor = d3.scaleLinear()
  .domain([0, 50, 100])
  .range(['#27A06A', '#F59E0B', '#E8562A'])  // green → amber → red

export default function DriftTree({ treeData, onNodeClick }) {
  const svgRef = useRef()

  useEffect(() => {
    if (!treeData) return
    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    const width  = 900
    const height = 600
    const margin = { top: 40, right: 40, bottom: 40, left: 40 }

    const root = d3.hierarchy(treeData)
    const treeLayout = d3.tree()
      .size([width - margin.left - margin.right, height - margin.top - margin.bottom])

    treeLayout(root)

    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

    // Draw links
    g.selectAll('.link')
      .data(root.links())
      .join('path')
      .attr('class', 'link')
      .attr('fill', 'none')
      .attr('stroke', '#CBD5E1')
      .attr('stroke-width', 2)
      .attr('d', d3.linkVertical()
        .x(d => d.x)
        .y(d => d.y))

    // Draw nodes
    const node = g.selectAll('.node')
      .data(root.descendants())
      .join('g')
      .attr('class', 'node')
      .attr('transform', d => `translate(${d.x},${d.y})`)
      .style('cursor', 'pointer')
      .on('click', (event, d) => onNodeClick && onNodeClick(d.data))

    node.append('circle')
      .attr('r', 18)
      .attr('fill', d => driftColor(d.data.drift_score || 0))
      .attr('stroke', '#fff')
      .attr('stroke-width', 3)

    // Drift score label inside node
    node.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .attr('fill', '#fff')
      .attr('font-size', '10px')
      .attr('font-weight', 'bold')
      .text(d => d.data.drift_score !== undefined ? d.data.drift_score : '')

    // Outlet name below node
    node.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '2.5em')
      .attr('fill', '#1B3A6B')
      .attr('font-size', '11px')
      .attr('font-weight', 'bold')
      .text(d => d.data.outlet || d.data.country || '')

  }, [treeData])

  return (
    <div className="w-full overflow-x-auto bg-white rounded-lg shadow p-4">
      <svg ref={svgRef} width="100%" viewBox="0 0 900 600" />
    </div>
  )
}
```

### Facts Diff Panel
```jsx
// frontend/components/DiffPanel.jsx
export default function DiffPanel({ node, root }) {
  if (!node || !node.dna) return null

  const rootFacts   = new Set(root?.dna?.facts_kept || [])
  const nodeFacts   = new Set(node.dna.facts_kept || [])
  const dropped     = [...rootFacts].filter(f => !nodeFacts.has(f))
  const added       = [...nodeFacts].filter(f => !rootFacts.has(f))

  return (
    <div className="bg-white rounded-lg shadow p-4 mt-4">
      <h3 className="font-bold text-lg text-[#1B3A6B] mb-3">
        {node.outlet} — Drift Score: <span style={{color: node.drift_score > 70 ? '#E8562A' : '#27A06A'}}>{node.drift_score}/100</span>
      </h3>
      <p className="text-sm text-gray-500 mb-4 italic">{node.dna.framing}</p>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <h4 className="font-semibold text-red-600 mb-2">❌ Facts Dropped</h4>
          {dropped.length === 0
            ? <p className="text-sm text-gray-400">None dropped</p>
            : dropped.map((f, i) => <div key={i} className="text-sm bg-red-50 text-red-700 p-2 rounded mb-1">{f}</div>)
          }
        </div>
        <div>
          <h4 className="font-semibold text-green-600 mb-2">✅ Facts Kept</h4>
          {[...nodeFacts].filter(f => rootFacts.has(f)).map((f, i) =>
            <div key={i} className="text-sm bg-green-50 text-green-700 p-2 rounded mb-1">{f}</div>
          )}
        </div>
      </div>
      <div className="mt-3 flex gap-4 text-sm">
        <span className="bg-gray-100 px-2 py-1 rounded">Tone: <strong>{node.dna.tone}</strong></span>
        <span className="bg-gray-100 px-2 py-1 rounded">Lean: <strong>{node.dna.political_lean}</strong></span>
      </div>
    </div>
  )
}
```

### Speechmatics Voice Input
```jsx
// frontend/components/VoiceInput.jsx
// Docs: https://docs.speechmatics.com/introduction/real-time-api
import { useState, useRef } from 'react'

export default function VoiceInput({ onTranscript }) {
  const [listening, setListening] = useState(false)
  const wsRef = useRef(null)

  const startListening = async () => {
    // 1. Get JWT from Speechmatics
    const res = await fetch('/api/speechmatics-token')
    const { token } = await res.json()

    // 2. Open WebSocket
    const ws = new WebSocket(`wss://eu2.rt.speechmatics.com/v2`)
    wsRef.current = ws

    ws.onopen = () => {
      ws.send(JSON.stringify({
        message:    'StartRecognition',
        audio_format: { type: 'raw', encoding: 'pcm_f32le', sample_rate: 44100 },
        transcription_config: { language: 'en', enable_partials: true }
      }))
    }

    ws.onmessage = (e) => {
      const data = JSON.parse(e.data)
      if (data.message === 'AddTranscript') {
        onTranscript(data.metadata.transcript)
      }
    }

    setListening(true)
  }

  const stopListening = () => {
    wsRef.current?.close()
    setListening(false)
  }

  return (
    <button
      onClick={listening ? stopListening : startListening}
      className={`p-3 rounded-full ${listening ? 'bg-red-500 animate-pulse' : 'bg-[#2E5FA3]'} text-white`}
    >
      {listening ? '⏹ Stop' : '🎙 Speak'}
    </button>
  )
}
```

---

## 20. Optional — Forecast Agent (D3)

Only build this after Use Case 1 is fully working.

```python
# agents/forecast_agent.py
import google.generativeai as genai
import json
import os

genai.configure(api_key=os.environ['GEMINI_API_KEY'])
pro = genai.GenerativeModel('gemini-1.5-pro')

PROMPT = """You are a geopolitical risk analyst. Analyze this news event and provide a structured impact forecast.

Return ONLY valid JSON in this exact format:
{{
  "event_type":  "geopolitical|economic|environmental|conflict|other",
  "countries": [
    {{
      "country":    "country name",
      "dependency": "how this country is connected to the event",
      "impact":     "specific projected impact with timeframe",
      "confidence": "high|medium|low"
    }}
  ],
  "panic_forecasts": ["list any exaggerated or unsupported claims circulating in media"],
  "evidence_assessment": "your evidence-based summary paragraph"
}}

Include the 5 most affected countries. Focus on real, measurable impacts.

NEWS EVENT:
{headline}

ARTICLE TEXT:
{text}
"""

def run(story: dict) -> dict:
    root = story.get('root', {})
    try:
        response = pro.generate_content(
            PROMPT.format(
                headline=root.get('headline', ''),
                text=root.get('text', '')[:1500]
            )
        )
        raw = response.text.strip().replace('```json','').replace('```','')
        return json.loads(raw)
    except Exception as e:
        return {'error': str(e)}
```

---

## 21. Environment Variables

```bash
# .env.example — copy to .env and fill in your keys
# NEVER commit .env to Git

# ── D1: Backend Infrastructure ──────────────────────────────
DATABASE_URL=postgresql://user:password@localhost:5432/storytrace
REDIS_URL=redis://localhost:6379
WEBHOOK_URL=https://your-webhook-endpoint.com/alerts

# ── D2: Data Sources ─────────────────────────────────────────
GDELT_BASE_URL=https://api.gdeltproject.org/api/v2/doc/doc
NEWSAPI_KEY=your_newsapi_key_here          # fallback for GDELT

# ── D3: AI Models ────────────────────────────────────────────
FEATHERLESS_API_KEY=your_featherless_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# ── D4: Frontend (NEXT_PUBLIC_ = exposed to browser) ─────────
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SPEECHMATICS_KEY=your_speechmatics_api_key_here
```

---

## 22. Docker & Deployment (D1)

### docker-compose.yml
```yaml
version: '3.8'
services:
  api:
    build: ./backend
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      - db
      - redis
    command: uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

  db:
    image: postgres:15
    environment:
      POSTGRES_DB:       storytrace
      POSTGRES_USER:     user
      POSTGRES_PASSWORD: password
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./backend/db/migrations.sql:/docker-entrypoint-initdb.d/init.sql

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    env_file: .env
    depends_on:
      - api

volumes:
  pgdata:
```

### backend/Dockerfile
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN python -m spacy download en_core_web_sm
COPY . .
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### requirements.txt
```
fastapi==0.111.0
uvicorn==0.29.0
langgraph==0.1.0
langchain==0.2.0
openai==1.30.0
google-generativeai==0.7.0
feedparser==6.0.11
spacy==3.7.4
langdetect==1.0.9
psycopg2-binary==2.9.9
redis==5.0.4
requests==2.32.0
python-dotenv==1.0.1
pydantic==2.7.0
```

### Vultr Server Setup (D1 runs this once)
```bash
# SSH into Vultr Ubuntu 22.04 VM
sudo apt update && sudo apt install -y docker.io docker-compose nginx certbot

# Clone repo
git clone https://github.com/your-team/storytrace.git
cd storytrace

# Set up environment
cp .env.example .env
nano .env   # fill in all API keys

# Start everything
docker-compose up -d

# Nginx config — /etc/nginx/sites-available/storytrace
sudo tee /etc/nginx/sites-available/storytrace << 'EOF'
server {
    listen 80;
    server_name YOUR_VULTR_IP;

    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
    }

    location / {
        proxy_pass http://localhost:3000/;
        proxy_set_header Host $host;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/storytrace /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx
```

---

## 23. GitHub Workflow

### Branch Structure
```
main              ← protected. Only D1 merges here at Hour 23 for submission.
  └── dev         ← everyone's working branch. All PRs target dev.
        ├── feature/backend-infra   ← D1
        ├── feature/core-agents     ← D2
        ├── feature/ai-agents       ← D3
        └── feature/frontend        ← D4
```

### First 30 Minutes (D1 does this immediately)
```bash
# D1 creates the repo and structure
git init storytrace
cd storytrace
mkdir -p backend/db agents frontend/pages frontend/components
touch .env.example .gitignore docker-compose.yml requirements.txt README.md

# Add to .gitignore
echo ".env\n__pycache__\nnode_modules\n.next" > .gitignore

git add .
git commit -m "[D1] Initial project structure"
git remote add origin https://github.com/your-team/storytrace.git
git push -u origin main

# Create dev branch
git checkout -b dev
git push origin dev

# Share repo invite link with D2, D3, D4
# Each dev then: git checkout -b feature/their-branch
```

### Commit Message Format
```
[D1] Add FastAPI skeleton with /analyze and /story endpoints
[D2] Implement Story Seed Agent with GDELT + NewsAPI fallback
[D3] Add Featherless DNA extractor with strict JSON schema
[D4] Render D3.js tree with static mock data — ready for API wire-up
```

### PR Rules
1. PR from `feature/*` → `dev` only. Never directly to `main`.
2. One teammate reviews and approves — max 10 minutes. Don't block the sprint.
3. Squash merge to keep history clean.
4. Tag final submission: `git tag v1.0.0 && git push origin v1.0.0`

---

## 24. Team Task Breakdown

### D1 — Backend + Infrastructure
| Hours | Task |
|---|---|
| 0–2h | Vultr VM setup, Docker, PostgreSQL, Redis, Nginx |
| 2–4h | FastAPI skeleton — /analyze, /story/{id}, /health |
| 4–6h | PostgreSQL migrations, DB connection module |
| 6–9h | LangGraph orchestrator — wire all 7 agents |
| 9–12h | Redis cache, background task runner, error handling |
| 12–24h | Integration testing, bug fixes, deployment, public URL |

**D1's most critical deliverable:** Publish the API contract JSON shapes by Hour 4. Everything else depends on this.

### D2 — Core Agents
| Hours | Task |
|---|---|
| 0–2h | Local env setup, install spaCy + feedparser, test GDELT API |
| 2–5h | Agent 1: Story Seed — GDELT query + NewsAPI fallback |
| 5–9h | Agent 2: Crawler — 15 RSS feeds, entity matching, 300-word fetch |
| 9–12h | Fallback logic — blocked outlets, failed feeds, silent continuation |
| 12–16h | Agent 7: Alert Agent — webhook, threshold logic, unit tests |
| 16–24h | Help D1 with integration, end-to-end pipeline testing |

### D3 — AI Agents
| Hours | Task |
|---|---|
| 0–2h | Setup Featherless API, Gemini API, test both connections |
| 2–7h | Agent 3: DNA Extractor — Featherless with strict JSON schema |
| 7–11h | Agent 5: Drift Scorer — compute_drift(), contagion chain |
| 11–15h | Agent 6: Geo-Branch Builder — outlet→country map, tree JSON |
| 15–18h | Agent 4: Translator — Gemini Flash, langdetect |
| 18–24h | Optional: Forecast Agent (Gemini Pro) — only if ahead of schedule |

### D4 — Frontend
| Hours | Task |
|---|---|
| 0–2h | Next.js setup, Tailwind, basic layout and routing |
| 2–6h | D3.js DriftTree component with static mock data |
| 6–10h | DiffPanel — facts added/dropped on node click |
| 10–14h | Wire to live API — POST /analyze, poll GET /story/{id} |
| 14–18h | Speechmatics voice input component |
| 18–24h | UI polish, loading states, error handling, mobile responsive |

---

## 25. Sync Points

| Hour | Name | Who | What Must Be True |
|---|---|---|---|
| **H4** | API Contract Lock | All 4 | D1 has published exact JSON shapes. Everyone codes against them. |
| **H10** | Pipeline End-to-End | D1+D2+D3 | A real URL runs through all 7 agents and returns a tree JSON. |
| **H16** | Frontend Integration | D1+D4 | D4 switches from mock to live API. Full stack working. |
| **H20** | Demo Run #1 | All 4 | Voice input → pipeline → tree → forecast. Fix top 3 issues. |
| **H23** | Code Freeze | All 4 | No more changes. Record video. Submit repo. Tag v1.0.0. |

**Rule:** If you're blocked for more than 30 minutes, message the group chat immediately. Do not go quiet.

---

## 26. Research Papers

| Feature | Paper | Link |
|---|---|---|
| Core idea — narrative drift gap | Fine-grained Narrative Classification in Biased News Articles (Dec 2025) | https://arxiv.org/pdf/2512.03582 |
| Comparable tool we extend | Media Bias Detector: Real-Time Framing Bias Analysis (Feb 2025) | https://arxiv.org/abs/2502.06009 |
| Geo-country divergence proof | Multilingual Similarity Dataset for News Article Frames | https://arxiv.org/abs/2405.13272 |
| Conflict framing by country | Beyond the Battlefield: Framing Analysis in Conflict Reporting (Jun 2026) | https://arxiv.org/abs/2506.10421 |
| Forecast feature basis | Forecasting Commodity Price Shocks Using Agentic AI (Jul 2025) | https://arxiv.org/abs/2508.06497 |
| Panic forecast vs evidence | The Verification Crisis: GenAI Disinformation (Feb 2026) | https://arxiv.org/abs/2602.02100 |

---

## 27. Why Not Claude or ChatGPT

Use this when judges ask.

| Capability | Claude / ChatGPT | StoryTrace |
|---|---|---|
| Memory across time | No — each session starts fresh. Cannot track how a story changed from Tuesday to Saturday. | Yes — persistent drift history in PostgreSQL. |
| Live data monitoring | No — knowledge cutoff. Cannot monitor today's outlets. | Yes — GDELT + RSS crawled live every cycle. |
| Cross-outlet drift graph | No — can summarize one article. Cannot compare 15 outlets and map mutation chain. | Yes — Git tree with full outlet attribution. |
| Geo-country comparison | No — cannot compare live coverage across Pakistan, Canada, Russia simultaneously. | Yes — branches by country, divergence visible. |
| Real-time drift alerts | No — passive, pull-only. | Yes — webhook fires when drift > 70. |
| Cached public research | No — every user regenerates the same analysis. | Yes — analyzed once, stored for everyone. |

---

*StoryTrace — The truth does not change. But the story does. We show you exactly how.*
