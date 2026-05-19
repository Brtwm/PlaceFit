"""Pure deterministic finance service."""

from dataclasses import dataclass

from app.config.scoring_rules import FINANCE_DEFAULTS


@dataclass(frozen=True)
class FinanceDefaults:
    """Editable finance assumptions."""

    salary: int = FINANCE_DEFAULTS.salary
    taxes: int = FINANCE_DEFAULTS.taxes
    utilities: int = FINANCE_DEFAULTS.utilities
    internet: int = FINANCE_DEFAULTS.internet
    consumables: int = FINANCE_DEFAULTS.consumables
    other_costs: int = FINANCE_DEFAULTS.other_costs
    reserve: int = FINANCE_DEFAULTS.reserve
    desired_profit: int = FINANCE_DEFAULTS.desired_profit
    investment: int = FINANCE_DEFAULTS.investment


@dataclass(frozen=True)
class FinanceInput:
    """Input fields for deterministic break-even and payback calculations."""

    rent: int
    expected_gross_income_by_user: int | None = None
    defaults: FinanceDefaults = FinanceDefaults()


@dataclass(frozen=True)
class FinanceResult:
    """Financial model output."""

    monthly_costs: int
    required_gross_income: int
    expected_gross_income_by_user: int | None
    net_profit: int | None
    payback_months: float | None


def calculate_finance(input_data: FinanceInput) -> FinanceResult:
    """Calculate deterministic monthly costs, required income, and payback."""

    monthly_costs = (
        input_data.rent
        + input_data.defaults.salary
        + input_data.defaults.taxes
        + input_data.defaults.utilities
        + input_data.defaults.internet
        + input_data.defaults.consumables
        + input_data.defaults.other_costs
        + input_data.defaults.reserve
    )
    required_gross_income = monthly_costs + input_data.defaults.desired_profit

    if input_data.expected_gross_income_by_user is None:
        return FinanceResult(
            monthly_costs=monthly_costs,
            required_gross_income=required_gross_income,
            expected_gross_income_by_user=None,
            net_profit=None,
            payback_months=None,
        )

    net_profit = input_data.expected_gross_income_by_user - monthly_costs
    payback_months = (
        round(
            input_data.defaults.investment / net_profit,
            FINANCE_DEFAULTS.payback_round_digits,
        )
        if net_profit > 0
        else None
    )

    return FinanceResult(
        monthly_costs=monthly_costs,
        required_gross_income=required_gross_income,
        expected_gross_income_by_user=input_data.expected_gross_income_by_user,
        net_profit=net_profit,
        payback_months=payback_months,
    )
