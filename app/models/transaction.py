from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.loan import Loan
    from app.models.wallet import Wallet


class TxnType(StrEnum):
    credit = "credit"
    debit = "debit"


class TxnStatus(StrEnum):
    success = "success"
    failed = "failed"
    skipped = "skipped"


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    wallet_id: Mapped[int] = mapped_column(ForeignKey("wallets.id"), index=True)
    loan_id: Mapped[int | None] = mapped_column(
        ForeignKey("loans.id"), nullable=True, index=True
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    type: Mapped[TxnType] = mapped_column(
        Enum(TxnType, native_enum=False, length=16)
    )
    status: Mapped[TxnStatus] = mapped_column(
        Enum(TxnStatus, native_enum=False, length=16)
    )

    idempotency_key: Mapped[str | None] = mapped_column(
        String(128), unique=True, nullable=True
    )
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    wallet: Mapped["Wallet"] = relationship(back_populates="transactions")
    loan: Mapped["Loan | None"] = relationship(back_populates="transactions")
