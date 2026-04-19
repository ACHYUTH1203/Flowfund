"""Wipe and seed the demo DB with a realistic 30-day history for a healthy
borrower.

Portfolio-first design:
  - Single user income: Rs 1,000/day
  - Two existing loans (one fixed-daily, one income-linked)
  - Combined daily commitment: Rs 208 (21% of income - well under the 30% cap)
  - 30 days of real simulated operation, including a 4-day shop closure
  - 100% reliability track record (the closure doesn't cause skips because
    the fixed loan is small and the income-linked loan auto-adjusts to 0
    on zero-income days)

This leaves meaningful headroom so the Loan Calculator's "Apply Now" flow
works end-to-end during the pitch demo.

Usage:
    poetry run python scripts/seed_demo.py
"""
import random
import sys
from decimal import Decimal
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.session import Base, SessionLocal, engine
import app.models  # noqa: F401
import assistant.conversation  # noqa: F401
from app.models.loan import IncomeType, Loan, RepaymentType
from app.services import loan as loan_service
from app.services import wallet as wallet_service

PAISE = Decimal("0.01")

USER_AVG_INCOME = Decimal("1000")

SIMULATION_DAYS = 30
SIM_SEED = 42
SIM_NOISE = Decimal("0.25")
CLOSURE_START_DAY = 3
CLOSURE_LENGTH = 4


def _rand_income(rng: random.Random) -> Decimal:
    low = float(Decimal("1") - SIM_NOISE)
    high = float(Decimal("1") + SIM_NOISE)
    return (USER_AVG_INCOME * Decimal(str(rng.uniform(low, high)))).quantize(PAISE)


def _income_for_day(day: int, rng: random.Random) -> Decimal:
    if CLOSURE_START_DAY <= day < CLOSURE_START_DAY + CLOSURE_LENGTH:
        return Decimal("0.00")
    return _rand_income(rng)


def simulate_operation(db, wallet_id: int, loans: list[Loan]) -> None:
    rng = random.Random(SIM_SEED)

    for day in range(SIMULATION_DAYS):
        today_income = _income_for_day(day, rng)

        if today_income > 0:
            wallet_service.add_funds(
                db,
                wallet_id=wallet_id,
                amount=today_income,
                idempotency_key=f"seed-day-{day}-income",
                note=f"Day {day + 1} shop earnings",
            )

        for loan in loans:
            if loan.repayment_type == RepaymentType.income_linked:
                assert loan.repayment_percentage is not None
                debit_amount = (today_income * loan.repayment_percentage).quantize(
                    PAISE
                )
                if debit_amount <= 0:
                    continue
            else:
                debit_amount = loan.daily_repayment

            wallet_service.debit(
                db,
                wallet_id=wallet_id,
                amount=debit_amount,
                idempotency_key=f"seed-day-{day}-loan-{loan.id}",
                loan_id=loan.id,
                note=f"Day {day + 1} debit for loan #{loan.id}",
            )


def main() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Dropped and recreated tables.")

    with SessionLocal() as db:
        wallet = wallet_service.create_wallet(db, user_id="demo_user")
        print(f"Created wallet #{wallet.id}")

        # Loan 1: fixed-daily Rs 8,000 over 100 days @10% -> Rs 88/day
        loan1, _, _ = loan_service.create_loan_with_simulation(
            db,
            user_id="demo_user",
            wallet_id=wallet.id,
            amount=Decimal("8000"),
            duration_days=100,
            interest_rate=Decimal("0.10"),
            income_type=IncomeType.fixed,
            avg_daily_income=USER_AVG_INCOME,
            daily_expenses=Decimal("0"),
            repayment_type=RepaymentType.fixed_daily,
        )
        print(f"Created loan #{loan1.id}: fixed-daily Rs 8000/100d @10% -> daily Rs {loan1.daily_repayment}")

        # Loan 2: income-linked at 12% of daily income -> ~Rs 120/day at avg
        loan2, _, _ = loan_service.create_loan_with_simulation(
            db,
            user_id="demo_user",
            wallet_id=wallet.id,
            amount=Decimal("6000"),
            duration_days=90,
            interest_rate=Decimal("0.05"),
            income_type=IncomeType.variable,
            avg_daily_income=USER_AVG_INCOME,
            daily_expenses=Decimal("0"),
            repayment_type=RepaymentType.income_linked,
            repayment_percentage=Decimal("0.12"),
        )
        print(f"Created loan #{loan2.id}: income-linked 12% (Rs 6000/90d @5%) -> daily Rs {loan2.daily_repayment}")

        loans = [loan1, loan2]
        total_daily = sum((l.daily_repayment for l in loans), Decimal("0"))
        safe_cap = USER_AVG_INCOME * Decimal("0.30")
        headroom = safe_cap - total_daily
        print(
            f"\nCombined daily commitment: Rs {total_daily} "
            f"({float(total_daily / USER_AVG_INCOME * 100):.0f}% of income). "
            f"Headroom: Rs {headroom}/day before the 30% cap."
        )

        print(
            f"\nSimulating {SIMULATION_DAYS} days of operation "
            f"(avg income Rs {USER_AVG_INCOME}, "
            f"{CLOSURE_LENGTH}-day closure starts day {CLOSURE_START_DAY + 1})..."
        )
        simulate_operation(db, wallet.id, loans)
        print("Simulation complete.")

        db.refresh(wallet)
        print(f"\nFinal wallet balance: Rs {wallet.balance}")
        print("\nSeed complete. Open http://127.0.0.1:5173/ - Apply Now flow is live.")


if __name__ == "__main__":
    main()
