import inspect
from pathlib import Path

from app.main import create_app
from ui.api_client import ApiClient


def test_export_endpoints_are_not_registered() -> None:
    app = create_app()
    registered_paths = {
        route.path
        for route in app.routes
        if getattr(route, "path", "").startswith("/api/v1")
    }

    assert "/api/v1/exports" not in registered_paths
    assert "/api/v1/exports/analysis" not in registered_paths
    assert "/api/v1/exports/compare" not in registered_paths
    assert not any(path.startswith("/api/v1/exports/") for path in registered_paths)


def test_api_v1_router_does_not_include_exports_router() -> None:
    source = Path("app/api/v1/router.py").read_text(encoding="utf-8")

    assert "exports" not in source
    assert "include_router(exports.router)" not in source


def test_api_sources_do_not_define_export_routes() -> None:
    sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in Path("app/api/v1").rglob("*.py")
    )

    prohibited_snippets = (
        '@router.post("/exports"',
        '@router.post("/exports/analysis"',
        '@router.post("/exports/compare"',
        '"/api/v1/exports/analysis"',
        '"/api/v1/exports/compare"',
    )
    for snippet in prohibited_snippets:
        assert snippet not in sources


def test_ui_api_client_has_no_export_methods_or_paths() -> None:
    method_names = {
        name
        for name, value in inspect.getmembers(ApiClient, predicate=inspect.isfunction)
        if not name.startswith("_")
    }
    source = Path("ui/api_client.py").read_text(encoding="utf-8")

    assert not any("export" in name for name in method_names)
    assert "/exports" not in source


def test_public_api_contract_does_not_claim_specific_export_endpoints() -> None:
    source = Path("docs/05_api_contract.md").read_text(encoding="utf-8")

    assert "POST /api/v1/exports/analysis" not in source
    assert "POST /api/v1/exports/compare" not in source
