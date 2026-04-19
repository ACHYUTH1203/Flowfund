"""Eligibility engine.

Pure rule-based pass/fail check for whether a user can take on a new loan,
based on their full profile (existing loans, payment history, outstanding
balance, wallet buffer) and the proposed loan terms.

Five rules, all must pass:
  1. income_coverage   - combined daily commitment stays within 30% of income
  2. wallet_buffer     - wallet has >= 3 x new daily repayment
  3. payment_history   - historical skip rate < 20% (skipped if < 3 debits)
  4. no_active_defaults - no existing loan currently in defaulted state
  5. outstanding_cap   - total outstanding principal <= 100 x avg daily income
"""
from dataclasses import dataclass
from decimal import ROUND_DOWN, Decimal

from sqlalchemy.orm import Session

from app.services.loan_simulator import DEFAULT_SAFE_PCT, compute_terms
from app.services.profile import UserProfile, get_profile

PAISE = Decimal("0.01")
BUFFER_DAYS_REQUIRED = 3
SKIP_RATE_THRESHOLD = 0.20
MIN_DEBITS_FOR_SKIP_CHECK = 3
OUTSTANDING_CAP_MULTIPLIER = 100


@dataclass(frozen=True)
class RuleResult:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class EligibilityDecision:
    eligible: bool
    rules: list[RuleResult]
    reasons_fail: list[str]
    proposed_daily_repayment: Decimal
    proposed_total_payable: Decimal
    suggested_max_amount: Decimal


def assess_eligibility(
    *,
    profile: UserProfile,
    amount: Decimal,
    duration_days: int,
    interest_rate: Decimal,
    repayment_type: str,
    repayment_percentage: Decimal | None,
    avg_daily_income: Decimal | None = None,
) -> EligibilityDecision:
    # Effective income: the caller can override; otherwise use what we know.
    avg_income = avg_daily_income if avg_daily_income is not None else profile.avg_daily_income
    if avg_income <= 0:
        avg_income = Decimal("1")  # avoids div-by-zero; income_coverage will fail

    terms = compute_terms(
        amount=amount,
        duration_days=duration_days,
        interest_rate=interest_rate,
        avg_daily_income=avg_income,
        repayment_type=repayment_type,
        repayment_percentage=repayment_percentage,
    )
    new_daily = terms.recommended_daily

    safe_daily_cap = avg_income * DEFAULT_SAFE_PCT
    combined_daily = new_daily + profile.total_daily_commitment

    rules: list[RuleResult] = []

    # 1. Income coverage
    rules.append(
        RuleResult(
            name="income_coverage",
            passed=combined_daily <= safe_daily_cap,
            detail=(
                f"combined daily commitment Rs {combined_daily:.2f} "
                f"vs safe cap Rs {safe_daily_cap:.2f} "
                f"(30% of income Rs {avg_income:.2f})"
            ),
        )
    )

    # 2. Wallet buffer
    required_buffer = new_daily * BUFFER_DAYS_REQUIRED
    rules.append(
        RuleResult(
            name="wallet_buffer",
            passed=profile.wallet_balance >= required_buffer,
            detail=(
                f"wallet has Rs {profile.wallet_balance:.2f}, "
                f"needs Rs {required_buffer:.2f} for a {BUFFER_DAYS_REQUIRED}-day buffer"
            ),
        )
    )

    # 3. Payment history (skip rate)
    if profile.total_debits >= MIN_DEBITS_FOR_SKIP_CHECK:
        rules.append(
            RuleResult(
                name="payment_history",
                passed=profile.overall_skip_rate < SKIP_RATE_THRESHOLD,
                detail=(
                    f"historical skip rate {profile.overall_skip_rate * 100:.0f}% "
                    f"(threshold {int(SKIP_RATE_THRESHOLD * 100)}%); "
                    f"{profile.total_skips} of {profile.total_debits} debits skipped"
                ),
            )
        )
    else:
        rules.append(
            RuleResult(
                name="payment_history",
                passed=True,
                detail=(
                    f"only {profile.total_debits} debits on record; "
                    "history signal is inconclusive"
                ),
            )
        )

    # 4. No active defaults
    rules.append(
        RuleResult(
            name="no_active_defaults",
            passed=not profile.has_defaulted_loan,
            detail=(
                "one or more loans currently in defaulted state"
                if profile.has_defaulted_loan
                else "no defaulted loans"
            ),
        )
    )

    # 5. Outstanding cap
    outstanding_cap = avg_income * OUTSTANDING_CAP_MULTIPLIER
    combined_outstanding = profile.total_outstanding + terms.total_payable
    rules.append(
        RuleResult(
            name="outstanding_cap",
            passed=combined_outstanding <= outstanding_cap,
            detail=(
                f"total outstanding Rs {combined_outstanding:.2f} "
                f"vs cap Rs {outstanding_cap:.2f} "
                f"({OUTSTANDING_CAP_MULTIPLIER}x daily income)"
            ),
        )
    )

    eligible = all(r.passed for r in rules)
    reasons_fail = [r.detail for r in rules if not r.passed]

    # Suggested max: the largest amount that would pass both the income
    # coverage and outstanding cap rules simultaneously.
    headroom_daily = max(Decimal("0"), safe_daily_cap - profile.total_daily_commitment)
    max_by_income = (
        headroom_daily * Decimal(duration_days) / (Decimal("1") + interest_rate)
    )
    headroom_outstanding = max(
        Decimal("0"), outstanding_cap - profile.total_outstanding
    )
    max_by_outstanding = headroom_outstanding / (Decimal("1") + interest_rate)

    suggested_max = min(max_by_income, max_by_outstanding).quantize(
        PAISE, rounding=ROUND_DOWN
    )

    return EligibilityDecision(
        eligible=eligible,
        rules=rules,
        reasons_fail=reasons_fail,
        proposed_daily_repayment=new_daily,
        proposed_total_payable=terms.total_payable,
        suggested_max_amount=suggested_max,
    )


def check_eligibility(
    db: Session,
    *,
    user_id: str,
    amount: Decimal,
    duration_days: int,
    interest_rate: Decimal,
    repayment_type: str,
    repayment_percentage: Decimal | None = None,
    avg_daily_income: Decimal | None = None,
) -> EligibilityDecision:
    profile = get_profile(db, user_id)
    return assess_eligibility(
        profile=profile,
        amount=amount,
        duration_days=duration_days,
        interest_rate=interest_rate,
        repayment_type=repayment_type,
        repayment_percentage=repayment_percentage,
        avg_daily_income=avg_daily_income,
    )
