from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.loan import IncomeType, Loan, RepaymentType
from app.models.simulation import SimulationDay, SimulationRun
from app.models.wallet import Wallet
from app.services.loan_simulator import LoanTerms, build_schedule, compute_terms


def create_loan_with_simulation(
    db: Session,
    *,
    user_id: str,
    wallet_id: int,
    amount: Decimal,
    duration_days: int,
    interest_rate: Decimal,
    income_type: IncomeType,
    avg_daily_income: Decimal,
    daily_expenses: Decimal,
    repayment_type: RepaymentType = RepaymentType.fixed_daily,
    repayment_percentage: Decimal | None = None,
) -> tuple[Loan, SimulationRun, LoanTerms]:
    wallet = db.get(Wallet, wallet_id)
    if wallet is None:
        raise HTTPException(status_code=404, detail="Wallet not found")

    terms = compute_terms(
        amount=amount,
        duration_days=duration_days,
        interest_rate=interest_rate,
        avg_daily_income=avg_daily_income,
        repayment_type=repayment_type.value,
        repayment_percentage=repayment_percentage,
    )

    schedule = build_schedule(
        duration_days=duration_days,
        avg_daily_income=avg_daily_income,
        daily_repayment=terms.recommended_daily,
        daily_expenses=daily_expenses,
    )

    loan = Loan(
        user_id=user_id,
        wallet_id=wallet_id,
        amount=amount,
        duration_days=duration_days,
        interest_rate=interest_rate,
        daily_repayment=terms.recommended_daily,
        repayment_type=repayment_type,
        repayment_percentage=repayment_percentage,
        income_type=income_type,
        avg_daily_income=avg_daily_income,
        daily_expenses=daily_expenses,
    )
    db.add(loan)
    db.flush()

    run = SimulationRun(loan_id=loan.id, scenario="baseline", trials=1)
    db.add(run)
    db.flush()

    db.add_all(
        SimulationDay(
            run_id=run.id,
            day_index=d.day,
            income=d.income,
            repayment=d.repayment,
            balance_after=d.balance_after,
            missed=(d.status == "missed"),
        )
        for d in schedule
    )

    db.commit()
    db.refresh(loan)
    db.refresh(run)
    return loan, run, terms


def get_loan(db: Session, loan_id: int) -> tuple[Loan, LoanTerms]:
    loan = db.get(Loan, loan_id)
    if loan is None:
        raise HTTPException(status_code=404, detail="Loan not found")

    terms = compute_terms(
        amount=loan.amount,
        duration_days=loan.duration_days,
        interest_rate=loan.interest_rate,
        avg_daily_income=loan.avg_daily_income,
        repayment_type=loan.repayment_type.value,
        repayment_percentage=loan.repayment_percentage,
    )
    return loan, terms


def get_schedule(
    db: Session, loan_id: int
) -> tuple[SimulationRun, list[SimulationDay]]:
    loan = db.get(Loan, loan_id)
    if loan is None:
        raise HTTPException(status_code=404, detail="Loan not found")

    run = db.scalar(
        select(SimulationRun)
        .where(SimulationRun.loan_id == loan_id)
        .order_by(SimulationRun.id.desc())
        .limit(1)
    )
    if run is None:
        raise HTTPException(status_code=404, detail="No simulation run for this loan")

    days = list(
        db.scalars(
            select(SimulationDay)
            .where(SimulationDay.run_id == run.id)
            .order_by(SimulationDay.day_index)
        ).all()
    )
    return run, days
