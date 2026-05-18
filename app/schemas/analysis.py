"""Full analysis API schemas."""

from typing import Literal

from app.schemas.common import AppBaseModel, CreatedAt, PositiveFloat, PositiveInt
from app.schemas.competitor import CompetitorsSummary
from app.schemas.finance import FinanceResult
from app.schemas.location import LocationInfo
from app.schemas.report import DataSourceInfo, MarketplaceRequirements, ReportResult
from app.schemas.score import ScoreResult


class AnalysisRequest(AppBaseModel):
    """Input fields for full address analysis."""

    address: str
    business_type: Literal["pvz"]
    rent: PositiveInt
    area_m2: PositiveFloat
    floor: int
    first_floor: bool
    separate_entrance: bool
    parking: bool
    signage_possible: bool
    storage_area: bool
    repair_condition: str
    new_residential_area: bool
    high_density_area: bool
    bus_stop_nearby: bool
    good_visibility: bool
    expected_gross_income_by_user: PositiveInt | None = None
    investment: PositiveInt
    desired_profit: PositiveInt


class AnalysisResponse(AppBaseModel):
    """Full analysis response contract."""

    location: LocationInfo
    competitors: CompetitorsSummary
    score: ScoreResult
    finance: FinanceResult
    marketplace_requirements: MarketplaceRequirements
    report: ReportResult
    checklist: list[str]
    data_sources: list[DataSourceInfo]
    created_at: CreatedAt
