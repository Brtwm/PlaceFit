"""Geocoding service with Krasnodar-only MVP validation."""

from dataclasses import dataclass

from app.providers.geocoder.base import (
    GeocoderProvider,
    GeocodingCandidate,
    GeocodingProviderResult,
    GeocodingStatus,
)
from app.schemas.error import ErrorCode
from app.services.cache import InMemoryCache, normalize_cache_key

SUPPORTED_CITY = "краснодар"


@dataclass(frozen=True)
class GeocodingServiceResult:
    """Service-level geocoding result for Phase 6 API adaptation."""

    status: GeocodingStatus
    provider: str
    candidates: tuple[GeocodingCandidate, ...] = ()
    error_code: ErrorCode | None = None
    message: str | None = None


class GeocodingService:
    """Geocode and validate one MVP address without DB or network coupling."""

    def __init__(
        self,
        provider: GeocoderProvider,
        *,
        cache: InMemoryCache[str, GeocodingServiceResult] | None = None,
    ) -> None:
        self._provider = provider
        self._cache = cache

    def geocode(self, address: str) -> GeocodingServiceResult:
        """Geocode an address and reject non-Krasnodar results deterministically."""

        cache_key = normalize_cache_key("geocode", address)
        if self._cache is not None:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        provider_result = self._provider.geocode(address)
        result = _validate_city(provider_result)

        if self._cache is not None:
            self._cache.set(cache_key, result)
        return result


def _validate_city(result: GeocodingProviderResult) -> GeocodingServiceResult:
    if result.status in {"not_found", "city_not_supported"}:
        return GeocodingServiceResult(
            status=result.status,
            provider=result.provider,
            candidates=result.candidates,
            error_code=result.error_code,
            message=result.message,
        )

    unsupported = [
        candidate
        for candidate in result.candidates
        if not _is_supported_city(candidate)
    ]
    if unsupported:
        return GeocodingServiceResult(
            status="city_not_supported",
            provider=result.provider,
            candidates=tuple(unsupported),
            error_code="CITY_NOT_SUPPORTED",
            message="MVP supports only Krasnodar addresses.",
        )

    if result.status == "ambiguous":
        return GeocodingServiceResult(
            status="ambiguous",
            provider=result.provider,
            candidates=result.candidates,
            error_code="ADDRESS_AMBIGUOUS",
            message=result.message or "Address has multiple matching candidates.",
        )

    return GeocodingServiceResult(
        status=result.status,
        provider=result.provider,
        candidates=result.candidates,
        error_code=result.error_code,
        message=result.message,
    )


def _is_supported_city(candidate: GeocodingCandidate) -> bool:
    city = (candidate.city or "").casefold()
    normalized_address = candidate.normalized_address.casefold()
    return city == SUPPORTED_CITY or f"г {SUPPORTED_CITY}" in normalized_address
