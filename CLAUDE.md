# Broadcast Revenue Intelligence — Agentic Layer

## Project Purpose
Build an agentic intelligence layer for a broadcast TV client that sits on top of their
WideOrbit (WO Traffic) data to deliver revenue intelligence, operational insights,
and proactive alerting. This is a single-broadcaster engagement using the client's
own WideOrbit data under their existing API agreement.

## Domain Context
WideOrbit WO Traffic is the industry-standard ad traffic and billing system
for broadcast television. Key data entities include:
- **Orders**: Ad buy contracts from agencies/advertisers
- **Spots**: Individual scheduled commercial placements
- **Inventory**: Available ad slots by daypart, program, station
- **Makegoods**: Replacement spots for preempted/missed airings
- **AUR**: Average Unit Rate — key pricing metric by daypart
- **Pacing**: Sell-out rate tracking against available inventory

## Tech Stack
- Python 3.11+ (pandas, polars for data processing)
- Claude API for agent reasoning layer
- FastAPI for API layer
- React + Vite + Tailwind for dashboard frontend

## Key Constraints
- **Read-only** access to WideOrbit data — we never write back to WO Traffic
- All data stays in the client's infrastructure
- Agents are **advisory** — all recommendations require human approval
- Client data is **confidential** — never committed to repo
- `data/raw/` and `data/processed/` are gitignored

## Directory Guide
```
CowlesProject/
├── data/
│   ├── raw/             # GITIGNORED. WideOrbit exports, never modify
│   ├── schemas/         # WO field definitions, normalization mappings
│   ├── sample/          # Anonymized data safe for development and testing
│   └── processed/       # GITIGNORED. Cleaned/normalized output tables
├── pipeline/
│   ├── ingest/          # ETL from WO exports → raw tables
│   └── normalize/       # Raw → clean, typed, deduplicated tables
├── agents/
│   └── revenue_intelligence/   # First agent: revenue analysis
│       ├── spec.md             # Agent specification
│       ├── run.py              # Entry point
│       ├── prompts/            # Claude API prompt templates
│       └── tools/              # Tool definitions the agent can use
├── backend/             # FastAPI API layer
├── frontend/            # React dashboard
├── deliverables/        # Client-facing reports and presentations
├── docs/                # Specs, data dictionary, architecture decisions
└── tests/               # Test suite
```

## Workflow Rules
- Feature branch per agent (e.g., `agent/revenue-intelligence`)
- **Never commit real client data**
- All agents must have a spec in `docs/agent-specs.md` before coding
- Test with sample data in `data/sample/`, validate with real data in client env

## Commands
```bash
# Backend
cd backend && pip install -r requirements.txt && python main.py

# Frontend
cd frontend && npm install && npm run dev

# Pipeline
python pipeline/ingest/run.py              # Run data ingestion
python pipeline/normalize/run.py           # Normalize ingested data

# Agents
python agents/revenue_intelligence/run.py --sample   # Test with sample data

# Tests
python -m pytest tests/
```

## Things to NEVER Do
| Action | Reason |
|--------|--------|
| Commit files from `data/raw/` | Contains confidential client WideOrbit data |
| Write back to WO Traffic | Read-only access agreement |
| Auto-execute agent recommendations | All actions require human approval |
| Hard-code station/market names | Should come from config or data |
| Skip agent spec before coding | Spec-first workflow prevents scope creep |
