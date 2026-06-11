"""Single-analysis export data contract and pure Markdown renderer.

Single-analysis or saved location exports may render only values already
present in an ``AnalysisResponse`` object or a saved public response-shaped
snapshot. Export code must not rerun geocoding, POI/provider calls, analysis,
scoring, finance, confidence, decision, report generation, or LLM calls. It
must not add facts that are absent from existing public response JSON.

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
- Regenerated report text, regenerated fallback report text, or LLM-authored
  facts.
- Network calls, arbitrary export path handling, filesystem reads outside
  normal source/test files, and new production dependencies.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import datetime

from app.schemas.analysis import AnalysisResponse

EXPORT_DISCLAIMER = (
    "PlaceFit does not guarantee profit and does not replace manual "
    "verification. Marketplace checks are manual-check guidance, not official "
    "compliance confirmation."
)

ANALYSIS_EXPORT_LIMITATION_NOTES = [
    "PlaceFit does not guarantee profit.",
    "PlaceFit does not replace manual verification.",
    (
        "expected_gross_income_by_user is a user-provided hypothesis, "
        "not a PlaceFit forecast."
    ),
    "Marketplace requirements require manual verification from official sources.",
    "Competitor/geodata quality depends on provider coverage and freshness.",
    "Export is generated from the existing analysis response snapshot only.",
    (
        "Export does not rerun geocoding, POI search, scoring, finance, "
        "confidence, decision, report generation, analysis, providers, or LLM."
    ),
]

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


def render_analysis_markdown(response: AnalysisResponse) -> str:
    """Return deterministic Markdown from an existing analysis response."""

    sections = [
        "# Отчёт PlaceFit по адресу",
        "",
        *_render_summary(response),
        *_render_location(response),
        *_render_score(response),
        *_render_risks(response),
        *_render_finance(response),
        *_render_competitors(response),
        *_render_checklist(response),
        *_render_marketplace_requirements(response),
        *_render_user_assumptions(response),
        *_render_warnings(response),
        *_render_existing_report(response),
        *_render_data_sources(response),
        *_render_limitations(),
        *_render_disclaimer(),
    ]
    return "\n".join(sections).rstrip() + "\n"


def _render_summary(response: AnalysisResponse) -> list[str]:
    return [
        "## Summary",
        "",
        _markdown_table(
            ("Field", "Value"),
            (
                ("created_at", response.created_at),
                ("address", response.location.address),
                ("total_score", response.score.total_score),
                ("confidence_score", response.score.confidence_score),
                ("decision", response.score.decision),
                ("report.status", response.report.status),
            ),
        ),
        "",
    ]


def _render_location(response: AnalysisResponse) -> list[str]:
    location = response.location
    return [
        "## Location",
        "",
        _markdown_table(
            ("Field", "Value"),
            (
                ("location.id", location.id),
                ("location.address", location.address),
                ("location.normalized_address", location.normalized_address),
                ("location.lat", location.lat),
                ("location.lon", location.lon),
            ),
        ),
        "",
    ]


def _render_score(response: AnalysisResponse) -> list[str]:
    score = response.score
    return [
        "## Score / Confidence / Decision",
        "",
        _markdown_table(
            ("Field", "Value"),
            (
                ("score.total_score", score.total_score),
                ("score.confidence_score", score.confidence_score),
                ("score.scoring_version", score.scoring_version),
                ("score.decision", score.decision),
                ("score.details.demand_score", score.details.demand_score),
                (
                    "score.details.competition_score",
                    score.details.competition_score,
                ),
                ("score.details.rent_score", score.details.rent_score),
                ("score.details.premises_score", score.details.premises_score),
                (
                    "score.details.accessibility_score",
                    score.details.accessibility_score,
                ),
            ),
        ),
        "",
    ]


def _render_risks(response: AnalysisResponse) -> list[str]:
    risks = [
        f"Decision in snapshot: {response.score.decision}.",
        f"Confidence score in snapshot: {response.score.confidence_score}/100.",
    ]
    if response.score.confidence_score < 70:
        risks.append("Confidence score is below 70/100 in the response snapshot.")
    if response.competitors.competitors_700m >= 5:
        risks.append(
            "Competitor count within 700m is high in the response snapshot: "
            f"{response.competitors.competitors_700m}.",
        )
    if response.finance.net_profit is None:
        risks.append("Net profit is not calculated in the response snapshot.")
    if response.finance.payback_months is None:
        risks.append("Payback months are not calculated in the response snapshot.")
    if response.report.status == "fallback":
        risks.append("Report status is fallback in the response snapshot.")
    risks.extend(_marketplace_warnings(response))

    return [
        "## Risks",
        "",
        *_markdown_list(_unique(risks)),
        "",
    ]


def _render_finance(response: AnalysisResponse) -> list[str]:
    finance = response.finance
    return [
        "## Finance",
        "",
        _markdown_table(
            ("Field", "Value", "Meaning"),
            (
                (
                    "finance.monthly_costs",
                    finance.monthly_costs,
                    "Deterministic monthly cost from the analysis snapshot.",
                ),
                (
                    "finance.required_gross_income",
                    finance.required_gross_income,
                    "Required gross income from the analysis snapshot.",
                ),
                (
                    "finance.expected_gross_income_by_user",
                    finance.expected_gross_income_by_user,
                    (
                        "User-provided hypothesis; not a PlaceFit forecast "
                        "or system forecast."
                    ),
                ),
                (
                    "finance.net_profit",
                    finance.net_profit,
                    "Calculated in the original analysis response, not export.",
                ),
                (
                    "finance.payback_months",
                    finance.payback_months,
                    "Calculated in the original analysis response, not export.",
                ),
            ),
        ),
        "",
    ]


def _render_competitors(response: AnalysisResponse) -> list[str]:
    competitors = response.competitors
    lines = [
        "## Competitors",
        "",
        _markdown_table(
            ("Field", "Value"),
            (
                ("competitors.competitors_300m", competitors.competitors_300m),
                ("competitors.competitors_500m", competitors.competitors_500m),
                ("competitors.competitors_700m", competitors.competitors_700m),
                (
                    "competitors.nearest_competitor_distance_m",
                    competitors.nearest_competitor_distance_m,
                ),
                (
                    "competitors.average_competitor_distance_m",
                    competitors.average_competitor_distance_m,
                ),
            ),
        ),
        "",
        _markdown_table(
            (
                "#",
                "name",
                "brand",
                "category",
                "address",
                "distance_m",
                "rating",
                "reviews_count",
                "source",
                "lat",
                "lon",
            ),
            (
                (
                    index,
                    competitor.name,
                    competitor.brand,
                    competitor.category,
                    competitor.address,
                    competitor.distance_m,
                    competitor.rating,
                    competitor.reviews_count,
                    competitor.source,
                    competitor.lat,
                    competitor.lon,
                )
                for index, competitor in enumerate(competitors.list, start=1)
            ),
        ),
        "",
    ]
    return lines


def _render_checklist(response: AnalysisResponse) -> list[str]:
    return [
        "## Checklist",
        "",
        *_markdown_list(response.checklist),
        "",
    ]


def _render_marketplace_requirements(response: AnalysisResponse) -> list[str]:
    requirements = response.marketplace_requirements
    return [
        "## Marketplace manual checks",
        "",
        (
            "Marketplace requirements require manual verification from official "
            "sources."
        ),
        "",
        _markdown_table(
            (
                "Marketplace",
                "status",
                "needs_manual_check",
                "manual_checks",
                "warning",
            ),
            (
                (
                    "ozon",
                    requirements.ozon.status,
                    requirements.ozon.needs_manual_check,
                    "; ".join(requirements.ozon.manual_checks),
                    requirements.ozon.warning,
                ),
                (
                    "wildberries",
                    requirements.wildberries.status,
                    requirements.wildberries.needs_manual_check,
                    "; ".join(requirements.wildberries.manual_checks),
                    requirements.wildberries.warning,
                ),
                (
                    "yandex_market",
                    requirements.yandex_market.status,
                    requirements.yandex_market.needs_manual_check,
                    "; ".join(requirements.yandex_market.manual_checks),
                    requirements.yandex_market.warning,
                ),
            ),
        ),
        "",
    ]


def _render_user_assumptions(response: AnalysisResponse) -> list[str]:
    return [
        "## User assumptions / hypotheses",
        "",
        (
            "- expected_gross_income_by_user = "
            f"{_format_value(response.finance.expected_gross_income_by_user)} "
            "is a user-provided hypothesis / пользовательская гипотеза, "
            "not a PlaceFit forecast and not a system forecast."
        ),
        "",
    ]


def _render_warnings(response: AnalysisResponse) -> list[str]:
    warnings = [
        "Marketplace requirements require manual verification from official sources.",
        "Competitor/geodata quality depends on provider coverage and freshness.",
    ]
    warnings.extend(_marketplace_warnings(response))

    return [
        "## Warnings",
        "",
        *_markdown_list(_unique(warnings)),
        "",
    ]


def _render_existing_report(response: AnalysisResponse) -> list[str]:
    lines = [
        "## Existing report text",
        "",
        _markdown_table(
            ("Field", "Value"),
            (
                ("report.status", response.report.status),
                ("report.provider", response.report.provider),
                ("report.model", response.report.model),
                ("report.prompt_version", response.report.prompt_version),
            ),
        ),
        "",
    ]
    if response.report.status == "fallback":
        lines.extend(
            [
                (
                    "This is existing fallback report text returned in the "
                    "AnalysisResponse. Export does not regenerate report text."
                ),
                "",
            ],
        )
    lines.extend([response.report.text, ""])
    return lines


def _render_data_sources(response: AnalysisResponse) -> list[str]:
    return [
        "## Data sources",
        "",
        _markdown_table(
            ("source", "data_type", "fetched_at", "confidence"),
            (
                (
                    source.source,
                    source.data_type,
                    source.fetched_at,
                    source.confidence,
                )
                for source in response.data_sources
            ),
        ),
        "",
    ]


def _render_limitations() -> list[str]:
    return [
        "## Limitations",
        "",
        *_markdown_list(ANALYSIS_EXPORT_LIMITATION_NOTES),
        "",
    ]


def _render_disclaimer() -> list[str]:
    return [
        "## Disclaimer",
        "",
        EXPORT_DISCLAIMER,
        "",
    ]


def _marketplace_warnings(response: AnalysisResponse) -> list[str]:
    requirements = response.marketplace_requirements
    return [
        requirements.ozon.warning,
        requirements.wildberries.warning,
        requirements.yandex_market.warning,
    ]


def _markdown_table(
    headers: Sequence[str],
    rows: Iterable[Sequence[object]],
) -> str:
    materialized_rows = list(rows)
    lines = [
        "| " + " | ".join(_format_value(header) for header in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend(
        "| " + " | ".join(_format_value(value) for value in row) + " |"
        for row in materialized_rows
    )
    return "\n".join(lines)


def _markdown_list(items: Sequence[str]) -> list[str]:
    if not items:
        return ["- "]
    return [f"- {_format_value(item)}" for item in items]


def _unique(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    unique_items: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            unique_items.append(item)
    return unique_items


def _format_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, datetime):
        return _format_datetime(value)
    return str(value).replace("|", "\\|").replace("\n", " ")


def _format_datetime(value: datetime) -> str:
    return value.isoformat()
