from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

DEFAULT_SAFE_PCT = Decimal("0.30")
PAISE = Decimal("0.01")


def _round(value: Decimal) -> Decimal:
    return value.quantize(PAISE, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class LoanTerms:
    amount: Decimal
    duration_days: int
    interest_rate: Decimal
    total_payable: Decimal
    base_daily: Decimal
    safe_daily: Decimal
    recommended_daily: Decimal
    is_sustainable: bool
    reason: str | None
    repayment_type: str = "fixed_daily"
    repayment_percentage: Decimal | None = None


@dataclass(frozen=True)
class DaySchedule:
    day: int
    income: Decimal
    expenses: Decimal
    repayment: Decimal
    balance_after: Decimal
    status: str  # "paid" | "missed"


def compute_terms(
    amount: Decimal,
    duration_days: int,
    interest_rate: Decimal,
    avg_daily_income: Decimal,
    repayment_type: str = "fixed_daily",
    repayment_percentage: Decimal | None = None,
    safe_pct: Decimal = DEFAULT_SAFE_PCT,
) -> LoanTerms:
    if amount <= 0:
        raise ValueError("amount must be positive")
    if duration_days <= 0:
        raise ValueError("duration_days must be positive")
    if interest_rate < 0:
        raise ValueError("interest_rate must be >= 0")
    if avg_daily_income <= 0:
        raise ValueError("avg_daily_income must be positive")

    total_payable = _round(amount * (Decimal("1") + interest_rate))
    base_daily = _round(total_payable / Decimal(duration_days))
    safe_daily = _round(avg_daily_income * safe_pct)

    if repayment_type == "income_linked":
        if repayment_percentage is None:
            raise ValueError("repayment_percentage is required for income_linked")
        if repayment_percentage <= 0 or repayment_percentage > 1:
            raise ValueError("repayment_percentage must be in (0, 1]")

        expected_daily = _round(avg_daily_income * repayment_percentage)
        sustainable = repayment_percentage <= safe_pct

        if sustainable:
            return LoanTerms(
                amount=amount,
                duration_days=duration_days,
                interest_rate=interest_rate,
                total_payable=total_payable,
                base_daily=base_daily,
                safe_daily=safe_daily,
                recommended_daily=expected_daily,
                is_sustainable=True,
                reason=None,
                repayment_type="income_linked",
                repayment_percentage=repayment_percentage,
            )

        return LoanTerms(
            amount=amount,
            duration_days=duration_days,
            interest_rate=interest_rate,
            total_payable=total_payable,
            base_daily=base_daily,
            safe_daily=safe_daily,
            recommended_daily=safe_daily,
            is_sustainable=False,
            reason=(
                f"repayment_percentage {int(repayment_percentage * 100)}% "
                f"exceeds safe {int(safe_pct * 100)}% of income; "
                "consider a lower percentage"
            ),
            repayment_type="income_linked",
            repayment_percentage=repayment_percentage,
        )

    # fixed_daily (default)
    if base_daily <= safe_daily:
        return LoanTerms(
            amount=amount,
            duration_days=duration_days,
            interest_rate=interest_rate,
            total_payable=total_payable,
            base_daily=base_daily,
            safe_daily=safe_daily,
            recommended_daily=base_daily,
            is_sustainable=True,
            reason=None,
            repayment_type="fixed_daily",
        )

    return LoanTerms(
        amount=amount,
        duration_days=duration_days,
        interest_rate=interest_rate,
        total_payable=total_payable,
        base_daily=base_daily,
        safe_daily=safe_daily,
        recommended_daily=safe_daily,
        is_sustainable=False,
        reason=(
            f"base_daily {base_daily} exceeds safe_daily {safe_daily} "
            f"({int(safe_pct * 100)}% of income); consider a longer duration "
            "or a smaller amount"
        ),
        repayment_type="fixed_daily",
    )


def run_schedule(
    income_series: list[Decimal],
    daily_repayment: Decimal,
    daily_expenses: Decimal = Decimal("0"),
    start_balance: Decimal = Decimal("0"),
    repayment_series: list[Decimal] | None = None,
) -> list[DaySchedule]:
    """Run a day-by-day cash-flow simulation.

    If ``repayment_series`` is provided, it overrides ``daily_repayment`` and
    supplies a per-day amount (used for income-linked loans where the debit is
    a percentage of each day's income).
    """
    if not income_series:
        raise ValueError("income_series must not be empty")
    if repayment_series is not None and len(repayment_series) != len(income_series):
        raise ValueError("repayment_series must match income_series length")

    schedule: list[DaySchedule] = []
    balance = start_balance

    for day, income in enumerate(income_series, start=1):
        repayment_for_day = (
            repayment_series[day - 1] if repayment_series is not None else daily_repayment
        )
        balance = balance + income - daily_expenses
        if balance >= repayment_for_day:
            balance = balance - repayment_for_day
            status = "paid"
        else:
            status = "missed"

        schedule.append(
            DaySchedule(
                day=day,
                income=_round(income),
                expenses=_round(daily_expenses),
                repayment=_round(repayment_for_day),
                balance_after=_round(balance),
                status=status,
            )
        )

    return schedule


def build_schedule(
    duration_days: int,
    avg_daily_income: Decimal,
    daily_repayment: Decimal,
    daily_expenses: Decimal = Decimal("0"),
    start_balance: Decimal = Decimal("0"),
) -> list[DaySchedule]:
    if duration_days <= 0:
        raise ValueError("duration_days must be positive")
    return run_schedule(
        income_series=[avg_daily_income] * duration_days,
        daily_repayment=daily_repayment,
        daily_expenses=daily_expenses,
        start_balance=start_balance,
    )
