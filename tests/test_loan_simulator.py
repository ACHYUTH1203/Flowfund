from decimal import Decimal

import pytest

from app.services.loan_simulator import build_schedule, compute_terms


class TestComputeTerms:
    def test_zero_interest(self):
        terms = compute_terms(
            amount=Decimal("10000"),
            duration_days=100,
            interest_rate=Decimal("0"),
            avg_daily_income=Decimal("1000"),
        )
        assert terms.total_payable == Decimal("10000.00")
        assert terms.base_daily == Decimal("100.00")
        assert terms.safe_daily == Decimal("300.00")
        assert terms.recommended_daily == Decimal("100.00")
        assert terms.is_sustainable is True
        assert terms.reason is None

    def test_flat_interest_applied(self):
        terms = compute_terms(
            amount=Decimal("10000"),
            duration_days=100,
            interest_rate=Decimal("0.10"),
            avg_daily_income=Decimal("1000"),
        )
        assert terms.total_payable == Decimal("11000.00")
        assert terms.base_daily == Decimal("110.00")
        assert terms.is_sustainable is True

    def test_unsustainable_flags_and_caps_recommended(self):
        # base_daily 200 vs safe_daily 30 -> recommend safe_daily, mark unsustainable
        terms = compute_terms(
            amount=Decimal("20000"),
            duration_days=100,
            interest_rate=Decimal("0"),
            avg_daily_income=Decimal("100"),
        )
        assert terms.base_daily == Decimal("200.00")
        assert terms.safe_daily == Decimal("30.00")
        assert terms.recommended_daily == Decimal("30.00")
        assert terms.is_sustainable is False
        assert terms.reason is not None
        assert "exceeds" in terms.reason

    def test_rounding_half_up_to_paise(self):
        # 1000 / 3 = 333.333... -> 333.33
        terms = compute_terms(
            amount=Decimal("1000"),
            duration_days=3,
            interest_rate=Decimal("0"),
            avg_daily_income=Decimal("10000"),
        )
        assert terms.base_daily == Decimal("333.33")

    def test_boundary_base_equals_safe_is_sustainable(self):
        # base_daily 300 == safe_daily 300 -> sustainable
        terms = compute_terms(
            amount=Decimal("30000"),
            duration_days=100,
            interest_rate=Decimal("0"),
            avg_daily_income=Decimal("1000"),
        )
        assert terms.base_daily == Decimal("300.00")
        assert terms.safe_daily == Decimal("300.00")
        assert terms.is_sustainable is True

    @pytest.mark.parametrize(
        "field,value,match",
        [
            ("amount", Decimal("0"), "amount"),
            ("duration_days", 0, "duration_days"),
            ("interest_rate", Decimal("-0.01"), "interest_rate"),
            ("avg_daily_income", Decimal("0"), "avg_daily_income"),
        ],
    )
    def test_invalid_inputs_raise(self, field, value, match):
        kwargs = dict(
            amount=Decimal("1000"),
            duration_days=10,
            interest_rate=Decimal("0"),
            avg_daily_income=Decimal("100"),
        )
        kwargs[field] = value
        with pytest.raises(ValueError, match=match):
            compute_terms(**kwargs)


class TestBuildSchedule:
    def test_all_paid_when_surplus_is_large(self):
        schedule = build_schedule(
            duration_days=5,
            avg_daily_income=Decimal("1000"),
            daily_repayment=Decimal("200"),
        )
        assert len(schedule) == 5
        assert all(d.status == "paid" for d in schedule)
        assert schedule[0].balance_after == Decimal("800.00")
        assert schedule[-1].balance_after == Decimal("4000.00")

    def test_all_missed_when_income_tiny(self):
        # Income 20, repayment 200, 5 days -> max balance 100, never enough.
        schedule = build_schedule(
            duration_days=5,
            avg_daily_income=Decimal("20"),
            daily_repayment=Decimal("200"),
        )
        assert all(d.status == "missed" for d in schedule)
        assert schedule[-1].balance_after == Decimal("100.00")

    def test_accumulates_then_pays(self):
        # Income 80, repayment 100:
        # d1: bal 80 < 100 -> missed, bal 80
        # d2: bal 160 >= 100 -> paid, bal 60
        # d3: bal 140 -> paid, bal 40
        # d4: bal 120 -> paid, bal 20
        # d5: bal 100 -> paid, bal 0
        schedule = build_schedule(
            duration_days=5,
            avg_daily_income=Decimal("80"),
            daily_repayment=Decimal("100"),
        )
        assert [d.status for d in schedule] == [
            "missed",
            "paid",
            "paid",
            "paid",
            "paid",
        ]
        assert schedule[-1].balance_after == Decimal("0.00")

    def test_expenses_reduce_net_surplus(self):
        # net surplus per day = 100 - 50 = 50, repayment 30 -> paid every day
        schedule = build_schedule(
            duration_days=3,
            avg_daily_income=Decimal("100"),
            daily_repayment=Decimal("30"),
            daily_expenses=Decimal("50"),
        )
        assert all(d.status == "paid" for d in schedule)
        assert schedule[-1].balance_after == Decimal("60.00")

    def test_expenses_can_make_schedule_stress(self):
        # net surplus 10/day, repayment 30/day
        # d1: bal 10 < 30 -> missed, bal 10
        # d2: bal 20 < 30 -> missed, bal 20
        # d3: bal 30 >= 30 -> paid, bal 0
        schedule = build_schedule(
            duration_days=3,
            avg_daily_income=Decimal("100"),
            daily_repayment=Decimal("30"),
            daily_expenses=Decimal("90"),
        )
        assert [d.status for d in schedule] == ["missed", "missed", "paid"]
        assert schedule[-1].balance_after == Decimal("0.00")

    def test_start_balance_carries_over(self):
        schedule = build_schedule(
            duration_days=1,
            avg_daily_income=Decimal("10"),
            daily_repayment=Decimal("50"),
            start_balance=Decimal("100"),
        )
        # day 1: bal 100 + 10 = 110, >= 50 -> paid, bal 60
        assert schedule[0].status == "paid"
        assert schedule[0].balance_after == Decimal("60.00")

    def test_zero_duration_raises(self):
        with pytest.raises(ValueError, match="duration_days"):
            build_schedule(
                duration_days=0,
                avg_daily_income=Decimal("100"),
                daily_repayment=Decimal("10"),
            )
