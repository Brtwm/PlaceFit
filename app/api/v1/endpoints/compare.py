"""Compare endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.api.v1.deps import get_compare_service
from app.api.v1.endpoints._errors import error_response
from app.schemas.compare import CompareRequest, CompareResponse
from app.services.compare import CompareService, CompareServiceError

router = APIRouter()


@router.post("/locations/compare", response_model=CompareResponse)
def compare_locations(
    request: CompareRequest,
    service: Annotated[CompareService, Depends(get_compare_service)],
) -> CompareResponse:
    """Compare 2-5 candidate locations through deterministic analysis."""

    return service.compare(request)


@router.get("/locations/compare/{compare_id}", response_model=CompareResponse)
def get_compare_session(
    compare_id: int,
    service: Annotated[CompareService, Depends(get_compare_service)],
) -> CompareResponse | JSONResponse:
    """Return a saved compare session snapshot without rerunning analysis."""

    try:
        return service.get_saved_compare_session(compare_id)
    except CompareServiceError as exc:
        return error_response(
            status_code=404,
            code=exc.code,
            message=exc.message,
            details=exc.details,
        )
