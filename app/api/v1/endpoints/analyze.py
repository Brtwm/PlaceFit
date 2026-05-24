"""Analyze endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.api.v1.deps import get_analysis_service
from app.api.v1.endpoints._errors import error_response
from app.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.services.analysis import (
    AnalysisService,
    AnalysisServiceError,
    to_geocode_candidates,
)

router = APIRouter()

_ERROR_STATUS = {
    "ADDRESS_AMBIGUOUS": 400,
    "CITY_NOT_SUPPORTED": 400,
    "GEOCODING_FAILED": 502,
    "COMPETITOR_SEARCH_FAILED": 502,
    "NOT_FOUND": 404,
    "INTERNAL_ERROR": 500,
}


@router.post("/analyze", response_model=AnalysisResponse)
def analyze_location(
    request: AnalysisRequest,
    service: Annotated[AnalysisService, Depends(get_analysis_service)],
) -> AnalysisResponse | JSONResponse:
    """Run the full deterministic MVP analysis."""

    try:
        return service.analyze(request)
    except AnalysisServiceError as exc:
        return error_response(
            status_code=_ERROR_STATUS[exc.code],
            code=exc.code,
            message=exc.message,
            details=exc.details,
            suggestions=to_geocode_candidates(exc.suggestions)
            if exc.suggestions
            else None,
        )
