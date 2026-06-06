"""Pure compare summary exporter for Markdown."""

from __future__ import annotations

from collections.abc import Iterable

from app.schemas.compare import CompareResponse

_LIMITATION_NOTES = [
    "PlaceFit does not guarantee profit.",
    "User-provided expected income is a hypothesis, not a system forecast.",
    "Marketplace requirements require manual verification from official sources.",
    "Export is generated from the compare response snapshot only.",
    "Export does not rerun analysis, providers, scoring, finance, reports, or ranking.",
]


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
