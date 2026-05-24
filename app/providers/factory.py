"""Provider factories driven by safe runtime settings."""

from collections.abc import Mapping, Sequence

from app.config.settings import Settings
from app.providers.geocoder.base import GeocoderProvider
from app.providers.geocoder.dgis import DgisGeocoder
from app.providers.geocoder.fake import FakeGeocoder
from app.providers.poi_search.base import PoiSearchProvider
from app.providers.poi_search.dgis import DgisPoiSearchProvider
from app.providers.poi_search.fake import FakePoiSearchProvider
from app.providers.poi_search.osm import OsmPoiSearchProvider


def build_geocoder_provider(settings: Settings) -> GeocoderProvider:
    """Build the configured geocoder, falling back to fake without secrets."""

    provider = _provider_name(settings.geocoder_provider)
    if provider == "fake":
        return _fake_geocoder()
    if provider == "dgis":
        if not settings.dgis_api_key.strip():
            return _fake_geocoder()
        return DgisGeocoder(
            api_key=settings.dgis_api_key,
            base_url=settings.dgis_base_url,
            timeout_seconds=settings.dgis_timeout_seconds,
        )
    raise ValueError(f"Unsupported geocoder provider: {settings.geocoder_provider}")


def build_poi_providers(settings: Settings) -> Sequence[PoiSearchProvider]:
    """Build the configured POI provider sequence."""

    provider = _provider_name(settings.poi_provider)
    if provider == "fake":
        return (_fake_poi_provider(),)
    if provider == "dgis":
        if not settings.dgis_api_key.strip():
            return (_fake_poi_provider(),)
        return (
            DgisPoiSearchProvider(
                api_key=settings.dgis_api_key,
                base_url=settings.dgis_base_url,
                timeout_seconds=settings.dgis_timeout_seconds,
            ),
        )
    if provider == "osm":
        return (
            OsmPoiSearchProvider(
                overpass_url=settings.osm_overpass_url,
                timeout_seconds=settings.osm_timeout_seconds,
                user_agent=settings.external_user_agent,
            ),
        )
    raise ValueError(f"Unsupported POI provider: {settings.poi_provider}")


def default_geocoder_payloads() -> tuple[Mapping[str, object], ...]:
    """Return deterministic geocoder payloads for demo/fallback mode."""

    return (
        {
            "provider": "2gis",
            "query": "Краснодар, ул. Восточно-Кругликовская, 30",
            "status": "resolved",
            "results": [
                {
                    "external_id": "fake-krasnodar-vk-30",
                    "address": "Краснодар, ул. Восточно-Кругликовская, 30",
                    "normalized_address": (
                        "г Краснодар, ул Восточно-Кругликовская, д 30"
                    ),
                    "city": "Краснодар",
                    "lat": 45.035,
                    "lon": 39.028,
                    "confidence": 0.95,
                },
            ],
        },
        {
            "provider": "2gis",
            "query": "Краснодар, ул. Красная, 1",
            "status": "resolved",
            "results": [
                {
                    "external_id": "fake-krasnodar-krasnaya-1",
                    "address": "Краснодар, ул. Красная, 1",
                    "normalized_address": "г Краснодар, ул Красная, д 1",
                    "city": "Краснодар",
                    "lat": 45.025,
                    "lon": 38.971,
                    "confidence": 0.95,
                },
            ],
        },
    )


def default_poi_payload() -> Mapping[str, object]:
    """Return deterministic POI payload for demo/fallback mode."""

    return {
        "provider": "osm",
        "pois": [
            {
                "external_id": "osm-ozon-vk-31",
                "name": "Ozon пункт выдачи",
                "brand": "Ozon",
                "category": "pvz",
                "business_type": "pvz",
                "lat": 45.0359,
                "lon": 39.0281,
                "address": "г Краснодар, ул Восточно-Кругликовская, д 31",
                "rating": 4.6,
                "reviews_count": 41,
            },
            {
                "external_id": "osm-wb-vk-28",
                "name": "Wildberries",
                "brand": "Wildberries",
                "category": "pvz",
                "business_type": "pvz",
                "lat": 45.0382,
                "lon": 39.029,
                "address": "г Краснодар, ул Восточно-Кругликовская, д 28",
                "rating": 4.4,
                "reviews_count": 27,
            },
            {
                "external_id": "osm-ym-vk-40",
                "name": "Яндекс Маркет",
                "brand": "Яндекс Маркет",
                "category": "pvz",
                "business_type": "pvz",
                "lat": 45.04,
                "lon": 39.03,
                "address": "г Краснодар, ул Восточно-Кругликовская, д 40",
                "rating": 4.3,
                "reviews_count": 18,
            },
        ],
    }


def _fake_geocoder() -> FakeGeocoder:
    return FakeGeocoder(default_geocoder_payloads())


def _fake_poi_provider() -> FakePoiSearchProvider:
    return FakePoiSearchProvider(default_poi_payload())


def _provider_name(value: str) -> str:
    return value.strip().casefold() or "fake"
