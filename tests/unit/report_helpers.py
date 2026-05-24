from datetime import UTC, datetime

from app.schemas.competitor import CompetitorInfo, CompetitorsSummary
from app.schemas.finance import FinanceResult
from app.schemas.report import (
    DataSourceInfo,
    MarketplaceRequirementResult,
    MarketplaceRequirements,
)
from app.schemas.score import ScoreDetails, ScoreResult
from app.services.report import PreparedAnalysisReportInput, PreparedReportLocation


def sample_report_input() -> PreparedAnalysisReportInput:
    return PreparedAnalysisReportInput(
        location=PreparedReportLocation(
            address="Краснодар, ул. Восточно-Кругликовская, 30",
            normalized_address="г Краснодар, ул Восточно-Кругликовская, д 30",
            city="Краснодар",
            business_type="pvz",
            lat=45.035,
            lon=39.028,
        ),
        competitors=CompetitorsSummary(
            competitors_300m=1,
            competitors_500m=3,
            competitors_700m=5,
            nearest_competitor_distance_m=180,
            average_competitor_distance_m=420,
            list=[
                CompetitorInfo(
                    name="Ozon пункт выдачи",
                    brand="Ozon",
                    category="pvz",
                    address="г Краснодар, ул Восточно-Кругликовская, д 31",
                    distance_m=180,
                    rating=4.6,
                    reviews_count=41,
                    source="osm",
                ),
            ],
        ),
        score=ScoreResult(
            total_score=82,
            confidence_score=90,
            scoring_version="v1.0",
            decision="можно рассматривать",
            details=ScoreDetails(
                demand_score=35,
                competition_score=12,
                rent_score=15,
                premises_score=10,
                accessibility_score=10,
            ),
        ),
        finance=FinanceResult(
            monthly_costs=295000,
            required_gross_income=375000,
            expected_gross_income_by_user=360000,
            net_profit=65000,
            payback_months=9.2,
        ),
        marketplace_requirements=_marketplace_requirements(),
        checklist=[
            "Проверить конкурентов вручную в картах перед подписанием аренды.",
            "Проверить требования маркетплейсов по официальным источникам.",
        ],
        data_sources=[
            DataSourceInfo(
                source="2gis",
                data_type="geocoding",
                fetched_at=datetime(2026, 5, 14, 10, 0, tzinfo=UTC),
                confidence=0.95,
            ),
            DataSourceInfo(
                source="osm",
                data_type="competitors",
                fetched_at=datetime(2026, 5, 14, 10, 0, tzinfo=UTC),
            ),
        ],
    )


def _marketplace_requirements() -> MarketplaceRequirements:
    warning = "Требования маркетплейсов нужно сверить с официальными источниками."
    manual = MarketplaceRequirementResult(
        status="needs_manual_check",
        needs_manual_check=True,
        manual_checks=["Проверить вручную по официальным источникам."],
        warning=warning,
    )
    return MarketplaceRequirements(
        ozon=manual,
        wildberries=manual,
        yandex_market=manual,
    )
