"""FastAPI dependencies for API v1."""

from collections.abc import Generator, Mapping, Sequence
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config.settings import Settings
from app.config.settings import get_settings as load_settings
from app.db.session import get_session
from app.providers.geocoder.fake import FakeGeocoder
from app.providers.llm.base import LlmReportProvider
from app.providers.llm.fallback import FallbackReportProvider
from app.providers.llm.openai_compatible import OpenAICompatibleReportProvider
from app.providers.poi_search.base import PoiSearchProvider
from app.providers.poi_search.fake import FakePoiSearchProvider
from app.services.analysis import AnalysisService
from app.services.geocoding import GeocodingService
from app.services.report import ReportService


def get_db_session() -> Generator[Session, None, None]:
    """Yield the request-scoped DB session."""

    yield from get_session()


def get_settings() -> Settings:
    """Return cached runtime settings."""

    return load_settings()


def get_geocoding_service() -> GeocodingService:
    """Return the deterministic mocked geocoding service."""

    return GeocodingService(FakeGeocoder(_default_geocoder_payloads()))


def get_poi_providers() -> Sequence[PoiSearchProvider]:
    """Return deterministic mocked POI providers."""

    return (FakePoiSearchProvider(_default_poi_payload()),)


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


def _default_geocoder_payloads() -> tuple[Mapping[str, object], ...]:
    return (
        {
            "provider": "2gis",
            "query": "Краснодар, ул. Восточно-Кругликовская, 30",
            "status": "resolved",
            "results": [
                {
                    "external_id": "fake-krasnodar-vk-30",
                    "address": "Краснодар, ул. Восточно-Кругликовская, 30",
                    "normalized_address": (
                        "г Краснодар, ул Восточно-Кругликовская, д 30"
                    ),
                    "city": "Краснодар",
                    "lat": 45.035,
                    "lon": 39.028,
                    "confidence": 0.95,
                },
            ],
        },
        {
            "provider": "2gis",
            "query": "Краснодар, ул. Красная, 1",
            "status": "resolved",
            "results": [
                {
                    "external_id": "fake-krasnodar-krasnaya-1",
                    "address": "Краснодар, ул. Красная, 1",
                    "normalized_address": "г Краснодар, ул Красная, д 1",
                    "city": "Краснодар",
                    "lat": 45.025,
                    "lon": 38.971,
                    "confidence": 0.95,
                },
            ],
        },
    )


def _default_poi_payload() -> Mapping[str, object]:
    return {
        "provider": "osm",
        "pois": [
            {
                "external_id": "osm-ozon-vk-31",
                "name": "Ozon пункт выдачи",
                "brand": "Ozon",
                "category": "pvz",
                "business_type": "pvz",
                "lat": 45.0359,
                "lon": 39.0281,
                "address": "г Краснодар, ул Восточно-Кругликовская, д 31",
                "rating": 4.6,
                "reviews_count": 41,
            },
            {
                "external_id": "osm-wb-vk-28",
                "name": "Wildberries",
                "brand": "Wildberries",
                "category": "pvz",
                "business_type": "pvz",
                "lat": 45.0382,
                "lon": 39.029,
                "address": "г Краснодар, ул Восточно-Кругликовская, д 28",
                "rating": 4.4,
                "reviews_count": 27,
            },
            {
                "external_id": "osm-ym-vk-40",
                "name": "Яндекс Маркет",
                "brand": "Яндекс Маркет",
                "category": "pvz",
                "business_type": "pvz",
                "lat": 45.04,
                "lon": 39.03,
                "address": "г Краснодар, ул Восточно-Кругликовская, д 40",
                "rating": 4.3,
                "reviews_count": 18,
            },
        ],
    }
