from datetime import UTC, datetime
from typing import Any

import pytest
from app.config.scoring_rules import DECISION_RULES
from app.schemas.compare import (
    DEFAULT_COMPARE_RANKING_RULES,
    CompareRequest,
    CompareResponse,
)
from pydantic import ValidationError


def test_compare_request_accepts_two_candidates() -> None:
    request = CompareRequest.model_validate(
        {"candidates": [_candidate_request(0), _candidate_request(1)]},
    )

    assert len(request.candidates) == 2
    assert request.candidates[0].label == "Candidate 1"
    assert request.candidates[0].analysis_request.business_type == "pvz"


def test_compare_request_accepts_five_candidates() -> None:
    request = CompareRequest.model_validate(
        {"candidates": [_candidate_request(index) for index in range(5)]},
    )

    assert len(request.candidates) == 5


@pytest.mark.parametrize("candidate_count", [3, 4])
def test_compare_request_accepts_three_and_four_candidates(
    candidate_count: int,
) -> None:
    request = CompareRequest.model_validate(
        {
            "candidates": [
                _candidate_request(index) for index in range(candidate_count)
            ],
        },
    )

    assert len(request.candidates) == candidate_count


def test_compare_request_rejects_zero_candidates() -> None:
    with pytest.raises(ValidationError):
        CompareRequest.model_validate({"candidates": []})


def test_compare_request_rejects_one_candidate() -> None:
    with pytest.raises(ValidationError):
        CompareRequest.model_validate({"candidates": [_candidate_request(0)]})


def test_compare_request_rejects_six_candidates() -> None:
    with pytest.raises(ValidationError):
        CompareRequest.model_validate(
            {"candidates": [_candidate_request(index) for index in range(6)]},
        )


def test_compare_response_validates_successful_candidates() -> None:
    response = CompareResponse.model_validate(
        _compare_response(
            ranked_candidates=[
                _successful_candidate(input_index=0, rank=1),
                _successful_candidate(input_index=1, rank=2),
            ],
            failed_candidates=[],
            requested_count=2,
        ),
    )

    assert len(response.ranked_candidates) == 2
    assert response.failed_candidates == []
    assert response.summary.successful_count == 2


def test_compare_response_validates_failed_candidates() -> None:
    response = CompareResponse.model_validate(
        _compare_response(
            ranked_candidates=[],
            failed_candidates=[
                _failed_candidate(input_index=0),
                _failed_candidate(input_index=1),
            ],
            requested_count=2,
        ),
    )

    assert response.ranked_candidates == []
    assert len(response.failed_candidates) == 2
    assert response.failed_candidates[0].error.code == "ADDRESS_AMBIGUOUS"
    assert response.failed_candidates[0].error.suggestions


def test_compare_response_validates_mixed_candidates() -> None:
    response = CompareResponse.model_validate(
        _compare_response(
            ranked_candidates=[_successful_candidate(input_index=0, rank=1)],
            failed_candidates=[_failed_candidate(input_index=1)],
            requested_count=2,
        ),
    )

    assert len(response.ranked_candidates) == 1
    assert len(response.failed_candidates) == 1
    assert response.summary.successful_count == 1
    assert response.summary.failed_count == 1


def test_compare_response_contains_deterministic_ranking_rules() -> None:
    response = CompareResponse.model_validate(
        _compare_response(
            ranked_candidates=[_successful_candidate(input_index=0, rank=1)],
            failed_candidates=[_failed_candidate(input_index=1)],
            requested_count=2,
        ),
    )

    assert response.ranking_rules.uses_llm is False
    assert response.ranking_rules.version == "v1.2-2"
    assert [key.field for key in response.ranking_rules.sort_keys] == [
        "score.total_score",
        "score.confidence_score",
        "score.decision",
        "finance.net_profit",
        "finance.payback_months",
        "input_index",
    ]
    assert response.ranking_rules.decision_severity_order == [
        DECISION_RULES.consider,
        DECISION_RULES.check_more,
        DECISION_RULES.likely_no,
    ]


def _candidate_request(index: int) -> dict[str, Any]:
    return {
        "label": f"Candidate {index + 1}",
        "analysis_request": _analysis_request(
            f"Краснодар, ул. Восточно-Кругликовская, {30 + index}",
        ),
    }


def _analysis_request(address: str) -> dict[str, Any]:
    return {
        "address": address,
        "business_type": "pvz",
        "rent": 85_000,
        "area_m2": 35,
        "floor": 1,
        "first_floor": True,
        "separate_entrance": True,
        "parking": True,
        "signage_possible": True,
        "storage_area": True,
        "repair_condition": "normal",
        "new_residential_area": True,
        "high_density_area": True,
        "bus_stop_nearby": True,
        "good_visibility": True,
        "expected_gross_income_by_user": 360_000,
        "investment": 600_000,
        "desired_profit": 80_000,
    }


def _compare_response(
    *,
    ranked_candidates: list[dict[str, Any]],
    failed_candidates: list[dict[str, Any]],
    requested_count: int,
) -> dict[str, Any]:
    return {
        "compare_id": None,
        "created_at": datetime(2026, 5, 31, 12, 0, tzinfo=UTC),
        "ranking_rules": DEFAULT_COMPARE_RANKING_RULES.model_dump(mode="json"),
        "ranked_candidates": ranked_candidates,
        "failed_candidates": failed_candidates,
        "summary": {
            "requested_count": requested_count,
            "successful_count": len(ranked_candidates),
            "failed_count": len(failed_candidates),
        },
    }


def _successful_candidate(input_index: int, rank: int) -> dict[str, Any]:
    return {
        "candidate_id": f"candidate-{input_index + 1}",
        "input_index": input_index,
        "rank": rank,
        "label": f"Candidate {input_index + 1}",
        "input_address": f"Краснодар, ул. Восточно-Кругликовская, {30 + input_index}",
        "status": "success",
        "source_analysis_id": None,
        "location_summary": {
            "id": input_index + 1,
            "address": f"Краснодар, ул. Восточно-Кругликовская, {30 + input_index}",
            "normalized_address": (
                f"г Краснодар, ул Восточно-Кругликовская, д {30 + input_index}"
            ),
            "lat": 45.035,
            "lon": 39.028,
        },
        "score": {
            "total_score": 82 - input_index,
            "confidence_score": 90,
            "scoring_version": "v1.0",
            "decision": DECISION_RULES.consider,
            "details": {
                "demand_score": 35,
                "competition_score": 12,
                "rent_score": 15,
                "premises_score": 10,
                "accessibility_score": 10,
            },
        },
        "finance": {
            "monthly_costs": 295_000,
            "required_gross_income": 375_000,
            "expected_gross_income_by_user": 360_000,
            "net_profit": 65_000,
            "payback_months": 9.2,
        },
        "competitors": {
            "competitors_300m": 1,
            "competitors_500m": 3,
            "competitors_700m": 5,
            "nearest_competitor_distance_m": 180,
            "average_competitor_distance_m": 420,
        },
        "assumptions": ["expected_gross_income_by_user is a user hypothesis"],
        "warnings": ["Marketplace requirements need manual verification"],
        "trade_offs": ["Higher score but longer payback than another candidate"],
    }


def _failed_candidate(input_index: int) -> dict[str, Any]:
    return {
        "candidate_id": f"candidate-{input_index + 1}",
        "input_index": input_index,
        "label": f"Candidate {input_index + 1}",
        "input_address": f"Краснодар, Восточно-Кругликовская {30 + input_index}",
        "status": "failed",
        "error": {
            "code": "ADDRESS_AMBIGUOUS",
            "message": "Найдено несколько вариантов адреса",
            "suggestions": [
                {
                    "address": "г Краснодар, ул Восточно-Кругликовская, д 30",
                    "lat": 45.035,
                    "lon": 39.028,
                    "confidence": 0.82,
                },
            ],
        },
    }
