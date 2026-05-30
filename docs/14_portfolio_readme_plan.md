# Portfolio README Plan — Historical Note

## Status

This document is a historical portfolio/README planning note. The active GitHub
README is [README.md](../README.md), and the active product roadmap is
[docs/10_roadmap.md](10_roadmap.md).

Do not use this file as a current implementation plan.

## Current README Direction

README should stay concise and honest:

- PlaceFit V1.1 stabilization is complete.
- Demo path works without real API keys and without LLM key.
- Deterministic backend code calculates score, confidence, finance, and
  decision.
- LLM is optional and only explains prepared JSON.
- Fallback report is valid behavior.
- PlaceFit does not guarantee profit.
- Marketplace requirements require manual verification.
- Detailed roadmap lives in `docs/10_roadmap.md`.

## Roadmap Summary For Portfolio

Use this concise roadmap wording:

```text
MVP / V1.0: local demo ready
V1.1: stabilization complete; broader manual benchmark deferred
V1.2: compare mode
V1.3: export/reporting polish
V1.4: saved-location refresh and deltas
V1.5: scoring governance and marketplace rule maturity
V2: city-wide PVZ-only intelligence
V3: ML/B2B/multi-business platform after dataset/backtesting
```

Telegram bot is not a product priority. It may be considered only as a thin
wrapper over a mature product if a real customer explicitly requests it.

## Avoid In README

- Do not claim the product automatically finds the best location.
- Do not say AI makes business decisions.
- Do not imply guaranteed profit.
- Do not imply official marketplace compliance.
- Do not list deferred ideas as active roadmap.
- Do not make README a huge roadmap document.

## Useful Portfolio Signals

- Product focus: narrow MVP before expansion.
- Engineering discipline: provider abstraction, deterministic core, scoring
  versioning.
- AI safety: structured input, hallucination prevention, fallback report.
- Testing: no real external APIs in ordinary tests.
- DevOps: Docker Compose and `.env.example` without secrets.
- Honesty: limitations, manual validation, marketplace caveats.
