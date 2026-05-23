from app.providers.poi_search.base import PoiCandidate
from app.services.deduplication import deduplicate_pois, normalize_brand_name


def poi(
    *,
    provider: str = "2gis",
    external_id: str = "1",
    name: str = "Ozon",
    brand: str = "Ozon",
    lat: float = 45.0359,
    lon: float = 39.0281,
) -> PoiCandidate:
    return PoiCandidate(
        provider=provider,
        external_id=external_id,
        name=name,
        brand=brand,
        category="pvz",
        lat=lat,
        lon=lon,
        address="г Краснодар, ул Восточно-Кругликовская, д 31",
    )


def test_dedup_exact_duplicate_by_provider_and_external_id() -> None:
    result = deduplicate_pois(
        [
            poi(provider="2gis", external_id="same", lat=45.0359),
            poi(provider="2gis", external_id="same", lat=45.05),
        ],
    )

    assert len(result) == 1
    assert result[0].external_id == "same"


def test_dedup_close_coordinates_and_normalized_name() -> None:
    result = deduplicate_pois(
        [
            poi(provider="2gis", external_id="dgis-1", brand="OZON"),
            poi(
                provider="yandex",
                external_id="ya-1",
                name="Озон, пункт выдачи",
                brand="Озон",
                lat=45.03591,
                lon=39.02812,
            ),
        ],
    )

    assert len(result) == 1
    assert result[0].provider == "2gis"


def test_name_normalization_handles_case_punctuation_and_aliases() -> None:
    assert normalize_brand_name("OZON") == "ozon"
    assert normalize_brand_name("Озон, пункт выдачи") == "ozon"
    assert normalize_brand_name("  wildberries! ") == "wildberries"


def test_nearby_distinct_competitors_do_not_collapse() -> None:
    result = deduplicate_pois(
        [
            poi(provider="2gis", external_id="ozon-1", brand="Ozon"),
            poi(
                provider="osm",
                external_id="wb-1",
                name="Wildberries",
                brand="Wildberries",
                lat=45.03591,
                lon=39.02811,
            ),
        ],
    )

    assert len(result) == 2
    assert {item.brand for item in result} == {"Ozon", "Wildberries"}


def test_same_brand_far_apart_does_not_collapse() -> None:
    result = deduplicate_pois(
        [
            poi(provider="2gis", external_id="ozon-1"),
            poi(provider="osm", external_id="ozon-2", lat=45.04, lon=39.03),
        ],
    )

    assert len(result) == 2
