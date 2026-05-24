from app.config.settings import Settings, get_settings


def test_settings_defaults_without_env_file() -> None:
    settings = Settings(_env_file=None)

    assert settings.geocoder_provider == "fake"
    assert settings.poi_provider == "fake"
    assert settings.dgis_api_key == ""
    assert settings.dgis_base_url == "https://catalog.api.2gis.com"
    assert settings.dgis_timeout_seconds == 5.0
    assert settings.osm_overpass_url == "https://overpass-api.de/api/interpreter"
    assert settings.osm_timeout_seconds == 10.0
    assert settings.external_user_agent.startswith("PlaceFit/")
    assert settings.llm_enabled is False
    assert settings.llm_provider == "openai_compatible"
    assert settings.llm_base_url == ""
    assert settings.llm_api_key == ""
    assert settings.llm_model == ""


def test_settings_env_override_for_llm_enabled(monkeypatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("LLM_ENABLED", "true")

    try:
        settings = get_settings()

        assert settings.llm_enabled is True
    finally:
        get_settings.cache_clear()
