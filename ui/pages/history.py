"""Analysis history Streamlit page."""

from __future__ import annotations

from datetime import date
from html import escape
from typing import Any

import streamlit as st

from ui.api_client import ApiClient, ApiError
from ui.components.layout import render_page_header, setup_page


def main() -> None:
    client = ApiClient(setup_page(title="История"))

    render_page_header(
        "История анализов",
        "Список сохранённых backend-анализов для business_type = pvz.",
    )

    params = _render_filters()
    response = client.list_locations(params)
    if isinstance(response, ApiError):
        _render_api_error(response)
        return

    items = response.get("items") or []
    total = response.get("total", 0)
    st.caption(f"Найдено: {total}")

    if not items:
        st.markdown(
            """
            <div class="pf-card">
              <div class="pf-section-title">История пока пустая</div>
              <p class="pf-muted">
                Запустите первый анализ на странице “Анализ адреса”.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    _render_history_cards(items)

    with st.expander("Табличный вид", expanded=False):
        st.dataframe(
            [_history_row(item) for item in items],
            hide_index=True,
            use_container_width=True,
        )


def _render_history_cards(items: list[dict[str, Any]]) -> None:
    st.markdown("### Сохранённые анализы")
    for item in items:
        cols = st.columns([4, 1])
        cols[0].markdown(
            _history_card(item),
            unsafe_allow_html=True,
        )
        if cols[1].button("Подробнее", key=f"detail_{item.get('id')}"):
            location_id = int(item["id"])
            st.session_state["selected_location_id"] = location_id
            st.query_params["id"] = str(location_id)
            try:
                st.switch_page("pages/detail.py")
            except Exception:
                st.info("Откройте страницу “detail” в меню слева.")


def _render_filters() -> dict[str, Any]:
    with st.expander("Фильтры", expanded=True):
        c1, c2, c3 = st.columns(3)
        min_score = c1.number_input("Минимальный score", 0, 100, value=0)
        max_score = c2.number_input("Максимальный score", 0, 100, value=100)
        decision = c3.text_input("Решение содержит точный текст")

        d1, d2, d3, d4 = st.columns(4)
        use_date_from = d1.checkbox("Дата от")
        date_from = d2.date_input(
            "date_from",
            value=date.today(),
            disabled=not use_date_from,
        )
        use_date_to = d3.checkbox("Дата до")
        date_to = d4.date_input("date_to", value=date.today(), disabled=not use_date_to)

        l1, l2 = st.columns(2)
        limit = l1.number_input("Limit", min_value=1, max_value=100, value=50)
        offset = l2.number_input("Offset", min_value=0, value=0)

    return {
        "business_type": "pvz",
        "min_score": int(min_score) if min_score > 0 else None,
        "max_score": int(max_score) if max_score < 100 else None,
        "decision": decision.strip() or None,
        "date_from": date_from.isoformat() if use_date_from else None,
        "date_to": date_to.isoformat() if use_date_to else None,
        "limit": int(limit),
        "offset": int(offset),
    }


def _history_card(item: dict[str, Any]) -> str:
    score = _value(item.get("total_score"))
    confidence = _value(item.get("confidence_score"))
    decision = _value(item.get("decision"))
    net_profit = _rub(item.get("net_profit"))
    payback = _months(item.get("payback_months"))
    created_at = _value(item.get("created_at"))
    address = _value(item.get("address"))
    location_id = _value(item.get("id"))
    return f"""
    <div class="pf-history-card">
      <div class="pf-history-title">#{escape(location_id)} · {escape(address)}</div>
      <div class="pf-history-meta">
        score {escape(score)} · confidence {escape(confidence)} · {escape(decision)}
      </div>
      <div class="pf-history-meta">
        прибыль {escape(net_profit)} · окупаемость {escape(payback)}
        · {escape(created_at)}
      </div>
    </div>
    """


def _history_row(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item.get("id"),
        "address": item.get("address"),
        "rent": item.get("rent"),
        "total_score": item.get("total_score"),
        "confidence_score": item.get("confidence_score"),
        "decision": item.get("decision"),
        "net_profit": item.get("net_profit"),
        "payback_months": item.get("payback_months"),
        "created_at": item.get("created_at"),
    }


def _render_api_error(error: ApiError) -> None:
    st.error(f"{error.message} ({error.code})")
    with st.expander("Технические детали"):
        st.write(error)


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


def _value(value: Any) -> str:
    if value is None or value == "":
        return "—"
    return str(value)


if __name__ == "__main__":
    main()
