"""Financial model result schemas."""

from app.schemas.common import AppBaseModel, PositiveFloat, PositiveInt


class FinanceResult(AppBaseModel):
    """Financial model output."""

    monthly_costs: PositiveInt
    required_gross_income: PositiveInt
    expected_gross_income_by_user: PositiveInt | None = None
    net_profit: int | None = None
    payback_months: PositiveFloat | None = None
