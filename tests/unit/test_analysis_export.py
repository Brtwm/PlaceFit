import importlib
import json
from pathlib import Path

from app.schemas.analysis import AnalysisResponse
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


def test_analysis_export_import_is_contract_only() -> None:
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


def _load_fixture(name: str) -> dict[str, object]:
    with (FIXTURES_DIR / name).open(encoding="utf-8") as file:
        return json.load(file)


def _contract_text(*values: object) -> str:
    return " ".join(str(value) for value in values)
