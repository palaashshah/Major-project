"""
Runs the out-of-sample backtest on stored prices and saves the results.
Read-only for the database. Output goes to backend/backtest/output/.

Usage (from backend/):  python scripts/run_backtest.py
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd

from backtest.backtest import performance, simulate, split_prices
from config.risk_constraints import ASSETS, RISK_FREE_RATE
from data import compute_mean_and_cov, compute_monthly_returns
from database import SessionLocal
from models import MarketData
from optimizer.engine import InfeasiblePortfolioError, optimize_portfolio, portfolio_metrics
from scoring.scoring import constraints_for_score

REFERENCE_SCORES = (10, 30, 50, 70, 90)   # one per risk bucket
TEST_DAYS = 365
VOL_TOLERANCE = 0.01                      # realised volatility may exceed its cap by 1 point
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backtest", "output")


def load_prices() -> pd.DataFrame:
    tickers = [a.ticker for a in ASSETS]
    db = SessionLocal()
    try:
        rows = (
            db.query(MarketData.asset_symbol, MarketData.date, MarketData.close_price)
            .filter(MarketData.asset_symbol.in_(tickers))
            .all()
        )
    finally:
        db.close()
    if not rows:
        sys.exit("No stored prices. Run: python scripts/data.py")
    frame = pd.DataFrame(rows, columns=["ticker", "date", "price"])
    frame["price"] = frame["price"].astype(float)
    frame["date"] = pd.to_datetime(frame["date"])
    return frame.pivot(index="date", columns="ticker", values="price").sort_index()


def main():
    train, test = split_prices(load_prices(), TEST_DAYS)
    print(f"Estimation period: {train.index[0].date()} to {train.index[-1].date()} ({len(train)} days)")
    print(f"Test period:       {test.index[0].date()} to {test.index[-1].date()} ({len(test)} days)\n")

    mu, cov = compute_mean_and_cov(compute_monthly_returns(train))

    rows, weights, paths = [], {}, {}

    # 1. One optimized portfolio per reference score.
    for score in REFERENCE_SCORES:
        constraints = constraints_for_score(score, "long")
        label = f"Score {score} ({constraints.name})"
        try:
            result = optimize_portfolio(mu, cov, constraints)
        except InfeasiblePortfolioError as exc:
            print(f"{label}: no portfolio possible - {exc}")
            continue
        values = simulate(result.weights, test, cash_rate=RISK_FREE_RATE)
        realised = performance(values, RISK_FREE_RATE)
        rows.append({
            "portfolio": label,
            "expected_return": result.expected_return,
            "expected_volatility": result.volatility,
            "realised_return": realised["return"],
            "realised_volatility": realised["volatility"],
            "realised_sharpe": realised["sharpe"],
            "max_drawdown": realised["max_drawdown"],
            "volatility_cap": constraints.max_volatility,
        })
        weights[label], paths[label] = result.weights, values

    # 2. Two benchmarks that need no optimizer.
    tickers = list(mu.index)
    broad_equity = next(a.ticker for a in ASSETS if a.asset_class == "equity" and a.sector is None)
    debt = next(a.ticker for a in ASSETS if a.asset_class == "debt")
    benchmarks = {
        "Equal weight": {t: 1 / len(tickers) for t in tickers},
        "60/40 equity/debt": {broad_equity: 0.6, debt: 0.4},
    }
    for label, bench_weights in benchmarks.items():
        expected_return, expected_vol, _ = portfolio_metrics(pd.Series(bench_weights), mu, cov, RISK_FREE_RATE)
        values = simulate(bench_weights, test, cash_rate=RISK_FREE_RATE)
        realised = performance(values, RISK_FREE_RATE)
        rows.append({
            "portfolio": label,
            "expected_return": expected_return,
            "expected_volatility": expected_vol,
            "realised_return": realised["return"],
            "realised_volatility": realised["volatility"],
            "realised_sharpe": realised["sharpe"],
            "max_drawdown": realised["max_drawdown"],
            "volatility_cap": np.nan,
        })
        weights[label], paths[label] = bench_weights, values

    results = pd.DataFrame(rows).set_index("portfolio")

    # 3. Print.
    pd.set_option("display.width", 220)
    shown = results.copy()
    for column in shown.columns:
        if column != "realised_sharpe":
            shown[column] = (shown[column] * 100).round(2)
    shown["realised_sharpe"] = shown["realised_sharpe"].round(2)
    print("--- Results (percent, except Sharpe) ---")
    print(shown.to_string())
    print("\n--- Weights (percent) ---")
    print((pd.DataFrame(weights).fillna(0) * 100).round(1).to_string())

    # 4. Acceptance checks from the PRD.
    optimized = results[results["volatility_cap"].notna()]
    vols = optimized["realised_volatility"].tolist()
    rising = all(later >= earlier for earlier, later in zip(vols, vols[1:]))
    within = (optimized["realised_volatility"] <= optimized["volatility_cap"] + VOL_TOLERANCE).all()
    print("\n--- Acceptance checks ---")
    print(f"Realised volatility rises with the score:        {'PASS' if rising else 'FAIL'}")
    print(f"Realised volatility within cap (+{VOL_TOLERANCE:.0%} tolerance):  {'PASS' if within else 'FAIL'}")

    # 5. Save for the report.
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    results.to_csv(os.path.join(OUTPUT_DIR, "results.csv"))
    pd.DataFrame(weights).fillna(0).to_csv(os.path.join(OUTPUT_DIR, "weights.csv"))
    pd.DataFrame(paths).to_csv(os.path.join(OUTPUT_DIR, "value_paths.csv"))
    print(f"\nSaved results.csv, weights.csv and value_paths.csv to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()