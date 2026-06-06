from typing import Any

import httpx
from ui.api_client import ApiClient, ApiError


def test_compare_locations_posts_to_compare_endpoint(
    monkeypatch,
) -> None:
    calls: list[tuple[str, str, dict[str, Any]]] = []
    response_payload = {"summary": {"requested_count": 2}}

    def fake_request(method: str, url: str, **kwargs: Any) -> httpx.Response:
        calls.append((method, url, kwargs))
        return httpx.Response(200, json=response_payload)

    monkeypatch.setattr(httpx, "request", fake_request)

    result = ApiClient("http://backend:8000/api/v1").compare_locations(
        {"candidates": []},
    )

    assert result == response_payload
    assert calls == [
        (
            "POST",
            "http://backend:8000/api/v1/locations/compare",
            {
                "json": {"candidates": []},
                "timeout": 120.0,
            },
        ),
    ]


def test_get_compare_session_uses_saved_compare_endpoint(monkeypatch) -> None:
    calls: list[tuple[str, str, dict[str, Any]]] = []
    response_payload = {"compare_id": 7}

    def fake_request(method: str, url: str, **kwargs: Any) -> httpx.Response:
        calls.append((method, url, kwargs))
        return httpx.Response(200, json=response_payload)

    monkeypatch.setattr(httpx, "request", fake_request)

    result = ApiClient("http://backend:8000/api/v1").get_compare_session(7)

    assert result == response_payload
    assert calls == [
        (
            "GET",
            "http://backend:8000/api/v1/locations/compare/7",
            {"timeout": 20.0},
        ),
    ]


def test_compare_locations_preserves_api_error(monkeypatch) -> None:
    def fake_request(method: str, url: str, **kwargs: Any) -> httpx.Response:
        return httpx.Response(
            400,
            json={
                "error": {
                    "code": "ADDRESS_AMBIGUOUS",
                    "message": "Найдено несколько вариантов адреса",
                    "suggestions": [{"address": "Краснодар, ул. Красная, 1"}],
                },
            },
        )

    monkeypatch.setattr(httpx, "request", fake_request)

    result = ApiClient("http://backend:8000/api/v1").compare_locations(
        {"candidates": []},
    )

    assert isinstance(result, ApiError)
    assert result.status_code == 400
    assert result.code == "ADDRESS_AMBIGUOUS"
    assert result.suggestions == [{"address": "Краснодар, ул. Красная, 1"}]
