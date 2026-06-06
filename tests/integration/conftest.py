import os
from collections.abc import Generator

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from app.api.v1.deps import get_db_session
from app.api.v1.deps import get_settings as get_api_settings
from app.config.settings import Settings, get_settings
from app.main import create_app
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import Session, sessionmaker


@pytest.fixture(scope="session")
def api_test_engine() -> Generator[Engine, None, None]:
    db_url = _api_test_db_url()
    _reset_public_schema(db_url)
    _run_alembic_upgrade(db_url)

    engine = sa.create_engine(db_url)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture()
def db_session(api_test_engine: Engine) -> Generator[Session, None, None]:
    _clear_analysis_tables(api_test_engine)
    session_factory = sessionmaker(bind=api_test_engine, autoflush=False)
    with session_factory() as session:
        yield session


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    app = create_app()

    def override_db_session() -> Generator[Session, None, None]:
        yield db_session

    def override_settings() -> Settings:
        return Settings(
            _env_file=None,
            geocoder_provider="fake",
            poi_provider="fake",
            llm_enabled=False,
        )

    app.dependency_overrides[get_db_session] = override_db_session
    app.dependency_overrides[get_api_settings] = override_settings
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def _api_test_db_url() -> str:
    settings = get_settings()
    test_db_url = os.getenv("TEST_DATABASE_URL", settings.test_database_url).strip()
    if test_db_url:
        return test_db_url

    db_url = os.getenv("DATABASE_URL", settings.database_url).strip()
    if not db_url:
        pytest.skip("Set TEST_DATABASE_URL to run API integration tests.")

    database_name = make_url(db_url).database or ""
    allow_reset = os.getenv("ALLOW_DB_RESET_FOR_TESTS", "false").lower() == "true"
    if "test" not in database_name.lower() and not allow_reset:
        pytest.skip(
            "Refusing to reset DATABASE_URL because database name does not contain "
            "'test'. Set TEST_DATABASE_URL or ALLOW_DB_RESET_FOR_TESTS=true.",
        )

    return db_url


def _reset_public_schema(db_url: str) -> None:
    engine = sa.create_engine(db_url, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as connection:
            connection.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
            connection.execute(text("GRANT ALL ON SCHEMA public TO public"))
            connection.execute(
                text(
                    """
                    DROP TABLE IF EXISTS
                        alembic_version,
                        compare_sessions,
                        marketplace_requirements,
                        reports,
                        financial_models,
                        scores,
                        location_poi_distances,
                        scoring_versions,
                        pois,
                        locations
                    CASCADE
                    """,
                ),
            )
    except (OperationalError, ProgrammingError) as exc:
        pytest.skip(f"Database is not available for API integration tests: {exc}")
    finally:
        engine.dispose()


def _run_alembic_upgrade(db_url: str) -> None:
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    try:
        command.upgrade(alembic_cfg, "head")
    except (OperationalError, ProgrammingError) as exc:
        pytest.skip(f"Database migration setup is not available: {exc}")


def _clear_analysis_tables(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM compare_sessions"))
        connection.execute(text("DELETE FROM reports"))
        connection.execute(text("DELETE FROM financial_models"))
        connection.execute(text("DELETE FROM scores"))
        connection.execute(text("DELETE FROM location_poi_distances"))
        connection.execute(text("DELETE FROM pois"))
        connection.execute(text("DELETE FROM locations"))
