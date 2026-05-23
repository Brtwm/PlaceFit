"""POI search provider contracts."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal, Protocol

BusinessType = Literal["pvz"]


@dataclass(frozen=True)
class PoiCandidate:
    """Single provider POI candidate before service-level distance enrichment."""

    provider: str
    external_id: str
    name: str
    brand: str
    category: str
    lat: float
    lon: float
    address: str
    business_type: BusinessType = "pvz"
    rating: float | None = None
    reviews_count: int | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class PoiSearchProviderResult:
    """Provider-level POI search result without HTTP or DB concerns."""

    provider: str
    pois: tuple[PoiCandidate, ...]


class PoiSearchProvider(Protocol):
    """POI search provider interface for fake and future real providers."""

    provider_name: str

    def search(
        self,
        *,
        lat: float,
        lon: float,
        radius_m: int,
        business_type: BusinessType,
    ) -> PoiSearchProviderResult:
        """Return deterministic POIs near a coordinate."""
