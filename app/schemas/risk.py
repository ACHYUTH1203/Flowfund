from typing import Literal

from pydantic import BaseModel


class RiskScoreResponse(BaseModel):
    loan_id: int
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    reasons: list[str]
    suggested_action: str
    buffer_days: float
    skip_count: int
    debit_count: int
    is_sustainable: bool
