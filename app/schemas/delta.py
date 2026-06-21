"""Strict contracts for future analysis refresh deltas."""

from typing import Literal, TypeAlias

from pydantic import StrictBool, StrictFloat, StrictInt, StrictStr

from app.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.schemas.common import AppBaseModel, CreatedAt, PositiveInt
from app.schemas.competitor import CompetitorInfo
from app.schemas.report import DataSourceInfo

DeltaStatus = Literal["unchanged", "changed", "added", "removed"]
DeltaDirection = Literal["improved", "worsened", "neutral", "not_applicable"]
SnapshotOrigin = Literal["native", "legacy_materialized"]
JsonScalar: TypeAlias = StrictStr | StrictInt | StrictFloat | StrictBool | None
CompetitorChangedField = Literal[
    "name",
    "brand",
    "category",
    "address",
    "lat",
    "lon",
    "distance_m",
    "rating",
    "reviews_count",
]


class ScalarDelta(AppBaseModel):
    """Exact before/after comparison for one scalar snapshot field."""

    field: str
    before: JsonScalar
    after: JsonScalar
    status: DeltaStatus
    direction: DeltaDirection


class DataSourcesDelta(AppBaseModel):
    """Typed exact comparison for public source metadata."""

    field: Literal["data_sources"]
    before: list[DataSourceInfo]
    after: list[DataSourceInfo]
    status: DeltaStatus
    direction: Literal["neutral", "not_applicable"]


class CompetitorDeltaItem(AppBaseModel):
    """Entity-level competitor change matched by deterministic identity."""

    identity: str
    status: DeltaStatus
    before: CompetitorInfo | None
    after: CompetitorInfo | None
    changed_fields: list[CompetitorChangedField]


class InputsDeltaSection(AppBaseModel):
    """User-controlled analysis assumptions."""

    rent: ScalarDelta
    area_m2: ScalarDelta
    floor: ScalarDelta
    first_floor: ScalarDelta
    separate_entrance: ScalarDelta
    parking: ScalarDelta
    signage_possible: ScalarDelta
    storage_area: ScalarDelta
    repair_condition: ScalarDelta
    new_residential_area: ScalarDelta
    high_density_area: ScalarDelta
    bus_stop_nearby: ScalarDelta
    good_visibility: ScalarDelta
    expected_gross_income_by_user: ScalarDelta
    investment: ScalarDelta
    desired_profit: ScalarDelta


class LocationProvenanceDeltaSection(AppBaseModel):
    """Normalized location and public source metadata changes."""

    normalized_address: ScalarDelta
    lat: ScalarDelta
    lon: ScalarDelta
    data_sources: DataSourcesDelta


class CompetitorsDeltaSection(AppBaseModel):
    """Competitor summary and deterministic entity changes."""

    competitors_300m: ScalarDelta
    competitors_500m: ScalarDelta
    competitors_700m: ScalarDelta
    nearest_competitor_distance_m: ScalarDelta
    average_competitor_distance_m: ScalarDelta
    items: list[CompetitorDeltaItem]


class ScoreDeltaSection(AppBaseModel):
    """Stored deterministic score, confidence, version, and decision changes."""

    scoring_version: ScalarDelta
    total_score: ScalarDelta
    confidence_score: ScalarDelta
    decision: ScalarDelta
    demand_score: ScalarDelta
    competition_score: ScalarDelta
    rent_score: ScalarDelta
    premises_score: ScalarDelta
    accessibility_score: ScalarDelta


class FinanceDeltaSection(AppBaseModel):
    """Stored deterministic finance output changes."""

    monthly_costs: ScalarDelta
    required_gross_income: ScalarDelta
    expected_gross_income_by_user: ScalarDelta
    net_profit: ScalarDelta
    payback_months: ScalarDelta


class AnalysisDeltaSummary(AppBaseModel):
    """Compact counts for delta presentation."""

    changed_inputs: PositiveInt
    competitors_added: PositiveInt
    competitors_removed: PositiveInt
    competitors_changed: PositiveInt
    competitors_unchanged: PositiveInt


class AnalysisDelta(AppBaseModel):
    """Complete deterministic delta between adjacent analysis snapshots."""

    previous_analysis_id: int
    current_analysis_id: int
    previous_created_at: CreatedAt
    current_created_at: CreatedAt
    previous_snapshot_origin: SnapshotOrigin
    current_snapshot_origin: SnapshotOrigin
    snapshot_schema_version: str
    scoring_version_warning: str | None = None
    inputs: InputsDeltaSection
    location_provenance: LocationProvenanceDeltaSection
    competitors: CompetitorsDeltaSection
    score: ScoreDeltaSection
    finance: FinanceDeltaSection
    summary: AnalysisDeltaSummary


class AnalysisLineage(AppBaseModel):
    """Identifiers for a linear saved-analysis lineage."""

    root_analysis_id: int
    previous_analysis_id: int | None
    current_analysis_id: int


class AnalysisRefreshRequest(AppBaseModel):
    """Validated full request used by a future manual refresh endpoint."""

    analysis_request: AnalysisRequest


class AnalysisRefreshResponse(AppBaseModel):
    """Future refresh result contract without persistence implementation."""

    analysis: AnalysisResponse
    delta: AnalysisDelta
    lineage: AnalysisLineage
