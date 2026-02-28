# AI Hunter

> **Autonomous B2B Lead Generation powered by LangGraph multi-agent pipelines**

AI Hunter is an open-source system that automatically discovers potential B2B buyers and distributors for your products. Provide your company website (or upload product documents) plus target regions — the system handles everything: deep company analysis, keyword generation, multi-channel search, lead extraction, contact discovery, and personalised outreach email drafting in the prospect's native language.

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-green)](https://github.com/langchain-ai/langgraph)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-red)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-blue)](https://react.dev)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-443%20passing-brightgreen)](https://github.com/your-org/ai-hunter)

[中文文档](README_CN.md)

## ✨ Features

- **Dual-model ReAct architecture** — reasoning model (e.g. `gpt-4o`) drives multi-step tool-use in InsightAgent and LeadExtractAgent; fast model (e.g. `gpt-4o-mini`) handles extraction, keyword gen, and email drafting
- **5 specialised agents** — Insight → KeywordGen → Search → LeadExtract → EmailCraft
- **Flexible input** — company website URL, uploaded files (PDF / Excel), or just product keywords
- **Adaptive hunting loop** — per-keyword effectiveness feedback drives iterative keyword refinement until the target lead count is reached or diminishing returns detected
- **Multi-channel search** — Google Search + Google Maps + 9 major B2B platform site-searches (Alibaba, Made-in-China, Global Sources, etc.)
- **Smart scraping** — ReAct agent adapts strategy per URL type: company site / B2B listing / LinkedIn / content page
- **Multi-LLM support** — unified via [litellm](https://github.com/BerriAI/litellm): OpenAI, Anthropic, OpenRouter, Groq, Zhipu (GLM), Moonshot (Kimi), MiniMax
- **Multi-search backend** — Serper (Google) → Brave → Tavily fallback chain
- **Multilingual emails with ReAct validation** — drafts, validates (language / formality / salutation / grammar), and revises 3-email sequences in 14+ languages
- **Real-time SSE streaming** — live pipeline progress with per-stage expandable detail panels
- **Cost tracking** — [Langfuse](https://langfuse.com) integration via litellm callbacks: token usage, cost, latency per LLM call
- **Email verification** — MX-record check removes undeliverable addresses
- **443 tests** — comprehensive unit + integration test suite

## Architecture

```text
Input: website URL / uploaded files (PDF, Excel) / product keywords + target regions
    │
    ▼
┌─────────────────────── LangGraph StateGraph ───────────────────────────┐
│                                                                         │
│  InsightAgent  [ReAct · reasoning_model]  (first round only)           │
│  ├── scrape_page       → homepage + key subpages (max 4 pages)         │
│  ├── read_uploaded_file → PDF / Excel documents                        │
│  └── search_web        → market context                                │
│       │                                                                 │
│       ▼                                                                 │
│  ┌──── Hunting Loop ────────────────────────────────────────────────┐  │
│  │  KeywordGenAgent  [llm_model]                                    │  │
│  │      │  5-8 keywords/round, guided by per-keyword feedback       │  │
│  │      ▼                                                           │  │
│  │  SearchAgent  [concurrent · Serper/Brave/Tavily + Maps + B2B]   │  │
│  │      │  asyncio.Semaphore(search_concurrency)                    │  │
│  │      ▼                                                           │  │
│  │  LeadExtractAgent  [ReAct · reasoning_model · concurrent]       │  │
│  │  ├── scrape_page       (extract emails/phones/social)            │  │
│  │  ├── google_search     (find official website)                   │  │
│  │  └── extract_lead_info (structured JSON extraction)              │  │
│  │      │                                                           │  │
│  │      ▼                                                           │  │
│  │  Evaluate  (per-keyword feedback · stop conditions)              │  │
│  │      │  not done → loop back with keyword feedback               │  │
│  │      └──────────────────────────────────────────────────────────┘  │
│       │  done: target reached / max rounds / diminishing returns       │
│       ▼                                                                 │
│  EmailCraftAgent  [ReAct · llm_model · concurrent]  (optional)        │
│  ├── Draft 3 emails in target locale language                          │
│  ├── validate_emails  (language · formality · salutation · grammar)    │
│  └── Revise based on feedback  (max 2 revision rounds)                 │
└─────────────────────────────────────────────────────────────────────────┘
    │
    ▼
FastAPI + SSE streaming → React frontend (live progress + expandable stage panels)
```

### Agent Model Assignment

| Agent | Model | Mode | Purpose |
|-------|-------|------|---------|
| InsightAgent | `reasoning_model` | ReAct multi-tool | Deep company/product analysis |
| KeywordGenAgent | `llm_model` | Single LLM call | Keyword generation with feedback |
| SearchAgent | — | Concurrent async | Google + Maps + B2B platform search |
| LeadExtractAgent (decisions) | `reasoning_model` | ReAct multi-tool | Scrape strategy + lead qualification |
| LeadExtractAgent (extraction) | `llm_model` | Single LLM call | Structured data extraction |
| EmailCraftAgent | `reasoning_model` | ReAct + validate | Draft → validate → revise emails |

## Project Structure

```text
ai_hunter/
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── backend/
│   ├── .env.example             # Environment variable template
│   ├── requirements.txt
│   ├── config/
│   │   └── settings.py          # pydantic-settings (dual-model + concurrency + Langfuse)
│   ├── graph/
│   │   ├── builder.py           # LangGraph StateGraph assembly
│   │   ├── state.py             # HuntState TypedDict
│   │   └── evaluate.py          # Loop evaluation + per-keyword feedback + stop conditions
│   ├── agents/
│   │   ├── insight_agent.py     # Company/product analysis (ReAct)
│   │   ├── keyword_gen_agent.py # Keyword generation with feedback loop
│   │   ├── search_agent.py      # Concurrent search (Google + Maps + B2B platforms)
│   │   ├── lead_extract_agent.py# Lead extraction (ReAct, concurrent, MX email verify)
│   │   └── email_craft_agent.py # Multilingual email generation (ReAct + validate)
│   ├── tools/
│   │   ├── llm_client.py        # Unified LLM client (litellm, dual-model)
│   │   ├── react_runner.py      # Lightweight ReAct loop engine
│   │   ├── llm_output.py        # LLM output validation (JSON parse + field check)
│   │   ├── google_search.py     # Google Search via Serper API
│   │   ├── brave_search.py      # Brave Search API (fallback)
│   │   ├── tavily_search.py     # Tavily Search API (fallback)
│   │   ├── google_maps_search.py# Google Maps Search via Serper
│   │   ├── amap_search.py       # Amap (高德) for China region searches
│   │   ├── jina_reader.py       # Web scraping via Jina Reader
│   │   ├── platform_registry.py # B2B platform registry (9 platforms)
│   │   ├── contact_extractor.py # Regex-based email/phone/social extraction
│   │   ├── email_finder.py      # Email discovery (Hunter.io + regex)
│   │   ├── email_verifier.py    # Email validation (MX record check)
│   │   ├── pdf_parser.py        # PDF parsing (pymupdf4llm)
│   │   ├── excel_parser.py      # Excel parsing (pandas)
│   │   └── url_filter.py        # URL classification and filtering
│   ├── api/
│   │   ├── app.py               # FastAPI app entry + Langfuse init
│   │   ├── routes.py            # REST routes + SSE stage-data broadcasting
│   │   └── hunt_store.py        # Hunt persistence (JSON files)
│   ├── observability/
│   │   └── setup.py             # Langfuse integration via litellm callback
│   └── tests/                   # 443 tests
└── frontend/
    ├── package.json             # Bun / npm
    ├── vite.config.ts
    └── src/
        ├── api/client.ts        # API client + TypeScript types
        └── routes/
            ├── dashboard.tsx    # Hunt list dashboard
            ├── new-hunt.tsx     # Create hunt form
            └── hunt-detail.tsx  # Live pipeline + expandable stage panels
```

## Quick Start

### Prerequisites

- **Python 3.11 or 3.12** (3.10 and below are **not** supported — requires `match` statements and modern typing)
  - Check: `python3 --version`
  - Install via [pyenv](https://github.com/pyenv/pyenv): `pyenv install 3.12.4 && pyenv local 3.12.4`
- **Node.js >= 18** or [Bun](https://bun.sh) >= 1.0 (for the frontend)
  - Check: `node --version` or `bun --version`
- At least one LLM provider API key (OpenAI recommended for first run)
- At least one search API key (Serper recommended)

### 1. Clone

```bash
git clone https://github.com/your-org/ai-hunter.git
cd ai-hunter
```

### 2. Backend setup

```bash
cd backend

# Create and activate a virtual environment (Python 3.11+)
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate.bat    # Windows CMD
# .venv\Scripts\Activate.ps1    # Windows PowerShell

# Install all dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Copy environment template and fill in your API keys
cp .env.example .env
```

Minimum required keys in `.env`:

```bash
# LLM — fast model (extraction, keywords, email)
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-xxx

# LLM — reasoning model (ReAct agent decisions)
REASONING_MODEL=gpt-4o

# Search (at least one required; priority: Serper > Brave > Tavily)
SERPER_API_KEY=xxx

# Web scraping (recommended)
JINA_API_KEY=xxx

# Email discovery (optional)
HUNTER_API_KEY=xxx
```

#### Supported LLM providers

| Provider | Model format | Env var |
| -------- | ------------ | ------- |
| OpenAI | `gpt-4o` / `gpt-4o-mini` | `OPENAI_API_KEY` |
| Anthropic | `anthropic/claude-3-5-sonnet-20241022` | `ANTHROPIC_API_KEY` |
| OpenRouter | `openrouter/google/gemini-2.5-flash` | `OPENROUTER_API_KEY` |
| Groq | `groq/llama-3.3-70b-versatile` | `GROQ_API_KEY` |
| Zhipu Z.AI | `zai/glm-4.7` | `ZAI_API_KEY` |
| Moonshot (Kimi) | `moonshot/moonshot-v1-128k` | `MOONSHOT_API_KEY` |
| MiniMax | `minimax/MiniMax-Text-01` | `MINIMAX_API_KEY` |

> `LLM_MODEL` and `REASONING_MODEL` can use different providers, e.g. `LLM_MODEL=groq/llama-3.3-70b-versatile` + `REASONING_MODEL=gpt-4o`.

### 3. Start the backend

```bash
cd backend
source .venv/bin/activate   # if not already activated
uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### 4. Start the frontend

```bash
cd frontend
bun install && bun dev    # or: npm install && npm run dev
```

Frontend: [http://localhost:3000](http://localhost:3000) — proxies `/api` to the backend.

### 5. Verify

```bash
curl http://localhost:8000/api/v1/health
# {"status":"ok","service":"ai-hunter"}
```

> **Troubleshooting**: If you see `ModuleNotFoundError`, ensure the virtual environment is activated (`source backend/.venv/bin/activate`) and dependencies installed (`pip install -r backend/requirements.txt`).

## Cost Tracking — Langfuse Observability

AI Hunter automatically tracks every LLM call via the **litellm → Langfuse callback**:

- Token usage (prompt / completion / total)
- Cost in USD (calculated by litellm from model pricing)
- Latency per call
- Full input/output messages

### Option A: Langfuse Cloud (recommended, free tier)

1. Sign up at [https://cloud.langfuse.com](https://cloud.langfuse.com) (free: 50k observations/month)
2. Create a project and copy your **Public Key** and **Secret Key**
3. Add to `.env`:

```bash
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_HOST=https://cloud.langfuse.com
```

4. Restart the backend and run a hunt.
5. Open your Langfuse project → **Traces** to see all LLM calls. <!-- markdownlint-disable-line MD029 -->

**What you can see in Langfuse:**

- **Traces** — full call chain per hunt
- **Generations** — per-LLM-call detail: input, output, tokens, cost
- **Dashboard** — total cost, token trend, model distribution, latency stats

### Option B: Self-hosted Langfuse

```bash
# One-command Docker deploy (see https://langfuse.com/docs/deployment/self-host)
docker compose up -d

LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_HOST=http://localhost:3001   # avoid conflict with frontend on 3000
```

## API Reference

| Method | Path | Description |
| ------ | ---- | ----------- |
| `POST` | `/api/v1/hunts` | Start a new hunt pipeline |
| `GET` | `/api/v1/hunts` | List all hunts |
| `GET` | `/api/v1/hunts/{id}/status` | Poll hunt status |
| `GET` | `/api/v1/hunts/{id}/result` | Get full result (insight, leads, emails, keyword_search_stats) |
| `GET` | `/api/v1/hunts/{id}/stream` | SSE stream: live progress + per-stage detail events |
| `GET` | `/api/v1/health` | Health check |

### Create a hunt

```bash
curl -X POST http://localhost:8000/api/v1/hunts \
  -H "Content-Type: application/json" \
  -d '{
    "website_url": "https://your-company.com",
    "product_keywords": ["solar inverter", "PV module"],
    "target_regions": ["Europe", "Eastern Europe"],
    "target_lead_count": 100,
    "max_rounds": 5,
    "enable_email_craft": true
  }'
# Returns: {"hunt_id": "...", "status": "pending"}
```

You can omit `website_url` and upload PDF/Excel files instead — InsightAgent will extract company info from the documents.

### SSE event types

| Event | Payload | When |
| ----- | ------- | ---- |
| `stage_change` | `{stage, hunt_round, leads_count}` | Each pipeline stage transition |
| `stage_data` | Stage-specific detail data | After each stage completes |
| `lead_progress` | `{url, status, lead}` | Per-URL extraction progress |
| `round_change` | `{hunt_round}` | Each new hunting round |
| `progress` | `{leads_count, stage, hunt_round}` | Periodic progress update |
| `completed` | `{leads_count, email_sequences_count}` | Hunt finished |
| `failed` | `{error}` | Hunt errored |

## Frontend

- **Dashboard** — hunt list with status, round count, lead count, created time
- **New Hunt** — form: website URL / file upload + keywords + target regions
- **Hunt Detail** — live pipeline progress bar; each stage is **clickable to expand**:
  - **Analyzing Company** → insight result (company name, products, ICP, recommended keywords)
  - **Generating Keywords** → keyword list per round
  - **Searching Web** → result count + per-keyword effectiveness table (results / leads / rating)
  - **Evaluating Progress** → new leads per round, best/worst keywords
  - **Crafting Emails** → generated email sequence count
- **Leads table** — company info, contacts, match score; CSV export
- **Email sequences** — view personalised outreach emails per lead

## Running Tests

```bash
cd backend

# Run all 443 tests
python -m pytest tests/ -v

# By module
python -m pytest tests/test_tools/ -v          # tool layer
python -m pytest tests/test_agents/ -v         # agent layer
python -m pytest tests/test_evaluate.py -v     # evaluation logic

# With coverage
python -m pytest tests/ --cov=. --cov-report=term-missing
```

## Configuration Reference

All settings can be overridden via `.env` or environment variables:

| Setting | Default | Description |
| ------- | ------- | ----------- |
| `LLM_MODEL` | `gpt-4o-mini` | Fast model (extraction, keywords, email) |
| `REASONING_MODEL` | `gpt-4o` | Reasoning model (ReAct decisions) |
| `LLM_TEMPERATURE` | `0.3` | Fast model temperature |
| `REASONING_TEMPERATURE` | `0.2` | Reasoning model temperature |
| `REACT_MAX_ITERATIONS` | `5` | Max ReAct loop iterations per agent call |
| `DEFAULT_TARGET_LEAD_COUNT` | `200` | Default target lead count |
| `DEFAULT_MAX_ROUNDS` | `10` | Default max hunting rounds |
| `DEFAULT_KEYWORDS_PER_ROUND` | `8` | Keywords generated per round |
| `MIN_NEW_LEADS_THRESHOLD` | `5` | Stop if fewer new leads than this per round |
| `SEARCH_CONCURRENCY` | `10` | Max concurrent search API calls |
| `SCRAPE_CONCURRENCY` | `5` | Max concurrent Jina Reader calls |
| `EMAIL_GEN_CONCURRENCY` | `3` | Max concurrent email generation calls |
| `LANGFUSE_ENABLED` | `false` | Enable Langfuse cost tracking |
| `LANGFUSE_HOST` | `http://localhost:3000` | Langfuse server URL |
| `HUNTS_DIR` | `data/hunts` | Directory for JSON hunt persistence |
| `UPLOAD_DIR` | `uploads` | File upload directory |
| `MAX_UPLOAD_SIZE_MB` | `50` | Max upload file size |

## Tech Stack

### Backend

- Python 3.11+ · FastAPI · Uvicorn
- LangGraph — multi-agent state graph orchestration
- litellm — unified multi-provider LLM client + Langfuse callback
- httpx — async HTTP client
- pydantic-settings — type-safe configuration
- pymupdf4llm · pandas — document parsing

### Frontend

- Vite · React 18 · TypeScript
- TanStack Router — type-safe routing
- TanStack Query — data fetching and caching
- Tailwind CSS 3 — utility-first styling
- shadcn/ui — component library
- Lucide React — icons

## Roadmap / TODO

- [ ] **EmailCraftAgent ReAct** — full validate→revise loop with per-language grammar LLM check *(in progress)*
- [ ] **Docker Compose** — one-command full-stack deployment
- [ ] **Authentication** — API key or OAuth for multi-user deployments
- [ ] **Lead deduplication** — cross-hunt dedup by domain/email
- [ ] **Export formats** — Excel / HubSpot CSV / Salesforce CSV
- [ ] **Webhook support** — push results to external CRMs on completion
- [ ] **Rate limit handling** — automatic backoff + retry for search APIs

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
# Run tests before submitting a PR
cd backend && python -m pytest tests/ -q
```

## License

MIT — see [LICENSE](LICENSE) for details.
