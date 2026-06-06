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


def render_compare_map(compare_response: dict[str, Any], *, height: int = 460) -> None:
    """Render successful compare candidates with known coordinates."""

    markers: list[tuple[dict[str, Any], float, float]] = []
    missing_coordinates: list[str] = []
    for candidate in compare_response.get("ranked_candidates") or []:
        location = candidate.get("location_summary") or {}
        lat = _to_float(location.get("lat"))
        lon = _to_float(location.get("lon"))
        if lat is None or lon is None:
            missing_coordinates.append(_candidate_label(candidate))
            continue
        markers.append((candidate, lat, lon))

    if not markers:
        st.info("Нет успешных кандидатов с координатами для карты.")
        if missing_coordinates:
            st.warning(
                "Успешные кандидаты без координат: "
                + ", ".join(missing_coordinates),
            )
        return

    center_lat = sum(lat for _, lat, _ in markers) / len(markers)
    center_lon = sum(lon for _, _, lon in markers) / len(markers)
    compare_map = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=13,
        control_scale=True,
    )

    for candidate, lat, lon in markers:
        rank = candidate.get("rank")
        label = _candidate_label(candidate)
        tooltip = f"#{rank} {label}" if rank else label
        folium.Marker(
            [lat, lon],
            tooltip=tooltip,
            popup=_compare_candidate_popup(candidate),
            icon=folium.Icon(color="red", icon="home", prefix="fa"),
        ).add_to(compare_map)

    _add_compare_legend(compare_map)
    st_folium(compare_map, height=height, use_container_width=True)

    if missing_coordinates:
        st.warning(
            "Успешные кандидаты без координат: " + ", ".join(missing_coordinates),
        )


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


def _add_compare_legend(compare_map: folium.Map) -> None:
    legend = """
    <div style="
        position: fixed; bottom: 28px; left: 28px; z-index: 9999;
        background: #111827; color: #f8fafc; padding: 10px 12px; border-radius: 8px;
        border: 1px solid #334155; box-shadow: 0 8px 24px rgba(0, 0, 0, .28);
        font-size: 13px;">
      <div><strong>Маркеры</strong></div>
      <div><span style="color:#ff5a5f;">●</span> успешный кандидат</div>
    </div>
    """
    compare_map.get_root().html.add_child(folium.Element(legend))


def _compare_candidate_popup(candidate: dict[str, Any]) -> str:
    location = candidate.get("location_summary") or {}
    score = candidate.get("score") or {}
    finance = candidate.get("finance") or {}
    competitors = candidate.get("competitors") or {}
    return _html(
        [
            ("Ранг", candidate.get("rank")),
            ("Метка", candidate.get("label")),
            ("Адрес", location.get("address") or candidate.get("input_address")),
            ("Score", score.get("total_score")),
            ("Confidence", score.get("confidence_score")),
            ("Решение", score.get("decision")),
            ("Чистая прибыль", _rub(finance.get("net_profit"))),
            ("Окупаемость", _months(finance.get("payback_months"))),
            ("Конкуренты 700 м", competitors.get("competitors_700m")),
        ],
    )


def _candidate_label(candidate: dict[str, Any]) -> str:
    label = candidate.get("label")
    if label:
        return str(label)
    input_index = candidate.get("input_index")
    if input_index is not None:
        return f"Кандидат {input_index + 1}"
    return "Кандидат"


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


def _rub(value: Any) -> str | None:
    if value is None:
        return None
    try:
        return f"{int(value):,} ₽".replace(",", " ")
    except (TypeError, ValueError):
        return str(value)


def _months(value: Any) -> str | None:
    if value is None:
        return None
    return f"{value} мес."


def _value(value: Any) -> str:
    if value is None or value == "":
        return "—"
    return str(value)
