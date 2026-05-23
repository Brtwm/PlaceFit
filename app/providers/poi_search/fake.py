"""Fake POI search provider backed by deterministic fixture-shaped payloads."""

from collections.abc import Mapping, Sequence

from app.providers.poi_search.base import (
    BusinessType,
    PoiCandidate,
    PoiSearchProviderResult,
)


class FakePoiSearchProvider:
    """Deterministic POI search provider for offline tests."""

    def __init__(self, payload: Mapping[str, object]) -> None:
        self._result = parse_poi_payload(payload)
        self.provider_name = self._result.provider

    def search(
        self,
        *,
        lat: float,
        lon: float,
        radius_m: int,
        business_type: BusinessType,
    ) -> PoiSearchProviderResult:
        """Return fixture POIs for the requested MVP business type."""

        del lat, lon, radius_m
        return PoiSearchProviderResult(
            provider=self.provider_name,
            pois=tuple(
                poi for poi in self._result.pois if poi.business_type == business_type
            ),
        )


def parse_poi_payload(payload: Mapping[str, object]) -> PoiSearchProviderResult:
    """Parse a small OSM/2GIS-like synthetic POI fixture."""

    provider = _required_str(payload, "provider")
    raw_pois = _optional_sequence(payload, "pois")
    pois = tuple(
        _parse_poi(provider, _string_key_mapping(item))
        for item in raw_pois
        if isinstance(item, Mapping)
    )
    return PoiSearchProviderResult(provider=provider, pois=pois)


def _parse_poi(provider: str, payload: Mapping[str, object]) -> PoiCandidate:
    return PoiCandidate(
        provider=provider,
        external_id=_required_str(payload, "external_id"),
        name=_required_str(payload, "name"),
        brand=_required_str(payload, "brand"),
        category=_required_str(payload, "category"),
        lat=_required_float(payload, "lat"),
        lon=_required_float(payload, "lon"),
        address=_required_str(payload, "address"),
        business_type=_parse_business_type(payload.get("business_type")),
        rating=_optional_float(payload, "rating"),
        reviews_count=_optional_int(payload, "reviews_count"),
        metadata=_optional_mapping(payload, "metadata"),
    )


def _parse_business_type(value: object) -> BusinessType:
    if value in {None, "pvz"}:
        return "pvz"
    raise ValueError(f"Unsupported business_type in fake POI fixture: {value}")


def _required_str(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise ValueError(f"Expected string field: {key}")
    return value


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


def _optional_int(payload: Mapping[str, object], key: str) -> int | None:
    value = payload.get(key)
    if value is None:
        return None
    if isinstance(value, int):
        return value
    raise ValueError(f"Expected optional integer field: {key}")


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


def _string_key_mapping(payload: Mapping[object, object]) -> Mapping[str, object]:
    return {str(key): value for key, value in payload.items()}
