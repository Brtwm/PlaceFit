from datetime import UTC, datetime
from typing import Any

from app.config.scoring_rules import DECISION_RULES
from app.schemas.compare import DEFAULT_COMPARE_RANKING_RULES, CompareResponse
from app.services.compare_export import export_compare_markdown


def test_export_compare_markdown_contains_snapshot_summary_only() -> None:
    response = _compare_response()

    markdown = export_compare_markdown(response)

    assert "# PlaceFit Compare Summary" in markdown
    assert "created_at" in markdown
    assert "2026-05-31" in markdown
    assert DEFAULT_COMPARE_RANKING_RULES.version in markdown
    assert "uses_llm" in markdown
    assert "False" in markdown
    assert "candidate-2" in markdown
    assert "candidate-1" in markdown
    assert "candidate-3" in markdown
    assert "ADDRESS_AMBIGUOUS" in markdown
    assert "Marketplace requirements need manual verification" in markdown
    assert "expected_gross_income_by_user is a user hypothesis" in markdown
    assert "PlaceFit does not guarantee profit" in markdown
    assert "Report text" not in markdown
    assert "best location because" not in markdown.lower()
    assert "recommendation" not in markdown.lower()
    assert markdown.index("candidate-2") < markdown.index("candidate-1")


def _compare_response() -> CompareResponse:
    return CompareResponse.model_validate(
        {
            "compare_id": 42,
            "created_at": datetime(2026, 5, 31, 12, 0, tzinfo=UTC),
            "ranking_rules": DEFAULT_COMPARE_RANKING_RULES.model_dump(mode="json"),
            "ranked_candidates": [
                _successful_candidate(
                    candidate_id="candidate-2",
                    input_index=1,
                    rank=1,
                    label="Candidate B",
                    total_score=90,
                    net_profit=80_000,
                    payback_months=7.5,
                ),
                _successful_candidate(
                    candidate_id="candidate-1",
                    input_index=0,
                    rank=2,
                    label="Candidate A",
                    total_score=80,
                    net_profit=None,
                    payback_months=None,
                ),
            ],
            "failed_candidates": [_failed_candidate()],
            "summary": {
                "requested_count": 3,
                "successful_count": 2,
                "failed_count": 1,
            },
        },
    )


def _successful_candidate(
    *,
    candidate_id: str,
    input_index: int,
    rank: int,
    label: str,
    total_score: int,
    net_profit: int | None,
    payback_months: float | None,
) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "input_index": input_index,
        "rank": rank,
        "label": label,
        "input_address": f"Input address {input_index}",
        "status": "success",
        "source_analysis_id": None,
        "location_summary": {
            "id": input_index + 1,
            "address": f"Resolved address {input_index}",
            "normalized_address": f"Normalized address {input_index}",
            "lat": 45.035 + input_index / 1000,
            "lon": 39.028 + input_index / 1000,
        },
        "score": {
            "total_score": total_score,
            "confidence_score": 88 - input_index,
            "scoring_version": "v1.0",
            "decision": DECISION_RULES.consider,
            "details": {
                "demand_score": 35,
                "competition_score": 12,
                "rent_score": 15,
                "premises_score": 10,
                "accessibility_score": 8,
            },
        },
        "finance": {
            "monthly_costs": 295_000,
            "required_gross_income": 375_000,
            "expected_gross_income_by_user": 360_000,
            "net_profit": net_profit,
            "payback_months": payback_months,
        },
        "competitors": {
            "competitors_300m": 1 + input_index,
            "competitors_500m": 3 + input_index,
            "competitors_700m": 5 + input_index,
            "nearest_competitor_distance_m": 180,
            "average_competitor_distance_m": 420,
        },
        "assumptions": [
            "expected_gross_income_by_user is a user hypothesis",
            "Shared assumption",
        ],
        "warnings": [
            "Marketplace requirements need manual verification",
            "Shared warning",
        ],
        "trade_offs": [],
    }


def _failed_candidate() -> dict[str, Any]:
    return {
        "candidate_id": "candidate-3",
        "input_index": 2,
        "label": "Candidate C",
        "input_address": "Краснодар, Восточно-Кругликовская 30",
        "status": "failed",
        "error": {
            "code": "ADDRESS_AMBIGUOUS",
            "message": "Найдено несколько вариантов адреса",
            "details": "ambiguous address",
            "suggestions": [
                {
                    "address": "г Краснодар, ул Восточно-Кругликовская, д 30",
                    "lat": 45.035,
                    "lon": 39.028,
                    "confidence": 0.82,
                },
                {
                    "address": "г Краснодар, ул Восточно-Кругликовская, д 30/1",
                    "lat": 45.036,
                    "lon": 39.029,
                    "confidence": 0.78,
                },
            ],
        },
    }
