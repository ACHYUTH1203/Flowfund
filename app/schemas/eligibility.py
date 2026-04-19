from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.models.loan import RepaymentType


class EligibilityRequest(BaseModel):
    user_id: str = Field(default="demo_user", max_length=64)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    duration_days: int = Field(gt=0, le=3650)
    interest_rate: Decimal = Field(
        default=Decimal("0"), ge=0, le=2, max_digits=5, decimal_places=4
    )
    repayment_type: RepaymentType = RepaymentType.fixed_daily
    repayment_percentage: Decimal | None = Field(
        default=None, gt=0, le=1, max_digits=5, decimal_places=4
    )
    # Optional override; if omitted, we use the profile's avg income.
    avg_daily_income: Decimal | None = Field(
        default=None, gt=0, max_digits=12, decimal_places=2
    )

    @model_validator(mode="after")
    def _validate_repayment(self) -> "EligibilityRequest":
        if (
            self.repayment_type == RepaymentType.income_linked
            and self.repayment_percentage is None
        ):
            raise ValueError(
                "repayment_percentage is required when repayment_type=income_linked"
            )
        return self


class RuleOut(BaseModel):
    name: str
    passed: bool
    detail: str


class EligibilityResponse(BaseModel):
    eligible: bool
    rules: list[RuleOut]
    reasons_fail: list[str]
    proposed_daily_repayment: Decimal
    proposed_total_payable: Decimal
    suggested_max_amount: Decimal
