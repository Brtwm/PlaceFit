import socket
from typing import Any

from app.api.v1.deps import get_geocoding_service
from app.models import FinancialModel, Location, Report, Score, ScoringVersion
from app.providers.geocoder.fake import FakeGeocoder
from app.services.geocoding import GeocodingService
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session


def valid_request(
    address: str = "Краснодар, ул. Восточно-Кругликовская, 30",
) -> dict[str, object]:
    return {
        "address": address,
        "business_type": "pvz",
        "rent": 85000,
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
        "expected_gross_income_by_user": 360000,
        "investment": 600000,
        "desired_profit": 80000,
    }


def test_analyze_success_returns_full_response(client: TestClient) -> None:
    response = client.post("/api/v1/analyze", json=valid_request())

    assert response.status_code == 200
    payload = response.json()
    for field in (
        "location",
        "competitors",
        "score",
        "finance",
        "marketplace_requirements",
        "report",
        "checklist",
        "data_sources",
        "created_at",
    ):
        assert field in payload
    assert 0 <= payload["score"]["total_score"] <= 100
    assert 0 <= payload["score"]["confidence_score"] <= 100
    assert payload["score"]["scoring_version"] == "v1.0"
    assert set(payload["marketplace_requirements"]) == {
        "ozon",
        "wildberries",
        "yandex_market",
    }
    assert {
        item["status"] for item in payload["marketplace_requirements"].values()
    } == {"needs_manual_check"}
    assert payload["report"]["status"] == "fallback"
    assert payload["report"]["provider"] == "fallback"
    first_competitor = payload["competitors"]["list"][0]
    assert first_competitor["lat"] is not None
    assert first_competitor["lon"] is not None


def test_analyze_saves_to_db(client: TestClient, db_session: Session) -> None:
    response = client.post("/api/v1/analyze", json=valid_request())

    assert response.status_code == 200
    location_id = response.json()["location"]["id"]

    location = db_session.get(Location, location_id)
    score = db_session.scalar(select(Score).where(Score.location_id == location_id))
    finance = db_session.scalar(
        select(FinancialModel).where(FinancialModel.location_id == location_id),
    )
    report = db_session.scalar(
        select(Report).where(Report.location_id == location_id),
    )
    scoring_version = db_session.scalar(
        select(ScoringVersion).where(
            ScoringVersion.business_type == "pvz",
            ScoringVersion.version == "v1.0",
            ScoringVersion.active.is_(True),
        ),
    )

    assert location is not None
    assert score is not None
    assert finance is not None
    assert report is not None
    assert scoring_version is not None
    assert score.scoring_version_id == scoring_version.id


def test_analyze_ambiguous_address_returns_400_with_suggestions(
    client: TestClient,
) -> None:
    _override_geocoder(
        client,
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
    )

    response = client.post(
        "/api/v1/analyze",
        json=valid_request("Краснодар, Восточно-Кругликовская 30"),
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["error"]["code"] == "ADDRESS_AMBIGUOUS"
    assert payload["error"]["suggestions"]


def test_analyze_city_not_supported_returns_400(client: TestClient) -> None:
    _override_geocoder(
        client,
        {
            "provider": "2gis",
            "query": "Москва, ул. Тверская, 1",
            "status": "resolved",
            "results": [
                {
                    "address": "Москва, ул. Тверская, 1",
                    "normalized_address": "г Москва, ул Тверская, д 1",
                    "city": "Москва",
                    "lat": 55.757,
                    "lon": 37.613,
                    "confidence": 0.96,
                },
            ],
        },
    )

    response = client.post(
        "/api/v1/analyze",
        json=valid_request("Москва, ул. Тверская, 1"),
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "CITY_NOT_SUPPORTED"


def test_analyze_geocoding_failed_returns_502(client: TestClient) -> None:
    client.app.dependency_overrides[get_geocoding_service] = lambda: GeocodingService(
        FakeGeocoder([]),
    )

    response = client.post("/api/v1/analyze", json=valid_request())

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "GEOCODING_FAILED"


def test_analyze_validation_error_returns_422(client: TestClient) -> None:
    response = client.post("/api/v1/analyze", json={"address": "Краснодар"})

    assert response.status_code == 422


def test_analyze_does_not_call_network(
    client: TestClient,
    monkeypatch: Any,
) -> None:
    def fail_network(*args: object, **kwargs: object) -> None:
        msg = "network calls are not allowed in mocked analyze tests"
        raise AssertionError(msg)

    monkeypatch.setattr(socket, "create_connection", fail_network)

    response = client.post("/api/v1/analyze", json=valid_request())

    assert response.status_code == 200


def _override_geocoder(
    client: TestClient,
    payload: dict[str, object],
) -> None:
    client.app.dependency_overrides[get_geocoding_service] = lambda: GeocodingService(
        FakeGeocoder([payload]),
    )
