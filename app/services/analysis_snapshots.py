"""Validated persistence helpers for immutable analysis snapshots."""

import logging

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.models import AnalysisSnapshot
from app.schemas.analysis import AnalysisRequest, AnalysisResponse

SNAPSHOT_SCHEMA_VERSION = "v1"
NATIVE_ORIGIN = "native"
LEGACY_MATERIALIZED_ORIGIN = "legacy_materialized"

logger = logging.getLogger(__name__)


class AnalysisSnapshotError(Exception):
    """Raised when a snapshot cannot be safely validated."""


class AnalysisSnapshotService:
    """Store and load validated public analysis snapshots."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def create_native_root_snapshot(
        self,
        *,
        location_id: int,
        request: AnalysisRequest,
        response: AnalysisResponse,
    ) -> AnalysisSnapshot:
        """Add a validated native root snapshot to the current transaction."""

        try:
            request_snapshot = AnalysisRequest.model_validate(
                request.model_dump(mode="json"),
            ).model_dump(mode="json")
            response_snapshot = AnalysisResponse.model_validate(
                response.model_dump(mode="json"),
            ).model_dump(mode="json")
        except ValidationError as exc:
            logger.error(
                "Analysis snapshot validation failed for location_id=%s error=%s",
                location_id,
                type(exc).__name__,
            )
            raise AnalysisSnapshotError("Analysis snapshot validation failed") from exc

        snapshot = AnalysisSnapshot(
            location_id=location_id,
            root_location_id=location_id,
            previous_location_id=None,
            request_snapshot=request_snapshot,
            response_snapshot=response_snapshot,
            snapshot_schema_version=SNAPSHOT_SCHEMA_VERSION,
            origin=NATIVE_ORIGIN,
        )
        self._db.add(snapshot)
        self._db.flush()
        return snapshot

    def get_snapshot(self, location_id: int) -> AnalysisSnapshot | None:
        """Return the stored snapshot row, if one exists."""

        return self._db.get(AnalysisSnapshot, location_id)

    def load_response(self, location_id: int) -> AnalysisResponse | None:
        """Return a validated stored response without reconstructing it."""

        snapshot = self.get_snapshot(location_id)
        if snapshot is None:
            return None
        try:
            return AnalysisResponse.model_validate(snapshot.response_snapshot)
        except ValidationError as exc:
            logger.error(
                "Stored response snapshot is invalid for location_id=%s error=%s",
                location_id,
                type(exc).__name__,
            )
            raise AnalysisSnapshotError("Stored response snapshot is invalid") from exc

    def load_request(self, location_id: int) -> AnalysisRequest | None:
        """Return a validated stored request, if one exists."""

        snapshot = self.get_snapshot(location_id)
        if snapshot is None:
            return None
        try:
            return AnalysisRequest.model_validate(snapshot.request_snapshot)
        except ValidationError as exc:
            logger.error(
                "Stored request snapshot is invalid for location_id=%s error=%s",
                location_id,
                type(exc).__name__,
            )
            raise AnalysisSnapshotError("Stored request snapshot is invalid") from exc
