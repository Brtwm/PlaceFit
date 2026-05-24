"""Competitor search endpoint."""

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.api.v1.deps import get_poi_providers
from app.api.v1.endpoints._errors import error_response
from app.providers.poi_search.base import PoiSearchProvider
from app.schemas.competitor import (
    CompetitorCounts,
    CompetitorInfo,
    CompetitorsSearchRequest,
    CompetitorsSearchResponse,
)
from app.services.competitors import search_competitors

router = APIRouter()


@router.post("/competitors/search", response_model=CompetitorsSearchResponse)
def search_competitor_locations(
    request: CompetitorsSearchRequest,
    providers: Annotated[Sequence[PoiSearchProvider], Depends(get_poi_providers)],
) -> CompetitorsSearchResponse | JSONResponse:
    """Search competitors using mocked POI providers."""

    try:
        result = search_competitors(
            providers,
            lat=request.lat,
            lon=request.lon,
            radius_m=request.radius_m,
            business_type=request.business_type,
        )
    except Exception as exc:
        return error_response(
            status_code=502,
            code="COMPETITOR_SEARCH_FAILED",
            message="Не удалось найти конкурентов",
            details=str(exc),
        )

    return CompetitorsSearchResponse(
        competitors=[
            CompetitorInfo(
                name=competitor.name,
                brand=competitor.brand,
                category=competitor.category,
                address=competitor.address,
                distance_m=competitor.distance_m,
                rating=competitor.rating,
                reviews_count=competitor.reviews_count,
                source=competitor.source,
            )
            for competitor in result.competitors
        ],
        counts=CompetitorCounts.model_validate(
            {
                "300m": result.competitors_300m,
                "500m": result.competitors_500m,
                "700m": result.competitors_700m,
            },
        ),
        source="+".join(result.sources),
        fetched_at=datetime.now(UTC),
    )
