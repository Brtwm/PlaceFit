"""Location history and detail endpoints."""

from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from app.api.v1.deps import get_analysis_service
from app.api.v1.endpoints._errors import error_response
from app.schemas.analysis import AnalysisResponse
from app.schemas.location import LocationsListRequest, LocationsListResponse
from app.services.analysis import AnalysisService, AnalysisServiceError

router = APIRouter()


@router.get("/locations", response_model=LocationsListResponse)
def list_locations(
    service: Annotated[AnalysisService, Depends(get_analysis_service)],
    business_type: Literal["pvz"] = "pvz",
    min_score: int | None = Query(default=None, ge=0, le=100),
    max_score: int | None = Query(default=None, ge=0, le=100),
    decision: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = Query(default=50, ge=0, le=100),
    offset: int = Query(default=0, ge=0),
) -> LocationsListResponse:
    """Return persisted analysis history."""

    filters = LocationsListRequest.model_validate(
        {
            "business_type": business_type,
            "min_score": min_score,
            "max_score": max_score,
            "decision": decision,
            "date_from": date_from,
            "date_to": date_to,
            "limit": limit,
            "offset": offset,
        },
    )
    return service.list_locations(filters)


@router.get("/locations/{location_id}", response_model=AnalysisResponse)
def get_location_detail(
    location_id: int,
    service: Annotated[AnalysisService, Depends(get_analysis_service)],
) -> AnalysisResponse | JSONResponse:
    """Return a full persisted analysis response."""

    try:
        return service.get_location_detail(location_id)
    except AnalysisServiceError as exc:
        status_code = 404 if exc.code == "NOT_FOUND" else 500
        return error_response(
            status_code=status_code,
            code=exc.code,
            message=exc.message,
            details=exc.details,
        )
