import importlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.schemas.analysis import AnalysisResponse
from app.schemas.competitor import CompetitorInfo, CompetitorsSummary
from app.schemas.finance import FinanceResult
from app.schemas.location import LocationInfo
from app.schemas.report import (
    DataSourceInfo,
    MarketplaceRequirementResult,
    MarketplaceRequirements,
    ReportResult,
)
from app.schemas.score import ScoreDetails, ScoreResult
from app.services import analysis_export

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "api"
ANALYSIS_EXPORT_SOURCE = Path("app/services/analysis_export.py")


def test_analysis_fixture_validates_before_contract_assertions() -> None:
    payload = _load_fixture("analyze_response_valid.json")

    response = AnalysisResponse.model_validate(payload)

    assert response.location.address
    assert response.score.total_score == 82
    assert response.finance.expected_gross_income_by_user == 360_000
    assert response.competitors.list[0].source == "2gis"


def test_render_analysis_markdown_is_deterministic() -> None:
    response = _analysis_response()

    first = analysis_export.render_analysis_markdown(response)
    second = analysis_export.render_analysis_markdown(response)

    assert first == second


def test_render_analysis_markdown_contains_required_sections_in_order() -> None:
    markdown = analysis_export.render_analysis_markdown(_analysis_response())

    headings = [
        "# Отчёт PlaceFit по адресу",
        "## Summary",
        "## Location",
        "## Score / Confidence / Decision",
        "## Risks",
        "## Finance",
        "## Competitors",
        "## Checklist",
        "## Marketplace manual checks",
        "## User assumptions / hypotheses",
        "## Warnings",
        "## Existing report text",
        "## Data sources",
        "## Limitations",
        "## Disclaimer",
    ]
    positions = [markdown.index(heading) for heading in headings]

    assert positions == sorted(positions)


def test_render_analysis_markdown_labels_expected_income_as_user_hypothesis() -> None:
    markdown = analysis_export.render_analysis_markdown(_analysis_response())

    assert "expected_gross_income_by_user" in markdown
    assert "360000" in markdown
    assert "user-provided hypothesis" in markdown
    assert "пользовательская гипотеза" in markdown
    assert "not a PlaceFit forecast" in markdown
    assert "not a system forecast" in markdown


def test_render_analysis_markdown_includes_disclaimer_and_manual_verification() -> None:
    markdown = analysis_export.render_analysis_markdown(_analysis_response())

    assert "PlaceFit does not guarantee profit" in markdown
    assert "does not replace manual verification" in markdown
    assert "Marketplace requirements require manual verification" in markdown
    assert "official sources" in markdown


def test_render_analysis_markdown_preserves_fallback_report_text() -> None:
    report_text = "Fallback text line 1\n\nFallback text line 2"
    response = _analysis_response(
        report=ReportResult(
            status="fallback",
            text=report_text,
            provider="fallback",
            model="none",
            prompt_version="v1.0",
        ),
    )

    markdown = analysis_export.render_analysis_markdown(response)

    assert report_text in markdown
    assert "| report.status | fallback |" in markdown
    assert "existing fallback report text" in markdown
    assert "Export does not regenerate report text" in markdown


def test_render_analysis_markdown_uses_stable_competitor_order() -> None:
    markdown = analysis_export.render_analysis_markdown(_analysis_response())

    first = markdown.index("Ozon пункт выдачи")
    second = markdown.index("Wildberries пункт выдачи")

    assert first < second


def test_render_analysis_markdown_does_not_call_runtime_services(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.services import (
        analysis as analysis_service,
    )
    from app.services import (
        competitors as competitors_service,
    )
    from app.services import (
        confidence as confidence_service,
    )
    from app.services import (
        decision as decision_service,
    )
    from app.services import (
        finance as finance_service,
    )
    from app.services import (
        geocoding as geocoding_service,
    )
    from app.services import (
        report as report_service,
    )
    from app.services import (
        scoring as scoring_service,
    )

    monkeypatch.setattr(
        analysis_service.AnalysisService,
        "analyze",
        _raise_if_called,
    )
    monkeypatch.setattr(
        geocoding_service.GeocodingService,
        "geocode",
        _raise_if_called,
    )
    monkeypatch.setattr(
        competitors_service,
        "search_competitors",
        _raise_if_called,
    )
    monkeypatch.setattr(scoring_service, "calculate_score", _raise_if_called)
    monkeypatch.setattr(confidence_service, "calculate_confidence", _raise_if_called)
    monkeypatch.setattr(finance_service, "calculate_finance", _raise_if_called)
    monkeypatch.setattr(decision_service, "make_decision", _raise_if_called)
    monkeypatch.setattr(
        report_service.ReportService,
        "generate_report",
        _raise_if_called,
    )

    markdown = analysis_export.render_analysis_markdown(_analysis_response())

    assert "# Отчёт PlaceFit по адресу" in markdown


def test_analysis_export_contract_exposes_allowed_sections_and_sources() -> None:
    contract_text = _contract_text(
        analysis_export.ANALYSIS_EXPORT_ALLOWED_SECTIONS,
        analysis_export.ANALYSIS_EXPORT_SOURCE_OF_TRUTH,
    )

    expected_sources = (
        "AnalysisResponse.location",
        "AnalysisResponse.score",
        "AnalysisResponse.finance",
        "AnalysisResponse.created_at",
        "AnalysisResponse.score.decision",
        "AnalysisResponse.score.confidence_score",
        "AnalysisResponse.marketplace_requirements.*.warning",
        "AnalysisResponse.checklist",
        "FinanceResult.monthly_costs",
        "FinanceResult.required_gross_income",
        "FinanceResult.expected_gross_income_by_user",
        "FinanceResult.net_profit",
        "FinanceResult.payback_months",
        "CompetitorsSummary.competitors_300m",
        "CompetitorsSummary.competitors_500m",
        "CompetitorsSummary.competitors_700m",
        "CompetitorsSummary.list",
        "AnalysisResponse.data_sources",
    )
    for source in expected_sources:
        assert source in contract_text


def test_analysis_export_contract_prohibits_unsafe_categories() -> None:
    contract_text = _contract_text(
        analysis_export.ANALYSIS_EXPORT_PROHIBITED_CATEGORIES,
    ).lower()

    expected_prohibitions = (
        "provider secrets",
        "api keys",
        "raw external api responses",
        "raw provider payloads",
        "invented competitor facts",
        "invented traffic facts",
        "invented revenue forecasts",
        "new score calculations",
        "new finance calculations",
        "new confidence calculations",
        "new decision calculations",
        "regenerated report text",
        "network calls",
        "filesystem reads outside normal source/test files",
        "arbitrary export path handling",
        "new production dependency",
    )
    for prohibition in expected_prohibitions:
        assert prohibition in contract_text


def test_analysis_export_contract_labels_user_income_as_hypothesis() -> None:
    contract_text = _contract_text(
        analysis_export.ANALYSIS_EXPORT_ALLOWED_SECTIONS,
        analysis_export.ANALYSIS_EXPORT_SOURCE_OF_TRUTH,
    )

    assert "expected_gross_income_by_user" in contract_text
    assert "user hypothesis" in contract_text
    assert "not a system forecast" in contract_text


def test_analysis_export_disclaimer_states_no_profit_guarantee() -> None:
    assert "PlaceFit does not guarantee profit" in analysis_export.EXPORT_DISCLAIMER
    assert "manual verification" in analysis_export.EXPORT_DISCLAIMER
    assert "not official compliance confirmation" in analysis_export.EXPORT_DISCLAIMER


def test_analysis_export_import_is_snapshot_only() -> None:
    module = importlib.import_module("app.services.analysis_export")

    assert module.EXPORT_DISCLAIMER == analysis_export.EXPORT_DISCLAIMER

    source = ANALYSIS_EXPORT_SOURCE.read_text(encoding="utf-8")
    forbidden_snippets = (
        "from app.providers",
        "import app.providers",
        "from app.services.analysis",
        "from app.services.compare",
        "from app.services.geocoding",
        "from app.services.competitors",
        "from app.services.scoring",
        "from app.services.finance",
        "from app.services.confidence",
        "from app.services.decision",
        "from app.services.report",
        "from app.providers.llm",
        "httpx",
        "requests",
        "openai",
        "sqlalchemy",
    )
    for snippet in forbidden_snippets:
        assert snippet not in source


def _analysis_response(*, report: ReportResult | None = None) -> AnalysisResponse:
    return AnalysisResponse(
        location=LocationInfo(
            id=1,
            address="Краснодар, ул. Восточно-Кругликовская, 30",
            normalized_address="г Краснодар, ул Восточно-Кругликовская, д 30",
            lat=45.035,
            lon=39.028,
        ),
        competitors=CompetitorsSummary(
            competitors_300m=1,
            competitors_500m=3,
            competitors_700m=5,
            nearest_competitor_distance_m=180,
            average_competitor_distance_m=420,
            list=[
                CompetitorInfo(
                    name="Ozon пункт выдачи",
                    brand="Ozon",
                    category="pvz",
                    address="г Краснодар, ул Восточно-Кругликовская, д 31",
                    lat=45.036,
                    lon=39.029,
                    distance_m=180,
                    rating=4.6,
                    reviews_count=41,
                    source="2gis",
                ),
                CompetitorInfo(
                    name="Wildberries пункт выдачи",
                    brand="Wildberries",
                    category="pvz",
                    address="г Краснодар, ул Восточно-Кругликовская, д 32",
                    lat=45.037,
                    lon=39.03,
                    distance_m=420,
                    rating=None,
                    reviews_count=None,
                    source="osm",
                ),
            ],
        ),
        score=ScoreResult(
            total_score=82,
            confidence_score=90,
            scoring_version="v1.0",
            decision="можно рассматривать",
            details=ScoreDetails(
                demand_score=35,
                competition_score=12,
                rent_score=15,
                premises_score=10,
                accessibility_score=10,
            ),
        ),
        finance=FinanceResult(
            monthly_costs=295_000,
            required_gross_income=375_000,
            expected_gross_income_by_user=360_000,
            net_profit=65_000,
            payback_months=9.2,
        ),
        marketplace_requirements=_marketplace_requirements(),
        report=report
        or ReportResult(
            status="success",
            text="## Краткий вывод\n\nАдрес подходит для дальнейшей проверки.",
            provider="openai_compatible",
            model="runtime-configured",
            prompt_version="v1.0",
        ),
        checklist=[
            "Проверить проходимость утром, днём и вечером.",
            "Проверить требования маркетплейсов по официальным источникам.",
        ],
        data_sources=[
            DataSourceInfo(
                source="2gis",
                data_type="geocoding",
                fetched_at=datetime(2026, 5, 14, 10, 0, tzinfo=UTC),
                confidence=0.95,
            ),
            DataSourceInfo(
                source="osm",
                data_type="competitors",
                fetched_at=datetime(2026, 5, 14, 10, 0, tzinfo=UTC),
            ),
        ],
        created_at=datetime(2026, 5, 14, 10, 0, 5, tzinfo=UTC),
    )


def _marketplace_requirements() -> MarketplaceRequirements:
    warning = "Требования маркетплейсов нужно сверить с официальными источниками."
    manual = MarketplaceRequirementResult(
        status="needs_manual_check",
        needs_manual_check=True,
        manual_checks=["Проверить вручную по официальным источникам."],
        warning=warning,
    )
    return MarketplaceRequirements(
        ozon=manual,
        wildberries=manual,
        yandex_market=manual,
    )


def _raise_if_called(*args: object, **kwargs: object) -> None:
    raise AssertionError("Runtime service should not be called by export renderer")


def _load_fixture(name: str) -> dict[str, object]:
    with (FIXTURES_DIR / name).open(encoding="utf-8") as file:
        return json.load(file)


def _contract_text(*values: object) -> str:
    return " ".join(str(value) for value in values)
