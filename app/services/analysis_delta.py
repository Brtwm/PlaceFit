"""Pure deterministic comparison of validated analysis snapshots."""

from typing import Literal, TypeAlias

from app.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.schemas.competitor import CompetitorInfo
from app.schemas.delta import (
    AnalysisDelta,
    AnalysisDeltaSummary,
    CompetitorChangedField,
    CompetitorDeltaItem,
    CompetitorsDeltaSection,
    DataSourcesDelta,
    DeltaDirection,
    DeltaStatus,
    FinanceDeltaSection,
    InputsDeltaSection,
    LocationProvenanceDeltaSection,
    ScalarDelta,
    ScoreDeltaSection,
    SnapshotOrigin,
)

ScalarValue: TypeAlias = str | int | float | bool | None
DirectionRule: TypeAlias = Literal["higher", "lower", "neutral", "decision"]

_INPUT_FIELDS = (
    "rent",
    "area_m2",
    "floor",
    "first_floor",
    "separate_entrance",
    "parking",
    "signage_possible",
    "storage_area",
    "repair_condition",
    "new_residential_area",
    "high_density_area",
    "bus_stop_nearby",
    "good_visibility",
    "expected_gross_income_by_user",
    "investment",
    "desired_profit",
)
_COMPETITOR_CHANGED_FIELDS: tuple[CompetitorChangedField, ...] = (
    "name",
    "brand",
    "category",
    "address",
    "lat",
    "lon",
    "distance_m",
    "rating",
    "reviews_count",
)
_COMPETITOR_STATUS_ORDER: dict[DeltaStatus, int] = {
    "added": 0,
    "removed": 1,
    "changed": 2,
    "unchanged": 3,
}
_DECISION_ORDER = {
    "скорее не открывать": 0,
    "проверить дополнительно": 1,
    "можно рассматривать": 2,
}


class AnalysisDeltaContractError(ValueError):
    """Validated snapshots violate lineage or identity invariants."""


def build_analysis_delta(
    *,
    previous_request: AnalysisRequest,
    previous_response: AnalysisResponse,
    current_request: AnalysisRequest,
    current_response: AnalysisResponse,
    previous_snapshot_origin: SnapshotOrigin,
    current_snapshot_origin: SnapshotOrigin,
    snapshot_schema_version: str,
) -> AnalysisDelta:
    """Compare stored outputs exactly without recalculation or side effects."""

    _validate_lineage(previous_request, current_request)
    inputs = _input_deltas(previous_request, current_request)
    competitors = _competitor_deltas(previous_response, current_response)
    score = _score_deltas(previous_response, current_response)
    warning = None
    if score.scoring_version.status == "changed":
        warning = (
            "Scoring version changed from "
            f"{score.scoring_version.before} to {score.scoring_version.after}; "
            "score changes may reflect rule changes as well as location changes."
        )

    return AnalysisDelta(
        previous_analysis_id=previous_response.location.id,
        current_analysis_id=current_response.location.id,
        previous_created_at=previous_response.created_at,
        current_created_at=current_response.created_at,
        previous_snapshot_origin=previous_snapshot_origin,
        current_snapshot_origin=current_snapshot_origin,
        snapshot_schema_version=snapshot_schema_version,
        scoring_version_warning=warning,
        inputs=inputs,
        location_provenance=_location_provenance_deltas(
            previous_response,
            current_response,
        ),
        competitors=competitors,
        score=score,
        finance=_finance_deltas(previous_response, current_response),
        summary=AnalysisDeltaSummary(
            changed_inputs=sum(
                delta.status != "unchanged"
                for delta in inputs.__dict__.values()
                if isinstance(delta, ScalarDelta)
            ),
            competitors_added=_count_competitors(competitors, "added"),
            competitors_removed=_count_competitors(competitors, "removed"),
            competitors_changed=_count_competitors(competitors, "changed"),
            competitors_unchanged=_count_competitors(competitors, "unchanged"),
        ),
    )


def _validate_lineage(
    previous: AnalysisRequest,
    current: AnalysisRequest,
) -> None:
    if previous.address != current.address:
        raise AnalysisDeltaContractError("address must be unchanged within lineage")
    if previous.business_type != current.business_type:
        raise AnalysisDeltaContractError(
            "business_type must be unchanged within lineage",
        )


def _input_deltas(
    previous: AnalysisRequest,
    current: AnalysisRequest,
) -> InputsDeltaSection:
    values = {
        field: _scalar_delta(
            field,
            _scalar_value(getattr(previous, field)),
            _scalar_value(getattr(current, field)),
            "neutral",
        )
        for field in _INPUT_FIELDS
    }
    return InputsDeltaSection.model_validate(values)


def _location_provenance_deltas(
    previous: AnalysisResponse,
    current: AnalysisResponse,
) -> LocationProvenanceDeltaSection:
    before_sources = [
        item.model_dump(mode="json") for item in previous.data_sources
    ]
    after_sources = [item.model_dump(mode="json") for item in current.data_sources]
    return LocationProvenanceDeltaSection(
        normalized_address=_scalar_delta(
            "normalized_address",
            previous.location.normalized_address,
            current.location.normalized_address,
            "neutral",
        ),
        lat=_scalar_delta(
            "lat",
            previous.location.lat,
            current.location.lat,
            "neutral",
        ),
        lon=_scalar_delta(
            "lon",
            previous.location.lon,
            current.location.lon,
            "neutral",
        ),
        data_sources=DataSourcesDelta(
            field="data_sources",
            before=previous.data_sources,
            after=current.data_sources,
            status="unchanged" if before_sources == after_sources else "changed",
            direction="neutral",
        ),
    )


def _competitor_deltas(
    previous: AnalysisResponse,
    current: AnalysisResponse,
) -> CompetitorsDeltaSection:
    previous_items = _competitors_by_identity(previous.competitors.list)
    current_items = _competitors_by_identity(current.competitors.list)
    items: list[CompetitorDeltaItem] = []
    for identity in previous_items.keys() | current_items.keys():
        before = previous_items.get(identity)
        after = current_items.get(identity)
        if before is None:
            status: DeltaStatus = "added"
            changed_fields: list[CompetitorChangedField] = []
        elif after is None:
            status = "removed"
            changed_fields = []
        else:
            changed_fields = [
                field
                for field in _COMPETITOR_CHANGED_FIELDS
                if getattr(before, field) != getattr(after, field)
            ]
            status = "changed" if changed_fields else "unchanged"
        items.append(
            CompetitorDeltaItem(
                identity=identity,
                status=status,
                before=before,
                after=after,
                changed_fields=changed_fields,
            ),
        )
    items.sort(key=lambda item: (_COMPETITOR_STATUS_ORDER[item.status], item.identity))

    previous_summary = previous.competitors
    current_summary = current.competitors
    return CompetitorsDeltaSection(
        competitors_300m=_scalar_delta(
            "competitors_300m",
            previous_summary.competitors_300m,
            current_summary.competitors_300m,
            "lower",
        ),
        competitors_500m=_scalar_delta(
            "competitors_500m",
            previous_summary.competitors_500m,
            current_summary.competitors_500m,
            "lower",
        ),
        competitors_700m=_scalar_delta(
            "competitors_700m",
            previous_summary.competitors_700m,
            current_summary.competitors_700m,
            "lower",
        ),
        nearest_competitor_distance_m=_scalar_delta(
            "nearest_competitor_distance_m",
            previous_summary.nearest_competitor_distance_m,
            current_summary.nearest_competitor_distance_m,
            "higher",
        ),
        average_competitor_distance_m=_scalar_delta(
            "average_competitor_distance_m",
            previous_summary.average_competitor_distance_m,
            current_summary.average_competitor_distance_m,
            "neutral",
        ),
        items=items,
    )


def _score_deltas(
    previous: AnalysisResponse,
    current: AnalysisResponse,
) -> ScoreDeltaSection:
    before = previous.score
    after = current.score
    return ScoreDeltaSection(
        scoring_version=_scalar_delta(
            "scoring_version",
            before.scoring_version,
            after.scoring_version,
            "neutral",
        ),
        total_score=_scalar_delta(
            "total_score",
            before.total_score,
            after.total_score,
            "higher",
        ),
        confidence_score=_scalar_delta(
            "confidence_score",
            before.confidence_score,
            after.confidence_score,
            "higher",
        ),
        decision=_scalar_delta(
            "decision",
            before.decision,
            after.decision,
            "decision",
        ),
        demand_score=_scalar_delta(
            "demand_score",
            before.details.demand_score,
            after.details.demand_score,
            "higher",
        ),
        competition_score=_scalar_delta(
            "competition_score",
            before.details.competition_score,
            after.details.competition_score,
            "higher",
        ),
        rent_score=_scalar_delta(
            "rent_score",
            before.details.rent_score,
            after.details.rent_score,
            "higher",
        ),
        premises_score=_scalar_delta(
            "premises_score",
            before.details.premises_score,
            after.details.premises_score,
            "higher",
        ),
        accessibility_score=_scalar_delta(
            "accessibility_score",
            before.details.accessibility_score,
            after.details.accessibility_score,
            "higher",
        ),
    )


def _finance_deltas(
    previous: AnalysisResponse,
    current: AnalysisResponse,
) -> FinanceDeltaSection:
    before = previous.finance
    after = current.finance
    return FinanceDeltaSection(
        monthly_costs=_scalar_delta(
            "monthly_costs",
            before.monthly_costs,
            after.monthly_costs,
            "lower",
        ),
        required_gross_income=_scalar_delta(
            "required_gross_income",
            before.required_gross_income,
            after.required_gross_income,
            "lower",
        ),
        expected_gross_income_by_user=_scalar_delta(
            "expected_gross_income_by_user",
            before.expected_gross_income_by_user,
            after.expected_gross_income_by_user,
            "neutral",
        ),
        net_profit=_scalar_delta(
            "net_profit",
            before.net_profit,
            after.net_profit,
            "higher",
        ),
        payback_months=_scalar_delta(
            "payback_months",
            before.payback_months,
            after.payback_months,
            "lower",
        ),
    )


def _scalar_delta(
    field: str,
    before: ScalarValue,
    after: ScalarValue,
    rule: DirectionRule,
) -> ScalarDelta:
    status = _scalar_status(before, after)
    return ScalarDelta(
        field=field,
        before=before,
        after=after,
        status=status,
        direction=_direction(before, after, status, rule),
    )


def _scalar_status(before: ScalarValue, after: ScalarValue) -> DeltaStatus:
    if before == after:
        return "unchanged"
    if before is None:
        return "added"
    if after is None:
        return "removed"
    return "changed"


def _direction(
    before: ScalarValue,
    after: ScalarValue,
    status: DeltaStatus,
    rule: DirectionRule,
) -> DeltaDirection:
    if status == "unchanged":
        return "neutral"
    if before is None or after is None:
        return "not_applicable"
    if rule == "neutral":
        return "neutral"
    if rule == "decision":
        before_rank = _DECISION_ORDER.get(str(before))
        after_rank = _DECISION_ORDER.get(str(after))
        if before_rank is None or after_rank is None:
            return "neutral"
        return "improved" if after_rank > before_rank else "worsened"
    before_number = float(before)
    after_number = float(after)
    improved = (
        after_number > before_number
        if rule == "higher"
        else after_number < before_number
    )
    return "improved" if improved else "worsened"


def _competitors_by_identity(
    competitors: list[CompetitorInfo],
) -> dict[str, CompetitorInfo]:
    result: dict[str, CompetitorInfo] = {}
    for competitor in competitors:
        identity, is_legacy = _competitor_identity(competitor)
        if identity in result:
            label = "legacy identity collision" if is_legacy else "identity collision"
            raise AnalysisDeltaContractError(f"{label}: {identity}")
        result[identity] = competitor
    return result


def _competitor_identity(competitor: CompetitorInfo) -> tuple[str, bool]:
    source = competitor.source.strip().casefold()
    external_id = (competitor.external_id or "").strip()
    if source and external_id:
        return f"{source}:{external_id}", False
    parts = (
        source,
        _normalized_text(competitor.brand),
        _normalized_text(competitor.name),
        _normalized_text(competitor.address),
        _normalized_coordinate(competitor.lat),
        _normalized_coordinate(competitor.lon),
    )
    return "legacy:" + "|".join(parts), True


def _normalized_text(value: str) -> str:
    return value.strip().casefold()


def _normalized_coordinate(value: float | None) -> str:
    return "null" if value is None else f"{value:.5f}"


def _count_competitors(
    section: CompetitorsDeltaSection,
    status: DeltaStatus,
) -> int:
    return sum(item.status == status for item in section.items)


def _scalar_value(value: object) -> ScalarValue:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    raise AnalysisDeltaContractError("delta field is not a JSON scalar")
