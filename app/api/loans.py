from dataclasses import asdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.eligibility import EligibilityRequest, EligibilityResponse
from app.schemas.loan import (
    LoanCreate,
    LoanCreateResponse,
    LoanDetailResponse,
    ScheduleResponse,
)
from app.schemas.risk import RiskScoreResponse
from app.services import eligibility as eligibility_service
from app.services import loan as loan_service
from app.services import risk as risk_service

router = APIRouter(prefix="/loans", tags=["loans"])


@router.post("/eligibility", response_model=EligibilityResponse)
def check_eligibility(
    payload: EligibilityRequest,
    db: Session = Depends(get_db),
) -> dict:
    decision = eligibility_service.check_eligibility(
        db,
        user_id=payload.user_id,
        amount=payload.amount,
        duration_days=payload.duration_days,
        interest_rate=payload.interest_rate,
        repayment_type=payload.repayment_type.value,
        repayment_percentage=payload.repayment_percentage,
        avg_daily_income=payload.avg_daily_income,
    )
    return {
        "eligible": decision.eligible,
        "rules": [asdict(r) for r in decision.rules],
        "reasons_fail": decision.reasons_fail,
        "proposed_daily_repayment": decision.proposed_daily_repayment,
        "proposed_total_payable": decision.proposed_total_payable,
        "suggested_max_amount": decision.suggested_max_amount,
    }


@router.post("", response_model=LoanCreateResponse, status_code=201)
def create_loan(payload: LoanCreate, db: Session = Depends(get_db)) -> dict:
    loan, run, terms = loan_service.create_loan_with_simulation(
        db,
        user_id=payload.user_id,
        wallet_id=payload.wallet_id,
        amount=payload.amount,
        duration_days=payload.duration_days,
        interest_rate=payload.interest_rate,
        income_type=payload.income_type,
        avg_daily_income=payload.avg_daily_income,
        daily_expenses=payload.daily_expenses,
        repayment_type=payload.repayment_type,
        repayment_percentage=payload.repayment_percentage,
    )
    return {"loan": loan, "terms": terms, "simulation_run_id": run.id}


@router.get("/{loan_id}", response_model=LoanDetailResponse)
def get_loan(loan_id: int, db: Session = Depends(get_db)) -> dict:
    loan, terms = loan_service.get_loan(db, loan_id)
    return {"loan": loan, "terms": terms}


@router.get("/{loan_id}/schedule", response_model=ScheduleResponse)
def get_schedule(loan_id: int, db: Session = Depends(get_db)) -> dict:
    run, days = loan_service.get_schedule(db, loan_id)
    missed_count = sum(1 for d in days if d.missed)
    return {
        "loan_id": loan_id,
        "run_id": run.id,
        "total_days": len(days),
        "missed_count": missed_count,
        "days": days,
    }


@router.get("/{loan_id}/risk-score", response_model=RiskScoreResponse)
def get_risk_score(loan_id: int, db: Session = Depends(get_db)) -> dict:
    loan, assessment = risk_service.score_loan(db, loan_id)
    return {
        "loan_id": loan.id,
        "risk_level": assessment.risk_level,
        "reasons": assessment.reasons,
        "suggested_action": assessment.suggested_action,
        "buffer_days": assessment.buffer_days,
        "skip_count": assessment.skip_count,
        "debit_count": assessment.debit_count,
        "is_sustainable": assessment.is_sustainable,
    }
