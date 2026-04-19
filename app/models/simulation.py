from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.loan import Loan


class SimulationRun(Base):
    __tablename__ = "simulation_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    loan_id: Mapped[int] = mapped_column(ForeignKey("loans.id"), index=True)
    scenario: Mapped[str] = mapped_column(String(32), default="baseline")
    trials: Mapped[int] = mapped_column(Integer, default=1)
    default_probability: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    loan: Mapped["Loan"] = relationship(back_populates="simulations")
    days: Mapped[list["SimulationDay"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class SimulationDay(Base):
    __tablename__ = "simulation_days"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("simulation_runs.id"), index=True
    )
    day_index: Mapped[int] = mapped_column(Integer)
    income: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    repayment: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    balance_after: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    missed: Mapped[bool] = mapped_column(Boolean, default=False)

    run: Mapped["SimulationRun"] = relationship(back_populates="days")
