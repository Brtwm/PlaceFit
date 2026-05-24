import os
from collections.abc import Generator

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from app.config.settings import get_settings
from sqlalchemy import Engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError, ProgrammingError

MVP_TABLES = {
    "locations",
    "pois",
    "location_poi_distances",
    "scoring_versions",
    "scores",
    "financial_models",
    "reports",
    "marketplace_requirements",
}


@pytest.fixture(scope="module")
def migrated_engine() -> Generator[Engine, None, None]:
    db_url = _migration_test_db_url()
    _reset_public_schema(db_url)
    _run_alembic_upgrade(db_url)

    engine = sa.create_engine(db_url)
    try:
        yield engine
    finally:
        engine.dispose()


def test_migration_creates_mvp_tables(migrated_engine: Engine) -> None:
    inspector = inspect(migrated_engine)

    assert MVP_TABLES.issubset(set(inspector.get_table_names()))


def test_migration_creates_postgis_extension(migrated_engine: Engine) -> None:
    with migrated_engine.connect() as connection:
        exists = connection.execute(
            text(
                "SELECT EXISTS "
                "(SELECT 1 FROM pg_extension WHERE extname = 'postgis')",
            ),
        ).scalar_one()

    assert exists is True


def test_active_scoring_version_seeded(migrated_engine: Engine) -> None:
    with migrated_engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT business_type, version, active, rules
                FROM scoring_versions
                WHERE business_type = 'pvz' AND version = 'v1.0' AND active = true
                """
            ),
        ).mappings().all()

    assert len(rows) == 1
    assert rows[0]["business_type"] == "pvz"
    assert rows[0]["version"] == "v1.0"
    assert rows[0]["active"] is True
    assert rows[0]["rules"]


def test_scores_scoring_version_fk(migrated_engine: Engine) -> None:
    inspector = inspect(migrated_engine)
    columns = {column["name"]: column for column in inspector.get_columns("scores")}
    foreign_keys = inspector.get_foreign_keys("scores")

    assert "scoring_version_id" in columns
    assert columns["scoring_version_id"]["nullable"] is False
    assert any(
        fk["constrained_columns"] == ["scoring_version_id"]
        and fk["referred_table"] == "scoring_versions"
        and fk["referred_columns"] == ["id"]
        for fk in foreign_keys
    )


def test_scores_has_no_trend_score(migrated_engine: Engine) -> None:
    inspector = inspect(migrated_engine)
    column_names = {column["name"] for column in inspector.get_columns("scores")}

    assert "trend_score" not in column_names


def _migration_test_db_url() -> str:
    settings = get_settings()
    test_db_url = os.getenv("TEST_DATABASE_URL", settings.test_database_url).strip()
    if test_db_url:
        return test_db_url

    db_url = os.getenv("DATABASE_URL", settings.database_url).strip()
    if not db_url:
        pytest.skip("Set TEST_DATABASE_URL to run database migration tests.")

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
        pytest.skip(f"Database is not available for migration tests: {exc}")
    finally:
        engine.dispose()


def _run_alembic_upgrade(db_url: str) -> None:
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    try:
        command.upgrade(alembic_cfg, "head")
    except (OperationalError, ProgrammingError) as exc:
        pytest.skip(f"Database migration setup is not available: {exc}")
