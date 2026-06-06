from copy import deepcopy
from typing import Any

from app.api.v1.deps import get_geocoding_service
from app.models import CompareSession
from app.providers.geocoder.fake import FakeGeocoder
from app.services.geocoding import GeocodingService
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session


def test_compare_accepts_two_valid_candidates(
    client: TestClient,
    db_session: Session,
) -> None:
    request_payload = _compare_request(
        _analysis_request(
            address="Краснодар, ул. Восточно-Кругликовская, 30",
            rent=70_000,
        ),
        _analysis_request(
            address="Краснодар, ул. Красная, 1",
            rent=150_000,
            high_density_area=False,
            new_residential_area=False,
            expected_gross_income_by_user=100_000,
        ),
    )
    response = client.post(
        "/api/v1/locations/compare",
        json=request_payload,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["compare_id"] is not None
    assert payload["summary"]["requested_count"] == 2
    assert payload["summary"]["successful_count"] == 2
    assert payload["summary"]["failed_count"] == 0
    assert payload["failed_candidates"] == []
    assert {candidate["status"] for candidate in payload["ranked_candidates"]} == {
        "success",
    }
    assert {candidate["input_index"] for candidate in payload["ranked_candidates"]} == {
        0,
        1,
    }
    assert all(
        candidate["source_analysis_id"] is not None
        for candidate in payload["ranked_candidates"]
    )

    ranking_rules = payload["ranking_rules"]
    assert ranking_rules["version"] == "v1.2-2"
    assert ranking_rules["uses_llm"] is False
    assert [key["field"] for key in ranking_rules["sort_keys"]] == [
        "score.total_score",
        "score.confidence_score",
        "score.decision",
        "finance.net_profit",
        "finance.payback_months",
        "input_index",
    ]
    assert [candidate["rank"] for candidate in payload["ranked_candidates"]] == [1, 2]
    scores = [
        candidate["score"]["total_score"]
        for candidate in payload["ranked_candidates"]
    ]
    assert scores == sorted(scores, reverse=True)

    session = db_session.scalar(select(CompareSession))
    assert session is not None
    assert session.id == payload["compare_id"]
    assert session.ranking_rules_version == ranking_rules["version"]
    assert session.request_snapshot["candidates"] == request_payload["candidates"]
    assert session.response_snapshot["compare_id"] == payload["compare_id"]
    assert len(session.response_snapshot["ranked_candidates"]) == 2
    assert all(
        candidate["source_analysis_id"] == candidate["location_summary"]["id"]
        for candidate in session.response_snapshot["ranked_candidates"]
    )

    saved_response = client.get(f"/api/v1/locations/compare/{payload['compare_id']}")
    assert saved_response.status_code == 200
    assert saved_response.json() == payload


def test_compare_rejects_one_candidate(client: TestClient) -> None:
    response = client.post(
        "/api/v1/locations/compare",
        json=_compare_request(_analysis_request()),
    )

    assert response.status_code == 422


def test_compare_rejects_six_candidates(client: TestClient) -> None:
    response = client.post(
        "/api/v1/locations/compare",
        json=_compare_request(*[_analysis_request() for _ in range(6)]),
    )

    assert response.status_code == 422


def test_compare_rejects_saved_analysis_reference_shape(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/locations/compare",
        json={
            "candidates": [
                {"label": "Saved candidate", "location_id": 1},
                {
                    "label": "New candidate",
                    "analysis_request": _analysis_request(),
                },
            ],
        },
    )

    assert response.status_code == 422


def test_compare_rejects_unsupported_business_type(client: TestClient) -> None:
    candidate = _analysis_request()
    candidate["business_type"] = "coffee"

    response = client.post(
        "/api/v1/locations/compare",
        json=_compare_request(
            candidate,
            _analysis_request("Краснодар, ул. Красная, 1"),
        ),
    )

    assert response.status_code == 422


def test_compare_returns_candidate_level_failure(
    client: TestClient,
    db_session: Session,
) -> None:
    response = client.post(
        "/api/v1/locations/compare",
        json=_compare_request(
            _analysis_request("Краснодар, ул. Восточно-Кругликовская, 30"),
            _analysis_request("Краснодар, ул. Неизвестная, 404"),
        ),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["requested_count"] == 2
    assert payload["summary"]["successful_count"] == 1
    assert payload["summary"]["failed_count"] == 1
    assert len(payload["ranked_candidates"]) == 1
    assert payload["failed_candidates"][0]["status"] == "failed"
    assert payload["failed_candidates"][0]["input_index"] == 1
    assert payload["failed_candidates"][0]["error"]["code"] == "GEOCODING_FAILED"
    assert payload["compare_id"] is not None

    session = db_session.get(CompareSession, payload["compare_id"])
    assert session is not None
    failed = session.response_snapshot["failed_candidates"][0]
    assert failed["error"]["code"] == "GEOCODING_FAILED"


def test_compare_preserves_ambiguous_candidate_suggestions(
    client: TestClient,
    db_session: Session,
) -> None:
    _override_geocoder(
        client,
        [
            _resolved_geocoder_payload(
                query="Краснодар, ул. Восточно-Кругликовская, 30",
                address="Краснодар, ул. Восточно-Кругликовская, 30",
                normalized_address="г Краснодар, ул Восточно-Кругликовская, д 30",
                lat=45.035,
                lon=39.028,
            ),
            {
                "provider": "yandex",
                "query": "Краснодар, Восточно-Кругликовская 30",
                "status": "ambiguous",
                "results": [
                    {
                        "address": "Краснодар, ул. Восточно-Кругликовская, 30",
                        "normalized_address": (
                            "г Краснодар, ул Восточно-Кругликовская, д 30"
                        ),
                        "city": "Краснодар",
                        "lat": 45.035,
                        "lon": 39.028,
                        "confidence": 0.82,
                    },
                    {
                        "address": "Краснодар, ул. Восточно-Кругликовская, 30/1",
                        "normalized_address": (
                            "г Краснодар, ул Восточно-Кругликовская, д 30/1"
                        ),
                        "city": "Краснодар",
                        "lat": 45.036,
                        "lon": 39.029,
                        "confidence": 0.78,
                    },
                ],
            },
        ],
    )

    response = client.post(
        "/api/v1/locations/compare",
        json=_compare_request(
            _analysis_request("Краснодар, ул. Восточно-Кругликовская, 30"),
            _analysis_request("Краснодар, Восточно-Кругликовская 30"),
        ),
    )

    assert response.status_code == 200
    failed = response.json()["failed_candidates"][0]
    assert failed["error"]["code"] == "ADDRESS_AMBIGUOUS"
    assert failed["error"]["suggestions"]
    assert failed["error"]["suggestions"][0]["address"] == (
        "г Краснодар, ул Восточно-Кругликовская, д 30"
    )
    assert failed["error"]["suggestions"][0]["confidence"] == 0.82

    compare_id = response.json()["compare_id"]
    assert compare_id is not None
    session = db_session.get(CompareSession, compare_id)
    assert session is not None
    saved_failed = session.response_snapshot["failed_candidates"][0]
    assert saved_failed["error"]["code"] == "ADDRESS_AMBIGUOUS"
    assert saved_failed["error"]["suggestions"][0]["confidence"] == 0.82


def test_compare_session_not_found_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/locations/compare/999999")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_compare_router_does_not_break_analyze(client: TestClient) -> None:
    response = client.post("/api/v1/analyze", json=_analysis_request())

    assert response.status_code == 200
    assert response.json()["report"]["status"] == "fallback"


def _compare_request(*analysis_requests: dict[str, object]) -> dict[str, object]:
    return {
        "candidates": [
            {
                "label": f"Candidate {index + 1}",
                "analysis_request": analysis_request,
            }
            for index, analysis_request in enumerate(analysis_requests)
        ],
    }


def _analysis_request(
    address: str = "Краснодар, ул. Восточно-Кругликовская, 30",
    *,
    rent: int = 85_000,
    high_density_area: bool = True,
    new_residential_area: bool = True,
    expected_gross_income_by_user: int = 360_000,
) -> dict[str, object]:
    return {
        "address": address,
        "business_type": "pvz",
        "rent": rent,
        "area_m2": 35,
        "floor": 1,
        "first_floor": True,
        "separate_entrance": True,
        "parking": True,
        "signage_possible": True,
        "storage_area": True,
        "repair_condition": "normal",
        "new_residential_area": new_residential_area,
        "high_density_area": high_density_area,
        "bus_stop_nearby": True,
        "good_visibility": True,
        "expected_gross_income_by_user": expected_gross_income_by_user,
        "investment": 600_000,
        "desired_profit": 80_000,
    }


def _resolved_geocoder_payload(
    *,
    query: str,
    address: str,
    normalized_address: str,
    lat: float,
    lon: float,
) -> dict[str, Any]:
    return {
        "provider": "2gis",
        "query": query,
        "status": "resolved",
        "results": [
            {
                "address": address,
                "normalized_address": normalized_address,
                "city": "Краснодар",
                "lat": lat,
                "lon": lon,
                "confidence": 0.95,
            },
        ],
    }


def _override_geocoder(
    client: TestClient,
    payloads: list[dict[str, Any]],
) -> None:
    copied_payloads = deepcopy(payloads)
    client.app.dependency_overrides[get_geocoding_service] = lambda: GeocodingService(
        FakeGeocoder(copied_payloads),
    )
