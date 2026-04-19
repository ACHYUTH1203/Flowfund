from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.transaction import TxnStatus, TxnType


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    wallet_id: int
    loan_id: int | None
    amount: Decimal
    type: TxnType
    status: TxnStatus
    idempotency_key: str | None
    note: str | None
    created_at: datetime
