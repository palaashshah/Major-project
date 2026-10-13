"""
Paper valuation and drift for an accepted portfolio (PRD 5.8).

WHY: drift detection needs the portfolio re-priced on later data, and the
same calculation tells the manager what the holding is worth. Pure function:
the router loads the prices. No trades are placed anywhere.

Cash holdings: the liquid fund's stored price stays flat because its return
is not reflected in the price series. When a cash_rate is given, cash is
valued by accruing interest at that rate instead. This is a documented
assumption, and each holding reports which basis was used.
"""
from dataclasses import dataclass
from datetime import date
from typing import Optional

import pandas as pd

from config.risk_constraints import ASSETS, DRIFT_THRESHOLD

CASH_TICKERS = {a.ticker for a in ASSETS if a.asset_class == "cash"}


@dataclass(frozen=True)
class Holding:
    ticker: str
    target_weight: float     # the approved weight
    start_price: float
    latest_price: float
    value: float
    current_weight: float
    drift: float             # current weight minus approved weight
    breached: bool           # drift beyond the threshold
    basis: str               # "price" or "accrual"


@dataclass(frozen=True)
class Valuation:
    start_date: date         # the price date actually used for the investment
    as_of_date: date         # the latest price date available
    amount: float
    current_value: float
    gain: float
    gain_pct: float
    drift_threshold: float
    rebalancing_suggested: bool
    cash_rate: Optional[float]   # yearly rate used for cash accrual, if any
    holdings: list[Holding]


def value_portfolio(weights: dict, amount: float, prices: pd.DataFrame,
                    invested_on: date, threshold: float = DRIFT_THRESHOLD,
                    cash_rate: Optional[float] = None) -> Valuation:
    """prices: one row per date, one column per ticker (closing prices)."""
    held = {t: w for t, w in weights.items() if w > 0}
    missing = sorted(t for t in held if t not in prices.columns)
    if missing:
        raise ValueError(f"No stored prices for: {missing}")

    series = prices[list(held)].sort_index().ffill().dropna()
    before = series.loc[:pd.Timestamp(invested_on)]
    if before.empty:
        raise ValueError(f"No stored prices on or before {invested_on}.")

    start, latest = before.iloc[-1], series.iloc[-1]
    days_held = (series.index[-1] - before.index[-1]).days

    growth, basis = {}, {}
    for ticker in held:
        if cash_rate is not None and ticker in CASH_TICKERS:
            growth[ticker] = (1 + cash_rate) ** (days_held / 365)
            basis[ticker] = "accrual"
        else:
            growth[ticker] = float(latest[ticker] / start[ticker])
            basis[ticker] = "price"

    values = {t: amount * w * growth[t] for t, w in held.items()}
    total = sum(values.values())

    holdings = []
    for ticker, target in held.items():
        current = values[ticker] / total
        drift = current - target
        holdings.append(Holding(
            ticker=ticker, target_weight=target,
            start_price=float(start[ticker]), latest_price=float(latest[ticker]),
            value=values[ticker], current_weight=current, drift=drift,
            breached=abs(drift) > threshold, basis=basis[ticker]))
    holdings.sort(key=lambda h: (-h.value, h.ticker))

    return Valuation(
        start_date=before.index[-1].date(),
        as_of_date=series.index[-1].date(),
        amount=amount,
        current_value=total,
        gain=total - amount,
        gain_pct=(total - amount) / amount,
        drift_threshold=threshold,
        rebalancing_suggested=any(h.breached for h in holdings),
        cash_rate=cash_rate,
        holdings=holdings,
    )

@dataclass(frozen=True)
class Trade:
    ticker: str
    action: str              # "buy" or "sell"
    amount: float            # rupees
    current_weight: float
    target_weight: float


def rebalancing_trades(valuation: Valuation, minimum: float = 1.0) -> list[Trade]:
    """What to buy and sell to return each holding to its approved weight.
    Trades smaller than `minimum` rupees are left out."""
    trades = []
    for holding in valuation.holdings:
        difference = valuation.current_value * holding.target_weight - holding.value
        if abs(difference) < minimum:
            continue
        trades.append(Trade(
            ticker=holding.ticker,
            action="buy" if difference > 0 else "sell",
            amount=abs(difference),
            current_weight=holding.current_weight,
            target_weight=holding.target_weight))
    trades.sort(key=lambda t: (-t.amount, t.ticker))
    return trades