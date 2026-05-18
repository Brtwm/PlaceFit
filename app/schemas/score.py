"""Scoring result schemas."""

from app.schemas.common import AppBaseModel, ScoreValue


class ScoreDetails(AppBaseModel):
    """Deterministic score component breakdown."""

    demand_score: int
    competition_score: int
    rent_score: int
    premises_score: int
    accessibility_score: int


class ScoreResult(AppBaseModel):
    """Full scoring result."""

    total_score: ScoreValue
    confidence_score: ScoreValue
    scoring_version: str
    decision: str
    details: ScoreDetails
