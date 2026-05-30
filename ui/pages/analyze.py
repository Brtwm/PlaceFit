"""Analyze address Streamlit page."""

from __future__ import annotations

from typing import Any

import streamlit as st

from ui.api_client import ApiClient, ApiError
from ui.components.layout import render_page_header, setup_page
from ui.components.result import render_analysis_result

DEFAULTS = {
    "address": "Краснодар, ул. Восточно-Кругликовская, 30",
    "rent": 85000,
    "area_m2": 35.0,
    "floor": 1,
    "first_floor": True,
    "separate_entrance": True,
    "parking": True,
    "signage_possible": True,
    "storage_area": True,
    "repair_condition": "normal",
    "new_residential_area": True,
    "high_density_area": True,
    "bus_stop_nearby": True,
    "good_visibility": True,
    "expected_gross_income_by_user": 360000,
    "investment": 600000,
    "desired_profit": 80000,
}


def main() -> None:
    client = ApiClient(setup_page(title="Анализ адреса"))

    render_page_header(
        "Анализ адреса",
        "Расчёты выполняет backend. UI только отправляет ввод и показывает результат.",
    )

    payload = _render_form()
    if payload is not None:
        errors = _validate_payload(payload)
        if errors:
            for error in errors:
                st.error(error)
        else:
            with st.spinner(
                "Backend анализирует адрес, конкурентов, score и финансы...",
            ):
                response = client.analyze(payload)
            if isinstance(response, ApiError):
                st.session_state.pop("last_analysis_result", None)
                _render_api_error(response)
            else:
                st.session_state["last_analysis_result"] = response
                st.success("Анализ готов.")

    result = st.session_state.get("last_analysis_result")
    if isinstance(result, dict):
        st.markdown("### Результат анализа")
        render_analysis_result(result)
    else:
        st.info(
            "Заполните форму и отправьте анализ. "
            "Демо-результаты без backend не создаются.",
        )


def _render_form() -> dict[str, Any] | None:
    for key, value in DEFAULTS.items():
        st.session_state.setdefault(key, value)

    with st.form("analysis_form"):
        st.markdown(
            '<div class="pf-section-title">Адрес и помещение</div>',
            unsafe_allow_html=True,
        )
        address = st.text_input("Адрес", key="address")
        st.text_input("Тип бизнеса", value="ПВЗ", disabled=True)

        c1, c2, c3 = st.columns(3)
        rent = c1.number_input("Аренда, ₽/мес", min_value=0, step=5000, key="rent")
        area_m2 = c2.number_input("Площадь, м²", min_value=0.0, step=1.0, key="area_m2")
        floor = c3.number_input("Этаж", step=1, key="floor")

        st.markdown(
            '<div class="pf-section-title">Условия локации</div>',
            unsafe_allow_html=True,
        )
        a, b, c, d = st.columns(4)
        first_floor = a.checkbox("Первый этаж", key="first_floor")
        separate_entrance = b.checkbox("Отдельный вход", key="separate_entrance")
        parking = c.checkbox("Парковка", key="parking")
        signage_possible = d.checkbox("Возможна вывеска", key="signage_possible")

        e, f, g, h = st.columns(4)
        storage_area = e.checkbox("Есть складская зона", key="storage_area")
        new_residential_area = f.checkbox(
            "Новый жилой район",
            key="new_residential_area",
        )
        high_density_area = g.checkbox("Высокая плотность", key="high_density_area")
        bus_stop_nearby = h.checkbox("Остановка рядом", key="bus_stop_nearby")

        i, j = st.columns(2)
        good_visibility = i.checkbox("Хорошая видимость", key="good_visibility")
        repair_condition = j.selectbox(
            "Состояние ремонта",
            options=["normal", "good", "bad"],
            index=["normal", "good", "bad"].index(st.session_state["repair_condition"]),
            key="repair_condition",
        )

        st.markdown(
            '<div class="pf-section-title">Финансовые гипотезы</div>',
            unsafe_allow_html=True,
        )
        f1, f2, f3 = st.columns(3)
        expected_income = f1.number_input(
            "Ожидаемый доход, ₽/мес",
            min_value=0,
            step=10000,
            key="expected_gross_income_by_user",
        )
        investment = f2.number_input(
            "Инвестиции, ₽",
            min_value=0,
            step=50000,
            key="investment",
        )
        desired_profit = f3.number_input(
            "Желаемая прибыль, ₽/мес",
            min_value=0,
            step=10000,
            key="desired_profit",
        )

        submitted = st.form_submit_button("Запустить анализ", type="primary")

    if not submitted:
        return None

    return {
        "address": address,
        "business_type": "pvz",
        "rent": int(rent),
        "area_m2": float(area_m2),
        "floor": int(floor),
        "first_floor": bool(first_floor),
        "separate_entrance": bool(separate_entrance),
        "parking": bool(parking),
        "signage_possible": bool(signage_possible),
        "storage_area": bool(storage_area),
        "repair_condition": repair_condition,
        "new_residential_area": bool(new_residential_area),
        "high_density_area": bool(high_density_area),
        "bus_stop_nearby": bool(bus_stop_nearby),
        "good_visibility": bool(good_visibility),
        "expected_gross_income_by_user": int(expected_income) or None,
        "investment": int(investment),
        "desired_profit": int(desired_profit),
    }


def _validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not str(payload.get("address", "")).strip():
        errors.append("Укажите адрес.")
    if payload["rent"] <= 0:
        errors.append("Аренда должна быть положительной.")
    if payload["area_m2"] <= 0:
        errors.append("Площадь должна быть положительной.")
    if payload["investment"] <= 0:
        errors.append("Инвестиции должны быть положительными.")
    if payload["desired_profit"] <= 0:
        errors.append("Желаемая прибыль должна быть положительной.")
    expected_income = payload.get("expected_gross_income_by_user")
    if expected_income is not None and expected_income <= 0:
        errors.append("Ожидаемый доход должен быть положительным.")
    return errors


def _render_api_error(error: ApiError) -> None:
    st.error(f"{error.message} ({error.code})")
    if error.code == "ADDRESS_AMBIGUOUS" and error.suggestions:
        st.warning("Выберите один из найденных вариантов и повторите анализ.")
        for index, suggestion in enumerate(error.suggestions):
            address = str(suggestion.get("address", ""))
            if st.button(address, key=f"suggestion_{index}"):
                st.session_state["address"] = address
                st.rerun()

    with st.expander("Технические детали"):
        st.write(error)


if __name__ == "__main__":
    main()
