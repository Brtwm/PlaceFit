from app.config.settings import Settings
from app.providers.llm.base import LlmReportProvider
from app.providers.llm.fallback import FallbackReportProvider
from app.services.report import ReportService

from tests.unit.report_helpers import sample_report_input


class FailingLlmProvider:
    def __init__(self) -> None:
        self.calls = 0

    def generate(self, report_input):  # noqa: ANN001
        self.calls += 1
        raise AssertionError("LLM provider should not be called")


def test_llm_disabled_returns_fallback_without_llm_call() -> None:
    llm_provider = FailingLlmProvider()
    service = ReportService(
        settings=Settings(llm_enabled=False, llm_api_key="", _env_file=None),
        llm_provider=llm_provider,
        fallback_provider=FallbackReportProvider(),
    )

    report = service.generate_report(sample_report_input())

    assert report.status == "fallback"
    assert report.provider == "fallback"
    assert report.model == "none"
    assert report.prompt_version == "v1.0"
    assert llm_provider.calls == 0


def test_empty_api_key_returns_fallback_when_llm_enabled() -> None:
    llm_provider = FailingLlmProvider()
    service = ReportService(
        settings=Settings(llm_enabled=True, llm_api_key="", _env_file=None),
        llm_provider=llm_provider,
        fallback_provider=FallbackReportProvider(),
    )

    report = service.generate_report(sample_report_input())

    assert report.status == "fallback"
    assert report.provider == "fallback"
    assert llm_provider.calls == 0


def test_fallback_text_contains_required_business_sections() -> None:
    report = FallbackReportProvider().generate(sample_report_input())

    assert "г Краснодар, ул Восточно-Кругликовская, д 30" in report.text
    assert "82/100" in report.text
    assert "90/100" in report.text
    assert "можно рассматривать" in report.text
    assert "Спрос: 35/35" in report.text
    assert "Конкуренция: 12/25" in report.text
    assert "300 м: 1" in report.text
    assert "500 м: 3" in report.text
    assert "700 м: 5" in report.text
    assert "Ближайший конкурент: 180 м" in report.text
    assert "Ежемесячные расходы: 295000" in report.text
    assert "Необходимый валовый доход: 375000" in report.text
    assert "Ожидаемый валовый доход пользователя: 360000" in report.text
    assert "Чистая прибыль: 65000" in report.text
    assert "Окупаемость: 9.2" in report.text
    assert "гипотеза пользователя" in report.text
    assert "ручной проверки" in report.text


def test_fallback_is_deterministic_for_same_input() -> None:
    provider = FallbackReportProvider()
    report_input = sample_report_input()

    first = provider.generate(report_input)
    second = provider.generate(report_input)

    assert first == second


def test_fallback_provider_matches_protocol_shape() -> None:
    provider: LlmReportProvider = FallbackReportProvider()

    report = provider.generate(sample_report_input())

    assert report.provider == "fallback"
