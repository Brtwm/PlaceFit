import json

from app.schemas.report import ReportResult
from app.services.report import PreparedAnalysisReportInput
from tests.unit.report_helpers import sample_report_input


def test_fallback_result_validates_through_public_schema() -> None:
    report = ReportResult.model_validate(
        {
            "status": "fallback",
            "text": "fallback text",
            "provider": "fallback",
            "model": "none",
            "prompt_version": "v1.0",
        },
    )

    assert report.status == "fallback"
    assert report.provider == "fallback"
    assert report.model == "none"
    assert report.prompt_version == "v1.0"


def test_openai_compatible_success_validates_through_public_schema() -> None:
    report = ReportResult.model_validate(
        {
            "status": "success",
            "text": "## Краткий вывод\nТекст отчёта.",
            "provider": "openai_compatible",
            "model": "gpt-compatible",
            "prompt_version": "v1.0",
        },
    )

    assert report.status == "success"
    assert report.provider == "openai_compatible"


def test_prepared_report_input_round_trips_as_safe_json() -> None:
    report_input = sample_report_input()

    payload = PreparedAnalysisReportInput.model_validate(
        report_input.model_dump(mode="json"),
    )

    assert payload == report_input


def test_prepared_report_json_does_not_contain_forbidden_secret_keys() -> None:
    payload = sample_report_input().model_dump(mode="json")
    serialized = json.dumps(payload, ensure_ascii=False).lower()

    for forbidden in ("api_key", "database_url", "secret", "token", "password"):
        assert forbidden not in serialized
