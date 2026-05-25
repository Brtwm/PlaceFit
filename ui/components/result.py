"""Shared full analysis result renderer."""

from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st

from ui.components.map import render_analysis_map
from ui.components.score_card import (
    render_checklist,
    render_competitors,
    render_created_at,
    render_data_sources,
    render_finance,
    render_marketplace_requirements,
    render_report,
    render_score_breakdown,
    render_score_summary,
)


def render_analysis_result(result: dict[str, Any]) -> None:
    """Render a full backend AnalysisResponse."""

    location = result.get("location", {})
    address = escape(str(location.get("address") or "Адрес не указан"))
    normalized_address = escape(str(location.get("normalized_address") or ""))
    st.markdown(
        f"""
        <div class="pf-hero">
          <div class="pf-kicker">Анализ локации</div>
          <h2>{address}</h2>
          <p>{normalized_address}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_score_summary(result)

    tab_score, tab_finance, tab_map, tab_report, tab_checks = st.tabs(
        [
            "Оценка",
            "Финансы",
            "Карта и конкуренты",
            "Отчёт",
            "Проверки",
        ],
    )

    with tab_score:
        st.markdown("#### Детализация score")
        render_score_breakdown(result)
        render_created_at(result)

    with tab_finance:
        render_finance(result)

    with tab_map:
        render_analysis_map(result)
        st.markdown("#### Конкуренты")
        render_competitors(result)

    with tab_report:
        render_report(result)

    with tab_checks:
        st.markdown("#### Чек-лист")
        render_checklist(result)
        st.markdown("#### Требования маркетплейсов")
        render_marketplace_requirements(result)
        st.markdown("#### Источники данных")
        render_data_sources(result)
