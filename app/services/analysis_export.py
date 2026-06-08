"""Single-analysis export data contract for future V1.3 renderers.

This module is intentionally contract-only. Future single-analysis or saved
location exports may render only values already present in an
``AnalysisResponse`` object or a saved public response-shaped snapshot. Export
code must not rerun geocoding, POI/provider calls, analysis, scoring, finance,
confidence, decision, report generation, or LLM calls. It must not add facts
that are absent from existing public response JSON.

Allowed source categories:

- Location fields from ``AnalysisResponse.location``: ``address``,
  ``normalized_address``, ``lat``, ``lon``, and public ``id`` when already
  present.
- Snapshot metadata from ``AnalysisResponse.created_at``.
- Deterministic score fields from ``AnalysisResponse.score``:
  ``total_score``, ``confidence_score``, ``scoring_version``, ``decision``, and
  ``details``.
- Finance fields from ``AnalysisResponse.finance`` only. The
  ``expected_gross_income_by_user`` value is always a user hypothesis, not a
  PlaceFit forecast.
- Competitor counts, distance summaries, and public competitor list fields from
  ``AnalysisResponse.competitors``.
- Marketplace manual-check fields already present in
  ``AnalysisResponse.marketplace_requirements``.
- Existing report metadata/text from ``AnalysisResponse.report`` only when the
  response already includes that text. Export must never regenerate report text.
- Checklist strings from ``AnalysisResponse.checklist``.
- Data source metadata from ``AnalysisResponse.data_sources``.
- User-provided assumptions/request/result fields already present in the public
  response-shaped object.
- Warnings and data limitations already present in the response JSON.

Prohibited source categories:

- Provider secrets, API keys, raw external API responses, raw provider payloads,
  database internals, ORM-only fields, and non-public internal IDs.
- Invented competitor facts, traffic facts, revenue forecasts, or official
  marketplace compliance claims.
- New score, finance, confidence, or decision calculations.
- Regenerated report text, fallback report text, or LLM-authored facts.
- Network calls, arbitrary export path handling, filesystem reads outside
  normal source/test files, and new production dependencies.
"""

EXPORT_DISCLAIMER = (
    "PlaceFit does not guarantee profit and does not replace manual "
    "verification. Marketplace checks are manual-check guidance, not official "
    "compliance confirmation."
)

ANALYSIS_EXPORT_ALLOWED_SECTIONS = {
    "summary": (
        "AnalysisResponse.location",
        "AnalysisResponse.score",
        "AnalysisResponse.finance",
        "AnalysisResponse.created_at",
    ),
    "risks": (
        "AnalysisResponse.score.decision",
        "AnalysisResponse.score.confidence_score",
        "AnalysisResponse.marketplace_requirements.*.warning",
        "AnalysisResponse.checklist",
    ),
    "finance": ("AnalysisResponse.finance",),
    "competitors": (
        "AnalysisResponse.competitors",
        "AnalysisResponse.competitors.list",
    ),
    "checklist": ("AnalysisResponse.checklist",),
    "assumptions": (
        "AnalysisResponse.finance.expected_gross_income_by_user is a user "
        "hypothesis, not a system forecast.",
    ),
    "warnings": (
        "AnalysisResponse.marketplace_requirements.*.warning",
        "AnalysisResponse.data_sources",
    ),
    "limitations": (
        "Fixed product caveats already present in docs/current export text.",
    ),
    "disclaimer": (EXPORT_DISCLAIMER,),
}

ANALYSIS_EXPORT_PROHIBITED_CATEGORIES = (
    "provider secrets",
    "API keys",
    "raw external API responses",
    "raw provider payloads",
    "database internals not present in public response JSON",
    "ORM-only fields not present in response schemas",
    "internal IDs unless already public response fields",
    "invented competitor facts",
    "invented traffic facts",
    "invented revenue forecasts",
    "official marketplace compliance claims",
    "LLM-authored ranking conclusions",
    "new score calculations",
    "new finance calculations",
    "new confidence calculations",
    "new decision calculations",
    "regenerated report text",
    "regenerated fallback report text",
    "network calls",
    "filesystem reads outside normal source/test files",
    "arbitrary export path handling",
    "new production dependency",
)

ANALYSIS_EXPORT_SOURCE_OF_TRUTH = {
    "Summary": (
        "AnalysisResponse.location",
        "AnalysisResponse.score",
        "AnalysisResponse.finance",
        "AnalysisResponse.created_at",
    ),
    "Risks": (
        "AnalysisResponse.score.decision",
        "AnalysisResponse.score.confidence_score",
        "AnalysisResponse.marketplace_requirements.*.warning",
        "AnalysisResponse.checklist",
    ),
    "Finance": (
        "FinanceResult.monthly_costs",
        "FinanceResult.required_gross_income",
        "FinanceResult.expected_gross_income_by_user",
        "FinanceResult.net_profit",
        "FinanceResult.payback_months",
    ),
    "Competitors": (
        "CompetitorsSummary.competitors_300m",
        "CompetitorsSummary.competitors_500m",
        "CompetitorsSummary.competitors_700m",
        "CompetitorsSummary.nearest_competitor_distance_m",
        "CompetitorsSummary.average_competitor_distance_m",
        "CompetitorsSummary.list",
    ),
    "Checklist": ("AnalysisResponse.checklist",),
    "Assumptions": (
        "User-provided request/result fields already present in response JSON.",
        "FinanceResult.expected_gross_income_by_user is a user hypothesis, not "
        "a system forecast.",
    ),
    "Warnings": (
        "AnalysisResponse.marketplace_requirements.*.warning",
        "Data limitations already present in response JSON.",
    ),
    "Limitations": (
        "Fixed product caveats already present in docs/current export text.",
    ),
    "Disclaimer": (EXPORT_DISCLAIMER,),
}
