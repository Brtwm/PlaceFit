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

### Integration tests

Implemented MVP endpoints:

```text
GET  /health
POST /api/v1/analyze
GET  /api/v1/locations
GET  /api/v1/locations/{id}
POST /api/v1/geocode
POST /api/v1/competitors/search
```

Important scenarios:

- Successful analysis returns full response.
- Analysis is saved to DB with `scoring_version_id`.
- History and detail endpoints return saved analysis data.
- Ambiguous address returns suggestions.
- Non-Krasnodar address is rejected.
- LLM disabled or unavailable returns HTTP 200 with `report.status = "fallback"`.
- Top-level `LLM_FAILED` is allowed only if no report can be created.
- Ordinary integration tests do not make network calls.

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

V1.1 turned manual validation into a first-class artifact. The original target
was 30-50 real Krasnodar addresses, but that full benchmark is deferred by owner
decision for the V1.1 completion declaration.

The present V1.1 release does not include a completed 30-50 case validation set.
If broader validation resumes, record real cases, manual competitor checks,
mismatch notes, and verdicts before claiming benchmark readiness.

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

- The 30-50 case benchmark is either recorded or explicitly deferred by owner
  decision.
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
not part of ordinary V1.1 automated gates unless external provider checks are
intentionally enabled for that run.
