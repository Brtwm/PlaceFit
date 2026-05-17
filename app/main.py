"""FastAPI application entrypoint."""

from fastapi import FastAPI

from app.api.v1.router import router as api_v1_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    fastapi_app = FastAPI(title="PlaceFit")

    fastapi_app.include_router(api_v1_router, prefix="/api/v1")

    @fastapi_app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return fastapi_app


app = create_app()
