from typing import Any

import httpx
from app.providers.geocoder.dgis import DgisGeocoder, parse_dgis_geocode_response


def test_dgis_geocoder_parses_single_krasnodar_result() -> None:
    result = parse_dgis_geocode_response(
        {
            "result": {
                "items": [
                    {
                        "id": "dgis-1",
                        "full_name": "Краснодар, Красная, 1",
                        "point": {"lat": 45.025, "lon": 38.971},
                        "adm_div": [{"type": "city", "name": "Краснодар"}],
                    },
                ],
            },
        },
    )

    assert result.status == "resolved"
    assert result.provider == "2gis"
    assert len(result.candidates) == 1
    candidate = result.candidates[0]
    assert candidate.external_id == "dgis-1"
    assert candidate.city == "Краснодар"
    assert candidate.lat == 45.025
    assert candidate.lon == 38.971


def test_dgis_geocoder_parses_multiple_results_as_ambiguous() -> None:
    result = parse_dgis_geocode_response(
        {
            "result": {
                "items": [
                    {
                        "id": "dgis-1",
                        "full_name": "Краснодар, Красная, 1",
                        "point": {"lat": 45.025, "lon": 38.971},
                        "adm_div": [{"type": "city", "name": "Краснодар"}],
                    },
                    {
                        "id": "dgis-2",
                        "full_name": "Краснодар, Красная, 1/1",
                        "point": {"lat": 45.026, "lon": 38.972},
                        "adm_div": [{"type": "city", "name": "Краснодар"}],
                    },
                ],
            },
        },
    )

    assert result.status == "ambiguous"
    assert result.error_code == "ADDRESS_AMBIGUOUS"
    assert len(result.candidates) == 2


def test_dgis_geocoder_empty_result_is_not_found() -> None:
    result = parse_dgis_geocode_response({"result": {"items": []}})

    assert result.status == "not_found"
    assert result.error_code == "GEOCODING_FAILED"


def test_dgis_geocoder_detects_outside_city() -> None:
    result = parse_dgis_geocode_response(
        {
            "result": {
                "items": [
                    {
                        "id": "dgis-moscow",
                        "full_name": "Москва, Тверская, 1",
                        "point": {"lat": 55.757, "lon": 37.613},
                        "adm_div": [{"type": "city", "name": "Москва"}],
                    },
                ],
            },
        },
    )

    assert result.status == "city_not_supported"
    assert result.error_code == "CITY_NOT_SUPPORTED"
    assert result.candidates[0].city == "Москва"


def test_dgis_geocoder_malformed_response_is_not_found() -> None:
    result = parse_dgis_geocode_response({"unexpected": {"shape": True}})

    assert result.status == "not_found"
    assert result.error_code == "GEOCODING_FAILED"


def test_dgis_geocoder_does_not_expose_api_key_on_http_error() -> None:
    secret = "secret-dgis-key"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=500, json={"error": "boom"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = DgisGeocoder(
        api_key=secret,
        base_url="https://catalog.api.2gis.com",
        timeout_seconds=1.0,
        client=client,
    )

    result = provider.geocode("Краснодар, Красная, 1")
    serialized = repr(result)

    assert result.status == "not_found"
    assert secret not in serialized


def test_dgis_geocoder_sends_expected_query_without_snapshotting_key() -> None:
    seen_params: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen_params.update(dict(request.url.params))
        return httpx.Response(
            status_code=200,
            json={
                "result": {
                    "items": [
                        {
                            "id": "dgis-1",
                            "full_name": "Краснодар, Красная, 1",
                            "point": {"lat": 45.025, "lon": 38.971},
                        },
                    ],
                },
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = DgisGeocoder(
        api_key="test-key",
        base_url="https://catalog.api.2gis.com",
        timeout_seconds=1.0,
        client=client,
    )

    result = provider.geocode("Краснодар, Красная, 1")

    assert result.status == "resolved"
    assert seen_params["q"] == "Краснодар, Красная, 1"
    assert seen_params["fields"] == "items.point,items.adm_div"
    assert "key" in seen_params
