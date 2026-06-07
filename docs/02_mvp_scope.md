# MVP Scope — PlaceFit

## Definition

MVP / V1.0 is a local-demo-ready service that evaluates one Krasnodar address
for a PVZ / ПВЗ location in 1-3 minutes.

## Implemented MVP Scope

### Product boundaries

- City: Krasnodar only.
- Business type: `pvz` only.
- Scenario: one address per analysis.
- UI: Streamlit.
- Backend: FastAPI.
- Storage: PostgreSQL/PostGIS with Alembic migrations.
- Demo mode: fake geodata providers and fallback report, no real API keys.

### Input

- Address, rent, area, floor, first floor, separate entrance.
- Parking, signage, storage area, repair condition.
- New residential area, high density area, bus stop nearby, visibility.
- User-provided income hypothesis, investment, desired profit.

### Processing

- Geocoding and Krasnodar validation.
- Competitor search within 700 m.
- Deduplication and radius buckets for 300/500/700 m.
- Rule-based score 0-100.
- Confidence score 0-100.
- Deterministic finance model.
- Deterministic decision.
- Simplified marketplace requirements response with `needs_manual_check=true`.
- AI report from prepared JSON or fallback report.
- Scoring version link for each analysis.

### Output

- Score, confidence, decision.
- Finance result.
- AI report or fallback report.
- Checklist.
- Competitor table and map.
- Saved analysis history and detail pages.

## MVP Non-Goals

- No ML revenue/order/payback forecast.
- No city-wide search, H3 grid, or heatmap.
- No autonomous trendwatcher.
- No Telegram bot or mobile app.
- No browser-agent.
- No Avito/Cian scraping.
- No auth/multi-user mode.
- No new business types.
- No official marketplace compliance decision.
- No guarantee of profit.

## Post-MVP Placement

| Capability | Version | Notes |
|---|---|---|
| Manual validation dataset and demo cases | V1.1 | First post-MVP step |
| Compare mode for 2-5 newly entered candidate locations | V1.2 | Implemented locally |
| Markdown compare export | V1.2 | Implemented from compare response snapshots |
| CSV/PDF/Excel export | V1.3 | Deferred reporting polish only |
| Saved location refresh and deltas | V1.4 | Manual refresh, no crawler |
| Scoring rule comparison and governance | V1.5 | Preserve historical versions |
| Marketplace rules with source tracking | V1.5 | Manual-check/versioned rules |
| City-wide PVZ intelligence | V2 | PVZ only, after validation |
| ML and multi-business platform | V3 | Requires dataset and backtesting |

## Deferred / Parking Lot

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

## Acceptance Criteria

MVP / V1.0 is accepted when:

1. User can analyze one Krasnodar PVZ address.
2. Backend returns score, confidence, finance, decision, report, checklist, and
   data sources.
3. Competitors are found, deduplicated, bucketed, listed, and displayed on the
   map when coordinates are available.
4. Analysis is saved and available in history/detail views.
5. Fallback report works without LLM key.
6. Demo path works without real external provider keys.
7. Docker Compose starts backend, PostGIS, and Streamlit.
8. Ordinary tests do not call real external APIs.
9. Documentation states limitations and does not imply profit guarantees.
