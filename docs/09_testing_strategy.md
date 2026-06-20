# Testing Strategy — PlaceFit

## Principles

- Deterministic code is tested directly.
- Ordinary tests must not call real external APIs.
- LLM is optional; fallback report is first-class successful behavior.
- Post-MVP validation is required before scope expansion.
- Manual validation findings should update docs and known limitations before
  new roadmap features are started.

## Automated Tests

### Unit tests

Core modules:

```text
scoring.py
finance.py
decision.py
confidence.py
deduplication.py
geocoding parser
provider factories
report fallback / OpenAI-compatible wrapper
schemas
settings
```

Expected coverage themes:

- Score stays in 0-100.
- Same input produces the same output.
- Finance formulas are stable.
- Decision thresholds are deterministic.
- Confidence reflects source count, freshness, manual inputs, competitors, and
  finance assumptions.
- Deduplication removes same external IDs and close same-brand duplicates.
- `business_type` is limited to `pvz`.
- Marketplace statuses reject automatic `passed` / `failed` in MVP.

V1.2 compare schema contract coverage:

- Compare request accepts 2, 3, 4, and 5 candidates.
- Compare request rejects 0, 1, and 6 candidates.
- Compare response validates all-success, all-failed, and mixed outcomes.
- Ranking metadata is present, deterministic, and has `uses_llm = false`.
- Ordinary compare schema tests do not call real external providers.

V1.2 compare persistence coverage:

- Compare session migration creates `compare_sessions`.
- Compare ORM model is imported into SQLAlchemy metadata.
- Successful compare runs persist request and response snapshots.
- Returned `compare_id` matches the saved `compare_sessions.id`.
- Failed candidate errors and suggestions are preserved in the stored snapshot.
- Loading a saved compare session returns the original public response snapshot
  without rerunning analysis, providers, scoring, finance, report generation, or
  ranking.

V1.3 export regression coverage:

- `tests/unit/test_analysis_export.py` covers deterministic single-analysis
  Markdown from `AnalysisResponse`, stable section and row ordering, Markdown
  escaping, nullable values, user-hypothesis labeling, existing fallback report
  preservation, disclaimers, and marketplace manual-verification wording.
- `tests/unit/test_compare_export.py` covers deterministic compare Markdown from
  `CompareResponse`, snapshot ordering without reranking, failed-candidate
  visibility, ambiguous-address suggestions, escaping, nullable values,
  assumptions, warnings, and `ranking_rules.uses_llm = false`.
- `tests/unit/test_export_boundary.py` enforces the service-only boundary: no
  public export endpoints/router, no UI API-client export methods, and no public
  API contract claim for specific export endpoints.
- `tests/unit/test_ui_export_controls.py` verifies schema-first snapshot
  validation, stable Markdown download labels/filenames/MIME, visible caveats,
  safe invalid-snapshot handling, and absence of CSV, Excel, or PDF controls.
- Export tests are pure unit tests over response-shaped fixtures/snapshots. They
  must not call providers, network, DB, HTTP, filesystem reads, geocoding, POI
  search, analysis, scoring, finance, confidence, decision, report/fallback
  generation, LLM, saved-session loading, or compare ranking.

V1.3 final export acceptance evidence is recorded in
[`validation/v1.3_export_validation.md`](validation/v1.3_export_validation.md).
Renderer-level artifacts for good, weak/risky, two-candidate, five-candidate,
and partial-failure scenarios passed fixture-to-Markdown inspection. The owner
also completed Docker, Streamlit download, and external-file opening checks for
the required scenarios. Final V1.3 acceptance is `PASS`.

V1.2 UI API client coverage:

- Streamlit API client posts compare payloads to
  `POST /api/v1/locations/compare`.
- Streamlit API client loads saved compare sessions from
  `GET /api/v1/locations/compare/{compare_id}`.
- UI client tests preserve normalized API errors without real HTTP calls.

### Integration tests

Implemented MVP endpoints:

```text
GET  /health
POST /api/v1/analyze
GET  /api/v1/locations
GET  /api/v1/locations/{id}
POST /api/v1/geocode
POST /api/v1/competitors/search
POST /api/v1/locations/compare
```

Important scenarios:

- Successful analysis returns full response.
- Analysis is saved to DB with `scoring_version_id`.
- History and detail endpoints return saved analysis data.
- Ambiguous address returns suggestions.
- Non-Krasnodar address is rejected.
- LLM disabled or unavailable returns HTTP 200 with `report.status = "fallback"`.
- Top-level `LLM_FAILED` is allowed only if no report can be created.
- Compare endpoint accepts 2-5 candidates, rejects invalid counts with HTTP 422,
  returns candidate-level failures with HTTP 200 when compare can represent
  them, and exposes deterministic ranking metadata with `uses_llm = false`.
- Compare endpoint persists saved sessions with full request/response snapshots,
  and `GET /api/v1/locations/compare/{compare_id}` returns the stored snapshot
  without real provider calls or recalculation.
- Compare endpoint preserves ambiguous candidate suggestions per failed
  candidate.
- Ordinary integration tests do not make network calls.

### Streamlit manual smoke checks

Manual UI smoke checks should verify the compare page can submit 2-5 newly
entered candidates, show ranked successful candidates, show failed candidates,
render the successful-candidate map, and offer Markdown download after a
successful compare response.

For V1.2, the local compare-mode Streamlit flow was manually reviewed by the
owner after release hardening and accepted as working.

### Mock and external provider strategy

External APIs and LLM providers are mocked or replaced by deterministic fakes in
ordinary tests:

- fake geocoder / fake POI provider;
- fixture-shaped 2GIS/Yandex/OSM responses;
- OpenAI-compatible mock responses;
- fallback report provider.

Real provider checks are manual/external only:

```bash
uv run pytest -m external
```

They require explicit environment variables such as
`RUN_EXTERNAL_PROVIDER_TESTS=true` and provider keys where applicable. They are
excluded from ordinary `uv run pytest -v --tb=short` runs by the `external`
marker in `pyproject.toml` and must not be treated as required local gates
unless intentionally enabled.

## V1.1 Manual Validation Strategy

V1.1 turned manual validation into a first-class activity. The owner
subsequently completed 45 manual validation cases and reported all checks as
`PASS`. This satisfies the original 30-50 case target. Detailed case sheets are
not committed, so the repository records this as owner-confirmed aggregate
evidence rather than inventing per-case results.

### Address selection

Use a balanced set:

- Dense residential area.
- Weak location.
- High-competition area.
- Low-competition area.
- Ambiguous geocoding case.
- Edge cases near Krasnodar city boundary.
- Good demo address.
- Medium/ordinary address.
- Bad address.
- Controversial address where score and manual intuition may disagree.

### What to check

For each case, verify:

- Coordinates and normalized address.
- City validation.
- Competitor count.
- Deduplication.
- Radius buckets: 300/500/700 m.
- Nearest and average competitor distance.
- Score components.
- Confidence score and data source explanation.
- Finance assumptions and user-entered income hypothesis.
- Decision wording.
- AI/fallback report hallucination risk.
- Marketplace requirement wording remains `needs_manual_check`.
- Streamlit map location marker.
- Streamlit map competitor markers and popups when coordinates exist.
- Checklist relevance.

### How to record results

Use [manual validation case template](templates/manual_validation_case.md) or an
equivalent table with these fields:

| Field | Purpose |
|---|---|
| address | Input address |
| case_type | Good / medium / weak / controversial / ambiguous / boundary |
| expected_notes | Manual expectation before running PlaceFit |
| automated_result | Score, confidence, decision, finance summary |
| competitor_manual_check | Map/manual notes |
| deduplication_notes | Duplicates found or missed |
| report_notes | Hallucination, overclaim, missing caveat |
| ui_map_notes | Marker/popup issues |
| issue_severity | none / low / medium / high |
| follow_up_action | Docs, test, bugfix, or accepted limitation |

### Acceptance for V1.1 validation

- The owner-confirmed benchmark contains 45 completed manual cases, all
  reported as `PASS`.
- At least five cases cover edge/ambiguous/boundary behavior.
- Manual competitor checks, mismatch notes, and verdicts are recorded; seed or
  pending rows do not count as completed validation cases.
- Known limitations are listed in docs.
- Any high-severity issue has a follow-up task.
- README quickstart still works from fresh clone.
- Ordinary automated tests pass.

## AI Report Validation

Report checks must confirm:

- Required report sections exist.
- Report uses only prepared analysis JSON.
- Report does not invent competitors, traffic, revenue, or compliance status.
- Report states that PlaceFit does not guarantee profit.
- Fallback report remains deterministic and useful.

## Commands

```bash
# Unit tests
uv run pytest tests/unit/ -v

# Integration tests
uv run pytest tests/integration/ -v

# All ordinary tests, excluding external provider tests
uv run pytest -v --tb=short

# Lint and typing
uv run ruff check .
uv run mypy app

# Compose config
docker compose config

# Manual external provider checks only
uv run pytest -m external
```

`uv run pytest -m external` is optional/manual external-provider evidence. It is
not part of ordinary automated gates unless external provider checks are
intentionally enabled for that run.
