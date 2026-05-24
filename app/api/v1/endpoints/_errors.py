"""API error response helpers."""

from collections.abc import Sequence

from fastapi.responses import JSONResponse

from app.schemas.error import ErrorCode, ErrorInfo, ErrorResponse
from app.schemas.location import GeocodeCandidate


def error_response(
    *,
    status_code: int,
    code: ErrorCode,
    message: str,
    details: str | None = None,
    suggestions: Sequence[GeocodeCandidate] | None = None,
) -> JSONResponse:
    """Build a contract-shaped error response."""

    payload = ErrorResponse(
        error=ErrorInfo(
            code=code,
            message=message,
            details=details,
            suggestions=list(suggestions) if suggestions is not None else None,
        ),
    )
    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(mode="json", exclude_none=True),
    )
