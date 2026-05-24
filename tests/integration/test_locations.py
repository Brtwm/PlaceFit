from app.schemas import AnalysisResponse
from fastapi.testclient import TestClient


def valid_request(
    *,
    rent: int = 85000,
    high_density_area: bool = True,
    new_residential_area: bool = True,
    expected_gross_income_by_user: int = 360000,
) -> dict[str, object]:
    return {
        "address": "Краснодар, ул. Восточно-Кругликовская, 30",
        "business_type": "pvz",
        "rent": rent,
        "area_m2": 35,
        "floor": 1,
        "first_floor": True,
        "separate_entrance": True,
        "parking": True,
        "signage_possible": True,
        "storage_area": True,
        "repair_condition": "normal",
        "new_residential_area": new_residential_area,
        "high_density_area": high_density_area,
        "bus_stop_nearby": True,
        "good_visibility": True,
        "expected_gross_income_by_user": expected_gross_income_by_user,
        "investment": 600000,
        "desired_profit": 80000,
    }


def test_locations_list_returns_saved_analysis(client: TestClient) -> None:
    analyze_response = client.post("/api/v1/analyze", json=valid_request())
    assert analyze_response.status_code == 200
    location_id = analyze_response.json()["location"]["id"]

    response = client.get("/api/v1/locations")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 1
    item = next(item for item in payload["items"] if item["id"] == location_id)
    assert item["address"] == "Краснодар, ул. Восточно-Кругликовская, 30"
    assert "total_score" in item
    assert "decision" in item
    assert "net_profit" in item
    assert "payback_months" in item


def test_locations_detail_returns_full_analysis(client: TestClient) -> None:
    analyze_response = client.post("/api/v1/analyze", json=valid_request())
    assert analyze_response.status_code == 200
    location_id = analyze_response.json()["location"]["id"]

    response = client.get(f"/api/v1/locations/{location_id}")

    assert response.status_code == 200
    detail = AnalysisResponse.model_validate(response.json())
    assert detail.location.id == location_id
    assert detail.report.provider == "fallback"


def test_locations_detail_not_found(client: TestClient) -> None:
    response = client.get("/api/v1/locations/999999")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_locations_filter_by_score(client: TestClient) -> None:
    first = client.post("/api/v1/analyze", json=valid_request())
    second = client.post(
        "/api/v1/analyze",
        json=valid_request(
            rent=150000,
            high_density_area=False,
            new_residential_area=False,
            expected_gross_income_by_user=100000,
        ),
    )
    assert first.status_code == 200
    assert second.status_code == 200
    first_score = first.json()["score"]["total_score"]
    second_score = second.json()["score"]["total_score"]

    min_score = max(first_score, second_score)
    response = client.get("/api/v1/locations", params={"min_score": min_score})

    assert response.status_code == 200
    items = response.json()["items"]
    assert items
    assert all(item["total_score"] >= min_score for item in items)

    max_score = min(first_score, second_score)
    response = client.get("/api/v1/locations", params={"max_score": max_score})

    assert response.status_code == 200
    items = response.json()["items"]
    assert items
    assert all(item["total_score"] <= max_score for item in items)


def test_locations_filter_by_decision(client: TestClient) -> None:
    analyze_response = client.post("/api/v1/analyze", json=valid_request())
    assert analyze_response.status_code == 200
    decision = analyze_response.json()["score"]["decision"]

    response = client.get("/api/v1/locations", params={"decision": decision})

    assert response.status_code == 200
    items = response.json()["items"]
    assert items
    assert all(item["decision"] == decision for item in items)
