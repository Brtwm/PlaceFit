"""Reusable result rendering helpers for Streamlit pages."""

from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st


def render_score_summary(result: dict[str, Any]) -> None:
    """Render score, confidence, decision, and version."""

    score = result.get("score", {})
    _render_metric_grid(
        [
            ("Итоговый score", _score(score.get("total_score")), "Оценка 0-100"),
            ("Confidence", _score(score.get("confidence_score")), "Надёжность данных"),
            ("Решение", _value(score.get("decision")), "Backend decision"),
            ("Версия scoring", _value(score.get("scoring_version")), "Правила расчёта"),
        ],
        columns=4,
    )


def render_score_breakdown(result: dict[str, Any]) -> None:
    """Render deterministic score component values."""

    details = result.get("score", {}).get("details", {})
    labels = {
        "demand_score": "Спрос",
        "competition_score": "Конкуренция",
        "rent_score": "Аренда",
        "premises_score": "Помещение",
        "accessibility_score": "Доступность",
    }
    _render_metric_grid(
        [(label, _value(details.get(key)), None) for key, label in labels.items()],
        columns=5,
    )


def render_finance(result: dict[str, Any]) -> None:
    """Render finance metrics returned by backend."""

    finance = result.get("finance", {})
    _render_metric_grid(
        [
            ("Ежемесячные расходы", _rub(finance.get("monthly_costs")), None),
            ("Нужный доход", _rub(finance.get("required_gross_income")), None),
            (
                "Гипотеза пользователя по валовой выручке",
                _rub(finance.get("expected_gross_income_by_user")),
                "Гипотеза пользователя",
            ),
            ("Чистая прибыль", _rub(finance.get("net_profit")), None),
            ("Окупаемость", _months(finance.get("payback_months")), None),
        ],
        columns=5,
    )
    st.warning(
        "Гипотеза пользователя по валовой выручке — не прогноз PlaceFit. "
        "PlaceFit не гарантирует прибыль.",
        icon="⚠️",
    )


def render_competitors(result: dict[str, Any]) -> None:
    """Render competitor counts and list."""

    competitors = result.get("competitors", {})
    _render_metric_grid(
        [
            ("До 300 м", _value(competitors.get("competitors_300m")), None),
            ("До 500 м", _value(competitors.get("competitors_500m")), None),
            ("До 700 м", _value(competitors.get("competitors_700m")), None),
            (
                "Ближайший",
                _meters(competitors.get("nearest_competitor_distance_m")),
                None,
            ),
            (
                "Средняя дистанция",
                _meters(competitors.get("average_competitor_distance_m")),
                None,
            ),
        ],
        columns=5,
    )

    items = competitors.get("list") or []
    if not items:
        st.info("Конкуренты в ответе backend не найдены.")
        return

    rows = [
        {
            "Бренд": item.get("brand"),
            "Название": item.get("name"),
            "Категория": item.get("category"),
            "Адрес": item.get("address"),
            "Дистанция, м": item.get("distance_m"),
            "Рейтинг": item.get("rating"),
            "Отзывы": item.get("reviews_count"),
            "Источник": item.get("source"),
        }
        for item in items
    ]
    st.dataframe(rows, hide_index=True, use_container_width=True)


def render_report(result: dict[str, Any]) -> None:
    """Render AI/fallback report metadata and markdown text."""

    report = result.get("report", {})
    if report.get("status") == "fallback":
        st.info("Отчёт сформирован fallback-шаблоном без LLM.")

    _render_metric_grid(
        [
            ("Статус", _value(report.get("status")), None),
            ("Provider", _value(report.get("provider")), None),
            ("Model", _value(report.get("model")), None),
            ("Prompt", _value(report.get("prompt_version")), None),
        ],
        columns=4,
    )

    text = report.get("text")
    if text:
        st.markdown(text)
    else:
        st.info("Текст отчёта отсутствует в ответе backend.")


def render_checklist(result: dict[str, Any]) -> None:
    """Render backend checklist exactly as returned."""

    checklist = result.get("checklist") or []
    if not checklist:
        st.info("Чек-лист отсутствует в ответе backend.")
        return

    for index, item in enumerate(checklist, start=1):
        st.markdown(
            f'<div class="pf-row"><strong>{index}.</strong> {escape(str(item))}</div>',
            unsafe_allow_html=True,
        )


def render_marketplace_requirements(result: dict[str, Any]) -> None:
    """Render manual-check marketplace requirements."""

    requirements = result.get("marketplace_requirements") or {}
    labels = {
        "ozon": "Ozon",
        "wildberries": "Wildberries",
        "yandex_market": "Яндекс Маркет",
    }
    for key, label in labels.items():
        item = requirements.get(key)
        if not item:
            continue
        with st.expander(label, expanded=False):
            st.markdown(_status_badge(item.get("status")), unsafe_allow_html=True)
            warning = item.get("warning")
            if warning:
                st.warning(warning)
            checks = item.get("manual_checks") or []
            for check in checks:
                st.markdown(f"- {check}")


def render_data_sources(result: dict[str, Any]) -> None:
    """Render data source metadata."""

    sources = result.get("data_sources") or []
    if not sources:
        st.info("Источники данных отсутствуют в ответе backend.")
        return

    rows = [
        {
            "Источник": source.get("source"),
            "Тип данных": source.get("data_type"),
            "Получено": source.get("fetched_at"),
            "Confidence": source.get("confidence"),
        }
        for source in sources
    ]
    st.dataframe(rows, hide_index=True, use_container_width=True)


def render_created_at(result: dict[str, Any]) -> None:
    """Render analysis creation timestamp."""

    st.caption(f"Создано: {_value(result.get('created_at'))}")


def _render_metric_grid(
    metrics: list[tuple[str, str, str | None]],
    *,
    columns: int,
) -> None:
    cols = st.columns(columns)
    for col, (label, value, help_text) in zip(cols, metrics, strict=False):
        col.markdown(_metric_card(label, value, help_text), unsafe_allow_html=True)


def _metric_card(label: str, value: str, help_text: str | None = None) -> str:
    help_html = ""
    if help_text:
        help_html = f'<div class="pf-metric-help">{escape(help_text)}</div>'
    return f"""
    <div class="pf-metric-card">
      <div class="pf-metric-label">{escape(label)}</div>
      <div class="pf-metric-value">{escape(value)}</div>
      {help_html}
    </div>
    """


def _status_badge(status: Any) -> str:
    return f'<span class="pf-badge pf-badge-muted">{escape(_value(status))}</span>'


def _score(value: Any) -> str:
    return "—" if value is None else f"{value}/100"


def _rub(value: Any) -> str:
    if value is None:
        return "—"
    try:
        return f"{int(value):,} ₽".replace(",", " ")
    except (TypeError, ValueError):
        return str(value)


def _months(value: Any) -> str:
    if value is None:
        return "—"
    return f"{value} мес."


def _meters(value: Any) -> str:
    if value is None:
        return "—"
    return f"{value} м"


def _value(value: Any) -> str:
    if value is None or value == "":
        return "—"
    return str(value)
