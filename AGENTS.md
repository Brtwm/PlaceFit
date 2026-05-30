# AGENTS.md — PlaceFit Agent Guide

## Project Summary

**PlaceFit** is a geoanalytics decision-support system for evaluating one
commercial location for a PVZ / ПВЗ pickup point.

Current status: **V1.1 stabilization complete**. The implemented demo path uses
FastAPI, deterministic backend services, PostgreSQL/PostGIS, fake/fallback
providers, optional real providers, optional LLM with fallback report, Streamlit
UI, map, checklist, Docker Compose, and saved analysis history.

Core principle: **AI explains, deterministic code decides.**

LLM must never calculate score, finance, confidence, or decision. It receives
prepared JSON and generates explanatory text only.

## Repo Layout

```text
app/                    FastAPI backend, services, providers, models, schemas
ui/                     Streamlit UI
tests/                  unit, integration, external provider tests
alembic/                DB migrations
docker/                 local Postgres init files
docs/                   product, architecture, roadmap, testing docs
docs/10_roadmap.md      active post-MVP roadmap
docs/13_*               historical MVP coding plan
```

`memory-bank/` may exist locally as working memory, but it is not public source
of truth.

## Start Here

Before changing product behavior or docs, read:

1. `README.md`
2. `docs/00_overview.md`
3. `docs/02_mvp_scope.md`
4. `docs/03_architecture.md`
5. `docs/05_api_contract.md`
6. `docs/06_scoring_model.md`
7. `docs/07_financial_model.md`
8. `docs/08_ai_report.md`
9. `docs/09_testing_strategy.md`
10. `docs/10_roadmap.md`

Use `docs/13_coding_plan_for_codex_mvp.md` only as historical context. Future
development should follow `docs/10_roadmap.md`.

## Local Run

Docker quickstart:

```bash
cp .env.example .env
docker compose up --build
```

Local backend:

```bash
uv sync --extra dev
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

Local UI:

```bash
uv run streamlit run ui/streamlit_app.py
```

URLs:

- Backend: <http://localhost:8000>
- API docs: <http://localhost:8000/docs>
- Health: <http://localhost:8000/health>
- Streamlit: <http://localhost:8501>

## Verification Commands

Use the narrowest relevant checks for small changes. For docs-only changes, run
at least `git status --short`, `git diff -- README.md docs AGENTS.md`, and a
consistency search for roadmap-sensitive terms.

Standard checks:

```bash
docker compose config
uv run pytest -v --tb=short
uv run ruff check .
uv run mypy app
```

External provider checks are manual only:

```bash
uv run pytest -m external
```

They require explicit environment variables and must not run in ordinary tests.

## Environment Variable Policy

- Copy `.env.example` to `.env` for local work.
- Keep real API keys out of git, docs, screenshots, fixtures, and Docker images.
- Real provider keys are optional.
- Default demo path must work with:
  - `GEOCODER_PROVIDER=fake`
  - `POI_PROVIDER=fake`
  - `LLM_ENABLED=false`
  - empty provider keys

## External Provider Policy

- External API integrations must stay behind provider/protocol abstractions.
- Ordinary tests must not call real network providers.
- Fake providers and fixtures are the default development path.
- Optional real provider code must degrade safely when keys are missing.
- Do not add scraping without a legal basis and a product decision.

## LLM Policy

- LLM receives only prepared analysis JSON.
- LLM has no DB, shell, external API, or secret access.
- LLM must not create facts, competitors, revenue forecasts, score,
  confidence, finance, or decision.
- If LLM is disabled, missing a key, or unavailable, fallback report returns a
  successful response with `report.status = "fallback"`.
- Top-level `LLM_FAILED` is allowed only if no report can be created at all.

## Product Constraints

- MVP / V1.0 supports only Krasnodar.
- MVP / V1.0 supports only `business_type = "pvz"`.
- MVP / V1.0 analyzes one address at a time.
- PlaceFit does not guarantee profit.
- `expected_gross_income_by_user` is a user hypothesis, not a forecast.
- Marketplace checks require manual verification from official sources.
- Marketplace requirements must not be presented as official compliance
  guarantees.

## Roadmap Discipline

Use `docs/10_roadmap.md` as the active future plan:

1. V1.1 stabilization complete; deferred 30-50 case manual benchmark remains
   future evidence work.
2. V1.2 compare mode.
3. V1.3 export/reporting polish.
4. V1.4 manual refresh and deltas for saved locations.
5. V1.5 scoring governance and marketplace rule maturity.
6. V2 city-wide PVZ-only intelligence.
7. V3 ML/B2B/multi-business platform after dataset/backtesting.

Do not pull V2/V3 ideas into V1.x unless the user explicitly asks and the scope
tradeoff is documented.

Telegram bot is not a product priority. It may be considered only as a thin
wrapper over a mature product if a real customer explicitly requests it.

## Do-Not Rules

- Do not add Telegram bot unless explicitly requested in a future task.
- Do not add ML before a dataset/backtesting plan exists.
- Do not add new business types before PVZ validation is complete.
- Do not make LLM part of decision logic.
- Do not call real external APIs in ordinary tests.
- Do not commit secrets or real API keys.
- Do not present marketplace checks as official compliance guarantees.
- Do not implement browser-agent or unsupported scraping.
- Do not add H3/city-wide code before V2 work is explicitly requested.
- Do not add auth/multi-user before V3 or a concrete product need.
- Do not rewrite Streamlit to React before limitations are proven.

## Definition of Done

For code changes:

- Behavior matches docs/API contracts.
- Relevant unit/integration tests pass.
- Deterministic code remains deterministic.
- External calls are mocked or marked `external`.
- No secrets are added.
- Docs/examples are updated when public behavior changes.

For documentation changes:

- README, overview, MVP scope, roadmap, testing strategy, and AGENTS agree.
- Old MVP plans are marked historical.
- Telegram remains deferred, not active roadmap.
- AI report is described as explanation layer only.
- Marketplace requirements remain manual-check/source-tracked, not guarantees.
