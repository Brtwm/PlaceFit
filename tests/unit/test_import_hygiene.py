from pathlib import Path

SERVICE_FILES = [
    Path("app/services/scoring.py"),
    Path("app/services/finance.py"),
    Path("app/services/confidence.py"),
    Path("app/services/decision.py"),
]
FORBIDDEN_IMPORTS = (
    "sqlalchemy",
    "alembic",
    "psycopg",
    "asyncpg",
    "fastapi",
    "httpx",
    "requests",
    "openai",
    "app.db",
    "app.providers",
)


def test_deterministic_services_do_not_import_forbidden_modules() -> None:
    for service_file in SERVICE_FILES:
        source = service_file.read_text(encoding="utf-8")
        for forbidden_import in FORBIDDEN_IMPORTS:
            assert forbidden_import not in source
