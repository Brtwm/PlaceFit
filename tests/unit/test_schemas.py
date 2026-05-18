import json
from pathlib import Path
from typing import Any

import pytest
from app.schemas import (
    AnalysisRequest,
    AnalysisResponse,
    ErrorResponse,
    MarketplaceRequirementResult,
    MarketplaceRequirements,
    ReportResult,
    ScoreResult,
)
from pydantic import ValidationError

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "api"


def load_fixture(name: str) -> dict[str, Any]:
    with (FIXTURES_DIR / name).open(encoding="utf-8") as file:
        return json.load(file)


def valid_marketplace_result() -> dict[str, Any]:
    return {
        "status": "needs_manual_check",
        "needs_manual_check": True,
        "manual_checks": ["Проверить вручную"],
        "warning": "Требования маркетплейсов нужно сверить с официальными источниками.",
    }


def valid_report_result(provider: str = "openai_compatible") -> dict[str, Any]:
    status = "fallback" if provider == "fallback" else "success"
    return {
        "status": status,
        "text": "report",
        "provider": provider,
        "model": "runtime-configured",
        "prompt_version": "v1.0",
    }


def valid_score_result(
    total_score: int = 82,
    confidence_score: int = 90,
) -> dict[str, Any]:
    return {
        "total_score": total_score,
        "confidence_score": confidence_score,
        "scoring_version": "v1.0",
        "decision": "можно рассматривать",
        "details": {
            "demand_score": 35,
            "competition_score": 12,
            "rent_score": 15,
            "premises_score": 10,
            "accessibility_score": 10,
        },
    }


def test_valid_analysis_request_fixture_validates() -> None:
    payload = load_fixture("analyze_request_valid.json")

    request = AnalysisRequest.model_validate(payload)

    assert request.business_type == "pvz"


def test_analysis_request_rejects_unsupported_business_type() -> None:
    payload = load_fixture("analyze_request_valid.json")
    payload["business_type"] = "cafe"

    with pytest.raises(ValidationError):
        AnalysisRequest.model_validate(payload)


def test_full_valid_analysis_response_fixture_validates() -> None:
    payload = load_fixture("analyze_response_valid.json")

    response = AnalysisResponse.model_validate(payload)

    assert response.score.total_score == 82
    assert response.report.provider == "openai_compatible"


def test_valid_error_response_fixture_validates() -> None:
    payload = load_fixture("error_response_valid.json")

    response = ErrorResponse.model_validate(payload)

    assert response.error.code == "GEOCODING_FAILED"


def test_marketplace_requirements_allow_only_mvp_marketplaces() -> None:
    payload = {
        "ozon": valid_marketplace_result(),
        "wildberries": valid_marketplace_result(),
        "yandex_market": valid_marketplace_result(),
    }
    MarketplaceRequirements.model_validate(payload)

    payload["cdek"] = valid_marketplace_result()

    with pytest.raises(ValidationError):
        MarketplaceRequirements.model_validate(payload)


@pytest.mark.parametrize("status", ["passed", "failed"])
def test_marketplace_status_rejects_passed_and_failed(status: str) -> None:
    payload = valid_marketplace_result()
    payload["status"] = status

    with pytest.raises(ValidationError):
        MarketplaceRequirementResult.model_validate(payload)


@pytest.mark.parametrize("provider", ["openai_compatible", "fallback"])
def test_report_provider_accepts_documented_providers(provider: str) -> None:
    report = ReportResult.model_validate(valid_report_result(provider))

    assert report.provider == provider


def test_report_provider_rejects_unknown_provider() -> None:
    payload = valid_report_result()
    payload["provider"] = "unknown"

    with pytest.raises(ValidationError):
        ReportResult.model_validate(payload)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("total_score", -1),
        ("total_score", 101),
        ("confidence_score", -1),
        ("confidence_score", 101),
    ],
)
def test_score_bounds_reject_values_outside_0_100(
    field_name: str,
    value: int,
) -> None:
    payload = valid_score_result()
    payload[field_name] = value

    with pytest.raises(ValidationError):
        ScoreResult.model_validate(payload)


@pytest.mark.parametrize(
    ("model", "fixture_name"),
    [
        (AnalysisRequest, "analyze_request_valid.json"),
        (AnalysisResponse, "analyze_response_valid.json"),
    ],
)
def test_analysis_schemas_reject_extra_fields(
    model: type[AnalysisRequest] | type[AnalysisResponse],
    fixture_name: str,
) -> None:
    payload = load_fixture(fixture_name)
    payload["extra_field"] = "not allowed"

    with pytest.raises(ValidationError):
        model.model_validate(payload)


def test_report_result_rejects_extra_fields() -> None:
    payload = valid_report_result()
    payload["extra_field"] = "not allowed"

    with pytest.raises(ValidationError):
        ReportResult.model_validate(payload)
