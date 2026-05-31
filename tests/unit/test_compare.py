from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest
from app.config.scoring_rules import DECISION_RULES
from app.providers.geocoder.base import GeocodingCandidate
from app.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.schemas.compare import CompareRequest
from app.services.analysis import AnalysisServiceError
from app.services.compare import CompareService


class FakeAnalysisService:
    def __init__(
        self,
        outcomes: dict[str, AnalysisResponse | AnalysisServiceError | Any],
    ) -> None:
        self.outcomes = outcomes
        self.requests: list[AnalysisRequest] = []

    def analyze(self, request: AnalysisRequest) -> AnalysisResponse | Any:
        self.requests.append(request)
        outcome = self.outcomes[request.address]
        if isinstance(outcome, AnalysisServiceError):
            raise outcome
        return outcome


def test_compare_ranks_by_total_score_descending() -> None:
    service = _compare_service(
        {
            "Candidate 1": _analysis_response("Candidate 1", total_score=70),
            "Candidate 2": _analysis_response("Candidate 2", total_score=90),
        },
    )

    response = service.compare(_compare_request("Candidate 1", "Candidate 2"))

    assert [candidate.candidate_id for candidate in response.ranked_candidates] == [
        "candidate-2",
        "candidate-1",
    ]
    assert [candidate.rank for candidate in response.ranked_candidates] == [1, 2]


def test_compare_ties_by_confidence_descending() -> None:
    service = _compare_service(
        {
            "Candidate 1": _analysis_response(
                "Candidate 1",
                total_score=80,
                confidence_score=70,
            ),
            "Candidate 2": _analysis_response(
                "Candidate 2",
                total_score=80,
                confidence_score=95,
            ),
        },
    )

    response = service.compare(_compare_request("Candidate 1", "Candidate 2"))

    assert [candidate.candidate_id for candidate in response.ranked_candidates] == [
        "candidate-2",
        "candidate-1",
    ]


def test_compare_ties_by_decision_severity() -> None:
    service = _compare_service(
        {
            "Candidate 1": _analysis_response(
                "Candidate 1",
                decision=DECISION_RULES.likely_no,
            ),
            "Candidate 2": _analysis_response(
                "Candidate 2",
                decision=DECISION_RULES.check_more,
            ),
            "Candidate 3": _analysis_response(
                "Candidate 3",
                decision=DECISION_RULES.consider,
            ),
        },
    )

    response = service.compare(
        _compare_request("Candidate 1", "Candidate 2", "Candidate 3"),
    )

    assert [candidate.candidate_id for candidate in response.ranked_candidates] == [
        "candidate-3",
        "candidate-2",
        "candidate-1",
    ]


def test_compare_ties_by_net_profit_descending_with_nulls_last() -> None:
    service = _compare_service(
        {
            "Candidate 1": _analysis_response("Candidate 1", net_profit=10_000),
            "Candidate 2": _analysis_response("Candidate 2", net_profit=None),
            "Candidate 3": _analysis_response("Candidate 3", net_profit=20_000),
        },
    )

    response = service.compare(
        _compare_request("Candidate 1", "Candidate 2", "Candidate 3"),
    )

    assert [candidate.candidate_id for candidate in response.ranked_candidates] == [
        "candidate-3",
        "candidate-1",
        "candidate-2",
    ]


def test_compare_ties_by_payback_months_ascending_with_nulls_last() -> None:
    service = _compare_service(
        {
            "Candidate 1": _analysis_response(
                "Candidate 1",
                net_profit=10_000,
                payback_months=12.0,
            ),
            "Candidate 2": _analysis_response(
                "Candidate 2",
                net_profit=10_000,
                payback_months=None,
            ),
            "Candidate 3": _analysis_response(
                "Candidate 3",
                net_profit=10_000,
                payback_months=8.0,
            ),
        },
    )

    response = service.compare(
        _compare_request("Candidate 1", "Candidate 2", "Candidate 3"),
    )

    assert [candidate.candidate_id for candidate in response.ranked_candidates] == [
        "candidate-3",
        "candidate-1",
        "candidate-2",
    ]


def test_compare_uses_original_input_order_for_exact_ties() -> None:
    service = _compare_service(
        {
            "Candidate 1": _analysis_response("Candidate 1"),
            "Candidate 2": _analysis_response("Candidate 2"),
            "Candidate 3": _analysis_response("Candidate 3"),
        },
    )

    response = service.compare(
        _compare_request("Candidate 1", "Candidate 2", "Candidate 3"),
    )

    assert [candidate.candidate_id for candidate in response.ranked_candidates] == [
        "candidate-1",
        "candidate-2",
        "candidate-3",
    ]


def test_compare_returns_mixed_success_and_failure() -> None:
    service = _compare_service(
        {
            "Good": _analysis_response("Good", total_score=80),
            "Bad": AnalysisServiceError(
                "GEOCODING_FAILED",
                "Не удалось геокодировать адрес",
                details="not found",
            ),
        },
    )

    response = service.compare(_compare_request("Good", "Bad"))

    assert [candidate.candidate_id for candidate in response.ranked_candidates] == [
        "candidate-1",
    ]
    assert response.failed_candidates[0].candidate_id == "candidate-2"
    assert response.failed_candidates[0].input_index == 1
    assert response.failed_candidates[0].error.code == "GEOCODING_FAILED"
    assert response.failed_candidates[0].error.details == "not found"
    assert response.summary.requested_count == 2
    assert response.summary.successful_count == 1
    assert response.summary.failed_count == 1


def test_compare_preserves_ambiguous_address_suggestions() -> None:
    service = _compare_service(
        {
            "Good": _analysis_response("Good"),
            "Ambiguous": AnalysisServiceError(
                "ADDRESS_AMBIGUOUS",
                "Найдено несколько вариантов адреса",
                suggestions=[
                    GeocodingCandidate(
                        address="Краснодар, Восточно-Кругликовская 30",
                        normalized_address=(
                            "г Краснодар, ул Восточно-Кругликовская, д 30"
                        ),
                        lat=45.035,
                        lon=39.028,
                        provider="fake",
                        confidence=0.82,
                    ),
                ],
            ),
        },
    )

    response = service.compare(_compare_request("Good", "Ambiguous"))

    error = response.failed_candidates[0].error
    assert error.code == "ADDRESS_AMBIGUOUS"
    assert error.suggestions is not None
    assert error.suggestions[0].address == (
        "г Краснодар, ул Восточно-Кругликовская, д 30"
    )
    assert error.suggestions[0].confidence == 0.82


def test_compare_returns_visible_errors_when_all_candidates_fail() -> None:
    service = _compare_service(
        {
            "Bad 1": AnalysisServiceError(
                "CITY_NOT_SUPPORTED",
                "MVP поддерживает только адреса в Краснодаре",
            ),
            "Bad 2": AnalysisServiceError(
                "GEOCODING_FAILED",
                "Не удалось геокодировать адрес",
            ),
        },
    )

    response = service.compare(_compare_request("Bad 1", "Bad 2"))

    assert response.ranked_candidates == []
    assert [candidate.error.code for candidate in response.failed_candidates] == [
        "CITY_NOT_SUPPORTED",
        "GEOCODING_FAILED",
    ]
    assert response.summary.successful_count == 0
    assert response.summary.failed_count == 2


def test_compare_does_not_require_report_text_for_ranking() -> None:
    base = _analysis_response("Candidate 1", total_score=80)
    analysis_without_report = SimpleNamespace(
        location=base.location,
        competitors=base.competitors,
        score=base.score,
        finance=base.finance,
        marketplace_requirements=base.marketplace_requirements,
    )
    service = _compare_service(
        {
            "Candidate 1": analysis_without_report,
            "Candidate 2": _analysis_response("Candidate 2", total_score=90),
        },
    )

    response = service.compare(_compare_request("Candidate 1", "Candidate 2"))

    assert [candidate.candidate_id for candidate in response.ranked_candidates] == [
        "candidate-2",
        "candidate-1",
    ]


def test_compare_does_not_call_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_network(*args: object, **kwargs: object) -> None:
        msg = "network calls are not allowed in compare unit tests"
        raise AssertionError(msg)

    import socket

    monkeypatch.setattr(socket, "create_connection", fail_network)
    service = _compare_service(
        {
            "Candidate 1": _analysis_response("Candidate 1", total_score=80),
            "Candidate 2": _analysis_response("Candidate 2", total_score=90),
        },
    )

    response = service.compare(_compare_request("Candidate 1", "Candidate 2"))

    assert response.ranked_candidates[0].candidate_id == "candidate-2"


def _compare_service(
    outcomes: dict[str, AnalysisResponse | AnalysisServiceError | Any],
) -> CompareService:
    return CompareService(FakeAnalysisService(outcomes))  # type: ignore[arg-type]


def _compare_request(*addresses: str) -> CompareRequest:
    return CompareRequest.model_validate(
        {
            "candidates": [
                {
                    "label": f"Candidate {index + 1}",
                    "analysis_request": _analysis_request(address),
                }
                for index, address in enumerate(addresses)
            ],
        },
    )


def _analysis_request(address: str) -> dict[str, object]:
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


def _analysis_response(
    address: str,
    *,
    total_score: int = 80,
    confidence_score: int = 80,
    decision: str = DECISION_RULES.consider,
    net_profit: int | None = 65_000,
    payback_months: float | None = 9.2,
) -> AnalysisResponse:
    candidate_number = _candidate_number(address)
    return AnalysisResponse.model_validate(
        {
            "location": {
                "id": candidate_number,
                "address": address,
                "normalized_address": f"г Краснодар, {address}",
                "lat": 45.035,
                "lon": 39.028,
            },
            "competitors": {
                "competitors_300m": 1,
                "competitors_500m": 3,
                "competitors_700m": 5,
                "nearest_competitor_distance_m": 180,
                "average_competitor_distance_m": 420,
                "list": [],
            },
            "score": {
                "total_score": total_score,
                "confidence_score": confidence_score,
                "scoring_version": "v1.0",
                "decision": decision,
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
            "marketplace_requirements": {
                "ozon": _marketplace_requirement(),
                "wildberries": _marketplace_requirement(),
                "yandex_market": _marketplace_requirement(),
            },
            "report": {
                "status": "fallback",
                "text": f"Report text for {address}",
                "provider": "fallback",
                "model": "none",
                "prompt_version": "v1.0",
            },
            "checklist": ["Проверить конкурентов вручную в картах."],
            "data_sources": [],
            "created_at": datetime(2026, 5, 31, 12, 0, tzinfo=UTC),
        },
    )


def _marketplace_requirement() -> dict[str, object]:
    return {
        "status": "needs_manual_check",
        "needs_manual_check": True,
        "manual_checks": ["Проверить вручную"],
        "warning": "Требования маркетплейсов нужно сверить с официальными источниками.",
    }


def _candidate_number(address: str) -> int:
    digits = "".join(character for character in address if character.isdigit())
    if digits:
        return int(digits)
    return sum(ord(character) for character in address) % 10_000 + 1
