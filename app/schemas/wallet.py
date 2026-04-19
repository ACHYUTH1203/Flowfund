from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.transaction import TransactionOut


class WalletCreate(BaseModel):
    user_id: str = Field(default="demo_user", max_length=64)


class WalletOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: str
    balance: Decimal
    created_at: datetime


class AddFundsRequest(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    idempotency_key: str | None = Field(default=None, max_length=128)
    note: str | None = Field(default=None, max_length=255)


class AddFundsResponse(BaseModel):
    transaction: TransactionOut
    wallet: WalletOut


class DebitRequest(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    idempotency_key: str | None = Field(default=None, max_length=128)
    loan_id: int | None = None
    note: str | None = Field(default=None, max_length=255)


class DebitResponse(BaseModel):
    transaction: TransactionOut
    wallet: WalletOut
