"""Compare candidate locations Streamlit page."""

from __future__ import annotations

from typing import Any

import streamlit as st

from ui.api_client import ApiClient, ApiError
from ui.components.export_controls import render_compare_download_controls
from ui.components.layout import render_page_header, setup_page
from ui.components.map import render_compare_map

DEFAULTS = {
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

CANDIDATE_LABELS = [
    "Вариант A",
    "Вариант B",
    "Вариант C",
    "Вариант D",
    "Вариант E",
]
CANDIDATE_ADDRESSES = [
    "Краснодар, ул. Восточно-Кругликовская, 30",
    "Краснодар, ул. Красная, 1",
    "",
    "",
    "",
]
CANDIDATE_RENTS = [85000, 95000, 85000, 85000, 85000]
REPAIR_OPTIONS = ["normal", "good", "bad"]


def main() -> None:
    client = ApiClient(setup_page(title="Сравнение"))

    render_page_header(
        "Сравнение локаций",
        "Сравнение 2-5 новых кандидатов. Backend считает score, финансы и ранг.",
    )
    st.info(
        "Текущий UI сравнивает только новые введённые адреса. "
        "Выбор сохранённых анализов не реализован в этой фазе. "
        "Экспорт доступен после успешного сравнения.",
    )

    payload = _render_form()
    if payload is not None:
        errors = _validate_payload(payload)
        if errors:
            for error in errors:
                st.error(error)
        else:
            with st.spinner("Backend анализирует кандидатов и строит рейтинг..."):
                response = client.compare_locations(payload)
            if isinstance(response, ApiError):
                st.session_state.pop("last_compare_result", None)
                _render_api_error(response)
            else:
                st.session_state["last_compare_result"] = response
                st.success("Сравнение готово.")

    result = st.session_state.get("last_compare_result")
    if isinstance(result, dict):
        st.markdown("### Результат сравнения")
        _render_compare_result(result)
    else:
        st.info("Заполните 2-5 кандидатов и запустите сравнение.")


def _render_form() -> dict[str, Any] | None:
    _set_form_defaults()

    with st.form("compare_form"):
        count = st.number_input(
            "Количество кандидатов",
            min_value=2,
            max_value=5,
            step=1,
            key="compare_candidate_count",
        )

        st.markdown(
            '<div class="pf-section-title">Общие допущения</div>',
            unsafe_allow_html=True,
        )
        st.text_input("Тип бизнеса", value="ПВЗ", disabled=True)

        c1, c2 = st.columns(2)
        area_m2 = c1.number_input(
            "Площадь, м²",
            min_value=0.0,
            step=1.0,
            key="compare_area_m2",
        )
        floor = c2.number_input("Этаж", step=1, key="compare_floor")

        a, b, c, d = st.columns(4)
        first_floor = a.checkbox("Первый этаж", key="compare_first_floor")
        separate_entrance = b.checkbox(
            "Отдельный вход",
            key="compare_separate_entrance",
        )
        parking = c.checkbox("Парковка", key="compare_parking")
        signage_possible = d.checkbox(
            "Возможна вывеска",
            key="compare_signage_possible",
        )

        e, f, g, h = st.columns(4)
        storage_area = e.checkbox("Есть складская зона", key="compare_storage_area")
        new_residential_area = f.checkbox(
            "Новый жилой район",
            key="compare_new_residential_area",
        )
        high_density_area = g.checkbox(
            "Высокая плотность",
            key="compare_high_density_area",
        )
        bus_stop_nearby = h.checkbox("Остановка рядом", key="compare_bus_stop_nearby")

        i, j = st.columns(2)
        good_visibility = i.checkbox("Хорошая видимость", key="compare_good_visibility")
        repair_condition = j.selectbox(
            "Состояние ремонта",
            options=REPAIR_OPTIONS,
            index=REPAIR_OPTIONS.index(st.session_state["compare_repair_condition"]),
            key="compare_repair_condition",
        )

        st.markdown(
            '<div class="pf-section-title">Финансовые гипотезы</div>',
            unsafe_allow_html=True,
        )
        f1, f2, f3 = st.columns(3)
        expected_income = f1.number_input(
            "Гипотеза пользователя по валовой выручке, ₽/мес",
            min_value=0,
            step=10000,
            key="compare_expected_gross_income_by_user",
        )
        f1.caption("Это введенная пользователем гипотеза, а не прогноз PlaceFit.")
        investment = f2.number_input(
            "Инвестиции, ₽",
            min_value=0,
            step=50000,
            key="compare_investment",
        )
        desired_profit = f3.number_input(
            "Желаемая прибыль, ₽/мес",
            min_value=0,
            step=10000,
            key="compare_desired_profit",
        )

        st.markdown(
            '<div class="pf-section-title">Кандидаты</div>',
            unsafe_allow_html=True,
        )
        candidate_inputs = []
        for index in range(int(count)):
            with st.expander(CANDIDATE_LABELS[index], expanded=index < 2):
                label = st.text_input(
                    "Метка",
                    key=f"compare_candidate_{index}_label",
                )
                address = st.text_input(
                    "Адрес",
                    key=f"compare_candidate_{index}_address",
                )
                rent = st.number_input(
                    "Аренда, ₽/мес",
                    min_value=0,
                    step=5000,
                    key=f"compare_candidate_{index}_rent",
                )
                candidate_inputs.append((label, address, rent))

        submitted = st.form_submit_button("Запустить сравнение", type="primary")

    if not submitted:
        return None

    shared_request = {
        "business_type": "pvz",
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
    candidates = []
    for index, (label, address, rent) in enumerate(candidate_inputs):
        clean_label = str(label).strip() or CANDIDATE_LABELS[index]
        clean_address = str(address).strip()
        candidates.append(
            {
                "label": clean_label,
                "analysis_request": {
                    **shared_request,
                    "address": clean_address,
                    "rent": int(rent),
                },
            },
        )

    return {"candidates": candidates}


def _set_form_defaults() -> None:
    st.session_state.setdefault("compare_candidate_count", 2)
    for key, value in DEFAULTS.items():
        st.session_state.setdefault(f"compare_{key}", value)
    for index, label in enumerate(CANDIDATE_LABELS):
        st.session_state.setdefault(f"compare_candidate_{index}_label", label)
        st.session_state.setdefault(
            f"compare_candidate_{index}_address",
            CANDIDATE_ADDRESSES[index],
        )
        st.session_state.setdefault(
            f"compare_candidate_{index}_rent",
            CANDIDATE_RENTS[index],
        )


def _validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    candidates = payload.get("candidates") or []
    if not 2 <= len(candidates) <= 5:
        errors.append("Укажите от 2 до 5 кандидатов.")

    non_empty_addresses = 0
    for index, candidate in enumerate(candidates, start=1):
        request = candidate.get("analysis_request") or {}
        address = str(request.get("address", "")).strip()
        if not address:
            errors.append(f"Укажите адрес для кандидата {index}.")
        else:
            non_empty_addresses += 1

        if request.get("rent", 0) <= 0:
            errors.append(f"Аренда кандидата {index} должна быть положительной.")

    if non_empty_addresses < 2:
        errors.append("Для сравнения нужны минимум два непустых адреса.")

    first_request = candidates[0].get("analysis_request") if candidates else {}
    if first_request:
        if first_request["area_m2"] <= 0:
            errors.append("Площадь должна быть положительной.")
        if first_request["investment"] <= 0:
            errors.append("Инвестиции должны быть положительными.")
        if first_request["desired_profit"] <= 0:
            errors.append("Желаемая прибыль должна быть положительной.")
        expected_income = first_request.get("expected_gross_income_by_user")
        if expected_income is not None and expected_income <= 0:
            errors.append("Ожидаемый доход должен быть положительным.")

    return errors


def _render_compare_result(result: dict[str, Any]) -> None:
    _render_summary(result)
    render_compare_download_controls(result)

    ranked = result.get("ranked_candidates") or []
    failed = result.get("failed_candidates") or []

    if ranked:
        st.markdown("#### Рейтинг успешных кандидатов")
        st.dataframe(
            [_ranked_row(candidate) for candidate in ranked],
            hide_index=True,
            use_container_width=True,
        )
        with st.expander("Карта успешных кандидатов", expanded=True):
            render_compare_map(result)
    else:
        st.warning("В сравнении нет успешных кандидатов.")

    _render_ranking_rules(result.get("ranking_rules") or {})

    if ranked:
        st.markdown("#### Детали успешных кандидатов")
        for candidate in ranked:
            title = f"#{candidate.get('rank')} · {_candidate_label(candidate)}"
            with st.expander(title, expanded=False):
                _render_successful_candidate_detail(candidate)

    st.markdown("#### Ошибки по кандидатам")
    if failed:
        for candidate in failed:
            title = f"{_candidate_label(candidate)} · {candidate.get('input_address')}"
            with st.expander(title, expanded=True):
                _render_failed_candidate(candidate)
    else:
        st.success("Ошибок по кандидатам нет.")


def _render_summary(result: dict[str, Any]) -> None:
    summary = result.get("summary") or {}
    cols = st.columns(4)
    cols[0].metric("Запрошено", _value(summary.get("requested_count")))
    cols[1].metric("Успешно", _value(summary.get("successful_count")))
    cols[2].metric("Ошибки", _value(summary.get("failed_count")))
    cols[3].metric("Compare ID", _value(result.get("compare_id")))
    st.caption(f"Создано: {_value(result.get('created_at'))}")


def _ranked_row(candidate: dict[str, Any]) -> dict[str, Any]:
    score = candidate.get("score") or {}
    finance = candidate.get("finance") or {}
    competitors = candidate.get("competitors") or {}
    location = candidate.get("location_summary") or {}
    return {
        "Ранг": candidate.get("rank"),
        "Метка": candidate.get("label") or _candidate_label(candidate),
        "Адрес": location.get("address") or candidate.get("input_address"),
        "Score": score.get("total_score"),
        "Confidence": score.get("confidence_score"),
        "Решение": score.get("decision"),
        "Чистая прибыль": finance.get("net_profit"),
        "Окупаемость, мес": finance.get("payback_months"),
        "300 м": competitors.get("competitors_300m"),
        "500 м": competitors.get("competitors_500m"),
        "700 м": competitors.get("competitors_700m"),
        "Ближайший, м": competitors.get("nearest_competitor_distance_m"),
        "Warnings": "; ".join(candidate.get("warnings") or []) or "—",
    }


def _render_ranking_rules(rules: dict[str, Any]) -> None:
    if not rules:
        st.info("Правила ранжирования отсутствуют в ответе backend.")
        return

    st.caption(
        "Рейтинг сформирован по детерминированным правилам PlaceFit; "
        "LLM не используется для ранжирования.",
    )
    with st.expander("Правила ранжирования", expanded=False):
        st.write(
            {
                "version": rules.get("version"),
                "uses_llm": rules.get("uses_llm"),
                "description": rules.get("description"),
            },
        )
        sort_keys = rules.get("sort_keys") or []
        if sort_keys:
            st.dataframe(
                [
                    {
                        "Поле": key.get("field"),
                        "Порядок": key.get("direction"),
                        "Nulls": key.get("nulls"),
                        "Описание": key.get("description"),
                    }
                    for key in sort_keys
                ],
                hide_index=True,
                use_container_width=True,
            )
        severity = rules.get("decision_severity_order") or []
        if severity:
            st.caption("Порядок decision severity: " + " → ".join(map(str, severity)))


def _render_successful_candidate_detail(candidate: dict[str, Any]) -> None:
    location = candidate.get("location_summary") or {}
    score = candidate.get("score") or {}
    finance = candidate.get("finance") or {}
    competitors = candidate.get("competitors") or {}

    st.write(
        {
            "source_analysis_id": candidate.get("source_analysis_id"),
            "input_address": candidate.get("input_address"),
            "address": location.get("address"),
            "normalized_address": location.get("normalized_address"),
            "lat": location.get("lat"),
            "lon": location.get("lon"),
        },
    )

    st.markdown("##### Score")
    st.dataframe([score], hide_index=True, use_container_width=True)

    st.markdown("##### Финансы")
    st.dataframe([finance], hide_index=True, use_container_width=True)

    st.markdown("##### Конкуренты")
    st.dataframe([competitors], hide_index=True, use_container_width=True)

    _render_text_list("Допущения", candidate.get("assumptions") or [])
    _render_text_list("Предупреждения", candidate.get("warnings") or [])
    _render_text_list("Trade-offs", candidate.get("trade_offs") or [])


def _render_failed_candidate(candidate: dict[str, Any]) -> None:
    error = candidate.get("error") or {}
    st.write(
        {
            "label": candidate.get("label"),
            "input_address": candidate.get("input_address"),
            "code": error.get("code"),
            "message": error.get("message"),
            "details": error.get("details"),
        },
    )

    suggestions = error.get("suggestions") or []
    if suggestions:
        st.warning("Возможные варианты адреса. Скопируйте нужный адрес и повторите.")
        for suggestion in suggestions:
            st.code(str(suggestion.get("address") or suggestion), language=None)
            meta = {
                key: value
                for key, value in suggestion.items()
                if key != "address" and value is not None
            }
            if meta:
                st.caption(str(meta))


def _render_api_error(error: ApiError) -> None:
    st.error(f"{error.message} ({error.code})")
    with st.expander("Технические детали"):
        st.write(error)


def _render_text_list(title: str, items: list[Any]) -> None:
    st.markdown(f"##### {title}")
    if not items:
        st.caption("—")
        return
    for item in items:
        st.markdown(f"- {item}")


def _candidate_label(candidate: dict[str, Any]) -> str:
    label = candidate.get("label")
    if label:
        return str(label)
    input_index = candidate.get("input_index")
    if input_index is not None:
        return f"Кандидат {input_index + 1}"
    return "Кандидат"


def _value(value: Any) -> str:
    if value is None or value == "":
        return "—"
    return str(value)


if __name__ == "__main__":
    main()
