"""Streamlit export controls for already loaded response snapshots."""

from __future__ import annotations

from typing import Any

import streamlit as st
from app.schemas.analysis import AnalysisResponse
from app.schemas.compare import CompareResponse
from app.services.analysis_export import render_analysis_markdown
from app.services.compare_export import export_compare_markdown
from pydantic import ValidationError

EXPORT_DISCLAIMER_RU = (
    "Экспорт содержит расчетные и справочные данные PlaceFit для поддержки "
    "решения. PlaceFit не гарантирует прибыль и не заменяет ручную проверку "
    "адреса, условий аренды и требований маркетплейсов."
)

MARKDOWN_MIME = "text/markdown; charset=utf-8"
ANALYSIS_MARKDOWN_FILENAME = "placefit_analysis.md"
COMPARE_MARKDOWN_FILENAME = "placefit_compare.md"
MARKDOWN_LABEL = "Скачать Markdown"


def available_analysis_export_labels() -> tuple[str, ...]:
    """Return supported single-analysis export labels."""

    return (MARKDOWN_LABEL,)


def available_compare_export_labels() -> tuple[str, ...]:
    """Return supported compare export labels."""

    return (MARKDOWN_LABEL,)


def render_analysis_download_controls(result: dict[str, Any]) -> None:
    """Render export controls for an already loaded analysis response."""

    try:
        response = AnalysisResponse.model_validate(result)
    except ValidationError:
        st.error(
            "Не удалось подготовить экспорт: результат анализа имеет "
            "неожиданный формат.",
        )
        return

    st.markdown("#### Экспорт")
    st.caption(EXPORT_DISCLAIMER_RU)
    st.download_button(
        MARKDOWN_LABEL,
        data=render_analysis_markdown(response),
        file_name=ANALYSIS_MARKDOWN_FILENAME,
        mime=MARKDOWN_MIME,
    )


def render_compare_download_controls(result: dict[str, Any]) -> None:
    """Render export controls for an already loaded compare response."""

    try:
        response = CompareResponse.model_validate(result)
    except ValidationError:
        st.error(
            "Не удалось подготовить экспорт: результат сравнения имеет "
            "неожиданный формат.",
        )
        return

    st.markdown("#### Экспорт")
    st.caption(EXPORT_DISCLAIMER_RU)
    st.download_button(
        MARKDOWN_LABEL,
        data=export_compare_markdown(response),
        file_name=COMPARE_MARKDOWN_FILENAME,
        mime=MARKDOWN_MIME,
    )
