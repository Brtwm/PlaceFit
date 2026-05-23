"""Deterministic POI deduplication utilities."""

from math import asin, cos, radians, sin, sqrt
from string import punctuation

from app.providers.poi_search.base import PoiCandidate

EARTH_RADIUS_M = 6_371_000
LIKELY_DUPLICATE_DISTANCE_M = 35

_BRAND_ALIASES = {
    "ozon": "ozon",
    "озон": "ozon",
    "wildberries": "wildberries",
    "вайлдберриз": "wildberries",
    "wb": "wildberries",
    "вб": "wildberries",
    "yandexmarket": "yandex_market",
    "яндексмаркет": "yandex_market",
    "яндекс": "yandex_market",
    "cdek": "cdek",
    "сдэк": "cdek",
    "boxberry": "boxberry",
    "боксберри": "boxberry",
}


def deduplicate_pois(pois: list[PoiCandidate]) -> list[PoiCandidate]:
    """Return POIs with exact and likely duplicates removed deterministically."""

    unique: list[PoiCandidate] = []
    seen_provider_ids: set[tuple[str, str]] = set()

    for poi in pois:
        provider_id = (poi.provider, poi.external_id)
        if provider_id in seen_provider_ids:
            continue
        if any(_is_likely_duplicate(poi, existing) for existing in unique):
            seen_provider_ids.add(provider_id)
            continue
        seen_provider_ids.add(provider_id)
        unique.append(poi)

    return unique


def normalize_brand_name(value: str) -> str:
    """Normalize brand/name for deterministic duplicate checks."""

    compact = _compact(value)
    for alias, canonical in _BRAND_ALIASES.items():
        if alias in compact:
            return canonical
    return compact


def distance_meters(
    *,
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """Calculate haversine distance in meters."""

    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)

    haversine = (
        sin(delta_lat / 2) ** 2
        + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
    )
    return 2 * EARTH_RADIUS_M * asin(sqrt(haversine))


def _is_likely_duplicate(candidate: PoiCandidate, existing: PoiCandidate) -> bool:
    if (
        distance_meters(
            lat1=candidate.lat,
            lon1=candidate.lon,
            lat2=existing.lat,
            lon2=existing.lon,
        )
        > LIKELY_DUPLICATE_DISTANCE_M
    ):
        return False

    candidate_name = normalize_brand_name(candidate.brand or candidate.name)
    existing_name = normalize_brand_name(existing.brand or existing.name)
    return candidate_name == existing_name


def _compact(value: str) -> str:
    remove_chars = punctuation + " «»„“”'`"
    translation = str.maketrans("", "", remove_chars)
    return "".join(value.casefold().translate(translation).split())
