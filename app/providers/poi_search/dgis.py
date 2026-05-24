"""2GIS POI search provider."""

from collections.abc import Mapping, Sequence

import httpx

from app.providers.poi_search.base import (
    BusinessType,
    PoiCandidate,
    PoiSearchProviderResult,
)
from app.services.deduplication import normalize_brand_name

PROVIDER_NAME = "2gis"
PVZ_QUERIES = ("пункт выдачи", "Ozon", "Wildberries", "Яндекс Маркет")


class DgisPoiSearchProvider:
    """Thin 2GIS Places client for MVP pickup-point competitors."""

    provider_name = PROVIDER_NAME

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        timeout_seconds: float,
        client: httpx.Client | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._client = client

    def search(
        self,
        *,
        lat: float,
        lon: float,
        radius_m: int,
        business_type: BusinessType,
    ) -> PoiSearchProviderResult:
        """Search 2GIS for MVP competitors, returning empty on provider errors."""

        if business_type != "pvz":
            return PoiSearchProviderResult(provider=PROVIDER_NAME, pois=())

        pois: list[PoiCandidate] = []
        seen_ids: set[str] = set()
        for query in PVZ_QUERIES:
            try:
                payload = self._get_json(
                    query=query,
                    lat=lat,
                    lon=lon,
                    radius_m=radius_m,
                )
            except (httpx.HTTPError, ValueError):
                continue
            for poi in parse_dgis_poi_response(payload).pois:
                if poi.external_id in seen_ids:
                    continue
                seen_ids.add(poi.external_id)
                pois.append(poi)

        return PoiSearchProviderResult(provider=PROVIDER_NAME, pois=tuple(pois))

    def _get_json(
        self,
        *,
        query: str,
        lat: float,
        lon: float,
        radius_m: int,
    ) -> Mapping[str, object]:
        params: dict[str, str | int] = {
            "q": query,
            "location": f"{lon},{lat}",
            "radius": radius_m,
            "fields": (
                "items.point,items.address,items.full_address_name,"
                "items.reviews,items.rubrics,items.brand"
            ),
            "key": self._api_key,
        }
        url = f"{self._base_url}/3.0/items"
        if self._client is not None:
            response = self._client.get(
                url,
                params=params,
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
            return _ensure_mapping(response.json())

        with httpx.Client(timeout=self._timeout_seconds) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            return _ensure_mapping(response.json())


def parse_dgis_poi_response(payload: Mapping[str, object]) -> PoiSearchProviderResult:
    """Parse a 2GIS Places response into POI candidates."""

    pois: list[PoiCandidate] = []
    seen_ids: set[str] = set()
    for raw_item in _items(payload):
        if not isinstance(raw_item, Mapping):
            continue
        poi = _poi(_string_key_mapping(raw_item))
        if poi is None or poi.external_id in seen_ids:
            continue
        seen_ids.add(poi.external_id)
        pois.append(poi)
    return PoiSearchProviderResult(provider=PROVIDER_NAME, pois=tuple(pois))


def _poi(item: Mapping[str, object]) -> PoiCandidate | None:
    point = item.get("point")
    if not isinstance(point, Mapping):
        return None
    point_mapping = _string_key_mapping(point)
    lat = _optional_float(point_mapping, "lat")
    lon = _optional_float(point_mapping, "lon")
    if lat is None or lon is None:
        return None

    external_id = _optional_str(item, "id")
    name = _first_str(item, ("name", "full_name"))
    if not external_id or not name:
        return None

    brand = _brand(item, name)
    return PoiCandidate(
        provider=PROVIDER_NAME,
        external_id=external_id,
        name=name,
        brand=brand,
        category="pvz",
        lat=lat,
        lon=lon,
        address=_address(item),
        rating=_rating(item),
        reviews_count=_reviews_count(item),
        metadata=_metadata(item),
    )


def _brand(item: Mapping[str, object], name: str) -> str:
    brand = item.get("brand")
    if isinstance(brand, Mapping):
        brand_name = _optional_str(_string_key_mapping(brand), "name")
        if brand_name:
            return brand_name

    rubrics = item.get("rubrics")
    if isinstance(rubrics, Sequence) and not isinstance(rubrics, str):
        for rubric in rubrics:
            if not isinstance(rubric, Mapping):
                continue
            rubric_name = _optional_str(_string_key_mapping(rubric), "name")
            if rubric_name and normalize_brand_name(rubric_name) in {
                "ozon",
                "wildberries",
                "yandex_market",
                "cdek",
                "boxberry",
            }:
                return rubric_name
    return name


def _address(item: Mapping[str, object]) -> str:
    full_address = _optional_str(item, "full_address_name")
    if full_address:
        return full_address
    address = item.get("address")
    if isinstance(address, Mapping):
        components = address.get("components")
        if isinstance(components, Sequence) and not isinstance(components, str):
            parts: list[str] = []
            for component in components:
                if not isinstance(component, Mapping):
                    continue
                component_mapping = _string_key_mapping(component)
                street = _optional_str(component_mapping, "street")
                number = _optional_str(component_mapping, "number")
                if street:
                    parts.append(street)
                if number:
                    parts.append(number)
            if parts:
                return ", ".join(parts)
    return _optional_str(item, "address_name") or ""


def _rating(item: Mapping[str, object]) -> float | None:
    reviews = item.get("reviews")
    if isinstance(reviews, Mapping):
        reviews_mapping = _string_key_mapping(reviews)
        return _optional_float(reviews_mapping, "rating") or _optional_float(
            reviews_mapping,
            "general_rating",
        )
    return None


def _reviews_count(item: Mapping[str, object]) -> int | None:
    reviews = item.get("reviews")
    if isinstance(reviews, Mapping):
        reviews_mapping = _string_key_mapping(reviews)
        return _optional_int(reviews_mapping, "count") or _optional_int(
            reviews_mapping,
            "org_review_count",
        )
    return None


def _metadata(item: Mapping[str, object]) -> Mapping[str, object]:
    metadata: dict[str, object] = {}
    item_type = _optional_str(item, "type")
    if item_type is not None:
        metadata["type"] = item_type
    return metadata


def _items(payload: Mapping[str, object]) -> Sequence[object]:
    result = payload.get("result")
    if not isinstance(result, Mapping):
        return ()
    items = result.get("items")
    if isinstance(items, Sequence) and not isinstance(items, str):
        return items
    return ()


def _ensure_mapping(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError("Provider returned invalid JSON shape.")
    return _string_key_mapping(value)


def _first_str(
    payload: Mapping[str, object],
    keys: Sequence[str],
) -> str | None:
    for key in keys:
        value = _optional_str(payload, key)
        if value:
            return value
    return None


def _optional_str(payload: Mapping[str, object], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    return value if isinstance(value, str) else None


def _optional_float(payload: Mapping[str, object], key: str) -> float | None:
    value = payload.get(key)
    if isinstance(value, int | float):
        return float(value)
    return None


def _optional_int(payload: Mapping[str, object], key: str) -> int | None:
    value = payload.get(key)
    if isinstance(value, int):
        return value
    return None


def _string_key_mapping(payload: Mapping[object, object]) -> Mapping[str, object]:
    return {str(key): value for key, value in payload.items()}
