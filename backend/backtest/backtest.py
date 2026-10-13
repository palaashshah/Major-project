"""
Out-of-sample backtest building blocks (PRD section 10).

WHY: everything the optimizer reports is in-sample. The backtest estimates on
an earlier period, then measures what each portfolio actually did in a later
period the optimizer never saw. Pure functions: the script loads the prices.
"""
import numpy as np
import pandas as pd

from config.risk_constraints import ASSETS

CASH_TICKERS = {a.ticker for a in ASSETS if a.asset_class == "cash"}


def split_prices(prices: pd.DataFrame, test_days: int = 365):
    """Split daily prices into an estimation period and a test period.
    The test period starts on the last estimation day, which is the purchase date."""
    prices = prices.sort_index().ffill().dropna()
    cutoff = prices.index[-1] - pd.Timedelta(days=test_days)
    train = prices.loc[:cutoff]
    test = prices.loc[train.index[-1]:]
    return train, test


def simulate(weights: dict, test: pd.DataFrame, cash_rate=None) -> pd.Series:
    """Value of 1 rupee invested on the first test day and left alone (buy and hold).
    Cash holdings grow at cash_rate when it is given, since their stored price is flat."""
    held = {t: w for t, w in weights.items() if w > 0}
    tickers = list(held)
    growth = test[tickers] / test[tickers].iloc[0]
    if cash_rate is not None:
        days = np.asarray((test.index - test.index[0]).days, dtype=float)
        for ticker in tickers:
            if ticker in CASH_TICKERS:
                growth[ticker] = (1 + cash_rate) ** (days / 365)
    return (growth * pd.Series(held)).sum(axis=1)


def performance(values: pd.Series, rf: float) -> dict:
    """Realised yearly return, volatility, Sharpe ratio and maximum drawdown."""
    days = (values.index[-1] - values.index[0]).days
    total = values.iloc[-1] / values.iloc[0] - 1
    yearly = (1 + total) ** (365 / days) - 1
    daily = values.pct_change().dropna()
    volatility = float(daily.std() * np.sqrt(252))      # 252 trading days in a year
    sharpe = (yearly - rf) / volatility if volatility > 0 else 0.0
    drawdown = float((values / values.cummax() - 1).min())   # worst fall from a peak
    return {"return": float(yearly), "volatility": volatility,
            "sharpe": float(sharpe), "max_drawdown": drawdown}

def walk_forward_windows(prices: pd.DataFrame, n_tests: int = 3, test_days: int = 365):
    """Several (estimation, test) pairs, oldest first. Each test year follows
    the previous one, and each is estimated on all the data before it."""
    prices = prices.sort_index().ffill().dropna()
    last = prices.index[-1]
    windows = []
    for k in reversed(range(n_tests)):
        test_end = last - pd.Timedelta(days=k * test_days)
        test_start = test_end - pd.Timedelta(days=test_days)
        train = prices.loc[:test_start]
        test = prices.loc[train.index[-1]:test_end]
        windows.append((train, test))
    return windows


def expected_volatility_daily(weights: dict, train: pd.DataFrame) -> float:
    """Expected volatility measured from daily returns, the same way realised
    volatility is measured, so the two can be compared like for like."""
    held = {t: w for t, w in weights.items() if w > 0}
    tickers = list(held)
    daily_cov = train[tickers].pct_change().dropna().cov().to_numpy() * 252
    w = np.array([held[t] for t in tickers])
    return float(np.sqrt(w @ daily_cov @ w))