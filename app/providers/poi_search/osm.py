"""OpenStreetMap Overpass POI search provider."""

from collections.abc import Mapping, Sequence

import httpx

from app.providers.poi_search.base import (
    BusinessType,
    PoiCandidate,
    PoiSearchProviderResult,
)
from app.services.deduplication import normalize_brand_name

PROVIDER_NAME = "osm"
OVERPASS_MAX_RESULTS = 50
PVZ_NAME_PATTERN = (
    "Ozon|OZON|Озон|Wildberries|wildberries|WB|ВБ|"
    "Яндекс Маркет|Yandex Market|pickup point|parcel pickup|пункт выдачи"
)


class OsmPoiSearchProvider:
    """Overpass-backed optional POI provider for bounded MVP searches."""

    provider_name = PROVIDER_NAME

    def __init__(
        self,
        *,
        overpass_url: str,
        timeout_seconds: float,
        user_agent: str,
        client: httpx.Client | None = None,
    ) -> None:
        self._overpass_url = overpass_url
        self._timeout_seconds = timeout_seconds
        self._user_agent = user_agent
        self._client = client

    def search(
        self,
        *,
        lat: float,
        lon: float,
        radius_m: int,
        business_type: BusinessType,
    ) -> PoiSearchProviderResult:
        """Search Overpass for bounded pickup-point-like objects."""

        if business_type != "pvz":
            return PoiSearchProviderResult(provider=PROVIDER_NAME, pois=())
        query = build_overpass_query(lat=lat, lon=lon, radius_m=radius_m)
        try:
            payload = self._post_query(query)
        except (httpx.HTTPError, ValueError):
            return PoiSearchProviderResult(provider=PROVIDER_NAME, pois=())
        return parse_osm_poi_response(payload)

    def _post_query(self, query: str) -> Mapping[str, object]:
        headers = {"User-Agent": self._user_agent}
        data = {"data": query}
        if self._client is not None:
            response = self._client.post(
                self._overpass_url,
                data=data,
                headers=headers,
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
            return _ensure_mapping(response.json())

        with httpx.Client(timeout=self._timeout_seconds) as client:
            response = client.post(self._overpass_url, data=data, headers=headers)
            response.raise_for_status()
            return _ensure_mapping(response.json())


def build_overpass_query(*, lat: float, lon: float, radius_m: int) -> str:
    """Build a bounded Overpass query around the requested coordinate."""

    radius = max(1, min(radius_m, 2_000))
    return f"""
[out:json][timeout:25];
(
  nwr(around:{radius},{lat:.6f},{lon:.6f})["name"~"{PVZ_NAME_PATTERN}",i];
  nwr(around:{radius},{lat:.6f},{lon:.6f})["brand"~"{PVZ_NAME_PATTERN}",i];
  nwr(around:{radius},{lat:.6f},{lon:.6f})["operator"~"{PVZ_NAME_PATTERN}",i];
);
out center {OVERPASS_MAX_RESULTS};
""".strip()


def parse_osm_poi_response(payload: Mapping[str, object]) -> PoiSearchProviderResult:
    """Parse Overpass JSON into POI candidates."""

    pois: list[PoiCandidate] = []
    seen_ids: set[str] = set()
    elements = payload.get("elements")
    if not isinstance(elements, Sequence) or isinstance(elements, str):
        return PoiSearchProviderResult(provider=PROVIDER_NAME, pois=())

    for raw_element in elements:
        if not isinstance(raw_element, Mapping):
            continue
        poi = _poi(_string_key_mapping(raw_element))
        if poi is None or poi.external_id in seen_ids:
            continue
        seen_ids.add(poi.external_id)
        pois.append(poi)
    return PoiSearchProviderResult(provider=PROVIDER_NAME, pois=tuple(pois))


def _poi(element: Mapping[str, object]) -> PoiCandidate | None:
    element_type = _optional_str(element, "type")
    element_id = _optional_int(element, "id")
    if element_type not in {"node", "way", "relation"} or element_id is None:
        return None

    coordinates = _coordinates(element)
    if coordinates is None:
        return None
    lat, lon = coordinates

    tags = element.get("tags")
    tag_mapping = _string_key_mapping(tags) if isinstance(tags, Mapping) else {}
    name = _first_str(tag_mapping, ("name", "brand", "operator"))
    if not name:
        return None

    return PoiCandidate(
        provider=PROVIDER_NAME,
        external_id=f"{element_type}/{element_id}",
        name=name,
        brand=_brand(tag_mapping, name),
        category="pvz",
        lat=lat,
        lon=lon,
        address=_address(tag_mapping),
        rating=None,
        reviews_count=None,
        metadata={"osm_type": element_type},
    )


def _coordinates(element: Mapping[str, object]) -> tuple[float, float] | None:
    lat = _optional_float(element, "lat")
    lon = _optional_float(element, "lon")
    if lat is not None and lon is not None:
        return lat, lon

    center = element.get("center")
    if isinstance(center, Mapping):
        center_mapping = _string_key_mapping(center)
        center_lat = _optional_float(center_mapping, "lat")
        center_lon = _optional_float(center_mapping, "lon")
        if center_lat is not None and center_lon is not None:
            return center_lat, center_lon
    return None


def _brand(tags: Mapping[str, object], name: str) -> str:
    raw_brand = _first_str(tags, ("brand", "operator", "name")) or name
    normalized = normalize_brand_name(raw_brand)
    if normalized == "ozon":
        return "Ozon"
    if normalized == "wildberries":
        return "Wildberries"
    if normalized == "yandex_market":
        return "Яндекс Маркет"
    return raw_brand


def _address(tags: Mapping[str, object]) -> str:
    parts = [
        _optional_str(tags, "addr:city"),
        _optional_str(tags, "addr:street"),
        _optional_str(tags, "addr:housenumber"),
    ]
    return ", ".join(part for part in parts if part)


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
