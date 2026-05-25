"""PlaceFit Streamlit entrypoint."""

from __future__ import annotations

from html import escape

import streamlit as st

from ui.api_client import ApiClient, ApiError
from ui.components.layout import setup_page


def main() -> None:
    base_url = setup_page(title="Главная")
    client = ApiClient(base_url)

    st.markdown(
        """
        <div class="pf-hero">
          <div class="pf-kicker">PLACEFIT MVP</div>
          <h1>PlaceFit — оценка локации под ПВЗ в Краснодаре</h1>
          <p>
            Backend детерминированно считает score, confidence, финансы и решение.
            Отчёт только объясняет уже подготовленные данные.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_status, col_scope = st.columns([1, 2])
    with col_status:
        _render_backend_status(client)
    with col_scope:
        st.markdown(
            """
            <div class="pf-card">
              <div class="pf-section-title">Быстрый старт</div>
              <ol>
                <li>
                  Запустите backend:
                  <code>uv run uvicorn app.main:app --reload</code>
                </li>
                <li>
                  Запустите UI:
                  <code>uv run streamlit run ui/streamlit_app.py</code>
                </li>
                <li>Откройте страницу “Анализ адреса”</li>
              </ol>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### Что показывает MVP")
    a, b, c = st.columns(3)
    a.markdown(
        '<div class="pf-card"><strong>Score 0–100</strong><br>'
        'Спрос, конкуренция, аренда, помещение и доступность.</div>',
        unsafe_allow_html=True,
    )
    b.markdown(
        '<div class="pf-card"><strong>Финансы</strong><br>'
        'Расходы, нужный доход, прибыль и окупаемость из backend.</div>',
        unsafe_allow_html=True,
    )
    c.markdown(
        '<div class="pf-card"><strong>Ручная проверка</strong><br>'
        'Чек-лист и marketplace checks без автоматического pass/fail.</div>',
        unsafe_allow_html=True,
    )


def _render_backend_status(client: ApiClient) -> None:
    health = client.health()
    if isinstance(health, ApiError):
        st.markdown(
            """
            <div class="pf-card">
              <div class="pf-section-title">Статус backend</div>
              <span class="pf-badge pf-status-error">недоступен</span>
              <p class="pf-muted">
                Запустите <code>uv run uvicorn app.main:app --reload</code>.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander("Технические детали"):
            st.write(health)
        return

    status = health.get("status", "ok")
    st.markdown(
        f"""
        <div class="pf-card">
          <div class="pf-section-title">Статус backend</div>
          <span class="pf-badge pf-status-ok">
            Backend отвечает: {escape(str(status))}
          </span>
          <p class="pf-muted">{escape(client.base_url)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
