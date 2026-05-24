"""Typed application settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables and optional .env."""

    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    geocoder_provider: str = "fake"
    poi_provider: str = "fake"
    dgis_api_key: str = ""
    dgis_base_url: str = "https://catalog.api.2gis.com"
    dgis_timeout_seconds: float = 5.0
    osm_overpass_url: str = "https://overpass-api.de/api/interpreter"
    osm_timeout_seconds: float = 10.0
    external_user_agent: str = "PlaceFit/0.1 (+https://github.com/Brtwm/PlaceFit)"

    llm_enabled: bool = False
    llm_provider: str = "openai_compatible"
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""

    database_url: str = (
        "postgresql+psycopg://placefit:placefit@localhost:5432/placefit"
    )
    test_database_url: str = ""
    allow_db_reset_for_tests: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
