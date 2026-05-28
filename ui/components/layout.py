"""Shared Streamlit layout helpers."""

from __future__ import annotations

import os
from html import escape

import streamlit as st

from ui.api_client import DEFAULT_API_BASE_URL
from ui.components.style import apply_global_styles


def setup_page(*, title: str, icon: str = "📍") -> str:
    """Configure the page, apply global styles, and render shared sidebar."""

    st.set_page_config(
        page_title=f"{title} · PlaceFit",
        page_icon=icon,
        layout="wide",
    )
    apply_global_styles()
    return render_sidebar()


def render_sidebar() -> str:
    """Render the only visible PlaceFit navigation and return API base URL."""

    st.sidebar.markdown(
        """
        <div class="pf-sidebar-brand">
          <div class="pf-sidebar-title">PlaceFit</div>
          <div class="pf-sidebar-subtitle">MVP: Краснодар, ПВЗ, один адрес</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.page_link("streamlit_app.py", label="Главная", icon="🏠")
    st.sidebar.page_link("pages/analyze.py", label="Анализ адреса", icon="📍")
    st.sidebar.page_link("pages/history.py", label="История", icon="🗂️")
    st.sidebar.page_link("pages/detail.py", label="Детали", icon="🔎")
    st.sidebar.divider()

    default_base = os.getenv("PLACEFIT_API_BASE_URL") or DEFAULT_API_BASE_URL
    base_url = st.sidebar.text_input(
        "API base URL",
        value=st.session_state.get("api_base_url", default_base),
    )
    st.session_state["api_base_url"] = base_url
    st.sidebar.markdown(
        """
        <p class="pf-sidebar-note">
        В UI не передаются ключи provider-ов, LLM или базы данных.
        </p>
        """,
        unsafe_allow_html=True,
    )
    return base_url


def render_page_header(title: str, subtitle: str | None = None) -> None:
    """Render a compact product page header."""

    subtitle_html = (
        f'<p class="pf-page-subtitle">{escape(subtitle)}</p>' if subtitle else ""
    )
    st.markdown(
        f"""
        <div class="pf-page-header">
          <h1>{escape(title)}</h1>
          {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
