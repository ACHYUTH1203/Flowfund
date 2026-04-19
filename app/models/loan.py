from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.simulation import SimulationRun
    from app.models.transaction import Transaction


class IncomeType(StrEnum):
    fixed = "fixed"
    variable = "variable"


class LoanStatus(StrEnum):
    active = "active"
    closed = "closed"
    defaulted = "defaulted"


class RepaymentType(StrEnum):
    fixed_daily = "fixed_daily"
    income_linked = "income_linked"


class Loan(Base):
    __tablename__ = "loans"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    wallet_id: Mapped[int] = mapped_column(ForeignKey("wallets.id"), index=True)

    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    duration_days: Mapped[int] = mapped_column(Integer)
    interest_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), default=Decimal("0")
    )
    daily_repayment: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    repayment_type: Mapped[RepaymentType] = mapped_column(
        Enum(RepaymentType, native_enum=False, length=16),
        default=RepaymentType.fixed_daily,
    )
    # Only populated when repayment_type == income_linked. Stored as fraction
    # (e.g. 0.2500 for 25% of daily income).
    repayment_percentage: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4), nullable=True, default=None
    )

    income_type: Mapped[IncomeType] = mapped_column(
        Enum(IncomeType, native_enum=False, length=16)
    )
    avg_daily_income: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    daily_expenses: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0")
    )

    status: Mapped[LoanStatus] = mapped_column(
        Enum(LoanStatus, native_enum=False, length=16),
        default=LoanStatus.active,
    )
    start_date: Mapped[date] = mapped_column(
        Date, server_default=func.current_date()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="loan")
    simulations: Mapped[list["SimulationRun"]] = relationship(
        back_populates="loan", cascade="all, delete-orphan"
    )
