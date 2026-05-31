# V1.2-0 Baseline Audit

## Scope

This phase inspected the existing PlaceFit repository before V1.2 compare mode
feature work.

No compare behavior was implemented in this phase.

`POST /api/v1/analyze` remains backward compatible.

## Current API surface

Confirmed implemented routes from `app/main.py`, `app/api/v1/router.py`, and
`app/api/v1/endpoints/*`:

- `GET /health`
- `POST /api/v1/analyze`
- `GET /api/v1/locations`
- `GET /api/v1/locations/{location_id}`
- `POST /api/v1/geocode`
- `POST /api/v1/competitors/search`

Endpoints mentioned only as future or not implemented in public docs:

- `POST /api/v1/locations/compare` is listed in `docs/05_api_contract.md` as a
  V1.2 future endpoint. It does not exist today.
- `POST /api/v1/report/generate` is documented as not implemented in MVP/V1.0;
  report generation currently happens inside `POST /api/v1/analyze`.
- V1.3+ future endpoints are listed in `docs/05_api_contract.md`, including
  exports, saved-location refresh/deltas, scoring-version comparison, and V2
  heatmap work.

## Endpoint decision for V1.2 compare

V1.2 should keep the public-doc endpoint path:

`POST /api/v1/locations/compare`

Reason: the current routing structure already groups persisted location history
under `/locations`, and `docs/05_api_contract.md` publicly reserves
`POST /api/v1/locations/compare` for V1.2. The path fits the existing
`/api/v1` prefix plus endpoint-module pattern, and no current code structure
requires a different path.

No endpoint was implemented in this phase.

## Current schema surface

Relevant schemas discovered in `app/schemas/*`:

- `app/schemas/analysis.py`: `AnalysisRequest`, `AnalysisResponse`
- `app/schemas/location.py`: `LocationInfo`, `LocationsListItem`,
  `LocationsListRequest`, `LocationsListResponse`, `GeocodeRequest`,
  `GeocodeCandidate`, `GeocodeResponse`
- `app/schemas/competitor.py`: `CompetitorInfo`, `CompetitorsSummary`,
  `CompetitorsSearchRequest`, `CompetitorCounts`,
  `CompetitorsSearchResponse`
- `app/schemas/finance.py`: `FinanceResult`
- `app/schemas/score.py`: `ScoreDetails`, `ScoreResult`
- `app/schemas/report.py`: `MarketplaceRequirementResult`,
  `MarketplaceRequirements`, `ReportResult`, `DataSourceInfo`,
  `ReportGenerateRequest`
- `app/schemas/error.py`: error response schemas
- `app/schemas/common.py`: `AppBaseModel` and shared constrained primitives

`POST /api/v1/analyze` currently uses `AnalysisRequest` and returns
`AnalysisResponse`.

Schema conventions future compare schemas should follow:

- inherit from `AppBaseModel`, which uses `extra="forbid"`;
- use existing constrained primitive aliases where they fit, such as
  `ScoreValue`, `PositiveInt`, `PositiveFloat`, `Latitude`, and `Longitude`;
- compose existing response schema fragments instead of duplicating score,
  finance, competitor, report, or location field shapes.

No schemas were added or modified in this phase.

## Current analysis pipeline

`app/services/analysis.py` contains the single-address orchestration in
`AnalysisService.analyze()`:

1. Geocode the submitted address through `GeocodingService`.
2. Resolve exactly one geocoding candidate or raise domain errors for ambiguous,
   unsupported-city, or failed geocoding results.
3. Search competitors through the configured POI provider boundary.
4. Calculate deterministic score with `calculate_score()`.
5. Calculate deterministic confidence with `calculate_confidence()`.
6. Calculate deterministic finance with `calculate_finance()`.
7. Calculate deterministic decision with `make_decision()`.
8. Load the active scoring version.
9. Build checklist and manual marketplace requirements.
10. Build prepared report input and call `ReportService`.
11. Persist the location, POIs, location-POI distances, score, financial model,
    and report.
12. Commit and return `AnalysisResponse`.

Provider boundaries:

- geocoding is behind `GeocodingService` and geocoder providers;
- competitor lookup is behind POI search providers and
  `app/services/competitors.py`;
- report generation is behind `ReportService` and LLM/fallback providers.

Deterministic boundaries:

- score, confidence, finance, and final decision are calculated before report
  generation;
- report/LLM receives prepared analysis JSON after deterministic calculations;
- report/LLM must not calculate score, confidence, finance, ranking, or final
  decision.

Future compare mode must preserve this separation. It should reuse the
single-address deterministic pipeline and derive any ranking deterministically
from visible analysis fields.

No analysis code was refactored in this phase.

## Current persistence model

Current SQLAlchemy models in `app/models/*`:

- `Location`
- `Poi`
- `ScoringVersion`
- `LocationPoiDistance`
- `Score`
- `FinancialModel`
- `Report`
- `MarketplaceRequirement`

Current DB tables implied by models and `alembic/versions/0001_create_mvp_schema.py`:

- `locations`
- `pois`
- `scoring_versions`
- `location_poi_distances`
- `scores`
- `financial_models`
- `reports`
- `marketplace_requirements`

Current analysis persistence:

- `locations` stores the analyzed address, normalized/geocoded location,
  business type, premises fields, geocoding metadata, and timestamps;
- `pois` stores provider POIs/competitors, keyed by source and external ID;
- `location_poi_distances` stores cached distances from one location to each
  persisted POI;
- `scores` stores deterministic component scores, total score, confidence,
  decision, details JSON, and scoring version reference;
- `financial_models` stores deterministic financial inputs and outputs;
- `reports` stores generated fallback or LLM report text/JSON and provider
  metadata;
- `scoring_versions` stores active versioned deterministic scoring rules;
- `marketplace_requirements` stores manual-check-only marketplace reference
  rows.

There is currently no compare-session model or compare-session table.

No migrations were created or modified in this phase.

## Current Streamlit UI structure

Current Streamlit entrypoint and pages:

- `ui/streamlit_app.py`: main page and backend health/quick-start summary.
- `ui/pages/analyze.py`: single-address analysis form that posts to
  `POST /api/v1/analyze` through `ApiClient.analyze()`.
- `ui/pages/history.py`: saved analysis history list with filters using
  `ApiClient.list_locations()`.
- `ui/pages/detail.py`: saved analysis detail view using
  `ApiClient.get_location()`.

`ui/api_client.py` currently supports:

- `health()`
- `analyze()`
- `list_locations()`
- `get_location()`

No compare page exists today, and no compare API client method exists today.

Future compare UI work should respect the current Streamlit structure: pages are
small route modules, API access is centralized in `ui/api_client.py`, and the UI
does not compute backend-owned score, finance, confidence, decision, or ranking.

No UI files were added or modified in this phase.

## Current test structure and commands

Relevant unit test areas:

- scoring, confidence, finance, and decision determinism;
- geocoding and POI provider parsing/factories;
- competitor search and deduplication;
- report fallback and OpenAI-compatible provider behavior;
- public schema validation and rejection of extra fields;
- settings, packaging, import hygiene, and cache behavior.

Relevant integration test areas:

- `POST /api/v1/analyze` success, persistence, validation, geocoding errors, and
  network-call blocking in mocked tests;
- `GET /health`;
- `GET /api/v1/locations` and `GET /api/v1/locations/{location_id}`;
- Alembic migration/table/scoring-version checks.

Ordinary tests use fake providers, fixtures, mocks, and dependency overrides.
External provider tests are marked `external` and excluded by default through
`pyproject.toml`:

```toml
addopts = "-m 'not external'"
```

Commands run in this phase:

| Command | Result |
|---|---|
| `git status --short` | `M .gitignore` before this audit note; `.gitignore` already contained the local-only `roadmap.md` ignore rule. |
| `rg -n "compare\|locations/compare\|roadmap.md" README.md docs app tests ui` | Found V1.2/public roadmap references; `POST /api/v1/locations/compare` appears only in docs as a future endpoint. |
| `uv run ruff check .` | Passed: `All checks passed!` |
| `uv run pytest -v --tb=short` | Passed: `136 passed, 3 deselected, 2 warnings`. The 3 deselected tests are external-provider tests. |
| `uv run mypy app` | Passed: `Success: no issues found in 65 source files`. |

## Public documentation consistency

`README.md` links users to `docs/10_roadmap.md`, not to the ignored root
`roadmap.md`.

The repository search found `roadmap.md` references in docs, including
historical/reference contexts, but no public README link points users to the
ignored root `roadmap.md`.

The public roadmap source of truth remains `docs/10_roadmap.md`.

The root `roadmap.md` remains local-only and ignored by `.gitignore`.

No public documentation consistency fix was needed in this phase.

## Constraints for future V1.2 phases

- Do not break `POST /api/v1/analyze`.
- Compare mode should reuse the existing deterministic single-address analysis
  pipeline.
- Compare ranking must be deterministic and explainable from visible fields.
- LLM output must not decide ranking.
- LLM output must not calculate score, confidence, finance, or final decision.
- Ordinary tests must not require real external provider calls.
- No DB persistence for compare should be assumed until explicitly implemented.
- No Streamlit compare page exists until implemented in a later phase.
- No compare schema/service/endpoint exists until implemented in a later phase.
- Root `roadmap.md` remains local-only and ignored.
- The broader 30-50 case manual benchmark remains deferred unless future repo
  evidence proves it complete.

## Open questions

- Should V1.2-1 compare accept only newly entered candidate payloads, only saved
  `location_id` values, or both?
- Should V1.2 ranking prioritize total score first, decision first, confidence
  first, finance first, or a documented deterministic composite?
- Should compare sessions be persisted in V1.2 initial implementation, or should
  persistence be deferred behind a separate migration phase?
- Should compare reports include an LLM/fallback explanatory summary, or should
  V1.2 initially return deterministic comparison data only?
- Should export comparison summary remain in V1.2 scope or move to V1.3 to match
  the export/reporting roadmap?

## Phase V1.2-0 verdict

Phase V1.2-0 is complete.

V1.2 feature implementation may proceed to V1.2-1.

No blockers were found. The only pre-existing dirty worktree item observed was
the `.gitignore` update that keeps root `roadmap.md` local-only.
