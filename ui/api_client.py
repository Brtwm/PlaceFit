"""Small HTTP client for the Streamlit UI."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx

DEFAULT_API_BASE_URL = "http://localhost:8000/api/v1"


@dataclass(frozen=True)
class ApiError:
    """Normalized API/client error for UI rendering."""

    status_code: int | None
    code: str
    message: str
    details: str | None = None
    suggestions: list[dict[str, Any]] | None = None
    raw: Any | None = None


class ApiClient:
    """Minimal client for PlaceFit API endpoints used by Streamlit."""

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = normalize_api_base_url(
            base_url or os.getenv("PLACEFIT_API_BASE_URL") or DEFAULT_API_BASE_URL,
        )

    def health(self) -> dict[str, Any] | ApiError:
        health_url = self.base_url.removesuffix("/api/v1") + "/health"
        return self._request("GET", health_url, timeout=5.0, absolute_url=True)

    def analyze(self, payload: dict[str, Any]) -> dict[str, Any] | ApiError:
        return self._request("POST", "/analyze", json=payload, timeout=60.0)

    def compare_locations(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any] | ApiError:
        return self._request(
            "POST",
            "/locations/compare",
            json=payload,
            timeout=120.0,
        )

    def list_locations(self, params: dict[str, Any]) -> dict[str, Any] | ApiError:
        clean_params = {
            key: value for key, value in params.items() if value is not None
        }
        return self._request("GET", "/locations", params=clean_params, timeout=20.0)

    def get_location(self, location_id: int) -> dict[str, Any] | ApiError:
        return self._request("GET", f"/locations/{location_id}", timeout=20.0)

    def get_compare_session(self, compare_id: int) -> dict[str, Any] | ApiError:
        return self._request("GET", f"/locations/compare/{compare_id}", timeout=20.0)

    def _request(
        self,
        method: str,
        path: str,
        *,
        timeout: float,
        absolute_url: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any] | ApiError:
        url = path if absolute_url else f"{self.base_url}{path}"
        try:
            response = httpx.request(method, url, timeout=timeout, **kwargs)
        except httpx.TimeoutException as exc:
            return ApiError(
                status_code=None,
                code="TIMEOUT",
                message="Сервер не ответил вовремя.",
                details=str(exc),
            )
        except httpx.RequestError as exc:
            return ApiError(
                status_code=None,
                code="CONNECTION_ERROR",
                message="Не удалось подключиться к backend.",
                details=str(exc),
            )

        try:
            payload = response.json()
        except ValueError:
            return ApiError(
                status_code=response.status_code,
                code="NON_JSON_RESPONSE",
                message="Backend вернул ответ в неизвестном формате.",
                details=response.text[:1000],
            )

        if response.is_error:
            return _api_error_from_payload(response.status_code, payload)

        if not isinstance(payload, dict):
            return ApiError(
                status_code=response.status_code,
                code="INVALID_RESPONSE",
                message="Backend вернул неожиданный формат данных.",
                raw=payload,
            )
        return payload


def normalize_api_base_url(value: str) -> str:
    """Return a normalized API base URL without a trailing slash."""

    normalized = value.strip().rstrip("/")
    return normalized or DEFAULT_API_BASE_URL


def is_api_error(value: dict[str, Any] | ApiError) -> bool:
    """Return whether a response is a normalized API error."""

    return isinstance(value, ApiError)


def _api_error_from_payload(status_code: int, payload: Any) -> ApiError:
    if isinstance(payload, dict) and isinstance(payload.get("error"), dict):
        error = payload["error"]
        return ApiError(
            status_code=status_code,
            code=str(error.get("code") or "API_ERROR"),
            message=str(error.get("message") or "Backend вернул ошибку."),
            details=error.get("details"),
            suggestions=error.get("suggestions"),
            raw=payload,
        )

    if status_code == 422 and isinstance(payload, dict):
        return ApiError(
            status_code=status_code,
            code="VALIDATION_ERROR",
            message="Backend отклонил введённые данные.",
            details=str(payload.get("detail")),
            raw=payload,
        )

    return ApiError(
        status_code=status_code,
        code="API_ERROR",
        message="Backend вернул ошибку.",
        raw=payload,
    )
