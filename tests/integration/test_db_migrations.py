import os
from collections.abc import Generator

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from app.config.settings import get_settings
from app.db.base import Base
from sqlalchemy import Engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError, ProgrammingError

MVP_TABLES = {
    "analysis_snapshots",
    "locations",
    "pois",
    "location_poi_distances",
    "scoring_versions",
    "scores",
    "financial_models",
    "reports",
    "marketplace_requirements",
    "compare_sessions",
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


def test_compare_session_model_is_registered_in_metadata() -> None:
    import app.models  # noqa: F401

    assert "compare_sessions" in Base.metadata.tables


def test_analysis_snapshot_model_is_registered_in_metadata() -> None:
    import app.models  # noqa: F401

    assert "analysis_snapshots" in Base.metadata.tables


def test_analysis_snapshots_schema(migrated_engine: Engine) -> None:
    inspector = inspect(migrated_engine)
    columns = {
        column["name"]: column
        for column in inspector.get_columns("analysis_snapshots")
    }
    foreign_keys = inspector.get_foreign_keys("analysis_snapshots")
    unique_constraints = inspector.get_unique_constraints("analysis_snapshots")
    indexes = inspector.get_indexes("analysis_snapshots")
    checks = inspector.get_check_constraints("analysis_snapshots")

    assert set(columns) == {
        "location_id",
        "root_location_id",
        "previous_location_id",
        "request_snapshot",
        "response_snapshot",
        "snapshot_schema_version",
        "origin",
        "created_at",
    }
    assert columns["location_id"]["nullable"] is False
    assert columns["root_location_id"]["nullable"] is False
    assert columns["previous_location_id"]["nullable"] is True
    assert columns["request_snapshot"]["type"].__class__.__name__ == "JSONB"
    assert columns["response_snapshot"]["type"].__class__.__name__ == "JSONB"
    assert {
        (
            tuple(fk["constrained_columns"]),
            fk["referred_table"],
            fk["options"].get("ondelete"),
        )
        for fk in foreign_keys
    } >= {
        (("location_id",), "locations", "CASCADE"),
        (("root_location_id",), "locations", "CASCADE"),
        (("previous_location_id",), "locations", "RESTRICT"),
    }
    assert any(
        constraint["column_names"] == ["previous_location_id"]
        for constraint in unique_constraints
    )
    assert any(
        index["column_names"]
        == ["root_location_id", "created_at", "location_id"]
        for index in indexes
    )
    check_sql = " ".join(check["sqltext"] for check in checks)
    assert "legacy_materialized" in check_sql
    assert "snapshot_schema_version" in check_sql
    assert "root_location_id" in check_sql
    assert "previous_location_id" in check_sql


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


def test_upgrade_preserves_existing_data_without_backfill_and_downgrade_is_narrow(
    migrated_engine: Engine,
) -> None:
    db_url = migrated_engine.url.render_as_string(hide_password=False)
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    command.downgrade(alembic_cfg, "0002_create_compare_sessions")

    with migrated_engine.begin() as connection:
        location_id = connection.execute(
            text(
                """
                INSERT INTO locations (address, business_type)
                VALUES ('legacy address', 'pvz')
                RETURNING id
                """,
            ),
        ).scalar_one()
        poi_id = connection.execute(
            text(
                """
                INSERT INTO pois (source, external_id)
                VALUES ('fake', 'legacy-poi')
                RETURNING id
                """,
            ),
        ).scalar_one()
        scoring_version_id = connection.execute(
            text(
                """
                SELECT id FROM scoring_versions
                WHERE business_type = 'pvz' AND version = 'v1.0'
                """,
            ),
        ).scalar_one()
        connection.execute(
            text(
                """
                INSERT INTO location_poi_distances
                    (location_id, poi_id, distance_m)
                VALUES (:location_id, :poi_id, 100)
                """,
            ),
            {"location_id": location_id, "poi_id": poi_id},
        )
        connection.execute(
            text(
                """
                INSERT INTO scores (location_id, scoring_version_id, total_score)
                VALUES (:location_id, :scoring_version_id, 50)
                """,
            ),
            {
                "location_id": location_id,
                "scoring_version_id": scoring_version_id,
            },
        )
        connection.execute(
            text(
                "INSERT INTO financial_models (location_id) VALUES (:location_id)",
            ),
            {"location_id": location_id},
        )
        connection.execute(
            text("INSERT INTO reports (location_id) VALUES (:location_id)"),
            {"location_id": location_id},
        )
        connection.execute(
            text(
                """
                INSERT INTO compare_sessions
                    (ranking_rules_version, request_snapshot, response_snapshot)
                VALUES ('v1', CAST(:request AS jsonb), CAST(:response AS jsonb))
                """,
            ),
            {"request": '{"request":"kept"}', "response": '{"response":"kept"}'},
        )

    command.upgrade(alembic_cfg, "0003_create_analysis_snapshots")
    with migrated_engine.connect() as connection:
        assert connection.scalar(text("SELECT count(*) FROM locations")) == 1
        assert connection.scalar(text("SELECT count(*) FROM scores")) == 1
        assert connection.scalar(text("SELECT count(*) FROM financial_models")) == 1
        assert connection.scalar(text("SELECT count(*) FROM reports")) == 1
        distance_count = connection.scalar(
            text("SELECT count(*) FROM location_poi_distances"),
        )
        assert distance_count == 1
        assert connection.scalar(text("SELECT count(*) FROM analysis_snapshots")) == 0
        compare_row = connection.execute(
            text("SELECT request_snapshot, response_snapshot FROM compare_sessions"),
        ).mappings().one()
        assert compare_row["request_snapshot"] == {"request": "kept"}
        assert compare_row["response_snapshot"] == {"response": "kept"}

    command.downgrade(alembic_cfg, "0002_create_compare_sessions")
    inspector = inspect(migrated_engine)
    assert "analysis_snapshots" not in inspector.get_table_names()
    with migrated_engine.connect() as connection:
        assert connection.scalar(text("SELECT count(*) FROM locations")) == 1
        assert connection.scalar(text("SELECT count(*) FROM scores")) == 1
        assert connection.scalar(text("SELECT count(*) FROM compare_sessions")) == 1

    command.upgrade(alembic_cfg, "0003_create_analysis_snapshots")


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
                        analysis_snapshots,
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
