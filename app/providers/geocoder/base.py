"""Geocoder provider contracts."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal, Protocol

from app.schemas.error import ErrorCode

GeocodingStatus = Literal[
    "resolved",
    "ambiguous",
    "not_found",
    "city_not_supported",
]


@dataclass(frozen=True)
class GeocodingCandidate:
    """Single normalized geocoding candidate from a provider."""

    address: str
    normalized_address: str
    lat: float
    lon: float
    provider: str
    confidence: float | None = None
    external_id: str | None = None
    city: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class GeocodingProviderResult:
    """Provider-level geocoding result without HTTP concerns."""

    status: GeocodingStatus
    provider: str
    candidates: tuple[GeocodingCandidate, ...] = ()
    error_code: ErrorCode | None = None
    message: str | None = None


class GeocoderProvider(Protocol):
    """Geocoder provider interface for fake and future real providers."""

    provider_name: str

    def geocode(self, address: str) -> GeocodingProviderResult:
        """Return deterministic provider result for an address."""
