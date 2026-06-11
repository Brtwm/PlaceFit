from pathlib import Path

from ui.components import export_controls


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
