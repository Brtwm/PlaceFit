"""2GIS geocoder provider."""

from collections.abc import Mapping, Sequence

import httpx

from app.providers.geocoder.base import (
    GeocodingCandidate,
    GeocodingProviderResult,
)

PROVIDER_NAME = "2gis"
GEOCODING_FAILED_MESSAGE = "2GIS geocoder returned no usable result."
SUPPORTED_CITY_NAMES = {"краснодар", "krasnodar"}


class DgisGeocoder:
    """Thin 2GIS geocoder client behind the geocoder provider protocol."""

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

    def geocode(self, address: str) -> GeocodingProviderResult:
        """Geocode an address through 2GIS without leaking provider details."""

        try:
            payload = self._get_json(address)
        except (httpx.HTTPError, ValueError):
            return _not_found()
        return parse_dgis_geocode_response(payload)

    def _get_json(self, address: str) -> Mapping[str, object]:
        params = {
            "q": address,
            "fields": "items.point,items.adm_div",
            "key": self._api_key,
        }
        url = f"{self._base_url}/3.0/items/geocode"
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


def parse_dgis_geocode_response(
    payload: Mapping[str, object],
) -> GeocodingProviderResult:
    """Parse a 2GIS geocoder JSON payload into provider candidates."""

    items = _items(payload)
    if not items:
        return _not_found()

    candidates = tuple(
        candidate
        for item in items
        if isinstance(item, Mapping)
        for candidate in (_candidate(_string_key_mapping(item)),)
        if candidate is not None
    )
    if not candidates:
        return _not_found()

    unsupported = tuple(
        candidate
        for candidate in candidates
        if candidate.city is not None and not _is_supported_city(candidate.city)
    )
    if unsupported:
        return GeocodingProviderResult(
            status="city_not_supported",
            provider=PROVIDER_NAME,
            candidates=unsupported,
            error_code="CITY_NOT_SUPPORTED",
            message="Address is outside Krasnodar.",
        )

    return GeocodingProviderResult(
        status="resolved" if len(candidates) == 1 else "ambiguous",
        provider=PROVIDER_NAME,
        candidates=candidates,
        error_code=None if len(candidates) == 1 else "ADDRESS_AMBIGUOUS",
        message=None if len(candidates) == 1 else "Address has multiple matches.",
    )


def _candidate(item: Mapping[str, object]) -> GeocodingCandidate | None:
    point = item.get("point")
    if not isinstance(point, Mapping):
        return None
    point_mapping = _string_key_mapping(point)
    lat = _optional_float(point_mapping, "lat")
    lon = _optional_float(point_mapping, "lon")
    if lat is None or lon is None:
        return None

    full_name = _first_str(item, ("full_name", "address_name", "name"))
    if full_name is None:
        return None
    city = _detect_city(item)
    return GeocodingCandidate(
        address=full_name,
        normalized_address=full_name,
        lat=lat,
        lon=lon,
        provider=PROVIDER_NAME,
        confidence=_optional_float(item, "confidence"),
        external_id=_optional_str(item, "id"),
        city=city,
        metadata=_metadata(item),
    )


def _items(payload: Mapping[str, object]) -> Sequence[object]:
    result = payload.get("result")
    if not isinstance(result, Mapping):
        return ()
    items = result.get("items")
    if isinstance(items, Sequence) and not isinstance(items, str):
        return items
    return ()


def _detect_city(item: Mapping[str, object]) -> str | None:
    adm_div = item.get("adm_div")
    if isinstance(adm_div, Sequence) and not isinstance(adm_div, str):
        for value in adm_div:
            if not isinstance(value, Mapping):
                continue
            adm_item = _string_key_mapping(value)
            name = _optional_str(adm_item, "name")
            if name is not None and _looks_like_city(adm_item, name):
                return name

    full_name = _optional_str(item, "full_name")
    if full_name is not None:
        first_part = full_name.split(",", maxsplit=1)[0].strip()
        if first_part:
            return first_part
    return None


def _looks_like_city(item: Mapping[str, object], name: str) -> bool:
    type_value = (_optional_str(item, "type") or "").casefold()
    subtype = (_optional_str(item, "subtype") or "").casefold()
    return (
        "city" in type_value
        or "city" in subtype
        or name.casefold() in SUPPORTED_CITY_NAMES
    )


def _is_supported_city(city: str) -> bool:
    return city.strip().casefold() in SUPPORTED_CITY_NAMES


def _metadata(item: Mapping[str, object]) -> Mapping[str, object]:
    metadata: dict[str, object] = {}
    item_type = _optional_str(item, "type")
    if item_type is not None:
        metadata["type"] = item_type
    purpose_name = _optional_str(item, "purpose_name")
    if purpose_name is not None:
        metadata["purpose_name"] = purpose_name
    return metadata


def _not_found() -> GeocodingProviderResult:
    return GeocodingProviderResult(
        status="not_found",
        provider=PROVIDER_NAME,
        error_code="GEOCODING_FAILED",
        message=GEOCODING_FAILED_MESSAGE,
    )


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


def _string_key_mapping(payload: Mapping[object, object]) -> Mapping[str, object]:
    return {str(key): value for key, value in payload.items()}
