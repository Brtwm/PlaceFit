"""Analysis detail Streamlit page."""

from __future__ import annotations

import streamlit as st

from ui.api_client import ApiClient, ApiError
from ui.components.layout import render_page_header, setup_page
from ui.components.result import render_analysis_result


def main() -> None:
    client = ApiClient(setup_page(title="Детали"))

    render_page_header(
        "Детальная карточка анализа",
        "Откройте сохранённый backend-анализ из истории или по ID.",
    )
    location_id = _resolve_location_id()

    id_col, _ = st.columns([1, 3])
    manual_id = id_col.number_input(
        "ID анализа",
        min_value=0,
        value=location_id or 0,
        step=1,
    )
    if manual_id:
        st.session_state["selected_location_id"] = int(manual_id)
        st.query_params["id"] = str(int(manual_id))
        location_id = int(manual_id)

    if not location_id:
        st.info("Выберите анализ из истории или введите ID вручную.")
        return

    response = client.get_location(location_id)
    if isinstance(response, ApiError):
        if response.code == "NOT_FOUND":
            st.error("Анализ с таким ID не найден.")
        else:
            st.error(f"{response.message} ({response.code})")
        with st.expander("Технические детали"):
            st.write(response)
        return

    render_analysis_result(response)


def _resolve_location_id() -> int | None:
    query_id = st.query_params.get("id")
    if isinstance(query_id, list):
        query_id = query_id[0] if query_id else None
    if query_id:
        try:
            return int(query_id)
        except ValueError:
            st.warning("ID в адресной строке должен быть числом.")

    selected = st.session_state.get("selected_location_id")
    if selected:
        try:
            return int(selected)
        except (TypeError, ValueError):
            return None
    return None


if __name__ == "__main__":
    main()
