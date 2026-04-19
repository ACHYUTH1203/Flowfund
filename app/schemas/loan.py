from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.loan import IncomeType, LoanStatus, RepaymentType


class LoanCreate(BaseModel):
    wallet_id: int
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    duration_days: int = Field(gt=0, le=3650)
    interest_rate: Decimal = Field(
        default=Decimal("0"), ge=0, le=2, max_digits=5, decimal_places=4
    )
    income_type: IncomeType = IncomeType.fixed
    avg_daily_income: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    daily_expenses: Decimal = Field(
        default=Decimal("0"), ge=0, max_digits=12, decimal_places=2
    )
    repayment_type: RepaymentType = RepaymentType.fixed_daily
    repayment_percentage: Decimal | None = Field(
        default=None, gt=0, le=1, max_digits=5, decimal_places=4
    )
    user_id: str = Field(default="demo_user", max_length=64)

    @model_validator(mode="after")
    def _validate_repayment(self) -> "LoanCreate":
        if self.repayment_type == RepaymentType.income_linked and self.repayment_percentage is None:
            raise ValueError("repayment_percentage is required when repayment_type=income_linked")
        if self.repayment_type == RepaymentType.fixed_daily and self.repayment_percentage is not None:
            raise ValueError("repayment_percentage must be null when repayment_type=fixed_daily")
        return self


class LoanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: str
    wallet_id: int
    amount: Decimal
    duration_days: int
    interest_rate: Decimal
    daily_repayment: Decimal
    repayment_type: RepaymentType
    repayment_percentage: Decimal | None
    income_type: IncomeType
    avg_daily_income: Decimal
    daily_expenses: Decimal
    status: LoanStatus
    start_date: date
    created_at: datetime


class LoanTermsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_payable: Decimal
    base_daily: Decimal
    safe_daily: Decimal
    recommended_daily: Decimal
    is_sustainable: bool
    reason: str | None
    repayment_type: str
    repayment_percentage: Decimal | None


class LoanCreateResponse(BaseModel):
    loan: LoanOut
    terms: LoanTermsOut
    simulation_run_id: int


class LoanDetailResponse(BaseModel):
    loan: LoanOut
    terms: LoanTermsOut


class ScheduleDay(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    day_index: int
    income: Decimal
    repayment: Decimal
    balance_after: Decimal
    missed: bool


class ScheduleResponse(BaseModel):
    loan_id: int
    run_id: int
    total_days: int
    missed_count: int
    days: list[ScheduleDay]
