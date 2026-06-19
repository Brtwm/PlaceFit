import importlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from app.config.scoring_rules import DECISION_RULES
from app.schemas.compare import DEFAULT_COMPARE_RANKING_RULES, CompareResponse
from app.services import compare_export
from app.services.compare_export import (
    COMPARE_EXPORT_ALLOWED_SECTIONS,
    COMPARE_EXPORT_PROHIBITED_CATEGORIES,
    COMPARE_EXPORT_SOURCE_OF_TRUTH,
    EXPORT_DISCLAIMER,
    export_compare_markdown,
)

COMPARE_EXPORT_SOURCE = Path("app/services/compare_export.py")
FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "api"


def test_export_compare_markdown_contains_snapshot_summary_only() -> None:
    response = _compare_response()

    markdown = export_compare_markdown(response)

    assert "# PlaceFit Compare Summary" in markdown
    assert "created_at" in markdown
    assert "2026-05-31" in markdown
    assert DEFAULT_COMPARE_RANKING_RULES.version in markdown
    assert "uses_llm" in markdown
    assert "False" in markdown
    assert "candidate-2" in markdown
    assert "candidate-1" in markdown
    assert "candidate-3" in markdown
    assert "ADDRESS_AMBIGUOUS" in markdown
    assert "Marketplace requirements need manual verification" in markdown
    assert "expected_gross_income_by_user is a user hypothesis" in markdown
    assert "PlaceFit does not guarantee profit" in markdown
    assert "Report text" not in markdown
    assert "best location because" not in markdown.lower()
    assert "recommendation" not in markdown.lower()
    assert markdown.index("candidate-2") < markdown.index("candidate-1")


def test_compare_fixture_validates_before_contract_assertions() -> None:
    response = CompareResponse.model_validate(
        _load_fixture("compare_response_valid.json"),
    )

    assert response.summary.requested_count == 3
    assert response.ranking_rules.uses_llm is False
    assert response.ranked_candidates[0].candidate_id == "candidate-2"
    assert response.failed_candidates[0].error.suggestions


def test_export_compare_markdown_is_deterministic() -> None:
    response = _compare_response()

    assert export_compare_markdown(response) == export_compare_markdown(response)


def test_compare_export_includes_metadata_and_complete_ranking_rules() -> None:
    response = _compare_response()

    markdown = export_compare_markdown(response)

    expected_values = (
        "| compare_id | 42 |",
        "| created_at | 2026-05-31T12:00:00+00:00 |",
        "| requested_count | 3 |",
        "| successful_count | 2 |",
        "| failed_count | 1 |",
        f"| ranking_rules.version | {response.ranking_rules.version} |",
        "| ranking_rules.uses_llm | False |",
        response.ranking_rules.description,
        "Decision severity order: "
        + " -> ".join(response.ranking_rules.decision_severity_order),
    )
    for value in expected_values:
        assert value in markdown
    for sort_key in response.ranking_rules.sort_keys:
        assert sort_key.field in markdown


def test_compare_export_preserves_snapshot_order_without_resorting() -> None:
    payload = _compare_response().model_dump(mode="json")
    payload["ranked_candidates"][0]["score"]["total_score"] = 1
    payload["ranked_candidates"][1]["score"]["total_score"] = 100
    response = CompareResponse.model_validate(payload)

    markdown = export_compare_markdown(response)

    assert markdown.index("candidate-2") < markdown.index("candidate-1")


def test_compare_export_preserves_ambiguous_address_suggestions() -> None:
    markdown = export_compare_markdown(_compare_response())

    first = "г Краснодар, ул Восточно-Кругликовская, д 30"
    second = "г Краснодар, ул Восточно-Кругликовская, д 30/1"

    assert first in markdown
    assert second in markdown
    assert markdown.index(first) < markdown.index(second)


def test_compare_export_includes_complete_failed_candidate_snapshot() -> None:
    markdown = export_compare_markdown(_compare_response())

    assert "## Failed Candidates" in markdown
    assert (
        "| candidate-3 | 2 | Candidate C | failed | "
        "Краснодар, Восточно-Кругликовская 30 | ADDRESS_AMBIGUOUS | "
        "Найдено несколько вариантов адреса | ambiguous address | 2 |"
    ) in markdown
    assert "| candidate-3 | 1 |" in markdown
    assert "| candidate-3 | 2 |" in markdown


def test_compare_export_keeps_failed_section_when_there_are_no_failures() -> None:
    payload = _compare_response().model_dump(mode="json")
    payload["failed_candidates"] = []
    payload["summary"]["requested_count"] = 2
    payload["summary"]["failed_count"] = 0
    response = CompareResponse.model_validate(payload)

    markdown = export_compare_markdown(response)

    assert "## Failed Candidates" in markdown
    assert "### Ambiguous-address Suggestions" in markdown
    assert "| candidate_id | input_index | label | status |" in markdown


def test_compare_export_aggregates_assumptions_and_warnings_first_seen() -> None:
    response = CompareResponse.model_validate(
        _load_fixture("compare_response_valid.json"),
    )

    markdown = export_compare_markdown(response)

    assert markdown.count("- Shared assumption") == 1
    assert markdown.count("- Shared warning") == 1
    assert markdown.index("- Shared assumption") < markdown.index(
        "- Second candidate assumption",
    )
    assert markdown.index("- Shared warning") < markdown.index(
        "- Second candidate warning",
    )


def test_compare_export_leaves_empty_assumptions_and_warnings_empty() -> None:
    payload = _compare_response().model_dump(mode="json")
    for candidate in payload["ranked_candidates"]:
        candidate["assumptions"] = []
        candidate["warnings"] = []
    response = CompareResponse.model_validate(payload)

    markdown = export_compare_markdown(response)
    assumptions = markdown.split("## Assumptions\n", maxsplit=1)[1].split(
        "## Warnings",
        maxsplit=1,
    )[0]
    warnings = markdown.split("## Warnings\n", maxsplit=1)[1].split(
        "## Limitation Notes",
        maxsplit=1,
    )[0]

    assert "- " not in assumptions
    assert "- " not in warnings


def test_compare_export_escapes_snapshot_table_text() -> None:
    payload = _compare_response().model_dump(mode="json")
    payload["ranked_candidates"][0]["label"] = "Candidate | B\nSouth"
    payload["failed_candidates"][0]["error"]["message"] = "Line 1 | Line 2\nLine 3"
    response = CompareResponse.model_validate(payload)

    markdown = export_compare_markdown(response)

    assert "Candidate \\| B South" in markdown
    assert "Line 1 \\| Line 2 Line 3" in markdown


def test_compare_export_has_no_hidden_recommendation_or_compliance_claims() -> None:
    markdown = export_compare_markdown(_compare_response()).lower()

    unsupported_claims = (
        "best location because the ai recommends it",
        "guaranteed profit",
        "officially compliant",
        "is a system forecast",
        "llm ranked",
        "llm recommends",
    )
    for claim in unsupported_claims:
        assert claim not in markdown

    assert "not a system forecast" in markdown
    assert "uses_llm | false" in markdown


def test_compare_export_does_not_call_runtime_services(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import httpx
    from app.providers import factory as provider_factory
    from app.providers.geocoder.dgis import DgisGeocoder
    from app.providers.geocoder.fake import FakeGeocoder
    from app.providers.llm import openai_compatible
    from app.providers.llm.fallback import FallbackReportProvider
    from app.providers.llm.openai_compatible import OpenAICompatibleReportProvider
    from app.providers.poi_search.dgis import DgisPoiSearchProvider
    from app.providers.poi_search.fake import FakePoiSearchProvider
    from app.providers.poi_search.osm import OsmPoiSearchProvider
    from app.services import analysis as analysis_service
    from app.services import compare as compare_service
    from app.services import competitors as competitors_service
    from app.services import confidence as confidence_service
    from app.services import decision as decision_service
    from app.services import finance as finance_service
    from app.services import geocoding as geocoding_service
    from app.services import report as report_service
    from app.services import scoring as scoring_service
    from sqlalchemy.orm import Session

    monkeypatch.setattr(analysis_service.AnalysisService, "analyze", _raise_if_called)
    monkeypatch.setattr(
        analysis_service.AnalysisService,
        "get_location_detail",
        _raise_if_called,
    )
    monkeypatch.setattr(compare_service.CompareService, "compare", _raise_if_called)
    monkeypatch.setattr(
        compare_service.CompareService,
        "get_saved_compare_session",
        _raise_if_called,
    )
    monkeypatch.setattr(
        geocoding_service.GeocodingService,
        "geocode",
        _raise_if_called,
    )
    monkeypatch.setattr(competitors_service, "search_competitors", _raise_if_called)
    monkeypatch.setattr(scoring_service, "calculate_score", _raise_if_called)
    monkeypatch.setattr(confidence_service, "calculate_confidence", _raise_if_called)
    monkeypatch.setattr(finance_service, "calculate_finance", _raise_if_called)
    monkeypatch.setattr(decision_service, "make_decision", _raise_if_called)
    monkeypatch.setattr(
        report_service.ReportService,
        "generate_report",
        _raise_if_called,
    )
    monkeypatch.setattr(FallbackReportProvider, "generate", _raise_if_called)
    monkeypatch.setattr(
        OpenAICompatibleReportProvider,
        "generate",
        _raise_if_called,
    )
    monkeypatch.setattr(DgisGeocoder, "geocode", _raise_if_called)
    monkeypatch.setattr(FakeGeocoder, "geocode", _raise_if_called)
    monkeypatch.setattr(DgisPoiSearchProvider, "search", _raise_if_called)
    monkeypatch.setattr(FakePoiSearchProvider, "search", _raise_if_called)
    monkeypatch.setattr(OsmPoiSearchProvider, "search", _raise_if_called)
    monkeypatch.setattr(
        provider_factory,
        "build_geocoder_provider",
        _raise_if_called,
    )
    monkeypatch.setattr(provider_factory, "build_poi_providers", _raise_if_called)
    monkeypatch.setattr(httpx, "request", _raise_if_called)
    monkeypatch.setattr(openai_compatible, "urlopen", _raise_if_called)
    monkeypatch.setattr(Session, "get", _raise_if_called)
    monkeypatch.setattr(Session, "execute", _raise_if_called)
    monkeypatch.setattr(Path, "open", _raise_if_called)
    monkeypatch.setattr(Path, "read_text", _raise_if_called)

    markdown = export_compare_markdown(_compare_response())

    assert "# PlaceFit Compare Summary" in markdown


def test_compare_export_contract_allows_existing_compare_json_fields_only() -> None:
    contract_text = _contract_text(
        COMPARE_EXPORT_ALLOWED_SECTIONS,
        COMPARE_EXPORT_SOURCE_OF_TRUTH,
    )

    expected_sources = (
        "CompareResponse.summary",
        "CompareResponse.compare_id",
        "CompareResponse.created_at",
        "CompareResponse.ranking_rules.version",
        "CompareResponse.ranking_rules.sort_keys",
        "CompareResponse.ranking_rules.decision_severity_order",
        "CompareResponse.ranking_rules.uses_llm = false",
        "CompareResponse.ranked_candidates",
        "CompareResponse.ranked_candidates.*.score",
        "CompareResponse.ranked_candidates.*.finance",
        "CompareResponse.ranked_candidates.*.competitors",
        "CompareResponse.ranked_candidates.*.assumptions",
        "CompareResponse.ranked_candidates.*.warnings",
        "CompareResponse.ranked_candidates.*.trade_offs",
        "CompareResponse.failed_candidates.*.status",
        "CompareResponse.failed_candidates.*.error.code",
        "CompareResponse.failed_candidates.*.error.message",
        "CompareResponse.failed_candidates.*.error.details",
        "CompareResponse.failed_candidates.*.error.suggestions",
    )
    for source in expected_sources:
        assert source in contract_text

    assert "only when present in public compare JSON" in contract_text
    assert "when already present" in contract_text


def test_compare_export_contract_prohibits_unsafe_categories() -> None:
    contract_text = _contract_text(COMPARE_EXPORT_PROHIBITED_CATEGORIES).lower()

    expected_prohibitions = (
        "llm-authored ranking conclusions",
        "recomputed ranking",
        "new score calculations",
        "new finance calculations",
        "new confidence calculations",
        "new decision calculations",
        "invented competitor facts",
        "invented traffic facts",
        "invented revenue forecasts",
        "raw external api responses",
        "regenerated report text",
    )
    for prohibition in expected_prohibitions:
        assert prohibition in contract_text


def test_compare_export_disclaimer_states_no_profit_guarantee() -> None:
    assert "PlaceFit does not guarantee profit" in EXPORT_DISCLAIMER
    assert "manual verification" in EXPORT_DISCLAIMER
    assert "not official compliance confirmation" in EXPORT_DISCLAIMER


def test_compare_export_boundary_decision_is_service_only() -> None:
    assert compare_export.COMPARE_EXPORT_BOUNDARY_DECISION == "service_only"
    assert compare_export.COMPARE_EXPORT_API_ENDPOINTS_IMPLEMENTED is False


def test_compare_export_contract_preserves_uses_llm_false_expectation() -> None:
    contract_text = _contract_text(
        COMPARE_EXPORT_ALLOWED_SECTIONS,
        COMPARE_EXPORT_SOURCE_OF_TRUTH,
    )

    assert "CompareResponse.ranking_rules.uses_llm = false" in contract_text
    assert DEFAULT_COMPARE_RANKING_RULES.uses_llm is False


def test_compare_export_contract_import_is_snapshot_only() -> None:
    module = importlib.import_module("app.services.compare_export")

    assert module.EXPORT_DISCLAIMER == compare_export.EXPORT_DISCLAIMER

    source = COMPARE_EXPORT_SOURCE.read_text(encoding="utf-8")
    forbidden_snippets = (
        "from app.api",
        "import app.api",
        "APIRouter",
        "FastAPI",
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
        "urllib",
        "socket",
        "sqlalchemy",
        "from pathlib",
        "import pathlib",
        "from os",
        "import os",
    )
    for snippet in forbidden_snippets:
        assert snippet not in source


def _compare_response() -> CompareResponse:
    return CompareResponse.model_validate(
        {
            "compare_id": 42,
            "created_at": datetime(2026, 5, 31, 12, 0, tzinfo=UTC),
            "ranking_rules": DEFAULT_COMPARE_RANKING_RULES.model_dump(mode="json"),
            "ranked_candidates": [
                _successful_candidate(
                    candidate_id="candidate-2",
                    input_index=1,
                    rank=1,
                    label="Candidate B",
                    total_score=90,
                    net_profit=80_000,
                    payback_months=7.5,
                ),
                _successful_candidate(
                    candidate_id="candidate-1",
                    input_index=0,
                    rank=2,
                    label="Candidate A",
                    total_score=80,
                    net_profit=None,
                    payback_months=None,
                ),
            ],
            "failed_candidates": [_failed_candidate()],
            "summary": {
                "requested_count": 3,
                "successful_count": 2,
                "failed_count": 1,
            },
        },
    )


def _successful_candidate(
    *,
    candidate_id: str,
    input_index: int,
    rank: int,
    label: str,
    total_score: int,
    net_profit: int | None,
    payback_months: float | None,
) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "input_index": input_index,
        "rank": rank,
        "label": label,
        "input_address": f"Input address {input_index}",
        "status": "success",
        "source_analysis_id": None,
        "location_summary": {
            "id": input_index + 1,
            "address": f"Resolved address {input_index}",
            "normalized_address": f"Normalized address {input_index}",
            "lat": 45.035 + input_index / 1000,
            "lon": 39.028 + input_index / 1000,
        },
        "score": {
            "total_score": total_score,
            "confidence_score": 88 - input_index,
            "scoring_version": "v1.0",
            "decision": DECISION_RULES.consider,
            "details": {
                "demand_score": 35,
                "competition_score": 12,
                "rent_score": 15,
                "premises_score": 10,
                "accessibility_score": 8,
            },
        },
        "finance": {
            "monthly_costs": 295_000,
            "required_gross_income": 375_000,
            "expected_gross_income_by_user": 360_000,
            "net_profit": net_profit,
            "payback_months": payback_months,
        },
        "competitors": {
            "competitors_300m": 1 + input_index,
            "competitors_500m": 3 + input_index,
            "competitors_700m": 5 + input_index,
            "nearest_competitor_distance_m": 180,
            "average_competitor_distance_m": 420,
        },
        "assumptions": [
            "expected_gross_income_by_user is a user hypothesis",
            "Shared assumption",
        ],
        "warnings": [
            "Marketplace requirements need manual verification",
            "Shared warning",
        ],
        "trade_offs": [],
    }


def _failed_candidate() -> dict[str, Any]:
    return {
        "candidate_id": "candidate-3",
        "input_index": 2,
        "label": "Candidate C",
        "input_address": "Краснодар, Восточно-Кругликовская 30",
        "status": "failed",
        "error": {
            "code": "ADDRESS_AMBIGUOUS",
            "message": "Найдено несколько вариантов адреса",
            "details": "ambiguous address",
            "suggestions": [
                {
                    "address": "г Краснодар, ул Восточно-Кругликовская, д 30",
                    "lat": 45.035,
                    "lon": 39.028,
                    "confidence": 0.82,
                },
                {
                    "address": "г Краснодар, ул Восточно-Кругликовская, д 30/1",
                    "lat": 45.036,
                    "lon": 39.029,
                    "confidence": 0.78,
                },
            ],
        },
    }


def _load_fixture(name: str) -> dict[str, object]:
    with (FIXTURES_DIR / name).open(encoding="utf-8") as file:
        return json.load(file)


def _raise_if_called(*args: object, **kwargs: object) -> None:
    raise AssertionError("Runtime service should not be called by export renderer")


def _contract_text(*values: object) -> str:
    return " ".join(str(value) for value in values)
