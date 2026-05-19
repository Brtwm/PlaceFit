"""Pure deterministic decision service."""

from dataclasses import dataclass

from app.config.scoring_rules import DECISION_RULES


@dataclass(frozen=True)
class DecisionResult:
    """Decision label and deterministic warnings."""

    decision: str
    warnings: tuple[str, ...]


def make_decision(
    total_score: int,
    rent: int,
    net_profit: int | None,
) -> DecisionResult:
    """Return deterministic MVP decision and warnings."""

    decision = _decision_label(total_score=total_score, net_profit=net_profit)
    warnings = _warnings(rent=rent, net_profit=net_profit)
    return DecisionResult(decision=decision, warnings=warnings)


def _decision_label(total_score: int, net_profit: int | None) -> str:
    if total_score >= DECISION_RULES.high_score_threshold:
        if net_profit is None or net_profit > 0:
            return DECISION_RULES.consider
        return DECISION_RULES.check_more
    if total_score >= DECISION_RULES.mid_score_threshold:
        return DECISION_RULES.check_more
    return DECISION_RULES.likely_no


def _warnings(rent: int, net_profit: int | None) -> tuple[str, ...]:
    warnings: list[str] = []
    if rent > DECISION_RULES.high_rent_threshold:
        warnings.append(DECISION_RULES.high_rent_warning)
    if net_profit is None:
        warnings.append(DECISION_RULES.income_missing_warning)
    elif net_profit <= 0:
        warnings.append(DECISION_RULES.unprofitable_warning)
    return tuple(warnings)
