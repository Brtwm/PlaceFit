from datetime import UTC, datetime

import pytest
from app.schemas import (
    AnalysisDelta,
    AnalysisDeltaSummary,
    AnalysisLineage,
    AnalysisRefreshRequest,
    CompetitorDeltaItem,
    CompetitorsDeltaSection,
    DataSourcesDelta,
    FinanceDeltaSection,
    InputsDeltaSection,
    LocationProvenanceDeltaSection,
    ScalarDelta,
    ScoreDeltaSection,
)
from pydantic import ValidationError


def _scalar(field: str, before: object, after: object) -> dict[str, object]:
    return {
        "field": field,
        "before": before,
        "after": after,
        "status": "unchanged" if before == after else "changed",
        "direction": "neutral",
    }


def _analysis_request() -> dict[str, object]:
    return {
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
        "expected_gross_income_by_user": None,
        "investment": 600_000,
        "desired_profit": 80_000,
    }


def _delta_payload() -> dict[str, object]:
    unchanged = _scalar("value", 1, 1)
    input_fields = {
        field: {**unchanged, "field": field}
        for field in (
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
        )
    }
    competitor_fields = {
        field: {**unchanged, "field": field}
        for field in (
            "competitors_300m",
            "competitors_500m",
            "competitors_700m",
            "nearest_competitor_distance_m",
            "average_competitor_distance_m",
        )
    }
    score_fields = {
        field: {**unchanged, "field": field}
        for field in (
            "scoring_version",
            "total_score",
            "confidence_score",
            "decision",
            "demand_score",
            "competition_score",
            "rent_score",
            "premises_score",
            "accessibility_score",
        )
    }
    finance_fields = {
        field: {**unchanged, "field": field}
        for field in (
            "monthly_costs",
            "required_gross_income",
            "expected_gross_income_by_user",
            "net_profit",
            "payback_months",
        )
    }
    return {
        "previous_analysis_id": 1,
        "current_analysis_id": 2,
        "previous_created_at": datetime(2026, 6, 20, tzinfo=UTC),
        "current_created_at": datetime(2026, 6, 21, tzinfo=UTC),
        "previous_snapshot_origin": "legacy_materialized",
        "current_snapshot_origin": "native",
        "snapshot_schema_version": "v1",
        "scoring_version_warning": None,
        "inputs": input_fields,
        "location_provenance": {
            "normalized_address": _scalar("normalized_address", "x", "x"),
            "lat": _scalar("lat", 45.0, 45.0),
            "lon": _scalar("lon", 39.0, 39.0),
            "data_sources": {
                "field": "data_sources",
                "before": [],
                "after": [],
                "status": "unchanged",
                "direction": "neutral",
            },
        },
        "competitors": {**competitor_fields, "items": []},
        "score": score_fields,
        "finance": finance_fields,
        "summary": {
            "changed_inputs": 0,
            "competitors_added": 0,
            "competitors_removed": 0,
            "competitors_changed": 0,
            "competitors_unchanged": 0,
        },
    }


def test_refresh_request_validates_full_analysis_request() -> None:
    request = AnalysisRefreshRequest.model_validate(
        {"analysis_request": _analysis_request()},
    )

    assert request.analysis_request.business_type == "pvz"


@pytest.mark.parametrize(
    "model",
    [
        ScalarDelta,
        CompetitorDeltaItem,
        InputsDeltaSection,
        LocationProvenanceDeltaSection,
        CompetitorsDeltaSection,
        ScoreDeltaSection,
        FinanceDeltaSection,
        AnalysisDeltaSummary,
        AnalysisLineage,
        AnalysisRefreshRequest,
        DataSourcesDelta,
        AnalysisDelta,
    ],
)
def test_delta_schemas_forbid_extra_fields(model: type[object]) -> None:
    payload = _payload_for_model(model)
    payload["unexpected"] = True

    with pytest.raises(ValidationError):
        model.model_validate(payload)  # type: ignore[attr-defined]


def test_scalar_delta_rejects_generic_payloads() -> None:
    payload = _scalar("rent", {"unvalidated": True}, 85_000)

    with pytest.raises(ValidationError):
        ScalarDelta.model_validate(payload)


@pytest.mark.parametrize("field", ["status", "direction"])
def test_scalar_delta_rejects_unknown_status_and_direction(field: str) -> None:
    payload = _scalar("rent", 85_000, 85_000)
    payload[field] = "unknown"

    with pytest.raises(ValidationError):
        ScalarDelta.model_validate(payload)


@pytest.mark.parametrize("origin", ["native", "legacy_materialized"])
def test_analysis_delta_accepts_snapshot_origins(origin: str) -> None:
    payload = _delta_payload()
    payload["previous_snapshot_origin"] = origin

    delta = AnalysisDelta.model_validate(payload)

    assert delta.previous_snapshot_origin == origin


def _payload_for_model(model: type[object]) -> dict[str, object]:
    delta = _delta_payload()
    if model is ScalarDelta:
        return _scalar("rent", 85_000, 85_000)
    if model is CompetitorDeltaItem:
        return {
            "identity": "osm:1",
            "status": "unchanged",
            "before": None,
            "after": None,
            "changed_fields": [],
        }
    if model is InputsDeltaSection:
        return dict(delta["inputs"])  # type: ignore[arg-type]
    if model is LocationProvenanceDeltaSection:
        return dict(delta["location_provenance"])  # type: ignore[arg-type]
    if model is CompetitorsDeltaSection:
        return dict(delta["competitors"])  # type: ignore[arg-type]
    if model is ScoreDeltaSection:
        return dict(delta["score"])  # type: ignore[arg-type]
    if model is FinanceDeltaSection:
        return dict(delta["finance"])  # type: ignore[arg-type]
    if model is AnalysisDeltaSummary:
        return dict(delta["summary"])  # type: ignore[arg-type]
    if model is AnalysisLineage:
        return {
            "root_analysis_id": 1,
            "previous_analysis_id": 1,
            "current_analysis_id": 2,
        }
    if model is AnalysisRefreshRequest:
        return {"analysis_request": _analysis_request()}
    if model is DataSourcesDelta:
        return {
            "field": "data_sources",
            "before": [],
            "after": [],
            "status": "unchanged",
            "direction": "neutral",
        }
    return delta
