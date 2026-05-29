# Trendwatcher — deferred / conditional idea

## Status

Trendwatcher is **not** part of the active V1.x roadmap. It must not be added as
an autonomous crawler, background parser, or near-term product feature.

V1.4 covers only **manual refresh of saved locations** and comparison of deltas
between analyses. That is intentionally different from a fully autonomous
trendwatcher.

## Why Deferred

1. Stable legal data sources are not proven.
2. Continuous monitoring needs scheduler, queues, storage, and operating
   discipline.
3. Background crawling can create legal and data-quality risk.
4. MVP value must be validated first through one-address PVZ analysis.
5. City-wide intelligence in V2 should remain PVZ-only and deterministic before
   adding automated trend signals.

## Possible Future Role

If the product matures and legal, stable data sources are available,
trendwatcher could collect structured signals that support deterministic scoring
or city-wide PVZ intelligence.

It must not:

- make decisions;
- replace deterministic scoring;
- invent facts;
- scrape unsupported sources;
- run in ordinary tests;
- present unverified external signals as certain.

## Candidate Signal Sources

These are examples for future evaluation, not active commitments.

| Source | Signal type | Requirement before use |
|---|---|---|
| 2GIS / OSM | Competitor opening/closing | Legal use, rate limits, source freshness |
| Marketplace news | Rule changes | Official source URL and retrieved date |
| New residential projects | Demand context | Stable dataset and manual validation |
| Competitor reviews | Service pressure | Legal access and anti-hallucination checks |
| User observations | Manual signal | Explicit user-entered source |

## Candidate Data Model

Do not implement this in V1.x. A future table could look like:

```sql
CREATE TABLE trend_signals (
    id SERIAL PRIMARY KEY,
    business_type TEXT NOT NULL,
    city TEXT,
    area_name TEXT,
    h3_index TEXT,
    signal_type TEXT NOT NULL,
    description TEXT,
    impact TEXT,
    confidence NUMERIC,
    source TEXT,
    source_url TEXT,
    detected_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Relationship To Roadmap

- **V1.4**: manual refresh of saved addresses and delta comparison only.
- **V2**: PVZ-only city-wide intelligence; trend signals remain optional and
  conditional.
- **V3**: data-driven platform work may revisit trendwatcher if the data and
  legal basis exist.
