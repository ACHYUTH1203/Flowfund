from dataclasses import asdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.portfolio import PortfolioRiskResponse
from app.schemas.profile import UserProfileResponse
from app.services import profile as profile_service
from app.services import risk as risk_service
from app.services.loan_simulator import DEFAULT_SAFE_PCT

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}/profile", response_model=UserProfileResponse)
def get_profile(user_id: str, db: Session = Depends(get_db)) -> dict:
    p = profile_service.get_profile(db, user_id)
    return {
        "user_id": p.user_id,
        "wallet_id": p.wallet_id,
        "wallet_balance": p.wallet_balance,
        "active_loans": [asdict(l) for l in p.active_loans],
        "closed_loans": [asdict(l) for l in p.closed_loans],
        "total_daily_commitment": p.total_daily_commitment,
        "total_outstanding": p.total_outstanding,
        "total_debits": p.total_debits,
        "total_skips": p.total_skips,
        "overall_skip_rate": p.overall_skip_rate,
        "avg_daily_income": p.avg_daily_income,
        "has_defaulted_loan": p.has_defaulted_loan,
    }


@router.get("/{user_id}/portfolio-risk", response_model=PortfolioRiskResponse)
def portfolio_risk(user_id: str, db: Session = Depends(get_db)) -> dict:
    profile, assessment = risk_service.score_portfolio(db, user_id)
    safe_cap = profile.avg_daily_income * DEFAULT_SAFE_PCT
    return {
        "user_id": user_id,
        "risk_level": assessment.risk_level,
        "reasons": assessment.reasons,
        "suggested_action": assessment.suggested_action,
        "avg_daily_income": profile.avg_daily_income,
        "safe_daily_cap": safe_cap,
        "total_daily_commitment": profile.total_daily_commitment,
        "buffer_days": assessment.buffer_days,
        "total_debits": assessment.debit_count,
        "total_skips": assessment.skip_count,
        "is_sustainable": assessment.is_sustainable,
    }
