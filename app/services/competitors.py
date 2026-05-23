"""Competitor search aggregation over offline POI providers."""

from collections.abc import Sequence
from dataclasses import dataclass

from app.providers.poi_search.base import BusinessType, PoiCandidate, PoiSearchProvider
from app.services.deduplication import deduplicate_pois, distance_meters


@dataclass(frozen=True)
class CompetitorItem:
    """Competitor enriched with deterministic distance from analyzed location."""

    source: str
    external_id: str
    name: str
    brand: str
    category: str
    address: str
    lat: float
    lon: float
    distance_m: int
    rating: float | None = None
    reviews_count: int | None = None


@dataclass(frozen=True)
class CompetitorsResult:
    """DB-free competitor summary ready for Phase 6 orchestration."""

    competitors_300m: int
    competitors_500m: int
    competitors_700m: int
    nearest_competitor_distance_m: int | None
    average_competitor_distance_m: int | None
    competitors: tuple[CompetitorItem, ...]
    sources: tuple[str, ...]


def search_competitors(
    providers: Sequence[PoiSearchProvider],
    *,
    lat: float,
    lon: float,
    radius_m: int = 700,
    business_type: BusinessType = "pvz",
) -> CompetitorsResult:
    """Search, deduplicate, filter by radius, and summarize MVP competitors."""

    raw_pois: list[PoiCandidate] = []
    sources: set[str] = set()
    for provider in providers:
        result = provider.search(
            lat=lat,
            lon=lon,
            radius_m=radius_m,
            business_type=business_type,
        )
        sources.add(result.provider)
        raw_pois.extend(result.pois)

    competitors = tuple(
        sorted(
            (
                _to_competitor_item(poi, lat=lat, lon=lon)
                for poi in deduplicate_pois(raw_pois)
            ),
            key=lambda item: (
                item.distance_m,
                item.source,
                item.external_id,
            ),
        )
    )
    competitors = tuple(
        item for item in competitors if item.distance_m <= radius_m
    )
    distances = [item.distance_m for item in competitors]

    return CompetitorsResult(
        competitors_300m=sum(1 for distance in distances if distance <= 300),
        competitors_500m=sum(1 for distance in distances if distance <= 500),
        competitors_700m=sum(1 for distance in distances if distance <= 700),
        nearest_competitor_distance_m=min(distances) if distances else None,
        average_competitor_distance_m=round(sum(distances) / len(distances))
        if distances
        else None,
        competitors=competitors,
        sources=tuple(sorted(sources)),
    )


def _to_competitor_item(
    poi: PoiCandidate,
    *,
    lat: float,
    lon: float,
) -> CompetitorItem:
    distance = distance_meters(lat1=lat, lon1=lon, lat2=poi.lat, lon2=poi.lon)
    return CompetitorItem(
        source=poi.provider,
        external_id=poi.external_id,
        name=poi.name,
        brand=poi.brand,
        category=poi.category,
        address=poi.address,
        lat=poi.lat,
        lon=poi.lon,
        distance_m=round(distance),
        rating=poi.rating,
        reviews_count=poi.reviews_count,
    )
