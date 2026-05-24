"""FastAPI dependencies for API v1."""

from collections.abc import Generator, Sequence
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config.settings import Settings
from app.config.settings import get_settings as load_settings
from app.db.session import get_session
from app.providers.factory import build_geocoder_provider, build_poi_providers
from app.providers.llm.base import LlmReportProvider
from app.providers.llm.fallback import FallbackReportProvider
from app.providers.llm.openai_compatible import OpenAICompatibleReportProvider
from app.providers.poi_search.base import PoiSearchProvider
from app.services.analysis import AnalysisService
from app.services.geocoding import GeocodingService
from app.services.report import ReportService


def get_db_session() -> Generator[Session, None, None]:
    """Yield the request-scoped DB session."""

    yield from get_session()


def get_settings() -> Settings:
    """Return cached runtime settings."""

    return load_settings()


def get_geocoding_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> GeocodingService:
    """Return the configured geocoding service."""

    return GeocodingService(build_geocoder_provider(settings))


def get_poi_providers(
    settings: Annotated[Settings, Depends(get_settings)],
) -> Sequence[PoiSearchProvider]:
    """Return configured POI providers."""

    return build_poi_providers(settings)


def get_fallback_report_provider() -> LlmReportProvider:
    """Return the deterministic fallback report provider."""

    return FallbackReportProvider()


def get_llm_provider(
    settings: Annotated[Settings, Depends(get_settings)],
) -> LlmReportProvider | None:
    """Return optional LLM provider when configured."""

    if settings.llm_provider != "openai_compatible":
        return None
    return OpenAICompatibleReportProvider(settings=settings)


def get_report_service(
    settings: Annotated[Settings, Depends(get_settings)],
    llm_provider: Annotated[
        LlmReportProvider | None,
        Depends(get_llm_provider),
    ],
    fallback_provider: Annotated[
        LlmReportProvider,
        Depends(get_fallback_report_provider),
    ],
) -> ReportService:
    """Return fallback-first report service."""

    return ReportService(
        settings=settings,
        llm_provider=llm_provider,
        fallback_provider=fallback_provider,
    )


def get_analysis_service(
    db: Annotated[Session, Depends(get_db_session)],
    geocoding_service: Annotated[
        GeocodingService,
        Depends(get_geocoding_service),
    ],
    poi_providers: Annotated[
        Sequence[PoiSearchProvider],
        Depends(get_poi_providers),
    ],
    report_service: Annotated[ReportService, Depends(get_report_service)],
) -> AnalysisService:
    """Return the Phase 6 analysis orchestration service."""

    return AnalysisService(
        db=db,
        geocoding_service=geocoding_service,
        poi_providers=poi_providers,
        report_service=report_service,
    )
