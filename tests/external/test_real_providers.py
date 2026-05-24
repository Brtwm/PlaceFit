import os

import pytest
from app.providers.geocoder.dgis import DgisGeocoder
from app.providers.poi_search.dgis import DgisPoiSearchProvider
from app.providers.poi_search.osm import OsmPoiSearchProvider

pytestmark = pytest.mark.external


def _external_enabled() -> bool:
    return os.getenv("RUN_EXTERNAL_PROVIDER_TESTS", "").casefold() == "true"


@pytest.mark.skipif(
    not _external_enabled() or not os.getenv("DGIS_API_KEY"),
    reason="Set RUN_EXTERNAL_PROVIDER_TESTS=true and DGIS_API_KEY to call 2GIS.",
)
def test_real_dgis_geocoder_krasnodar_smoke() -> None:
    provider = DgisGeocoder(
        api_key=os.environ["DGIS_API_KEY"],
        base_url=os.getenv("DGIS_BASE_URL", "https://catalog.api.2gis.com"),
        timeout_seconds=float(os.getenv("DGIS_TIMEOUT_SECONDS", "5.0")),
    )

    result = provider.geocode("Краснодар, ул. Красная, 1")

    assert result.status in {"resolved", "ambiguous"}
    assert result.candidates


@pytest.mark.skipif(
    not _external_enabled() or not os.getenv("DGIS_API_KEY"),
    reason="Set RUN_EXTERNAL_PROVIDER_TESTS=true and DGIS_API_KEY to call 2GIS.",
)
def test_real_dgis_poi_smoke() -> None:
    provider = DgisPoiSearchProvider(
        api_key=os.environ["DGIS_API_KEY"],
        base_url=os.getenv("DGIS_BASE_URL", "https://catalog.api.2gis.com"),
        timeout_seconds=float(os.getenv("DGIS_TIMEOUT_SECONDS", "5.0")),
    )

    result = provider.search(
        lat=45.035,
        lon=39.028,
        radius_m=700,
        business_type="pvz",
    )

    assert result.provider == "2gis"


@pytest.mark.skipif(
    not _external_enabled(),
    reason="Set RUN_EXTERNAL_PROVIDER_TESTS=true to call Overpass.",
)
def test_real_osm_overpass_smoke() -> None:
    provider = OsmPoiSearchProvider(
        overpass_url=os.getenv(
            "OSM_OVERPASS_URL",
            "https://overpass-api.de/api/interpreter",
        ),
        timeout_seconds=float(os.getenv("OSM_TIMEOUT_SECONDS", "10.0")),
        user_agent=os.getenv(
            "EXTERNAL_USER_AGENT",
            "PlaceFit/0.1 (+https://github.com/Brtwm/PlaceFit)",
        ),
    )

    result = provider.search(
        lat=45.035,
        lon=39.028,
        radius_m=700,
        business_type="pvz",
    )

    assert result.provider == "osm"
