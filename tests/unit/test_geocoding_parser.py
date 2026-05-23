import json
import socket
from pathlib import Path
from typing import Any

from app.providers.geocoder.fake import FakeGeocoder, parse_geocode_payload
from app.services.geocoding import GeocodingService

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "providers"


def load_fixture(name: str) -> dict[str, Any]:
    with (FIXTURES_DIR / name).open(encoding="utf-8") as file:
        return json.load(file)


def test_parses_dgis_like_geocode_success_fixture() -> None:
    payload = load_fixture("dgis_geocode_success.json")

    result = parse_geocode_payload(payload)

    assert result.status == "resolved"
    assert result.provider == "2gis"
    assert len(result.candidates) == 1
    candidate = result.candidates[0]
    assert candidate.normalized_address == "г Краснодар, ул Красная, д 1"
    assert candidate.lat == 45.025
    assert candidate.lon == 38.971
    assert candidate.confidence == 0.95


def test_mocked_yandex_like_ambiguous_result_returns_suggestions() -> None:
    payload = load_fixture("yandex_geocode_ambiguous.json")
    provider = FakeGeocoder([payload])
    service = GeocodingService(provider)

    result = service.geocode("Краснодар, Восточно-Кругликовская 30")

    assert result.status == "ambiguous"
    assert result.error_code == "ADDRESS_AMBIGUOUS"
    assert len(result.candidates) == 2
    assert [candidate.normalized_address for candidate in result.candidates] == [
        "г Краснодар, ул Восточно-Кругликовская, д 30",
        "г Краснодар, ул Восточно-Кругликовская, д 30/1",
    ]


def test_city_validation_rejects_non_krasnodar_result() -> None:
    provider = FakeGeocoder(
        [
            {
                "provider": "2gis",
                "query": "Москва, ул. Тверская, 1",
                "status": "resolved",
                "results": [
                    {
                        "external_id": "dgis-moscow-tverskaya-1",
                        "address": "Москва, ул. Тверская, 1",
                        "normalized_address": "г Москва, ул Тверская, д 1",
                        "city": "Москва",
                        "lat": 55.757,
                        "lon": 37.613,
                        "confidence": 0.96,
                    },
                ],
            },
        ],
    )
    service = GeocodingService(provider)

    result = service.geocode("Москва, ул. Тверская, 1")

    assert result.status == "city_not_supported"
    assert result.error_code == "CITY_NOT_SUPPORTED"
    assert result.message == "MVP supports only Krasnodar addresses."


def test_fake_geocoder_does_not_require_network(
    monkeypatch: Any,
) -> None:
    def fail_network(*args: object, **kwargs: object) -> None:
        msg = "network calls are not allowed in fake geocoder tests"
        raise AssertionError(msg)

    monkeypatch.setattr(socket, "create_connection", fail_network)
    provider = FakeGeocoder([load_fixture("dgis_geocode_success.json")])
    service = GeocodingService(provider)

    result = service.geocode("Краснодар, ул. Красная, 1")

    assert result.status == "resolved"
