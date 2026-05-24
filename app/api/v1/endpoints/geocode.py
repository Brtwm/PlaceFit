"""Geocoding endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.api.v1.deps import get_geocoding_service
from app.api.v1.endpoints._errors import error_response
from app.schemas.location import GeocodeRequest, GeocodeResponse
from app.services.analysis import to_geocode_candidates
from app.services.geocoding import GeocodingService

router = APIRouter()


@router.post("/geocode", response_model=GeocodeResponse)
def geocode_address(
    request: GeocodeRequest,
    service: Annotated[GeocodingService, Depends(get_geocoding_service)],
) -> GeocodeResponse | JSONResponse:
    """Geocode an address using the mocked provider stack."""

    result = service.geocode(request.address)
    if result.candidates:
        return GeocodeResponse(
            results=to_geocode_candidates(result.candidates),
            source=result.provider,
        )
    if result.status == "city_not_supported":
        return error_response(
            status_code=400,
            code="CITY_NOT_SUPPORTED",
            message="MVP поддерживает только адреса в Краснодаре",
        )
    return error_response(
        status_code=502,
        code="GEOCODING_FAILED",
        message="Не удалось геокодировать адрес",
        details=result.message,
    )
