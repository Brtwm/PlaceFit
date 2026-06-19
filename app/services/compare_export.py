"""Compare export data contract and pure Markdown renderer.

Future compare or saved compare session exports may render only values already
present in a ``CompareResponse`` object or a saved public response snapshot.
Export code must not rerun geocoding, POI/provider calls, analysis, scoring,
finance, confidence, decision, report generation, LLM calls, or compare
ranking. It must not add facts that are absent from existing public compare
JSON.

Allowed source categories:

- Compare summary fields from ``CompareResponse.summary`` and snapshot metadata
  from ``CompareResponse.compare_id`` and ``CompareResponse.created_at``.
- Ranking rules from ``CompareResponse.ranking_rules``, including ``version``,
  ``sort_keys``, ``decision_severity_order``, and ``uses_llm``. The contract
  expects ``uses_llm = false`` when that public field exists.
- Ranked candidate fields already present in
  ``CompareResponse.ranked_candidates``.
- Candidate score, confidence, decision, finance summary, competitor summary,
  marketplace warnings, assumptions, warnings, trade-offs, and checklist-like
  fields only when already present in compare JSON.
- Failed candidate status, error code/message/details, and ambiguous-address
  suggestions from ``CompareResponse.failed_candidates``.
- Compare-level assumptions and warnings only when present in a future public
  compare response shape.
- Compare limitations already present in current compare export/docs.

Prohibited source categories:

- Provider secrets, API keys, raw external API responses, raw provider payloads,
  database internals, ORM-only fields, and non-public internal IDs.
- Invented competitor facts, traffic facts, revenue forecasts, or official
  marketplace compliance claims.
- LLM-authored ranking conclusions, recomputed ranking, new score calculations,
  new finance calculations, new confidence calculations, or new decision
  calculations.
- Regenerated report text, network calls, arbitrary export path handling,
  filesystem reads outside normal source/test files, and new production
  dependencies.

V1.3-6 boundary decision: compare exports are intentionally service/UI-only for
local Streamlit downloads. Public backend export endpoints are deferred until
API clients or non-Streamlit workflows need them. This renderer remains a pure
snapshot renderer and must not rerun analysis, provider, scoring, finance,
confidence, decision, report, LLM, or compare ranking work.
"""

from __future__ import annotations

from collections.abc import Iterable

from app.schemas.compare import CompareResponse

EXPORT_DISCLAIMER = (
    "PlaceFit does not guarantee profit and does not replace manual "
    "verification. Marketplace checks are manual-check guidance, not official "
    "compliance confirmation."
)

COMPARE_EXPORT_BOUNDARY_DECISION = "service_only"
COMPARE_EXPORT_API_ENDPOINTS_IMPLEMENTED = False

COMPARE_EXPORT_LIMITATION_NOTES = [
    "PlaceFit does not guarantee profit.",
    "User-provided expected income is a hypothesis, not a system forecast.",
    "Marketplace requirements require manual verification from official sources.",
    "Export is generated from the compare response snapshot only.",
    "Export does not rerun analysis, providers, scoring, finance, reports, or ranking.",
]
_LIMITATION_NOTES = COMPARE_EXPORT_LIMITATION_NOTES

COMPARE_EXPORT_ALLOWED_SECTIONS = {
    "summary": (
        "CompareResponse.summary",
        "CompareResponse.compare_id",
        "CompareResponse.created_at",
    ),
    "ranking_rules": (
        "CompareResponse.ranking_rules.version",
        "CompareResponse.ranking_rules.sort_keys",
        "CompareResponse.ranking_rules.decision_severity_order",
        "CompareResponse.ranking_rules.uses_llm = false",
    ),
    "ranked_candidates": (
        "CompareResponse.ranked_candidates",
        "CompareResponse.ranked_candidates.*.score",
        "CompareResponse.ranked_candidates.*.finance",
        "CompareResponse.ranked_candidates.*.competitors",
        "CompareResponse.ranked_candidates.*.assumptions",
        "CompareResponse.ranked_candidates.*.warnings",
        "CompareResponse.ranked_candidates.*.trade_offs",
    ),
    "failed_candidates": (
        "CompareResponse.failed_candidates.*.status",
        "CompareResponse.failed_candidates.*.error.code",
        "CompareResponse.failed_candidates.*.error.message",
        "CompareResponse.failed_candidates.*.error.details",
        "CompareResponse.failed_candidates.*.error.suggestions",
    ),
    "assumptions": (
        "Candidate assumptions already present in compare JSON.",
        "Compare-level assumptions only when present in public compare JSON.",
    ),
    "warnings": (
        "Candidate warnings already present in compare JSON.",
        "Compare-level warnings only when present in public compare JSON.",
        "Failed candidates already present in compare JSON.",
    ),
    "trade_offs": (
        "CompareResponse.ranked_candidates.*.trade_offs when already present.",
    ),
    "limitations": ("Compare limitations already present in current export/docs.",),
    "disclaimer": (EXPORT_DISCLAIMER,),
}

COMPARE_EXPORT_PROHIBITED_CATEGORIES = (
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
    "recomputed ranking",
    "regenerated report text",
    "regenerated fallback report text",
    "network calls",
    "filesystem reads outside normal source/test files",
    "arbitrary export path handling",
    "new production dependency",
)

COMPARE_EXPORT_SOURCE_OF_TRUTH = {
    "Summary": ("CompareResponse.summary",),
    "Risks": (
        "CompareResponse.failed_candidates",
        "CompareResponse.ranked_candidates.*.warnings",
        "CompareResponse.ranked_candidates.*.score.confidence_score",
        "CompareResponse.ranked_candidates.*.score.decision",
    ),
    "Finance": (
        "CompareResponse.ranked_candidates.*.finance.monthly_costs",
        "CompareResponse.ranked_candidates.*.finance.required_gross_income",
        "CompareResponse.ranked_candidates.*.finance.expected_gross_income_by_user",
        "CompareResponse.ranked_candidates.*.finance.net_profit",
        "CompareResponse.ranked_candidates.*.finance.payback_months",
    ),
    "Competitors": ("CompareResponse.ranked_candidates.*.competitors",),
    "Checklist": (
        "CompareResponse.ranked_candidates.*.assumptions",
        "CompareResponse.ranked_candidates.*.warnings",
        "CompareResponse.ranked_candidates.*.trade_offs",
    ),
    "Assumptions": (
        "CompareResponse.ranked_candidates.*.assumptions",
        "Compare-level assumptions only when present in public compare JSON.",
        "expected_gross_income_by_user is a user hypothesis, not a system forecast.",
    ),
    "Warnings": (
        "CompareResponse.ranked_candidates.*.warnings",
        "CompareResponse.failed_candidates",
    ),
    "Limitations": (
        "Compare limitations already present in current export/docs.",
    ),
    "Disclaimer": (EXPORT_DISCLAIMER,),
}


def export_compare_markdown(response: CompareResponse) -> str:
    """Return a deterministic Markdown summary from an existing compare response."""

    lines = [
        "# PlaceFit Compare Summary",
        "",
        "## Metadata",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| compare_id | {_markdown_value(response.compare_id)} |",
        f"| created_at | {_markdown_value(response.created_at.isoformat())} |",
        f"| requested_count | {_markdown_value(response.summary.requested_count)} |",
        f"| successful_count | {_markdown_value(response.summary.successful_count)} |",
        f"| failed_count | {_markdown_value(response.summary.failed_count)} |",
        "",
        "## Disclaimer",
        "",
        "- PlaceFit does not guarantee profit.",
        (
            "- expected_gross_income_by_user is a user hypothesis, "
            "not a system forecast."
        ),
        (
            "- Marketplace requirements require manual verification from "
            "official sources."
        ),
        "",
        "## Ranking Rules",
        "",
        "| Field | Value |",
        "|---|---|",
        (
            "| ranking_rules.version | "
            f"{_markdown_value(response.ranking_rules.version)} |"
        ),
        (
            "| ranking_rules.uses_llm | "
            f"{_markdown_value(response.ranking_rules.uses_llm)} |"
        ),
        (
            "| ranking_rules.description | "
            f"{_markdown_value(response.ranking_rules.description)} |"
        ),
        "",
        "| # | Field | Direction | Nulls | Description |",
        "|---|---|---|---|---|",
    ]

    for index, sort_key in enumerate(response.ranking_rules.sort_keys, start=1):
        lines.append(
            "| "
            f"{index} | "
            f"{_markdown_value(sort_key.field)} | "
            f"{_markdown_value(sort_key.direction)} | "
            f"{_markdown_value(sort_key.nulls)} | "
            f"{_markdown_value(sort_key.description)} |",
        )

    lines.extend(
        [
            "",
            "Decision severity order: "
            + " -> ".join(response.ranking_rules.decision_severity_order),
            "",
            "## Ranked Candidates",
            "",
            (
                "| rank | candidate_id | input_index | label | status | address | "
                "score_total | confidence_score | decision | net_profit | "
                "payback_months | competitors_300m | competitors_500m | "
                "competitors_700m | nearest_competitor_distance_m | warnings_count |"
            ),
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
        ],
    )

    for candidate in response.ranked_candidates:
        address = candidate.location_summary.address or candidate.input_address
        lines.append(
            "| "
            f"{_markdown_value(candidate.rank)} | "
            f"{_markdown_value(candidate.candidate_id)} | "
            f"{_markdown_value(candidate.input_index)} | "
            f"{_markdown_value(candidate.label)} | "
            f"{_markdown_value(candidate.status)} | "
            f"{_markdown_value(address)} | "
            f"{_markdown_value(candidate.score.total_score)} | "
            f"{_markdown_value(candidate.score.confidence_score)} | "
            f"{_markdown_value(candidate.score.decision)} | "
            f"{_markdown_value(candidate.finance.net_profit)} | "
            f"{_markdown_value(candidate.finance.payback_months)} | "
            f"{_markdown_value(candidate.competitors.competitors_300m)} | "
            f"{_markdown_value(candidate.competitors.competitors_500m)} | "
            f"{_markdown_value(candidate.competitors.competitors_700m)} | "
            f"{_markdown_value(candidate.competitors.nearest_competitor_distance_m)} | "
            f"{_markdown_value(len(candidate.warnings))} |",
        )

    lines.extend(
        [
            "",
            "## Failed Candidates",
            "",
            (
                "| candidate_id | input_index | label | status | input_address | "
                "error_code | error_message | error_details | suggestions_count |"
            ),
            "|---|---|---|---|---|---|---|---|---|",
        ],
    )

    for failed_candidate in response.failed_candidates:
        lines.append(
            "| "
            f"{_markdown_value(failed_candidate.candidate_id)} | "
            f"{_markdown_value(failed_candidate.input_index)} | "
            f"{_markdown_value(failed_candidate.label)} | "
            f"{_markdown_value(failed_candidate.status)} | "
            f"{_markdown_value(failed_candidate.input_address)} | "
            f"{_markdown_value(failed_candidate.error.code)} | "
            f"{_markdown_value(failed_candidate.error.message)} | "
            f"{_markdown_value(failed_candidate.error.details)} | "
            f"{_markdown_value(len(failed_candidate.error.suggestions or []))} |",
        )

    lines.extend(
        [
            "",
            "### Ambiguous-address Suggestions",
            "",
            (
                "| candidate_id | suggestion_index | address | lat | lon | "
                "confidence |"
            ),
            "|---|---|---|---|---|---|",
        ],
    )

    for failed_candidate in response.failed_candidates:
        for index, suggestion in enumerate(
            failed_candidate.error.suggestions or [],
            start=1,
        ):
            lines.append(
                "| "
                f"{_markdown_value(failed_candidate.candidate_id)} | "
                f"{_markdown_value(index)} | "
                f"{_markdown_value(suggestion.address)} | "
                f"{_markdown_value(suggestion.lat)} | "
                f"{_markdown_value(suggestion.lon)} | "
                f"{_markdown_value(suggestion.confidence)} |",
            )

    lines.extend(
        [
            "",
            "## Assumptions",
            "",
            *_markdown_list(
                _unique(
                    assumption
                    for candidate in response.ranked_candidates
                    for assumption in candidate.assumptions
                ),
            ),
            "",
            "## Warnings",
            "",
            *_markdown_list(
                _unique(
                    warning
                    for candidate in response.ranked_candidates
                    for warning in candidate.warnings
                ),
            ),
            "",
            "## Limitation Notes",
            "",
            *_markdown_list(_LIMITATION_NOTES),
        ],
    )

    return "\n".join(lines) + "\n"


def _markdown_list(items: list[str]) -> list[str]:
    if not items:
        return []
    return [f"- {_markdown_value(item)}" for item in items]


def _unique(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    unique_items: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            unique_items.append(item)
    return unique_items


def _markdown_value(value: object) -> str:
    if value is None or value == "":
        return ""
    return str(value).replace("|", "\\|").replace("\n", " ")
