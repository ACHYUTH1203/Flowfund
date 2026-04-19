from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class PortfolioRiskResponse(BaseModel):
    user_id: str
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    reasons: list[str]
    suggested_action: str

    # The numbers behind the scoring
    avg_daily_income: Decimal
    safe_daily_cap: Decimal
    total_daily_commitment: Decimal
    buffer_days: float
    total_debits: int
    total_skips: int
    is_sustainable: bool
