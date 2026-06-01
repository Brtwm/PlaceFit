"""Compare endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.v1.deps import get_compare_service
from app.schemas.compare import CompareRequest, CompareResponse
from app.services.compare import CompareService

router = APIRouter()


@router.post("/locations/compare", response_model=CompareResponse)
def compare_locations(
    request: CompareRequest,
    service: Annotated[CompareService, Depends(get_compare_service)],
) -> CompareResponse:
    """Compare 2-5 candidate locations through deterministic analysis."""

    return service.compare(request)
