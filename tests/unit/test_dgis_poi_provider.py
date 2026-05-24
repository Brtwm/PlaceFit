from app.providers.poi_search.dgis import parse_dgis_poi_response


def test_dgis_poi_normalizes_pickup_point_items() -> None:
    result = parse_dgis_poi_response(
        {
            "result": {
                "items": [
                    {
                        "id": "ozon-1",
                        "name": "Ozon пункт выдачи",
                        "point": {"lat": 45.0359, "lon": 39.0281},
                        "full_address_name": "Краснодар, Восточно-Кругликовская, 31",
                        "brand": {"name": "Ozon"},
                        "reviews": {"rating": 4.6, "count": 41},
                    },
                    {
                        "id": "wb-1",
                        "name": "Wildberries",
                        "point": {"lat": 45.0382, "lon": 39.029},
                        "full_address_name": "Краснодар, Восточно-Кругликовская, 28",
                        "brand": {"name": "Wildberries"},
                    },
                    {
                        "id": "ym-1",
                        "name": "Яндекс Маркет",
                        "point": {"lat": 45.04, "lon": 39.03},
                        "full_address_name": "Краснодар, Восточно-Кругликовская, 40",
                    },
                ],
            },
        },
    )

    assert result.provider == "2gis"
    assert [poi.brand for poi in result.pois] == [
        "Ozon",
        "Wildberries",
        "Яндекс Маркет",
    ]
    assert result.pois[0].category == "pvz"
    assert result.pois[0].rating == 4.6
    assert result.pois[0].reviews_count == 41


def test_dgis_poi_missing_optional_rating_and_reviews_are_none() -> None:
    result = parse_dgis_poi_response(
        {
            "result": {
                "items": [
                    {
                        "id": "wb-1",
                        "name": "Wildberries",
                        "point": {"lat": 45.0382, "lon": 39.029},
                    },
                ],
            },
        },
    )

    assert len(result.pois) == 1
    assert result.pois[0].rating is None
    assert result.pois[0].reviews_count is None


def test_dgis_poi_skips_items_without_required_coordinates() -> None:
    result = parse_dgis_poi_response(
        {
            "result": {
                "items": [
                    {"id": "bad-1", "name": "Ozon"},
                    {
                        "id": "good-1",
                        "name": "Ozon",
                        "point": {"lat": 45.035, "lon": 39.028},
                    },
                ],
            },
        },
    )

    assert [poi.external_id for poi in result.pois] == ["good-1"]


def test_dgis_poi_deduplicates_external_ids() -> None:
    result = parse_dgis_poi_response(
        {
            "result": {
                "items": [
                    {
                        "id": "same",
                        "name": "Ozon 1",
                        "point": {"lat": 45.035, "lon": 39.028},
                    },
                    {
                        "id": "same",
                        "name": "Ozon 2",
                        "point": {"lat": 45.04, "lon": 39.03},
                    },
                ],
            },
        },
    )

    assert len(result.pois) == 1
    assert result.pois[0].name == "Ozon 1"
