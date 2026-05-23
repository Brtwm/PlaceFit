"""Fake geocoder provider backed by deterministic fixture-shaped payloads."""

from collections.abc import Mapping, Sequence
from typing import cast

from app.providers.geocoder.base import (
    GeocodingCandidate,
    GeocodingProviderResult,
    GeocodingStatus,
)
from app.schemas.error import ErrorCode


class FakeGeocoder:
    """Deterministic geocoder for offline tests and mocked orchestration."""

    def __init__(self, payloads: Sequence[Mapping[str, object]]) -> None:
        self._results_by_query = {
            _normalize_query(_required_str(payload, "query")): parse_geocode_payload(
                payload,
            )
            for payload in payloads
        }
        provider_names = {
            result.provider for result in self._results_by_query.values()
        }
        self.provider_name = "+".join(sorted(provider_names)) or "fake"

    def geocode(self, address: str) -> GeocodingProviderResult:
        """Return a fixture result or a deterministic not-found result."""

        result = self._results_by_query.get(_normalize_query(address))
        if result is not None:
            return result

        return GeocodingProviderResult(
            status="not_found",
            provider=self.provider_name,
            error_code="GEOCODING_FAILED",
            message="Address is not present in fake geocoder fixtures.",
        )


def parse_geocode_payload(payload: Mapping[str, object]) -> GeocodingProviderResult:
    """Parse a small 2GIS/Yandex-like synthetic geocoding fixture."""

    provider = _required_str(payload, "provider")
    status = _parse_status(_required_str(payload, "status"))
    raw_results = _optional_sequence(payload, "results")
    candidates = tuple(
        _parse_candidate(provider, _string_key_mapping(item))
        for item in raw_results
        if isinstance(item, Mapping)
    )
    error_code = payload.get("error_code")
    message = payload.get("message")

    return GeocodingProviderResult(
        status=status,
        provider=provider,
        candidates=candidates,
        error_code=cast(ErrorCode, error_code)
        if _is_error_code(error_code)
        else None,
        message=message if isinstance(message, str) else None,
    )


def _parse_candidate(
    provider: str,
    payload: Mapping[str, object],
) -> GeocodingCandidate:
    return GeocodingCandidate(
        address=_required_str(payload, "address"),
        normalized_address=_required_str(payload, "normalized_address"),
        lat=_required_float(payload, "lat"),
        lon=_required_float(payload, "lon"),
        provider=provider,
        confidence=_optional_float(payload, "confidence"),
        external_id=_optional_str(payload, "external_id"),
        city=_optional_str(payload, "city"),
        metadata=_optional_mapping(payload, "metadata"),
    )


def _normalize_query(value: str) -> str:
    return " ".join(value.casefold().split())


def _parse_status(value: str) -> GeocodingStatus:
    if value in {"resolved", "ambiguous", "not_found", "city_not_supported"}:
        return cast("GeocodingStatus", value)
    raise ValueError(f"Unsupported geocoding status: {value}")


def _required_str(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise ValueError(f"Expected string field: {key}")
    return value


def _optional_str(payload: Mapping[str, object], key: str) -> str | None:
    value = payload.get(key)
    if value is None or isinstance(value, str):
        return value
    raise ValueError(f"Expected optional string field: {key}")


def _required_float(payload: Mapping[str, object], key: str) -> float:
    value = payload.get(key)
    if isinstance(value, int | float):
        return float(value)
    raise ValueError(f"Expected numeric field: {key}")


def _optional_float(payload: Mapping[str, object], key: str) -> float | None:
    value = payload.get(key)
    if value is None:
        return None
    if isinstance(value, int | float):
        return float(value)
    raise ValueError(f"Expected optional numeric field: {key}")


def _optional_sequence(
    payload: Mapping[str, object],
    key: str,
) -> Sequence[object]:
    value = payload.get(key)
    if value is None:
        return ()
    if isinstance(value, Sequence) and not isinstance(value, str):
        return value
    raise ValueError(f"Expected sequence field: {key}")


def _optional_mapping(
    payload: Mapping[str, object],
    key: str,
) -> Mapping[str, object]:
    value = payload.get(key)
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return {str(map_key): map_value for map_key, map_value in value.items()}
    raise ValueError(f"Expected mapping field: {key}")


def _is_error_code(value: object) -> bool:
    return value in {
        "VALIDATION_ERROR",
        "GEOCODING_FAILED",
        "CITY_NOT_SUPPORTED",
        "ADDRESS_AMBIGUOUS",
        "COMPETITOR_SEARCH_FAILED",
        "LLM_FAILED",
        "NOT_FOUND",
        "INTERNAL_ERROR",
    }


def _string_key_mapping(payload: Mapping[object, object]) -> Mapping[str, object]:
    return {str(key): value for key, value in payload.items()}
