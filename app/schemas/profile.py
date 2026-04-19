from decimal import Decimal

from pydantic import BaseModel


class LoanStatsOut(BaseModel):
    id: int
    amount: Decimal
    daily_repayment: Decimal
    repayment_type: str
    repayment_percentage: Decimal | None
    duration_days: int
    status: str
    is_sustainable: bool
    avg_daily_income: Decimal
    paid: Decimal
    outstanding: Decimal
    debit_attempts: int
    skip_count: int
    skip_rate: float


class UserProfileResponse(BaseModel):
    user_id: str
    wallet_id: int | None
    wallet_balance: Decimal
    active_loans: list[LoanStatsOut]
    closed_loans: list[LoanStatsOut]
    total_daily_commitment: Decimal
    total_outstanding: Decimal
    total_debits: int
    total_skips: int
    overall_skip_rate: float
    avg_daily_income: Decimal
    has_defaulted_loan: bool
