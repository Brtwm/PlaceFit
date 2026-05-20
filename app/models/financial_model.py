"""Financial model ORM model."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FinancialModel(Base):
    """Persisted deterministic finance calculation."""

    __tablename__ = "financial_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
    )
    rent: Mapped[int | None] = mapped_column(Integer)
    salary: Mapped[int | None] = mapped_column(Integer, server_default=text("120000"))
    taxes: Mapped[int | None] = mapped_column(Integer, server_default=text("30000"))
    utilities: Mapped[int | None] = mapped_column(Integer, server_default=text("10000"))
    internet: Mapped[int | None] = mapped_column(Integer, server_default=text("5000"))
    consumables: Mapped[int | None] = mapped_column(
        Integer,
        server_default=text("10000"),
    )
    other_costs: Mapped[int | None] = mapped_column(
        Integer,
        server_default=text("15000"),
    )
    reserve: Mapped[int | None] = mapped_column(Integer, server_default=text("20000"))
    desired_profit: Mapped[int | None] = mapped_column(
        Integer,
        server_default=text("80000"),
    )
    investment: Mapped[int | None] = mapped_column(
        Integer,
        server_default=text("600000"),
    )
    monthly_costs: Mapped[int | None] = mapped_column(Integer)
    required_gross_income: Mapped[int | None] = mapped_column(Integer)
    expected_gross_income_by_user: Mapped[int | None] = mapped_column(Integer)
    net_profit: Mapped[int | None] = mapped_column(Integer)
    payback_months: Mapped[Decimal | None] = mapped_column(Numeric)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
    )
