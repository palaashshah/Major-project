from datetime import date

import pandas as pd
import pytest

from valuation.valuation import rebalancing_trades, value_portfolio


def prices():
    """Fund A doubles, fund B stays flat. No price on 3 Jan (a holiday)."""
    index = pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-05"])
    return pd.DataFrame({"A": [100.0, 150.0, 200.0], "B": [50.0, 50.0, 50.0]}, index=index)


def test_value_gain_and_drift():
    v = value_portfolio({"A": 0.5, "B": 0.5}, 100.0, prices(), date(2026, 1, 1))
    assert v.current_value == pytest.approx(150.0)      # A: 50 -> 100, B: 50 -> 50
    assert v.gain_pct == pytest.approx(0.5)
    a = next(h for h in v.holdings if h.ticker == "A")
    assert a.current_weight == pytest.approx(2 / 3)
    assert a.drift == pytest.approx(2 / 3 - 0.5)
    assert a.breached and v.rebalancing_suggested


def test_uses_last_price_on_or_before_the_investment_date():
    v = value_portfolio({"A": 1.0}, 100.0, prices(), date(2026, 1, 3))
    assert v.start_date == date(2026, 1, 2)
    assert v.current_value == pytest.approx(100.0 * 200 / 150)


def test_no_change_means_no_gain_and_no_alert():
    v = value_portfolio({"A": 0.5, "B": 0.5}, 100.0, prices(), date(2026, 1, 5))
    assert v.gain == pytest.approx(0.0)
    assert not v.rebalancing_suggested


def test_zero_weight_holdings_are_ignored():
    v = value_portfolio({"A": 1.0, "B": 0.0}, 100.0, prices(), date(2026, 1, 1))
    assert [h.ticker for h in v.holdings] == ["A"]


def test_rejects_dates_before_any_price():
    with pytest.raises(ValueError):
        value_portfolio({"A": 1.0}, 100.0, prices(), date(2025, 12, 1))

def test_cash_accrues_at_the_given_rate():
    index = pd.to_datetime(["2025-01-01", "2026-01-01"])          # 365 days apart
    flat = pd.DataFrame({"LIQUIDBEES.NS": [1000.0, 1000.0]}, index=index)
    v = value_portfolio({"LIQUIDBEES.NS": 1.0}, 100.0, flat, date(2025, 1, 1), cash_rate=0.05)
    assert v.current_value == pytest.approx(105.0)
    assert v.holdings[0].basis == "accrual"

def test_rebalancing_trades_restore_the_approved_weights():
    v = value_portfolio({"A": 0.5, "B": 0.5}, 100.0, prices(), date(2026, 1, 1))
    trades = {t.ticker: t for t in rebalancing_trades(v)}
    assert trades["A"].action == "sell" and trades["A"].amount == pytest.approx(25.0)   # 100 down to 75
    assert trades["B"].action == "buy" and trades["B"].amount == pytest.approx(25.0)    # 50 up to 75