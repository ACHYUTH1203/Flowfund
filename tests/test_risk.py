from decimal import Decimal

from app.services.risk import assess_risk


def _base(**overrides):
    defaults = dict(
        is_sustainable=True,
        balance=Decimal("1000"),
        daily_repayment=Decimal("100"),
        debit_count=0,
        skip_count=0,
    )
    defaults.update(overrides)
    return defaults


def test_all_healthy_returns_low():
    r = assess_risk(**_base())
    assert r.risk_level == "LOW"
    assert r.reasons == []
    assert r.suggested_action == "No action needed"


def test_unsustainable_flag_forces_high():
    r = assess_risk(**_base(is_sustainable=False))
    assert r.risk_level == "HIGH"
    assert any("30%" in reason for reason in r.reasons)


def test_low_buffer_medium():
    # 200 / 100 = 2 days (between 1 and 3)
    r = assess_risk(**_base(balance=Decimal("200")))
    assert r.risk_level == "MEDIUM"
    assert any("buffer" in reason.lower() for reason in r.reasons)
    # Action should suggest topping up to 3-day buffer: 300 - 200 = 100
    assert "100" in r.suggested_action


def test_buffer_below_one_day_is_high():
    # 50 / 100 = 0.5 days
    r = assess_risk(**_base(balance=Decimal("50")))
    assert r.risk_level == "HIGH"
    assert any("cannot cover" in reason.lower() for reason in r.reasons)


def test_buffer_at_three_days_is_low():
    # 300 / 100 = exactly 3 days - on the safe side of the threshold
    r = assess_risk(**_base(balance=Decimal("300")))
    assert r.risk_level == "LOW"


def test_skip_ratio_triggers_high():
    # 3 of 10 skipped = 30% >= 20%
    r = assess_risk(**_base(debit_count=10, skip_count=3))
    assert r.risk_level == "HIGH"
    assert any("skipped" in reason.lower() for reason in r.reasons)


def test_skip_ratio_below_threshold_stays_low():
    # 1 of 10 = 10% < 20%
    r = assess_risk(**_base(debit_count=10, skip_count=1))
    assert r.risk_level == "LOW"


def test_skip_signal_ignored_below_min_debits():
    # 50% skip rate but only 2 debits -> not enough data
    r = assess_risk(**_base(debit_count=2, skip_count=1))
    assert r.risk_level == "LOW"


def test_multiple_issues_accumulate_reasons():
    # unsustainable + low buffer + high skip ratio
    r = assess_risk(
        **_base(
            is_sustainable=False,
            balance=Decimal("50"),
            debit_count=10,
            skip_count=3,
        )
    )
    assert r.risk_level == "HIGH"
    assert len(r.reasons) == 3


def test_zero_repayment_gives_infinite_buffer():
    r = assess_risk(**_base(daily_repayment=Decimal("0")))
    assert r.risk_level == "LOW"
    assert r.buffer_days == float("inf")
