import pandas as pd
import pytest

from backtest.backtest import performance, simulate, split_prices, walk_forward_windows


def test_split_puts_the_purchase_day_in_both_periods():
    index = pd.date_range("2024-01-01", periods=800, freq="D")
    prices = pd.DataFrame({"A": range(1, 801)}, index=index, dtype=float)
    train, test = split_prices(prices, test_days=365)
    assert test.index[0] == train.index[-1]
    assert (test.index[-1] - test.index[0]).days == 365


def test_simulate_is_a_weighted_mix():
    index = pd.to_datetime(["2025-01-01", "2025-07-01", "2026-01-01"])
    test = pd.DataFrame({"A": [100.0, 150.0, 200.0], "B": [50.0, 50.0, 50.0]}, index=index)
    values = simulate({"A": 0.5, "B": 0.5}, test)
    assert values.iloc[0] == pytest.approx(1.0)
    assert values.iloc[-1] == pytest.approx(1.5)


def test_cash_grows_at_the_given_rate():
    index = pd.to_datetime(["2025-01-01", "2025-07-01", "2026-01-01"])   # 365 days
    test = pd.DataFrame({"LIQUIDBEES.NS": [1000.0, 1000.0, 1000.0]}, index=index)
    values = simulate({"LIQUIDBEES.NS": 1.0}, test, cash_rate=0.05)
    assert values.iloc[-1] == pytest.approx(1.05)


def test_performance_return_and_drawdown():
    index = pd.to_datetime(["2025-01-01", "2025-05-01", "2025-09-01", "2026-01-01"])
    values = pd.Series([100.0, 120.0, 102.0, 110.0], index=index)
    result = performance(values, rf=0.05)
    assert result["return"] == pytest.approx(0.10)
    assert result["max_drawdown"] == pytest.approx(102 / 120 - 1)   # 120 down to 102 is -15%

def test_walk_forward_windows_follow_one_another():
    index = pd.date_range("2021-01-01", periods=1900, freq="D")
    prices = pd.DataFrame({"A": range(1, 1901)}, index=index, dtype=float)
    windows = walk_forward_windows(prices, n_tests=3, test_days=365)
    assert len(windows) == 3
    for train, test in windows:
        assert test.index[0] == train.index[-1]          # bought on the last estimation day
        assert (test.index[-1] - test.index[0]).days == 365
    assert windows[0][1].index[-1] == windows[1][1].index[0]   # one test year ends where the next starts
    assert windows[-1][1].index[-1] == index[-1]