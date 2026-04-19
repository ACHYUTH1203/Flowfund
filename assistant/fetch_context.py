"""NODE RESPONSIBILITY
Pull every piece of user data the assistant might need and pack it into the
state. We always fetch the user profile (scoped to demo_user for this
single-account prototype). If a loan_id is provided, we additionally fetch
that specific loan's details + risk score so the assistant can answer
questions about it.

Reads:  loan_id
Writes: db_context, user_profile, is_personal
Calls:  SQLite via app.services.{loan, risk, profile}
"""
from decimal import Decimal

from app.db.session import SessionLocal
from app.models.wallet import Wallet
from app.services import loan as loan_service
from app.services import profile as profile_service
from app.services import risk as risk_service
from app.services.profile import UserProfile
from assistant.state import AssistantState

DEMO_USER_ID = "demo_user"


def _serialise_profile(p: UserProfile) -> dict:
    return {
        "user_id": p.user_id,
        "wallet_balance": str(p.wallet_balance),
        "avg_daily_income": str(p.avg_daily_income),
        "total_daily_commitment": str(p.total_daily_commitment),
        "total_outstanding": str(p.total_outstanding),
        "total_debits": p.total_debits,
        "total_skips": p.total_skips,
        "overall_skip_rate": round(p.overall_skip_rate, 4),
        "has_defaulted_loan": p.has_defaulted_loan,
        "active_loans_count": len(p.active_loans),
        "closed_loans_count": len(p.closed_loans),
        "active_loans": [
            {
                "id": l.id,
                "amount": str(l.amount),
                "daily_repayment": str(l.daily_repayment),
                "repayment_type": l.repayment_type,
                "repayment_percentage": (
                    str(l.repayment_percentage) if l.repayment_percentage is not None else None
                ),
                "duration_days": l.duration_days,
                "status": l.status,
                "is_sustainable": l.is_sustainable,
                "paid": str(l.paid),
                "outstanding": str(l.outstanding),
                "debit_attempts": l.debit_attempts,
                "skip_count": l.skip_count,
                "skip_rate": round(l.skip_rate, 4),
            }
            for l in p.active_loans
        ],
    }


def run(state: AssistantState) -> dict:
    loan_id = state.get("loan_id")

    with SessionLocal() as db:
        profile = profile_service.get_profile(db, DEMO_USER_ID)
        profile_dict = _serialise_profile(profile)

        db_context: dict | None = None
        is_personal = False

        if loan_id is not None:
            try:
                loan, terms = loan_service.get_loan(db, loan_id)
                _, assessment = risk_service.score_loan(db, loan_id)
                wallet = db.get(Wallet, loan.wallet_id)
                db_context = {
                    "loan_id": loan.id,
                    "amount": str(loan.amount),
                    "daily_repayment": str(loan.daily_repayment),
                    "repayment_type": loan.repayment_type.value,
                    "repayment_percentage": (
                        str(loan.repayment_percentage)
                        if loan.repayment_percentage is not None
                        else None
                    ),
                    "avg_daily_income": str(loan.avg_daily_income),
                    "daily_expenses": str(loan.daily_expenses),
                    "duration_days": loan.duration_days,
                    "status": (
                        loan.status.value
                        if hasattr(loan.status, "value")
                        else str(loan.status)
                    ),
                    "is_sustainable": terms.is_sustainable,
                    "wallet_balance": str(wallet.balance) if wallet else "0",
                    "risk_level": assessment.risk_level,
                    "risk_reasons": list(assessment.reasons),
                    "buffer_days": assessment.buffer_days,
                }
                is_personal = True
            except Exception:
                is_personal = True

    return {
        "db_context": db_context,
        "user_profile": profile_dict,
        "is_personal": is_personal,
        "node_trail": ["fetch_context"],
    }
