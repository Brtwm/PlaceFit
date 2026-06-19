import json
from pathlib import Path
from typing import Any

import pytest
from app.schemas.analysis import AnalysisResponse
from app.schemas.compare import CompareResponse
from ui.components import export_controls

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "api"


def test_analysis_export_labels_include_only_markdown() -> None:
    labels = export_controls.available_analysis_export_labels()

    assert labels == ("Скачать Markdown",)
    assert "Скачать CSV" not in labels
    assert "Скачать Excel" not in labels
    assert "Скачать PDF" not in labels


def test_compare_export_labels_include_only_markdown() -> None:
    labels = export_controls.available_compare_export_labels()

    assert labels == ("Скачать Markdown",)
    assert "Скачать CSV" not in labels
    assert "Скачать Excel" not in labels
    assert "Скачать PDF" not in labels


def test_ui_export_filenames_and_mime_are_stable() -> None:
    assert export_controls.ANALYSIS_MARKDOWN_FILENAME == "placefit_analysis.md"
    assert export_controls.COMPARE_MARKDOWN_FILENAME == "placefit_compare.md"
    assert export_controls.MARKDOWN_MIME == "text/markdown; charset=utf-8"


def test_ui_export_disclaimer_is_visible_and_manual_check_oriented() -> None:
    disclaimer = export_controls.EXPORT_DISCLAIMER_RU

    assert "не гарантирует прибыль" in disclaimer
    assert "ручную проверку адреса" in disclaimer
    assert "требований маркетплейсов" in disclaimer


def test_user_hypothesis_labels_are_present_in_ui_sources() -> None:
    for path in (
        Path("ui/pages/analyze.py"),
        Path("ui/pages/compare.py"),
        Path("ui/components/score_card.py"),
    ):
        source = path.read_text(encoding="utf-8")

        assert "Гипотеза пользователя" in source


def test_compare_page_does_not_use_overclaim_copy() -> None:
    source = Path("ui/pages/compare.py").read_text(encoding="utf-8")

    banned_phrases = ("AI выбрал", "гарантированно", "прибыльный вариант")
    for phrase in banned_phrases:
        assert phrase not in source


def test_analysis_download_validates_snapshot_and_uses_markdown_renderer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    downloads: list[tuple[str, dict[str, Any]]] = []
    captions: list[str] = []

    def fake_renderer(response: AnalysisResponse) -> str:
        assert isinstance(response, AnalysisResponse)
        return "analysis markdown"

    monkeypatch.setattr(export_controls, "render_analysis_markdown", fake_renderer)
    monkeypatch.setattr(export_controls.st, "markdown", lambda value: None)
    monkeypatch.setattr(export_controls.st, "caption", captions.append)
    monkeypatch.setattr(
        export_controls.st,
        "download_button",
        lambda label, **kwargs: downloads.append((label, kwargs)),
    )

    export_controls.render_analysis_download_controls(
        _load_fixture("analyze_response_valid.json"),
    )

    assert captions == [export_controls.EXPORT_DISCLAIMER_RU]
    assert downloads == [
        (
            "Скачать Markdown",
            {
                "data": "analysis markdown",
                "file_name": "placefit_analysis.md",
                "mime": "text/markdown; charset=utf-8",
            },
        ),
    ]


def test_compare_download_validates_snapshot_and_uses_markdown_renderer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    downloads: list[tuple[str, dict[str, Any]]] = []
    captions: list[str] = []

    def fake_renderer(response: CompareResponse) -> str:
        assert isinstance(response, CompareResponse)
        return "compare markdown"

    monkeypatch.setattr(export_controls, "export_compare_markdown", fake_renderer)
    monkeypatch.setattr(export_controls.st, "markdown", lambda value: None)
    monkeypatch.setattr(export_controls.st, "caption", captions.append)
    monkeypatch.setattr(
        export_controls.st,
        "download_button",
        lambda label, **kwargs: downloads.append((label, kwargs)),
    )

    export_controls.render_compare_download_controls(
        _load_fixture("compare_response_valid.json"),
    )

    assert captions == [export_controls.EXPORT_DISCLAIMER_RU]
    assert downloads == [
        (
            "Скачать Markdown",
            {
                "data": "compare markdown",
                "file_name": "placefit_compare.md",
                "mime": "text/markdown; charset=utf-8",
            },
        ),
    ]


@pytest.mark.parametrize(
    ("render_controls", "renderer_name"),
    (
        (export_controls.render_analysis_download_controls, "render_analysis_markdown"),
        (export_controls.render_compare_download_controls, "export_compare_markdown"),
    ),
)
def test_invalid_snapshot_shows_error_without_rendering_or_download(
    monkeypatch: pytest.MonkeyPatch,
    render_controls,
    renderer_name: str,
) -> None:
    errors: list[str] = []
    monkeypatch.setattr(export_controls.st, "error", errors.append)
    monkeypatch.setattr(export_controls, renderer_name, _raise_if_called)
    monkeypatch.setattr(export_controls.st, "download_button", _raise_if_called)

    render_controls({})

    assert len(errors) == 1
    assert "неожиданный формат" in errors[0]


def test_ui_export_controls_import_only_snapshot_export_dependencies() -> None:
    source = Path("ui/components/export_controls.py").read_text(encoding="utf-8")
    forbidden_snippets = (
        "ui.api_client",
        "app.providers",
        "app.services.analysis import",
        "app.services.compare import",
        "app.services.scoring",
        "app.services.finance",
        "app.services.confidence",
        "app.services.decision",
        "app.services.geocoding",
        "app.services.competitors",
        "app.services.report",
        "sqlalchemy",
        "httpx",
        "requests",
        "openai",
        "urllib",
    )
    for snippet in forbidden_snippets:
        assert snippet not in source


def _load_fixture(name: str) -> dict[str, Any]:
    with (FIXTURES_DIR / name).open(encoding="utf-8") as file:
        return json.load(file)


def _raise_if_called(*args: object, **kwargs: object) -> None:
    raise AssertionError("Unexpected renderer or download call")
