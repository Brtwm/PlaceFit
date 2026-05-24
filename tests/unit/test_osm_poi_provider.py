from app.providers.poi_search.osm import build_overpass_query, parse_osm_poi_response


def test_osm_poi_parses_node_way_and_relation_elements() -> None:
    result = parse_osm_poi_response(
        {
            "elements": [
                {
                    "type": "node",
                    "id": 1,
                    "lat": 45.0359,
                    "lon": 39.0281,
                    "tags": {
                        "name": "Ozon пункт выдачи",
                        "brand": "Ozon",
                        "addr:city": "Краснодар",
                        "addr:street": "Восточно-Кругликовская",
                        "addr:housenumber": "31",
                    },
                },
                {
                    "type": "way",
                    "id": 2,
                    "center": {"lat": 45.0382, "lon": 39.029},
                    "tags": {"name": "Wildberries", "operator": "Wildberries"},
                },
                {
                    "type": "relation",
                    "id": 3,
                    "center": {"lat": 45.04, "lon": 39.03},
                    "tags": {"name": "Яндекс Маркет"},
                },
            ],
        },
    )

    assert result.provider == "osm"
    assert [poi.external_id for poi in result.pois] == [
        "node/1",
        "way/2",
        "relation/3",
    ]
    assert [poi.brand for poi in result.pois] == [
        "Ozon",
        "Wildberries",
        "Яндекс Маркет",
    ]
    assert result.pois[0].address == "Краснодар, Восточно-Кругликовская, 31"
    assert result.pois[0].rating is None
    assert result.pois[0].reviews_count is None


def test_osm_poi_skips_elements_without_coordinates() -> None:
    result = parse_osm_poi_response(
        {
            "elements": [
                {"type": "node", "id": 1, "tags": {"name": "Ozon"}},
                {
                    "type": "node",
                    "id": 2,
                    "lat": 45.035,
                    "lon": 39.028,
                    "tags": {"name": "Ozon"},
                },
            ],
        },
    )

    assert [poi.external_id for poi in result.pois] == ["node/2"]


def test_overpass_query_is_radius_bounded_and_not_city_wide() -> None:
    query = build_overpass_query(lat=45.035, lon=39.028, radius_m=700)

    assert "around:700,45.035000,39.028000" in query
    assert "out center 50" in query
    assert "area[" not in query
    assert "bbox" not in query.casefold()
