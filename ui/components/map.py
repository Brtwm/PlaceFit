"""Folium map rendering for analysis results."""

from __future__ import annotations

from html import escape
from typing import Any

import folium
import streamlit as st
from streamlit_folium import st_folium


def render_analysis_map(result: dict[str, Any], *, height: int = 580) -> None:
    """Render analyzed location and optional competitor markers."""

    location = result.get("location", {})
    lat = _to_float(location.get("lat"))
    lon = _to_float(location.get("lon"))
    if lat is None or lon is None:
        st.warning("Координаты локации отсутствуют в ответе backend.")
        return

    analysis_map = folium.Map(location=[lat, lon], zoom_start=15, control_scale=True)
    folium.Marker(
        [lat, lon],
        tooltip="Анализируемая локация",
        popup=_html(
            [
                ("Адрес", location.get("address")),
                ("Нормализованный адрес", location.get("normalized_address")),
            ],
        ),
        icon=folium.Icon(color="red", icon="home", prefix="fa"),
    ).add_to(analysis_map)

    competitor_markers = 0
    missing_coordinates = 0
    for competitor in result.get("competitors", {}).get("list") or []:
        comp_lat = _to_float(competitor.get("lat"))
        comp_lon = _to_float(competitor.get("lon"))
        if comp_lat is None or comp_lon is None:
            missing_coordinates += 1
            continue

        competitor_markers += 1
        folium.Marker(
            [comp_lat, comp_lon],
            tooltip=str(competitor.get("brand") or competitor.get("name") or "POI"),
            popup=_competitor_popup(competitor),
            icon=folium.Icon(color="blue", icon="shopping-bag", prefix="fa"),
        ).add_to(analysis_map)

    _add_legend(analysis_map)
    st_folium(analysis_map, height=height, use_container_width=True)

    if missing_coordinates:
        st.info(
            "В текущем API-контракте координаты конкурентов не передаются, "
            "поэтому POI-маркеры не строятся. Список конкурентов ниже отображает "
            "все данные, полученные от backend.",
        )
    elif competitor_markers == 0:
        st.info("В ответе backend нет конкурентов с координатами для отображения.")


def _competitor_popup(competitor: dict[str, Any]) -> str:
    return _html(
        [
            ("Бренд", competitor.get("brand")),
            ("Тип/категория", competitor.get("category")),
            ("Дистанция", _meters(competitor.get("distance_m"))),
            ("Название", competitor.get("name")),
            ("Адрес", competitor.get("address")),
            ("Рейтинг", competitor.get("rating")),
            ("Отзывы", competitor.get("reviews_count")),
            ("Источник", competitor.get("source")),
        ],
    )


def _add_legend(analysis_map: folium.Map) -> None:
    legend = """
    <div style="
        position: fixed; bottom: 28px; left: 28px; z-index: 9999;
        background: #111827; color: #f8fafc; padding: 10px 12px; border-radius: 8px;
        border: 1px solid #334155; box-shadow: 0 8px 24px rgba(0, 0, 0, .28);
        font-size: 13px;">
      <div><strong>Маркеры</strong></div>
      <div><span style="color:#ff5a5f;">●</span> анализируемая локация</div>
      <div><span style="color:#38bdf8;">●</span> конкурент/POI с координатами</div>
    </div>
    """
    analysis_map.get_root().html.add_child(folium.Element(legend))


def _html(rows: list[tuple[str, Any]]) -> str:
    items = "".join(
        f"<tr><th>{escape(label)}</th><td>{escape(_value(value))}</td></tr>"
        for label, value in rows
        if value is not None and value != ""
    )
    return f"""
    <table style="min-width:240px">
      <tbody>{items}</tbody>
    </table>
    """


def _to_float(value: Any) -> float | None:
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


def _meters(value: Any) -> str | None:
    if value is None:
        return None
    return f"{value} м"


def _value(value: Any) -> str:
    if value is None or value == "":
        return "—"
    return str(value)
