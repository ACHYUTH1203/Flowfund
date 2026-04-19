from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.loan import Loan
from app.models.transaction import Transaction, TxnStatus, TxnType
from app.models.wallet import Wallet
from app.services.loan_simulator import DEFAULT_SAFE_PCT, compute_terms
from app.services.profile import UserProfile, get_profile

PAISE = Decimal("0.01")
BUFFER_DAYS_THRESHOLD = 3
SKIP_RATIO_THRESHOLD = Decimal("0.20")
MIN_DEBITS_FOR_SKIP_SIGNAL = 3

RiskLevel = Literal["LOW", "MEDIUM", "HIGH"]
_LEVELS: tuple[RiskLevel, RiskLevel, RiskLevel] = ("LOW", "MEDIUM", "HIGH")


@dataclass(frozen=True)
class RiskAssessment:
    risk_level: RiskLevel
    reasons: list[str] = field(default_factory=list)
    suggested_action: str = ""
    buffer_days: float = 0.0
    skip_count: int = 0
    debit_count: int = 0
    is_sustainable: bool = True


def assess_risk(
    *,
    is_sustainable: bool,
    balance: Decimal,
    daily_repayment: Decimal,
    debit_count: int,
    skip_count: int,
) -> RiskAssessment:
    reasons: list[str] = []
    severity = 0  # 0=LOW, 1=MEDIUM, 2=HIGH

    if not is_sustainable:
        reasons.append(
            "Loan exceeds safe daily repayment threshold (30% of income)"
        )
        severity = max(severity, 2)

    buffer_days = (
        float(balance / daily_repayment) if daily_repayment > 0 else float("inf")
    )

    if buffer_days < 1:
        reasons.append("Wallet cannot cover the next scheduled debit")
        severity = max(severity, 2)
    elif buffer_days < BUFFER_DAYS_THRESHOLD:
        reasons.append(
            f"Wallet buffer only {buffer_days:.1f} days "
            f"(below {BUFFER_DAYS_THRESHOLD}-day minimum)"
        )
        severity = max(severity, 1)

    if debit_count >= MIN_DEBITS_FOR_SKIP_SIGNAL:
        skip_ratio = Decimal(skip_count) / Decimal(debit_count)
        if skip_ratio >= SKIP_RATIO_THRESHOLD:
            reasons.append(
                f"{skip_count} of {debit_count} recent debits were skipped"
            )
            severity = max(severity, 2)

    risk_level = _LEVELS[severity]

    if severity == 0:
        suggested_action = "No action needed"
    elif daily_repayment > 0 and buffer_days < BUFFER_DAYS_THRESHOLD:
        required = (
            daily_repayment * BUFFER_DAYS_THRESHOLD - balance
        ).quantize(PAISE, rounding=ROUND_HALF_UP)
        suggested_action = (
            f"Add Rs {required} to wallet to reach a {BUFFER_DAYS_THRESHOLD}-day buffer"
            if required > 0
            else "Review loan terms"
        )
    else:
        suggested_action = (
            "Review loan terms; consider a longer duration or smaller amount"
        )

    return RiskAssessment(
        risk_level=risk_level,
        reasons=reasons,
        suggested_action=suggested_action,
        buffer_days=buffer_days,
        skip_count=skip_count,
        debit_count=debit_count,
        is_sustainable=is_sustainable,
    )


def score_loan(db: Session, loan_id: int) -> tuple[Loan, RiskAssessment]:
    loan = db.get(Loan, loan_id)
    if loan is None:
        raise HTTPException(status_code=404, detail="Loan not found")

    wallet = db.get(Wallet, loan.wallet_id)
    if wallet is None:
        raise HTTPException(status_code=500, detail="Loan's wallet missing")

    terms = compute_terms(
        amount=loan.amount,
        duration_days=loan.duration_days,
        interest_rate=loan.interest_rate,
        avg_daily_income=loan.avg_daily_income,
        repayment_type=loan.repayment_type.value,
        repayment_percentage=loan.repayment_percentage,
    )

    debit_count = db.scalar(
        select(func.count(Transaction.id))
        .where(Transaction.wallet_id == loan.wallet_id)
        .where(Transaction.type == TxnType.debit)
    ) or 0

    skip_count = db.scalar(
        select(func.count(Transaction.id))
        .where(Transaction.wallet_id == loan.wallet_id)
        .where(Transaction.type == TxnType.debit)
        .where(Transaction.status == TxnStatus.skipped)
    ) or 0

    assessment = assess_risk(
        is_sustainable=terms.is_sustainable,
        balance=wallet.balance,
        daily_repayment=loan.daily_repayment,
        debit_count=debit_count,
        skip_count=skip_count,
    )
    return loan, assessment


# ---------- PORTFOLIO-LEVEL RISK (Stage 10) ----------
#
# The portfolio engine evaluates the user as a whole, not each loan in
# isolation. Every rule operates on the aggregate profile: total daily
# commitment across ALL active loans, the user's one wallet balance, the
# overall skip rate, and the presence of any defaulted loan.


def assess_portfolio_risk(profile: UserProfile) -> RiskAssessment:
    reasons: list[str] = []
    severity = 0

    avg_income = profile.avg_daily_income if profile.avg_daily_income > 0 else Decimal("1")
    safe_cap = (avg_income * DEFAULT_SAFE_PCT).quantize(PAISE, rounding=ROUND_HALF_UP)
    commitment = profile.total_daily_commitment

    # Rule 1: combined income coverage (the 30% rule applied to the whole portfolio)
    over_committed = commitment > safe_cap
    if over_committed:
        pct = (commitment / avg_income * Decimal("100")).quantize(Decimal("1"))
        reasons.append(
            f"Combined daily commitment Rs {commitment} is {pct}% of income, "
            f"over the 30% safe cap of Rs {safe_cap}"
        )
        severity = max(severity, 2)

    # Rule 2: wallet buffer against TOTAL daily commitment
    if commitment > 0:
        buffer_days = float(profile.wallet_balance / commitment)
    else:
        buffer_days = float("inf")

    if buffer_days < 1:
        reasons.append(
            "Wallet cannot cover even tomorrow's combined debits"
        )
        severity = max(severity, 2)
    elif buffer_days < BUFFER_DAYS_THRESHOLD:
        reasons.append(
            f"Wallet buffer only {buffer_days:.1f} days for combined debits "
            f"(below {BUFFER_DAYS_THRESHOLD}-day target)"
        )
        severity = max(severity, 1)

    # Rule 3: aggregate skip rate across all loans
    if profile.total_debits >= MIN_DEBITS_FOR_SKIP_SIGNAL:
        ratio = Decimal(profile.total_skips) / Decimal(profile.total_debits)
        if ratio >= SKIP_RATIO_THRESHOLD:
            reasons.append(
                f"Aggregate skip rate {profile.total_skips}/{profile.total_debits} "
                f"= {float(ratio * 100):.0f}%"
            )
            severity = max(severity, 2)

    # Rule 4: any active defaulted loan
    if profile.has_defaulted_loan:
        reasons.append("One or more active loans are in defaulted state")
        severity = max(severity, 2)

    risk_level = _LEVELS[severity]

    # Suggested action
    if severity == 0:
        suggested_action = "No action needed"
    elif over_committed:
        overage = (commitment - safe_cap).quantize(PAISE, rounding=ROUND_HALF_UP)
        suggested_action = (
            f"Your portfolio commits Rs {commitment}/day (Rs {overage} over "
            f"the Rs {safe_cap}/day cap). Close or restructure loans to fit "
            f"inside the 30% cap."
        )
    elif buffer_days < BUFFER_DAYS_THRESHOLD:
        target = (commitment * BUFFER_DAYS_THRESHOLD).quantize(
            PAISE, rounding=ROUND_HALF_UP
        )
        needed = max(Decimal("0"), target - profile.wallet_balance).quantize(
            PAISE, rounding=ROUND_HALF_UP
        )
        if needed > 0:
            suggested_action = (
                f"Add Rs {needed} to wallet to reach a {BUFFER_DAYS_THRESHOLD}-day "
                f"buffer for the combined Rs {commitment}/day commitment"
            )
        else:
            suggested_action = "Review portfolio health"
    else:
        suggested_action = "Review portfolio health"

    return RiskAssessment(
        risk_level=risk_level,
        reasons=reasons,
        suggested_action=suggested_action,
        buffer_days=buffer_days,
        skip_count=profile.total_skips,
        debit_count=profile.total_debits,
        is_sustainable=not over_committed,
    )


def score_portfolio(
    db: Session, user_id: str
) -> tuple[UserProfile, RiskAssessment]:
    profile = get_profile(db, user_id)
    assessment = assess_portfolio_risk(profile)
    return profile, assessment
