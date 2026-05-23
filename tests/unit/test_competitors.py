import json
from pathlib import Path
from typing import Any

from app.providers.poi_search.fake import FakePoiSearchProvider, parse_poi_payload
from app.services.competitors import search_competitors

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "providers"


def load_fixture(name: str) -> dict[str, Any]:
    with (FIXTURES_DIR / name).open(encoding="utf-8") as file:
        return json.load(file)


def test_parses_osm_like_poi_fixture() -> None:
    result = parse_poi_payload(load_fixture("osm_poi_pvz.json"))

    assert result.provider == "osm"
    assert len(result.pois) == 3
    assert result.pois[0].business_type == "pvz"
    assert result.pois[0].brand == "Ozon"


def test_competitor_search_computes_counts_and_distances() -> None:
    provider = FakePoiSearchProvider(load_fixture("osm_poi_pvz.json"))

    result = search_competitors(
        [provider],
        lat=45.035,
        lon=39.028,
        radius_m=700,
    )

    assert result.competitors_300m == 1
    assert result.competitors_500m == 2
    assert result.competitors_700m == 3
    assert result.nearest_competitor_distance_m is not None
    assert result.nearest_competitor_distance_m < 120
    assert result.average_competitor_distance_m is not None
    assert result.sources == ("osm",)


def test_competitor_search_returns_stable_sorted_list() -> None:
    provider = FakePoiSearchProvider(load_fixture("osm_poi_pvz.json"))

    result = search_competitors(
        [provider],
        lat=45.035,
        lon=39.028,
        radius_m=700,
    )

    distances = [competitor.distance_m for competitor in result.competitors]
    assert distances == sorted(distances)
    assert [competitor.brand for competitor in result.competitors] == [
        "Ozon",
        "Wildberries",
        "Яндекс Маркет",
    ]


def test_competitor_search_deduplicates_mixed_provider_fixture() -> None:
    provider = FakePoiSearchProvider(load_fixture("mixed_poi_duplicates.json"))

    result = search_competitors(
        [provider],
        lat=45.035,
        lon=39.028,
        radius_m=700,
    )

    assert len(result.competitors) == 2
    assert [competitor.brand for competitor in result.competitors] == [
        "OZON",
        "Wildberries",
    ]
