"""Phase 6 analysis orchestration over mocked providers and persistence."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from typing import Literal

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models import (
    FinancialModel,
    Location,
    LocationPoiDistance,
    Poi,
    Report,
    Score,
    ScoringVersion,
)
from app.providers.geocoder.base import GeocodingCandidate
from app.providers.poi_search.base import PoiSearchProvider
from app.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.schemas.competitor import CompetitorInfo, CompetitorsSummary
from app.schemas.error import ErrorCode
from app.schemas.finance import FinanceResult as FinanceSchema
from app.schemas.location import (
    GeocodeCandidate,
    LocationInfo,
    LocationsListItem,
    LocationsListRequest,
    LocationsListResponse,
)
from app.schemas.report import DataSourceInfo, MarketplaceRequirements, ReportResult
from app.schemas.score import ScoreDetails as ScoreDetailsSchema
from app.schemas.score import ScoreResult as ScoreResultSchema
from app.services.competitors import CompetitorItem, CompetitorsResult
from app.services.competitors import search_competitors as run_competitor_search
from app.services.confidence import (
    ConfidenceInput,
    ManualInputReliability,
    calculate_confidence,
)
from app.services.decision import make_decision
from app.services.finance import (
    FinanceDefaults,
    FinanceInput,
    FinanceResult,
    calculate_finance,
)
from app.services.geocoding import GeocodingService
from app.services.marketplace import get_marketplace_requirements
from app.services.report import (
    PreparedAnalysisReportInput,
    PreparedReportLocation,
    ReportService,
    ReportServiceError,
)
from app.services.scoring import ScoringInput, ScoringResult, calculate_score


class AnalysisServiceError(Exception):
    """Domain error raised by the analysis service."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        *,
        details: str | None = None,
        suggestions: Sequence[GeocodingCandidate] = (),
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details
        self.suggestions = tuple(suggestions)


@dataclass(frozen=True)
class PersistedAnalysisParts:
    """Persisted rows needed to assemble an analysis response."""

    location: Location
    score: Score
    financial_model: FinancialModel
    report: Report


class AnalysisService:
    """Orchestrate geocoding, competitors, deterministic core, and DB writes."""

    def __init__(
        self,
        *,
        db: Session,
        geocoding_service: GeocodingService,
        poi_providers: Sequence[PoiSearchProvider],
        report_service: ReportService,
    ) -> None:
        self._db = db
        self._geocoding_service = geocoding_service
        self._poi_providers = poi_providers
        self._report_service = report_service

    def analyze(self, request: AnalysisRequest) -> AnalysisResponse:
        """Run the full mocked-provider analysis pipeline and persist it."""

        now = datetime.now(UTC)
        geocoding = self._geocoding_service.geocode(request.address)
        candidate = self._resolved_candidate(geocoding.candidates, geocoding.status)

        try:
            competitors = run_competitor_search(
                self._poi_providers,
                lat=candidate.lat,
                lon=candidate.lon,
                radius_m=700,
                business_type=request.business_type,
            )
        except Exception as exc:
            raise AnalysisServiceError(
                "COMPETITOR_SEARCH_FAILED",
                "Не удалось найти конкурентов",
                details=str(exc),
            ) from exc

        scoring = calculate_score(
            ScoringInput(
                high_density_area=request.high_density_area,
                new_residential_area=request.new_residential_area,
                competitors_300m=competitors.competitors_300m,
                competitors_700m=competitors.competitors_700m,
                nearest_competitor_distance_m=(
                    competitors.nearest_competitor_distance_m
                ),
                rent=request.rent,
                first_floor=request.first_floor,
                separate_entrance=request.separate_entrance,
                area_m2=request.area_m2,
                storage_area=request.storage_area,
                signage_possible=request.signage_possible,
                parking=request.parking,
                bus_stop_nearby=request.bus_stop_nearby,
                good_visibility=request.good_visibility,
            ),
        )
        confidence = calculate_confidence(
            ConfidenceInput(
                poi_source_count=len(competitors.sources),
                as_of_date=now.date(),
                freshness_date=now.date(),
                manual_input_reliability=ManualInputReliability.MANUAL,
                competitors_700m=competitors.competitors_700m,
                expected_gross_income_by_user=(
                    request.expected_gross_income_by_user
                ),
            ),
        )
        finance = calculate_finance(
            FinanceInput(
                rent=request.rent,
                expected_gross_income_by_user=(
                    request.expected_gross_income_by_user
                ),
                defaults=FinanceDefaults(
                    desired_profit=request.desired_profit,
                    investment=request.investment,
                ),
            ),
        )
        decision = make_decision(
            scoring.total_score,
            request.rent,
            finance.net_profit,
        )
        scoring_version = self._active_scoring_version(request.business_type)
        checklist = _build_checklist(decision.warnings)
        marketplace_requirements = get_marketplace_requirements()

        try:
            report = self._report_service.generate_report(
                self._build_report_input(
                    request=request,
                    candidate=candidate,
                    competitors=competitors,
                    scoring=scoring,
                    confidence_score=confidence.confidence_score,
                    scoring_version=scoring_version.version,
                    decision=decision.decision,
                    finance=finance,
                    marketplace_requirements=marketplace_requirements,
                    checklist=checklist,
                    fetched_at=now,
                ),
            )
        except ReportServiceError as exc:
            raise AnalysisServiceError(
                "LLM_FAILED",
                "Отчёт не удалось создать",
                details=str(exc),
            ) from exc

        try:
            persisted = self._persist_analysis(
                request=request,
                candidate=candidate,
                competitors=competitors,
                scoring=scoring,
                confidence_score=confidence.confidence_score,
                decision=decision.decision,
                finance=finance,
                scoring_version=scoring_version,
                report=report,
                fetched_at=now,
            )
            response = self._build_response(
                parts=persisted,
                competitors=competitors,
                scoring_version=scoring_version.version,
                checklist=checklist,
            )
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise

        return response

    def list_locations(
        self,
        filters: LocationsListRequest,
    ) -> LocationsListResponse:
        """Return persisted analysis history with supported filters."""

        base_stmt = (
            select(Location, Score, FinancialModel)
            .join(Score, Score.location_id == Location.id)
            .join(FinancialModel, FinancialModel.location_id == Location.id)
        )
        filtered_stmt = _apply_location_filters(base_stmt, filters)
        total = self._db.scalar(
            select(func.count()).select_from(filtered_stmt.subquery()),
        )
        rows = self._db.execute(
            filtered_stmt.order_by(Location.created_at.desc(), Location.id.desc())
            .limit(filters.limit)
            .offset(filters.offset),
        ).all()

        return LocationsListResponse(
            items=[
                _to_list_item(
                    location=location,
                    score=score,
                    financial_model=financial_model,
                )
                for location, score, financial_model in rows
            ],
            total=total or 0,
        )

    def get_location_detail(self, location_id: int) -> AnalysisResponse:
        """Return full persisted analysis details for a location."""

        parts = self._load_persisted_analysis(location_id)
        scoring_version = self._db.get(
            ScoringVersion,
            parts.score.scoring_version_id,
        )
        if scoring_version is None:
            raise AnalysisServiceError(
                "INTERNAL_ERROR",
                "Версия скоринга для анализа не найдена",
            )

        competitors = self._load_competitors(location_id)
        return self._build_response(
            parts=parts,
            competitors=competitors,
            scoring_version=scoring_version.version,
            checklist=_build_checklist(()),
        )

    def _resolved_candidate(
        self,
        candidates: Sequence[GeocodingCandidate],
        status: str,
    ) -> GeocodingCandidate:
        if status == "resolved" and candidates:
            return candidates[0]
        if status == "ambiguous":
            raise AnalysisServiceError(
                "ADDRESS_AMBIGUOUS",
                "Найдено несколько вариантов адреса",
                suggestions=candidates,
            )
        if status == "city_not_supported":
            raise AnalysisServiceError(
                "CITY_NOT_SUPPORTED",
                "MVP поддерживает только адреса в Краснодаре",
            )
        raise AnalysisServiceError(
            "GEOCODING_FAILED",
            "Не удалось геокодировать адрес",
        )

    def _active_scoring_version(self, business_type: str) -> ScoringVersion:
        scoring_version = self._db.scalar(
            select(ScoringVersion).where(
                ScoringVersion.business_type == business_type,
                ScoringVersion.active.is_(True),
            ),
        )
        if scoring_version is None:
            raise AnalysisServiceError(
                "INTERNAL_ERROR",
                "Активная версия скоринга не найдена",
            )
        return scoring_version

    def _persist_analysis(
        self,
        *,
        request: AnalysisRequest,
        candidate: GeocodingCandidate,
        competitors: CompetitorsResult,
        scoring: ScoringResult,
        confidence_score: int,
        decision: str,
        finance: FinanceResult,
        scoring_version: ScoringVersion,
        report: ReportResult,
        fetched_at: datetime,
    ) -> PersistedAnalysisParts:
        location = Location(
            address=request.address,
            normalized_address=candidate.normalized_address,
            city="Краснодар",
            lat=candidate.lat,
            lon=candidate.lon,
            business_type=request.business_type,
            rent=request.rent,
            area_m2=Decimal(str(request.area_m2)),
            floor=request.floor,
            first_floor=request.first_floor,
            separate_entrance=request.separate_entrance,
            parking=request.parking,
            signage_possible=request.signage_possible,
            storage_area=request.storage_area,
            repair_condition=request.repair_condition,
            new_residential_area=request.new_residential_area,
            high_density_area=request.high_density_area,
            bus_stop_nearby=request.bus_stop_nearby,
            good_visibility=request.good_visibility,
            geocoding_source=candidate.provider,
            geocoding_fetched_at=fetched_at,
            geocoding_confidence=_decimal_or_none(candidate.confidence),
        )
        self._db.add(location)
        self._db.flush()

        for competitor in competitors.competitors:
            poi = self._get_or_create_poi(competitor, fetched_at=fetched_at)
            self._db.flush()
            self._db.add(
                LocationPoiDistance(
                    location_id=location.id,
                    poi_id=poi.id,
                    distance_m=competitor.distance_m,
                    radius_bucket=_radius_bucket(competitor.distance_m),
                ),
            )

        score = Score(
            location_id=location.id,
            scoring_version_id=scoring_version.id,
            demand_score=scoring.details.demand_score,
            competition_score=scoring.details.competition_score,
            rent_score=scoring.details.rent_score,
            premises_score=scoring.details.premises_score,
            accessibility_score=scoring.details.accessibility_score,
            total_score=scoring.total_score,
            confidence_score=confidence_score,
            decision=decision,
            details=_score_details_dict(scoring),
        )
        financial_model = FinancialModel(
            location_id=location.id,
            rent=request.rent,
            desired_profit=request.desired_profit,
            investment=request.investment,
            monthly_costs=finance.monthly_costs,
            required_gross_income=finance.required_gross_income,
            expected_gross_income_by_user=finance.expected_gross_income_by_user,
            net_profit=finance.net_profit,
            payback_months=_decimal_or_none(finance.payback_months),
        )
        report_row = Report(
            location_id=location.id,
            report_text=report.text,
            report_json=report.model_dump(mode="json"),
            provider=report.provider,
            model_name=report.model,
            prompt_version=report.prompt_version,
            generation_status=report.status,
        )
        self._db.add_all([score, financial_model, report_row])
        self._db.flush()

        return PersistedAnalysisParts(
            location=location,
            score=score,
            financial_model=financial_model,
            report=report_row,
        )

    def _build_report_input(
        self,
        *,
        request: AnalysisRequest,
        candidate: GeocodingCandidate,
        competitors: CompetitorsResult,
        scoring: ScoringResult,
        confidence_score: int,
        scoring_version: str,
        decision: str,
        finance: FinanceResult,
        marketplace_requirements: MarketplaceRequirements,
        checklist: list[str],
        fetched_at: datetime,
    ) -> PreparedAnalysisReportInput:
        return PreparedAnalysisReportInput(
            location=PreparedReportLocation(
                address=request.address,
                normalized_address=candidate.normalized_address,
                city="Краснодар",
                business_type=request.business_type,
                lat=candidate.lat,
                lon=candidate.lon,
            ),
            competitors=_to_competitors_summary(competitors),
            score=ScoreResultSchema(
                total_score=scoring.total_score,
                confidence_score=confidence_score,
                scoring_version=scoring_version,
                decision=decision,
                details=ScoreDetailsSchema(
                    demand_score=scoring.details.demand_score,
                    competition_score=scoring.details.competition_score,
                    rent_score=scoring.details.rent_score,
                    premises_score=scoring.details.premises_score,
                    accessibility_score=scoring.details.accessibility_score,
                ),
            ),
            finance=FinanceSchema(
                monthly_costs=finance.monthly_costs,
                required_gross_income=finance.required_gross_income,
                expected_gross_income_by_user=finance.expected_gross_income_by_user,
                net_profit=finance.net_profit,
                payback_months=finance.payback_months,
            ),
            marketplace_requirements=marketplace_requirements,
            checklist=checklist,
            data_sources=_report_data_sources(
                candidate=candidate,
                competitors=competitors,
                fetched_at=fetched_at,
            ),
        )

    def _get_or_create_poi(
        self,
        competitor: CompetitorItem,
        *,
        fetched_at: datetime,
    ) -> Poi:
        poi = self._db.scalar(
            select(Poi).where(
                Poi.source == competitor.source,
                Poi.external_id == competitor.external_id,
            ),
        )
        if poi is not None:
            return poi

        poi = Poi(
            external_id=competitor.external_id,
            source=competitor.source,
            name=competitor.name,
            brand=competitor.brand,
            category=competitor.category,
            address=competitor.address,
            lat=competitor.lat,
            lon=competitor.lon,
            rating=_decimal_or_none(competitor.rating),
            reviews_count=competitor.reviews_count,
            fetched_at=fetched_at,
        )
        self._db.add(poi)
        return poi

    def _load_persisted_analysis(self, location_id: int) -> PersistedAnalysisParts:
        row = self._db.execute(
            select(Location, Score, FinancialModel, Report)
            .join(Score, Score.location_id == Location.id)
            .join(FinancialModel, FinancialModel.location_id == Location.id)
            .join(Report, Report.location_id == Location.id)
            .where(Location.id == location_id)
            .order_by(Score.created_at.desc(), Report.created_at.desc()),
        ).first()
        if row is None:
            raise AnalysisServiceError(
                "NOT_FOUND",
                "Анализ не найден",
            )
        location, score, financial_model, report = row
        return PersistedAnalysisParts(
            location=location,
            score=score,
            financial_model=financial_model,
            report=report,
        )

    def _load_competitors(self, location_id: int) -> CompetitorsResult:
        rows = self._db.execute(
            select(Poi, LocationPoiDistance)
            .join(LocationPoiDistance, LocationPoiDistance.poi_id == Poi.id)
            .where(LocationPoiDistance.location_id == location_id)
            .order_by(LocationPoiDistance.distance_m.asc(), Poi.id.asc()),
        ).all()
        competitors = tuple(
            CompetitorItem(
                source=poi.source,
                external_id=poi.external_id or "",
                name=poi.name or "",
                brand=poi.brand or "",
                category=poi.category or "",
                address=poi.address or "",
                lat=poi.lat or 0.0,
                lon=poi.lon or 0.0,
                distance_m=distance.distance_m,
                rating=_float_or_none(poi.rating),
                reviews_count=poi.reviews_count,
            )
            for poi, distance in rows
        )
        distances = [competitor.distance_m for competitor in competitors]
        return CompetitorsResult(
            competitors_300m=sum(1 for distance in distances if distance <= 300),
            competitors_500m=sum(1 for distance in distances if distance <= 500),
            competitors_700m=sum(1 for distance in distances if distance <= 700),
            nearest_competitor_distance_m=min(distances) if distances else None,
            average_competitor_distance_m=round(sum(distances) / len(distances))
            if distances
            else None,
            competitors=competitors,
            sources=tuple(sorted({competitor.source for competitor in competitors})),
        )

    def _build_response(
        self,
        *,
        parts: PersistedAnalysisParts,
        competitors: CompetitorsResult,
        scoring_version: str,
        checklist: list[str],
    ) -> AnalysisResponse:
        return AnalysisResponse(
            location=_to_location_info(parts.location),
            competitors=_to_competitors_summary(competitors),
            score=_to_score_result(parts.score, scoring_version=scoring_version),
            finance=_to_finance_result(parts.financial_model),
            marketplace_requirements=get_marketplace_requirements(),
            report=_to_report_result(parts.report),
            checklist=checklist,
            data_sources=self._data_sources(parts.location, competitors, parts.report),
            created_at=parts.location.created_at,
        )

    def _data_sources(
        self,
        location: Location,
        competitors: CompetitorsResult,
        report: Report,
    ) -> list[DataSourceInfo]:
        sources: list[DataSourceInfo] = []
        if location.geocoding_source and location.geocoding_fetched_at:
            sources.append(
                DataSourceInfo(
                    source=location.geocoding_source,
                    data_type="geocoding",
                    fetched_at=location.geocoding_fetched_at,
                    confidence=_float_or_none(location.geocoding_confidence),
                ),
            )
        for source in competitors.sources:
            sources.append(
                DataSourceInfo(
                    source=source,
                    data_type="competitors",
                    fetched_at=location.geocoding_fetched_at
                    or location.created_at,
                ),
            )
        if report.provider and report.created_at:
            sources.append(
                DataSourceInfo(
                    source=report.provider,
                    data_type="report",
                    fetched_at=report.created_at,
                ),
            )
        return sources


def _apply_location_filters(
    stmt: Select[tuple[Location, Score, FinancialModel]],
    filters: LocationsListRequest,
) -> Select[tuple[Location, Score, FinancialModel]]:
    stmt = stmt.where(Location.business_type == filters.business_type)
    if filters.min_score is not None:
        stmt = stmt.where(Score.total_score >= filters.min_score)
    if filters.max_score is not None:
        stmt = stmt.where(Score.total_score <= filters.max_score)
    if filters.decision is not None:
        stmt = stmt.where(Score.decision == filters.decision)
    if filters.date_from is not None:
        stmt = stmt.where(Location.created_at >= _date_start(filters.date_from))
    if filters.date_to is not None:
        stmt = stmt.where(
            Location.created_at < _date_start(filters.date_to) + timedelta(days=1),
        )
    return stmt


def _date_start(value: date) -> datetime:
    return datetime.combine(value, time.min, tzinfo=UTC)


def _to_list_item(
    *,
    location: Location,
    score: Score,
    financial_model: FinancialModel,
) -> LocationsListItem:
    return LocationsListItem(
        id=location.id,
        address=location.address,
        business_type="pvz",
        rent=location.rent or 0,
        total_score=score.total_score or 0,
        confidence_score=score.confidence_score or 0,
        decision=score.decision or "",
        net_profit=financial_model.net_profit,
        payback_months=_float_or_none(financial_model.payback_months),
        created_at=location.created_at,
    )


def _to_location_info(location: Location) -> LocationInfo:
    return LocationInfo(
        id=location.id,
        address=location.address,
        normalized_address=location.normalized_address or location.address,
        lat=location.lat or 0.0,
        lon=location.lon or 0.0,
    )


def _to_competitors_summary(result: CompetitorsResult) -> CompetitorsSummary:
    return CompetitorsSummary(
        competitors_300m=result.competitors_300m,
        competitors_500m=result.competitors_500m,
        competitors_700m=result.competitors_700m,
        nearest_competitor_distance_m=result.nearest_competitor_distance_m,
        average_competitor_distance_m=result.average_competitor_distance_m,
        list=[
            CompetitorInfo(
                name=competitor.name,
                brand=competitor.brand,
                category=competitor.category,
                address=competitor.address,
                distance_m=competitor.distance_m,
                rating=competitor.rating,
                reviews_count=competitor.reviews_count,
                source=competitor.source,
            )
            for competitor in result.competitors
        ],
    )


def _to_score_result(score: Score, *, scoring_version: str) -> ScoreResultSchema:
    return ScoreResultSchema(
        total_score=score.total_score or 0,
        confidence_score=score.confidence_score or 0,
        scoring_version=scoring_version,
        decision=score.decision or "",
        details=ScoreDetailsSchema(
            demand_score=score.demand_score or 0,
            competition_score=score.competition_score or 0,
            rent_score=score.rent_score or 0,
            premises_score=score.premises_score or 0,
            accessibility_score=score.accessibility_score or 0,
        ),
    )


def _to_finance_result(financial_model: FinancialModel) -> FinanceSchema:
    return FinanceSchema(
        monthly_costs=financial_model.monthly_costs or 0,
        required_gross_income=financial_model.required_gross_income or 0,
        expected_gross_income_by_user=financial_model.expected_gross_income_by_user,
        net_profit=financial_model.net_profit,
        payback_months=_float_or_none(financial_model.payback_months),
    )


def _to_report_result(report: Report) -> ReportResult:
    status: Literal["success", "fallback"] = (
        "success" if report.generation_status == "success" else "fallback"
    )
    provider: Literal["openai_compatible", "fallback"] = (
        "openai_compatible"
        if report.provider == "openai_compatible"
        else "fallback"
    )
    return ReportResult(
        status=status,
        text=report.report_text or "",
        provider=provider,
        model=report.model_name or "none",
        prompt_version=report.prompt_version or "v1.0",
    )


def _build_checklist(warnings: Sequence[str]) -> list[str]:
    checklist = [
        "Проверить конкурентов вручную в картах перед подписанием аренды.",
        "Проверить проходимость утром, днём и вечером.",
        "Сверить договор аренды, каникулы и коммунальные условия.",
        "Проверить требования маркетплейсов по официальным источникам.",
    ]
    checklist.extend(warnings)
    return checklist


def _report_data_sources(
    *,
    candidate: GeocodingCandidate,
    competitors: CompetitorsResult,
    fetched_at: datetime,
) -> list[DataSourceInfo]:
    sources = [
        DataSourceInfo(
            source=candidate.provider,
            data_type="geocoding",
            fetched_at=fetched_at,
            confidence=candidate.confidence,
        ),
    ]
    sources.extend(
        DataSourceInfo(
            source=source,
            data_type="competitors",
            fetched_at=fetched_at,
        )
        for source in competitors.sources
    )
    return sources


def _score_details_dict(scoring: ScoringResult) -> dict[str, object]:
    return {
        "demand_score": scoring.details.demand_score,
        "competition_score": scoring.details.competition_score,
        "rent_score": scoring.details.rent_score,
        "premises_score": scoring.details.premises_score,
        "accessibility_score": scoring.details.accessibility_score,
    }


def _radius_bucket(distance_m: int) -> str:
    if distance_m <= 300:
        return "300m"
    if distance_m <= 500:
        return "500m"
    return "700m"


def _decimal_or_none(value: float | int | None) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _float_or_none(value: Decimal | int | float | None) -> float | None:
    if value is None:
        return None
    return float(value)


def to_geocode_candidates(
    candidates: Sequence[GeocodingCandidate],
) -> list[GeocodeCandidate]:
    """Convert provider candidates to public API suggestions."""

    return [
        GeocodeCandidate(
            address=candidate.normalized_address,
            lat=candidate.lat,
            lon=candidate.lon,
            confidence=candidate.confidence,
        )
        for candidate in candidates
    ]
