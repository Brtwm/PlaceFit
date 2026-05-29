# Requirements Audit — Historical Note

## Status

This document is a historical requirements audit created before MVP completion.
It is useful as context, but it is **not** the active roadmap or current source
of truth for future development.

Current sources of truth:

1. [README](../README.md) — current project status and quickstart.
2. [Product overview](00_overview.md) — concise current product overview.
3. [MVP scope](02_mvp_scope.md) — implemented MVP boundaries.
4. [Roadmap](10_roadmap.md) — active post-MVP roadmap.

The original developer requirements live in
[docs/reference/developer_tz.md](reference/developer_tz.md). That file is also
historical and has been superseded by the current docs and roadmap.

## What Remains Valid

- The core product idea: decision support for PVZ location evaluation.
- The MVP focus: one Krasnodar address, `business_type = "pvz"`.
- The principle: AI explains, deterministic code decides.
- Provider abstraction for external APIs.
- Fallback-first operation without mandatory real provider keys.
- Scoring versioning from MVP.
- Manual marketplace verification.
- No profit guarantees.

## What Changed After MVP Completion

- MVP / V1.0 is now considered implemented and local demo ready.
- README, Docker Compose, Streamlit UI, backend, DB, fake providers, optional
  real providers, and fallback/optional LLM report are current implemented
  scope, not future work.
- The old coarse roadmap `MVP -> V1.5 -> V2 -> V3` has been replaced by the
  staged post-MVP roadmap in [docs/10_roadmap.md](10_roadmap.md).
- First post-MVP step is V1.1 stabilization/manual validation, not a feature
  expansion.
- Compare mode is V1.2.
- Export/reporting polish is V1.3.
- Saved-location refresh/delta monitoring is V1.4.
- Scoring governance and marketplace rule maturity are V1.5.
- City-wide intelligence remains V2 and PVZ-only.
- ML, multi-business, auth/multi-user, and B2B platform work are V3.

## Deferred Decisions

Telegram bot is not a product priority. It may be considered only as a thin
wrapper over a mature product if a real customer explicitly requests it.

The following ideas are deferred or conditional:

- Telegram bot.
- Mobile app.
- Browser-agent.
- Avito/Cian parsing without legal basis.
- Fully autonomous trendwatcher.
- Premature ML without dataset/backtesting.
- Premature multi-business expansion.
- Premature React rewrite before Streamlit limitations are proven.

## Audit Outcome

The initial requirements were strong enough to guide the MVP build, but their
versioning and future roadmap are now historical. Future Codex work should use
the narrower, validation-first roadmap in [docs/10_roadmap.md](10_roadmap.md).
