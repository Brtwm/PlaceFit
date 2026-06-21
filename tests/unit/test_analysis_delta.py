import builtins
import socket
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from app.config.scoring_rules import DECISION_RULES
from app.schemas import AnalysisRequest, AnalysisResponse
from app.services.analysis_delta import (
    AnalysisDeltaContractError,
    build_analysis_delta,
)


def test_unchanged_snapshots_cover_all_specified_fields() -> None:
    request = _request()
    response = _response()

    delta = _delta(request, response, request, response)

    assert list(type(delta.inputs).model_fields) == [
        "rent",
        "area_m2",
        "floor",
        "first_floor",
        "separate_entrance",
        "parking",
        "signage_possible",
        "storage_area",
        "repair_condition",
        "new_residential_area",
        "high_density_area",
        "bus_stop_nearby",
        "good_visibility",
        "expected_gross_income_by_user",
        "investment",
        "desired_profit",
    ]
    assert list(type(delta.competitors).model_fields) == [
        "competitors_300m",
        "competitors_500m",
        "competitors_700m",
        "nearest_competitor_distance_m",
        "average_competitor_distance_m",
        "items",
    ]
    assert list(type(delta.score).model_fields) == [
        "scoring_version",
        "total_score",
        "confidence_score",
        "decision",
        "demand_score",
        "competition_score",
        "rent_score",
        "premises_score",
        "accessibility_score",
    ]
    assert list(type(delta.finance).model_fields) == [
        "monthly_costs",
        "required_gross_income",
        "expected_gross_income_by_user",
        "net_profit",
        "payback_months",
    ]
    scalar_sections = (
        delta.inputs,
        delta.location_provenance,
        delta.competitors,
        delta.score,
        delta.finance,
    )
    statuses = {
        item.status
        for section in scalar_sections
        for item in section.__dict__.values()
        if hasattr(item, "status")
    }
    assert statuses == {"unchanged"}
    assert delta.previous_snapshot_origin == "legacy_materialized"
    assert delta.current_snapshot_origin == "native"
    assert delta.summary.changed_inputs == 0


def test_scalar_statuses_and_directions_follow_contract() -> None:
    previous_request = _request(expected_gross_income_by_user=None)
    current_request = _request(
        rent=90_000,
        expected_gross_income_by_user=360_000,
        investment=700_000,
    )
    previous = _response()
    current_payload = previous.model_dump(mode="python")
    current_payload["competitors"].update(
        {
            "competitors_300m": 0,
            "competitors_500m": 4,
            "nearest_competitor_distance_m": 220,
            "average_competitor_distance_m": 460,
        },
    )
    current_payload["score"].update(
        {
            "total_score": 84,
            "confidence_score": 88,
            "decision": DECISION_RULES.consider,
        },
    )
    current_payload["score"]["details"].update(
        {
            "demand_score": 34,
            "competition_score": 14,
            "rent_score": 14,
            "premises_score": 9,
            "accessibility_score": 8,
        },
    )
    current_payload["finance"].update(
        {
            "monthly_costs": 294_000,
            "required_gross_income": 380_000,
            "expected_gross_income_by_user": 360_000,
            "net_profit": None,
            "payback_months": 8.0,
        },
    )
    current = AnalysisResponse.model_validate(current_payload)

    delta = _delta(previous_request, previous, current_request, current)

    assert (delta.inputs.rent.status, delta.inputs.rent.direction) == (
        "changed",
        "neutral",
    )
    assert delta.inputs.expected_gross_income_by_user.status == "added"
    assert delta.inputs.expected_gross_income_by_user.direction == "not_applicable"
    assert delta.competitors.competitors_300m.direction == "improved"
    assert delta.competitors.competitors_500m.direction == "worsened"
    assert delta.competitors.nearest_competitor_distance_m.direction == "improved"
    assert delta.competitors.average_competitor_distance_m.direction == "neutral"
    assert delta.score.total_score.direction == "improved"
    assert delta.score.confidence_score.direction == "worsened"
    assert delta.score.demand_score.direction == "worsened"
    assert delta.score.competition_score.direction == "improved"
    assert delta.finance.monthly_costs.direction == "improved"
    assert delta.finance.required_gross_income.direction == "worsened"
    assert (delta.finance.net_profit.status, delta.finance.net_profit.direction) == (
        "removed",
        "not_applicable",
    )
    assert delta.finance.payback_months.direction == "improved"
    assert delta.summary.changed_inputs == 3


@pytest.mark.parametrize(
    ("before", "after", "direction"),
    [
        (DECISION_RULES.likely_no, DECISION_RULES.check_more, "improved"),
        (DECISION_RULES.check_more, DECISION_RULES.consider, "improved"),
        (DECISION_RULES.consider, DECISION_RULES.check_more, "worsened"),
        (DECISION_RULES.check_more, DECISION_RULES.likely_no, "worsened"),
    ],
)
def test_decision_direction_uses_documented_order(
    before: str,
    after: str,
    direction: str,
) -> None:
    previous = _response(decision=before)
    current = _response(decision=after)

    delta = _delta(_request(), previous, _request(), current)

    assert delta.score.decision.direction == direction


def test_scoring_version_change_is_neutral_and_warned() -> None:
    delta = _delta(
        _request(),
        _response(scoring_version="v1.0"),
        _request(),
        _response(scoring_version="v1.1"),
    )

    assert delta.score.scoring_version.status == "changed"
    assert delta.score.scoring_version.direction == "neutral"
    assert delta.scoring_version_warning is not None
    assert "v1.0" in delta.scoring_version_warning
    assert "v1.1" in delta.scoring_version_warning


def test_competitors_use_external_identity_and_fixed_status_order() -> None:
    previous = _response(
        competitors=[
            _competitor("Removed", external_id="removed"),
            _competitor("Changed", external_id="changed", rating=4.0),
            _competitor("Same", external_id="same"),
        ],
    )
    current = _response(
        competitors=[
            _competitor("Same", external_id="same"),
            _competitor("Added", external_id="added"),
            _competitor("Changed", external_id="changed", rating=4.7),
        ],
    )

    items = _delta(_request(), previous, _request(), current).competitors.items

    assert [(item.status, item.identity) for item in items] == [
        ("added", "osm:added"),
        ("removed", "osm:removed"),
        ("changed", "osm:changed"),
        ("unchanged", "osm:same"),
    ]
    assert items[2].changed_fields == ["rating"]


def test_competitor_changed_fields_follow_schema_order() -> None:
    previous = _response(
        competitors=[_competitor("Old", external_id="same", rating=4.0)],
    )
    current = _response(
        competitors=[
            _competitor(
                "New",
                external_id="same",
                address="New address",
                distance_m=250,
                rating=4.5,
                reviews_count=20,
            ),
        ],
    )

    item = _delta(_request(), previous, _request(), current).competitors.items[0]

    assert item.changed_fields == [
        "name",
        "address",
        "distance_m",
        "rating",
        "reviews_count",
    ]


def test_legacy_fingerprint_matches_normalized_values() -> None:
    previous = _response(
        competitors=[
            _competitor(
                " Legacy Name ",
                external_id=None,
                brand=" Brand ",
                address=" Address ",
                lat=45.1234561,
                lon=39.1234561,
            ),
        ],
    )
    current = _response(
        competitors=[
            _competitor(
                "legacy name",
                external_id=None,
                brand="brand",
                address="address",
                lat=45.1234562,
                lon=39.1234562,
            ),
        ],
    )

    item = _delta(_request(), previous, _request(), current).competitors.items[0]

    assert item.identity.startswith("legacy:")
    assert item.status == "changed"
    assert item.changed_fields == ["name", "brand", "address", "lat", "lon"]


def test_legacy_identity_collision_is_explicit_contract_error() -> None:
    duplicate = _competitor("Same", external_id=None)
    response = _response(competitors=[duplicate, deepcopy(duplicate)])

    with pytest.raises(AnalysisDeltaContractError, match="legacy identity collision"):
        _delta(_request(), response, _request(), _response())


def test_competitor_result_is_stable_when_input_lists_are_permuted() -> None:
    previous_items = [
        _competitor("B", external_id="b"),
        _competitor("A", external_id="a"),
    ]
    current_items = [
        _competitor("C", external_id="c"),
        _competitor("A", external_id="a"),
    ]

    first = _delta(
        _request(),
        _response(competitors=previous_items),
        _request(),
        _response(competitors=current_items),
    )
    second = _delta(
        _request(),
        _response(competitors=list(reversed(previous_items))),
        _request(),
        _response(competitors=list(reversed(current_items))),
    )

    assert first.model_dump(mode="json") == second.model_dump(mode="json")


@pytest.mark.parametrize("field", ["address", "business_type"])
def test_lineage_request_invariants_are_enforced(field: str) -> None:
    previous = _request()
    replacement = "Краснодар, ул. Северная, 2" if field == "address" else "cafe"
    current = previous.model_copy(update={field: replacement})

    with pytest.raises(AnalysisDeltaContractError, match=field):
        _delta(previous, _response(), current, _response())


def test_report_marketplace_and_checklist_prose_do_not_affect_delta() -> None:
    previous = _response()
    payload = previous.model_dump(mode="python")
    payload["report"]["text"] = "Completely different report"
    payload["checklist"] = ["Different checklist prose"]
    payload["marketplace_requirements"]["ozon"]["manual_checks"] = ["Different"]
    current = AnalysisResponse.model_validate(payload)

    delta = _delta(_request(), previous, _request(), current)

    assert delta.summary.changed_inputs == 0
    assert delta.scoring_version_warning is None
    assert all(item.status == "unchanged" for item in delta.competitors.items)


def test_delta_runtime_has_no_io_or_network_side_effects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise AssertionError("side effect attempted")

    monkeypatch.setattr(builtins, "open", forbidden)
    monkeypatch.setattr(Path, "open", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)

    delta = _delta(_request(), _response(), _request(), _response())

    assert delta.previous_analysis_id == 1
    assert delta.current_analysis_id == 2


def _delta(
    previous_request: AnalysisRequest,
    previous_response: AnalysisResponse,
    current_request: AnalysisRequest,
    current_response: AnalysisResponse,
) -> Any:
    current_response = current_response.model_copy(
        update={
            "location": current_response.location.model_copy(update={"id": 2}),
            "created_at": datetime(2026, 6, 21, tzinfo=UTC),
        },
    )
    return build_analysis_delta(
        previous_request=previous_request,
        previous_response=previous_response,
        current_request=current_request,
        current_response=current_response,
        previous_snapshot_origin="legacy_materialized",
        current_snapshot_origin="native",
        snapshot_schema_version="v1",
    )


def _request(**changes: object) -> AnalysisRequest:
    payload: dict[str, object] = {
        "address": "Краснодар, ул. Красная, 1",
        "business_type": "pvz",
        "rent": 85_000,
        "area_m2": 35,
        "floor": 1,
        "first_floor": True,
        "separate_entrance": True,
        "parking": True,
        "signage_possible": True,
        "storage_area": True,
        "repair_condition": "normal",
        "new_residential_area": True,
        "high_density_area": True,
        "bus_stop_nearby": True,
        "good_visibility": True,
        "expected_gross_income_by_user": 360_000,
        "investment": 600_000,
        "desired_profit": 80_000,
    }
    payload.update(changes)
    return AnalysisRequest.model_validate(payload)


def _response(
    *,
    decision: str = DECISION_RULES.check_more,
    scoring_version: str = "v1.0",
    competitors: list[dict[str, object]] | None = None,
) -> AnalysisResponse:
    items = competitors if competitors is not None else [_competitor("Same")]
    return AnalysisResponse.model_validate(
        {
            "location": {
                "id": 1 if scoring_version == "v1.0" else 2,
                "address": "Краснодар, ул. Красная, 1",
                "normalized_address": "г Краснодар, ул Красная, д 1",
                "lat": 45.035,
                "lon": 39.028,
            },
            "competitors": {
                "competitors_300m": 1,
                "competitors_500m": 3,
                "competitors_700m": 5,
                "nearest_competitor_distance_m": 180,
                "average_competitor_distance_m": 420,
                "list": items,
            },
            "score": {
                "total_score": 82,
                "confidence_score": 90,
                "scoring_version": scoring_version,
                "decision": decision,
                "details": {
                    "demand_score": 35,
                    "competition_score": 12,
                    "rent_score": 15,
                    "premises_score": 10,
                    "accessibility_score": 10,
                },
            },
            "finance": {
                "monthly_costs": 295_000,
                "required_gross_income": 375_000,
                "expected_gross_income_by_user": 360_000,
                "net_profit": 65_000,
                "payback_months": 9.2,
            },
            "marketplace_requirements": {
                name: {
                    "status": "needs_manual_check",
                    "needs_manual_check": True,
                    "manual_checks": ["Проверить вручную"],
                    "warning": "Требования нужно проверить вручную.",
                }
                for name in ("ozon", "wildberries", "yandex_market")
            },
            "report": {
                "status": "fallback",
                "text": "Stored report",
                "provider": "fallback",
                "model": "none",
                "prompt_version": "v1.0",
            },
            "checklist": ["Проверить вручную"],
            "data_sources": [
                {
                    "source": "osm",
                    "data_type": "competitors",
                    "fetched_at": datetime(2026, 6, 20, tzinfo=UTC),
                },
            ],
            "created_at": datetime(
                2026,
                6,
                20 if scoring_version == "v1.0" else 21,
                tzinfo=UTC,
            ),
        },
    )


def _competitor(
    name: str,
    *,
    external_id: str | None = "same",
    brand: str = "Ozon",
    address: str = "ул. Красная, 2",
    lat: float = 45.036,
    lon: float = 39.029,
    distance_m: int = 180,
    rating: float | None = 4.2,
    reviews_count: int | None = 10,
) -> dict[str, object]:
    return {
        "external_id": external_id,
        "name": name,
        "brand": brand,
        "category": "pvz",
        "address": address,
        "lat": lat,
        "lon": lon,
        "distance_m": distance_m,
        "rating": rating,
        "reviews_count": reviews_count,
        "source": "osm",
    }
