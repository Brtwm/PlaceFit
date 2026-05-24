import pytest
from app.config.settings import Settings
from app.providers.llm.fallback import FallbackReportProvider
from app.providers.llm.openai_compatible import OpenAICompatibleReportProvider
from app.schemas.report import ReportResult
from app.services.report import ReportService, ReportServiceError
from tests.unit.report_helpers import sample_report_input


def test_openai_compatible_mock_success_returns_success_report() -> None:
    provider = OpenAICompatibleReportProvider(
        settings=Settings(
            llm_enabled=True,
            llm_api_key="test-key",
            llm_base_url="https://llm.example.test/v1",
            llm_model="gpt-compatible",
            _env_file=None,
        ),
        chat_completion_client=lambda _payload, _timeout: {
            "choices": [
                {
                    "message": {
                        "content": "## Краткий вывод\nАдрес можно рассматривать.",
                    },
                },
            ],
        },
    )
    service = ReportService(
        settings=Settings(llm_enabled=True, llm_api_key="test-key", _env_file=None),
        llm_provider=provider,
        fallback_provider=FallbackReportProvider(),
    )

    report = service.generate_report(sample_report_input())

    assert report == ReportResult(
        status="success",
        text="## Краткий вывод\nАдрес можно рассматривать.",
        provider="openai_compatible",
        model="gpt-compatible",
        prompt_version="v1.0",
    )


def test_provider_error_falls_back() -> None:
    provider = OpenAICompatibleReportProvider(
        settings=Settings(
            llm_enabled=True,
            llm_api_key="test-key",
            llm_base_url="https://llm.example.test/v1",
            llm_model="gpt-compatible",
            _env_file=None,
        ),
        chat_completion_client=_raise_provider_error,
    )
    service = ReportService(
        settings=Settings(llm_enabled=True, llm_api_key="test-key", _env_file=None),
        llm_provider=provider,
        fallback_provider=FallbackReportProvider(),
    )

    report = service.generate_report(sample_report_input())

    assert report.status == "fallback"
    assert report.provider == "fallback"


def test_malformed_provider_response_falls_back() -> None:
    provider = OpenAICompatibleReportProvider(
        settings=Settings(
            llm_enabled=True,
            llm_api_key="test-key",
            llm_base_url="https://llm.example.test/v1",
            llm_model="gpt-compatible",
            _env_file=None,
        ),
        chat_completion_client=lambda _payload, _timeout: {"choices": []},
    )
    service = ReportService(
        settings=Settings(llm_enabled=True, llm_api_key="test-key", _env_file=None),
        llm_provider=provider,
        fallback_provider=FallbackReportProvider(),
    )

    report = service.generate_report(sample_report_input())

    assert report.status == "fallback"
    assert report.provider == "fallback"


def test_llm_failed_only_when_fallback_also_fails() -> None:
    service = ReportService(
        settings=Settings(llm_enabled=True, llm_api_key="test-key", _env_file=None),
        llm_provider=BrokenProvider(),
        fallback_provider=BrokenProvider(),
    )

    with pytest.raises(ReportServiceError):
        service.generate_report(sample_report_input())


class BrokenProvider:
    def generate(self, report_input):  # noqa: ANN001
        raise RuntimeError("provider failed")


def _raise_provider_error(_payload: object, _timeout: float) -> object:
    raise TimeoutError("timeout")
