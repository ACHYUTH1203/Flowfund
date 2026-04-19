"""User profile aggregator.

Given a user_id, assembles every signal we have on that user into a single
structure: wallet state, all loans with per-loan paid/outstanding/skip stats,
aggregate payment history, and derived flags (has_defaulted_loan, etc).

This is the common input to the eligibility engine and the chat assistant.
"""
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.loan import Loan
from app.models.transaction import Transaction, TxnStatus, TxnType
from app.models.wallet import Wallet
from app.services.loan_simulator import compute_terms


@dataclass(frozen=True)
class LoanStats:
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


@dataclass(frozen=True)
class UserProfile:
    user_id: str
    wallet_id: int | None
    wallet_balance: Decimal
    active_loans: list[LoanStats]
    closed_loans: list[LoanStats]
    total_daily_commitment: Decimal
    total_outstanding: Decimal
    total_debits: int
    total_skips: int
    overall_skip_rate: float
    avg_daily_income: Decimal
    has_defaulted_loan: bool


def _loan_stats(db: Session, loan: Loan) -> LoanStats:
    debits = list(
        db.scalars(
            select(Transaction)
            .where(Transaction.loan_id == loan.id)
            .where(Transaction.type == TxnType.debit)
        ).all()
    )
    attempts = len(debits)
    skips = sum(1 for t in debits if t.status == TxnStatus.skipped)
    paid = sum(
        (t.amount for t in debits if t.status == TxnStatus.success), Decimal("0")
    )

    terms = compute_terms(
        amount=loan.amount,
        duration_days=loan.duration_days,
        interest_rate=loan.interest_rate,
        avg_daily_income=loan.avg_daily_income,
        repayment_type=loan.repayment_type.value,
        repayment_percentage=loan.repayment_percentage,
    )
    outstanding = max(Decimal("0"), terms.total_payable - paid)
    skip_rate = (skips / attempts) if attempts > 0 else 0.0

    return LoanStats(
        id=loan.id,
        amount=loan.amount,
        daily_repayment=loan.daily_repayment,
        repayment_type=loan.repayment_type.value,
        repayment_percentage=loan.repayment_percentage,
        duration_days=loan.duration_days,
        status=loan.status.value,
        is_sustainable=terms.is_sustainable,
        avg_daily_income=loan.avg_daily_income,
        paid=paid,
        outstanding=outstanding,
        debit_attempts=attempts,
        skip_count=skips,
        skip_rate=skip_rate,
    )


def get_profile(db: Session, user_id: str) -> UserProfile:
    wallet = db.scalar(select(Wallet).where(Wallet.user_id == user_id))

    loans = list(
        db.scalars(
            select(Loan).where(Loan.user_id == user_id).order_by(Loan.id)
        ).all()
    )

    stats = [_loan_stats(db, loan) for loan in loans]
    active = [s for s in stats if s.status == "active"]
    closed = [s for s in stats if s.status != "active"]

    total_daily = sum(
        (s.daily_repayment for s in active), Decimal("0")
    )
    total_outstanding = sum(
        (s.outstanding for s in active), Decimal("0")
    )
    total_debits = sum(s.debit_attempts for s in stats)
    total_skips = sum(s.skip_count for s in stats)
    overall_skip_rate = (
        (total_skips / total_debits) if total_debits > 0 else 0.0
    )

    # Most recent active loan's avg_income is the best estimate of "current"
    # income we have on file. Fall back to most recent closed loan, then 0.
    avg_income = Decimal("0")
    active_loans_full = [l for l in loans if l.status.value == "active"]
    if active_loans_full:
        avg_income = active_loans_full[-1].avg_daily_income
    elif loans:
        avg_income = loans[-1].avg_daily_income

    has_default = any(l.status.value == "defaulted" for l in loans)

    return UserProfile(
        user_id=user_id,
        wallet_id=wallet.id if wallet else None,
        wallet_balance=wallet.balance if wallet else Decimal("0"),
        active_loans=active,
        closed_loans=closed,
        total_daily_commitment=total_daily,
        total_outstanding=total_outstanding,
        total_debits=total_debits,
        total_skips=total_skips,
        overall_skip_rate=overall_skip_rate,
        avg_daily_income=avg_income,
        has_defaulted_loan=has_default,
    )
