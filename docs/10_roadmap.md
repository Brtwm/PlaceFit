# Roadmap — PlaceFit

## Roadmap Principles

- AI explains, deterministic code decides.
- Validate core quality before expanding scope.
- Prefer manual validation before automation.
- No ML before a dataset and backtesting plan exist.
- No new business types before PVZ validation is complete.
- No scraping without legal basis.
- No Telegram/mobile wrappers in the active roadmap.
- External provider calls must remain optional and excluded from ordinary tests.
- Marketplace requirements are manual-check, source-tracked rules, not official
  compliance guarantees.

## Current Status

**V1.2 compare mode is implemented locally and release-hardened with ordinary
automated checks passing.**

Implemented scope:

- One Krasnodar address for `business_type = "pvz"`.
- Deterministic scoring, confidence, finance, and decision.
- Competitor search, radius buckets, and deduplication.
- PostgreSQL/PostGIS persistence and scoring version link.
- AI/fallback report.
- Checklist.
- Streamlit UI with analysis, map, history, and detail views.
- Compare mode for 2-5 newly entered candidate PVZ locations.
- Deterministic compare ranking from visible response fields only.
- Candidate-level compare failures with visible error details.
- Saved compare sessions loaded from response snapshots.
- Streamlit compare page and candidate-only compare map.
- Markdown compare export from an existing compare response snapshot.
- Docker Compose.
- Fake/fallback demo path without external API keys or LLM key.
- Optional real 2GIS/OSM providers and optional OpenAI-compatible LLM.

Known limitations:

- No validated 30-50 case manual benchmark dataset yet.
- V1.1 stabilization is complete by owner acceptance; the broader 30-50 case
  benchmark remains deferred and must not be presented as completed evidence.
- Demand inputs such as high density/new residential area are user-provided.
- Marketplace requirements are `needs_manual_check`.
- Real provider quality depends on external data freshness and coverage.
- No profit guarantee or automatic revenue forecast.
- CSV/PDF/Excel exports are deferred reporting/export polish.

## V1.1 — Stabilization, Validation, Documentation Hardening

**Goal:** prove that MVP results are adequate, reproducible, and honestly
documented.

**Why:** before new features, PlaceFit needs evidence that one-address PVZ
analysis is useful and explainable.

**Scope:**

- Manual validation harness for 30-50 real Krasnodar addresses.
- Validation cases for good, medium, weak, controversial, and ambiguous
  addresses.
- Manual competitor checks against maps.
- Deduplication and radius bucket review for 300/500/700 m.
- AI/fallback report hallucination review.
- Streamlit map marker review.
- Known limitations log.
- Fresh-clone demo walkthrough.
- Lightweight docs checklist before releases.

**Current evidence status:** V1.1 is accepted as complete. A broader 30-50 case
manual benchmark is deferred and is not claimed as completed validation
evidence.

**Non-goals:**

- No compare mode.
- No new providers required for ordinary tests.
- No ML, H3, city-wide scan, Telegram, auth, or new business types.

**Acceptance criteria:**

- Manual validation table or documents exist and distinguish completed cases
  from seed/pending cases.
- 30-50 real validation cases are recorded or explicitly deferred by owner
  decision without being presented as completed benchmark evidence.
- Known errors/limitations are recorded.
- Demo path is reproducible from fresh clone.
- Ordinary tests pass.
- README and docs match implemented behavior.

**Recommended Codex phases:**

1. Create validation case format and seed demo cases.
2. Add a small command or script only if it reduces manual repetition.
3. Run manual checks and record issues.
4. Update docs and release checklist.

## V1.2 — Compare Mode and Decision Support

**Goal:** turn PlaceFit from a one-address calculator into a tool for choosing
between candidate locations.

**Why:** users usually decide between several premises, not one isolated point.

**Current status:** implemented locally and release-hardened with ordinary
automated checks passing. The implemented export format is Markdown only.

**Implemented scope:**

- Compare 2-5 newly entered candidate locations.
- Unified table: score, confidence, finance, decision, competitor counts.
- Transparent deterministic ranking from visible response fields.
- Candidate-level failures remain visible.
- Saved compare sessions from request/response snapshots.
- Streamlit compare page and candidate-only compare map.
- Markdown comparison summary export from an existing compare response snapshot.

**Non-goals:**

- No ML ranking.
- No automatic city-wide candidate search.
- No change to per-address scoring logic unless separately versioned.
- No saved analysis references as compare inputs in V1.2.
- No CSV, Excel, or PDF export in V1.2.

**Acceptance criteria:**

- User can compare multiple addresses.
- Each address still runs through the deterministic pipeline.
- Ranking is explainable from visible metrics.
- Saved compare sessions load stored response snapshots without rerunning
  providers, analysis, scoring, finance, report generation, or ranking.
- Ordinary automated checks pass.

**Completed Codex phases:**

1. Define compare API/UI contract.
2. Build deterministic ranking and saved compare persistence.
3. Add Streamlit compare view.
4. Add focused tests for ordering and saved sessions.
5. Add Markdown compare export from existing response snapshots.
6. Complete documentation and release hardening.

## V1.3 — Export and Reporting Polish

**Goal:** make results easy to share with a partner, investor, landlord, or
internal reviewer.

**Why:** a decision-support tool needs portable evidence, not only an on-screen
result.

**Scope:**

- Broader export/reporting polish beyond the V1.2 Markdown compare helper.
- CSV/PDF/Excel exports if still needed.
- Better report layout without changing decision logic.
- Sections: summary, risks, finance, competitors, checklist, assumptions.
- Clear labels for user hypotheses.
- Clear disclaimer that PlaceFit does not guarantee profit.

**Non-goals:**

- No new facts beyond analysis JSON.
- No LLM authority over score, finance, confidence, or decision.
- No automatic marketplace compliance claims.

**Acceptance criteria:**

- Export does not change deterministic pipeline output.
- Report does not add facts absent from analysis JSON.
- Fallback report remains available.

**Recommended Codex phases:**

1. Define export data contract from existing analysis response.
2. Decide whether CSV/PDF/Excel are still needed after the V1.2 Markdown helper.
3. Add report/export regression tests.
4. Validate exported files manually.

## V1.4 — Monitoring Saved Locations

**Goal:** track changes for already saved addresses through manual refresh.

**Why:** a location can become better or worse as competitors and assumptions
change.

**Scope:**

- Re-run analysis for a saved location.
- Compare current result with previous result.
- Show deltas for competitor count, score, confidence, finance assumptions, and
  decision.
- Manual refresh initiated by user.

**Non-goals:**

- No continuous crawler.
- No autonomous trendwatcher.
- No city-wide scan.
- No background scraping.

**Acceptance criteria:**

- User can re-analyze a saved address.
- User can see deltas between two analyses.
- No permanent background parsing or monitoring process exists.

**Recommended Codex phases:**

1. Define re-analysis and delta model.
2. Add backend history comparison.
3. Add Streamlit delta UI.
4. Add tests for unchanged, improved, and worsened cases.

## V1.5 — Scoring Governance and Marketplace Rule Maturity

**Goal:** make scoring and marketplace rules more manageable, comparable, and
auditable.

**Why:** once MVP quality is validated, rule changes need traceability.

**Scope:**

- Scoring version comparison.
- History of scoring rule versions.
- Admin/config interface only if manual file/DB updates become a real bottleneck.
- Marketplace requirements as versioned/manual-check rules.
- Marketplace source tracking fields:
  - marketplace;
  - rule text;
  - source_url;
  - retrieved_at or valid_from;
  - valid_to when needed;
  - needs_manual_check=true.

**Non-goals:**

- No official marketplace compliance guarantee.
- No hardcoded illustrative marketplace requirements as truth.
- No new business types.

**Acceptance criteria:**

- Old analyses preserve scoring version references.
- New scoring rules can be compared with old rules.
- Marketplace rules clearly read as manual-check/source-tracked guidance.

**Recommended Codex phases:**

1. Design scoring version diff contract.
2. Add rule comparison views/tests.
3. Add marketplace rule source metadata.
4. Review wording for compliance risk.

## V2 — City-Wide Location Intelligence for PVZ Only

**Goal:** move from one-address analysis to discovering promising PVZ zones.

**Why:** after validating core quality, users may need help finding areas, not
only checking known addresses.

**Scope:**

- H3/grid-based city-wide scan.
- Heatmap of PVZ attractiveness.
- Infrastructure layers.
- Batch calculation for candidate zones.
- Map-first UI.
- React/Next.js frontend only if Streamlit limitations are proven.
- Krasnodar only or a carefully limited city list after validation.

**Non-goals:**

- No new business types.
- No ML forecast.
- No trendwatcher unless legal, stable, and useful data sources exist.
- No scraping without legal basis.

**Acceptance criteria:**

- City-wide outputs are explainable from deterministic components.
- PVZ-only scope remains enforced.
- Batch/external provider calls are controllable and testable without real
  network calls in ordinary tests.

**Recommended Codex phases:**

1. Prototype grid computation on static/local data.
2. Define zone scoring separate from address scoring.
3. Add map-first UI after backend evidence is useful.
4. Validate zones manually before expanding cities.

## V3 — Data-Driven / ML / B2B Platform

**Goal:** evolve into a B2B location intelligence platform after evidence and
data exist.

**Why:** ML, multi-business profiles, and production workflows need validated
data and proven core value.

**Scope:**

- ML forecast for revenue/orders/payback only with dataset and backtesting.
- Backtesting.
- Network optimization.
- Cannibalization analysis.
- Multi-business scoring profiles.
- Auth, multi-user, roles.
- Dashboards.
- API integrations.
- Production monitoring and observability.

**Non-goals:**

- V3 is not the next implementation task.
- No ML without training data, target definitions, and evaluation.
- No multi-business expansion before PVZ validation is complete.

**Acceptance criteria:**

- Dataset exists and is documented.
- Backtesting results are available.
- ML does not replace explainable deterministic baselines without evidence.
- Multi-business rules are versioned and domain-specific.

**Recommended Codex phases:**

1. Define dataset/backtesting plan.
2. Build read-only analytics around existing validated data.
3. Add ML baselines only after data readiness review.
4. Add B2B platform capabilities only after product need is proven.

## Parking Lot / Deferred

- Telegram bot.
- Mobile app.
- Browser-agent.
- Avito/Cian parsing without legal basis.
- Fully autonomous trendwatcher.
- Premature ML without dataset.
- Premature multi-business expansion.
- Premature React rewrite before Streamlit limitations are proven.

Telegram bot is not a product priority. It may be considered only as a thin
wrapper over a mature product if a real customer explicitly requests it.
