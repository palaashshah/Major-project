"""
Multi-year (walk-forward) backtest with rule variants.

Each test year is estimated only on data before it. The earlier test years
are for TUNING: compare the variants there and pick one. The last test year
is the FINAL check: read it once, after choosing.
Read-only for the database. Output goes to backend/backtest/output/.

Usage (from backend/):  python scripts/run_walk_forward.py
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd

from backtest.backtest import (
    expected_volatility_daily, performance, simulate, walk_forward_windows,
)
from config.risk_constraints import ASSETS, RISK_FREE_RATE
from data import compute_mean_and_cov, compute_monthly_returns
from database import SessionLocal
from models import MarketData
from optimizer.engine import InfeasiblePortfolioError, optimize_portfolio
from scoring.scoring import constraints_for_score

REFERENCE_SCORES = (10, 30, 50, 70, 90)
N_TEST_YEARS = 3
TEST_DAYS = 365
HURDLE = 0.08                 # shown for information only
VOL_TOLERANCE = 0.01          # realised volatility may exceed its cap by 2 points

NIFTY = next(a.ticker for a in ASSETS if a.asset_class == "equity" and a.sector is None)
DEBT = next(a.ticker for a in ASSETS if a.asset_class == "debt")
GOLD = next(a.ticker for a in ASSETS if a.asset_class == "gold")

# Rule variants to compare: name -> per-instrument caps.
VARIANTS = {
    "A. gold up to 35% (current)": {},
    "B. gold capped at 30%": {GOLD: 0.30},
    "C. gold capped at 25%": {GOLD: 0.25},
    "D. gold capped at 20%": {GOLD: 0.20},
}

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backtest", "output")
RESULT_COLUMNS = [
    "expected_return", "expected_volatility_monthly_basis", "expected_volatility_daily_basis",
    "realised_return", "realised_volatility", "realised_sharpe", "max_drawdown", "gold_weight", "note",
]


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


def year_label(test: pd.DataFrame) -> str:
    return f"{test.index[0].year}-{str(test.index[-1].year)[2:]}"


def summarise(rows: pd.DataFrame) -> dict:
    """Acceptance checks and gaps for one variant over a set of test years."""
    order_ok, n_years = 0, 0
    for _, group in rows.groupby("year"):
        vols = group.sort_values("score")["realised_volatility"].tolist()
        n_years += 1
        if not any(pd.isna(vols)) and all(b >= a for a, b in zip(vols, vols[1:])):
            order_ok += 1
    valid = rows.dropna(subset=["realised_volatility"])
    within = int((valid["realised_volatility"] <= valid["volatility_cap"] + VOL_TOLERANCE).sum())
    gap = (valid["realised_volatility"] - valid["expected_volatility_daily_basis"]).mean()
    return {
        "risk rises with score": f"{order_ok}/{n_years} years",
        "within volatility cap": f"{within}/{len(rows)}",
        "avg volatility surprise": f"{gap * 100:+.1f} pts" if pd.notna(gap) else "n/a",
    }


def main():
    windows = walk_forward_windows(load_prices(), N_TEST_YEARS, TEST_DAYS)
    labels = [year_label(test) for _, test in windows]
    final = labels[-1]

    print("Test years (each is estimated only on data before it):")
    for (train, test), label in zip(windows, labels):
        role = "FINAL CHECK" if label == final else "tuning"
        print(f"  {label}: estimated on {train.index[0].date()} to {train.index[-1].date()}, "
              f"tested to {test.index[-1].date()}   [{role}]")

    records, bench_records = [], []
    for (train, test), label in zip(windows, labels):
        mu, cov = compute_mean_and_cov(compute_monthly_returns(train))

        benchmarks = {
            "Nifty 50 (NIFTYBEES)": {NIFTY: 1.0},
            "Equal weight": {t: 1 / len(mu) for t in mu.index},
            "60/40 equity/debt": {NIFTY: 0.6, DEBT: 0.4},
        }
        for name, bench_weights in benchmarks.items():
            perf = performance(simulate(bench_weights, test, cash_rate=RISK_FREE_RATE), RISK_FREE_RATE)
            bench_records.append({"year": label, "portfolio": name, **perf})
        nifty_return = bench_records[-3]["return"]

        for variant, caps in VARIANTS.items():
            for score in REFERENCE_SCORES:
                constraints = constraints_for_score(score, "long")
                row = {"variant": variant, "year": label, "score": score, "bucket": constraints.name,
                       "volatility_cap": constraints.max_volatility, "nifty_return": nifty_return}
                try:
                    result = optimize_portfolio(mu, cov, constraints, asset_caps=caps)
                except InfeasiblePortfolioError as exc:
                    row["note"] = f"no portfolio possible: {exc}"
                    records.append(row)
                    continue
                perf = performance(simulate(result.weights, test, cash_rate=RISK_FREE_RATE), RISK_FREE_RATE)
                row.update({
                    "expected_return": result.expected_return,
                    "expected_volatility_monthly_basis": result.volatility,
                    "expected_volatility_daily_basis": expected_volatility_daily(result.weights, train),
                    "realised_return": perf["return"],
                    "realised_volatility": perf["volatility"],
                    "realised_sharpe": perf["sharpe"],
                    "max_drawdown": perf["max_drawdown"],
                    "gold_weight": result.weights.get(GOLD, 0.0),
                })
                records.append(row)

    results = pd.DataFrame(records)
    for column in RESULT_COLUMNS:
        if column not in results:
            results[column] = np.nan
    bench = pd.DataFrame(bench_records)

    pd.set_option("display.width", 220)

    print("\n=== Benchmarks: realised return by test year (%) ===")
    print((bench.pivot(index="portfolio", columns="year", values="return")[labels] * 100).round(1).to_string())

    for variant in VARIANTS:
        rows = results[results["variant"] == variant]
        print(f"\n=== {variant} ===")
        print("Realised return by test year (%):")
        print((rows.pivot(index="score", columns="year", values="realised_return")[labels] * 100).round(1).to_string())
        print("Realised volatility by test year (%):")
        print((rows.pivot(index="score", columns="year", values="realised_volatility")[labels] * 100).round(1).to_string())
        print("Gold weight by test year (%):")
        print((rows.pivot(index="score", columns="year", values="gold_weight")[labels] * 100).round(1).to_string())
        for note in rows["note"].dropna().unique():
            print(f"  note: {note}")

    scoreboard = {}
    for variant in VARIANTS:
        rows = results[results["variant"] == variant]
        tuning = summarise(rows[rows["year"] != final])
        check = summarise(rows[rows["year"] == final])
        valid = rows.dropna(subset=["realised_return"])
        scoreboard[variant] = {
            "TUNING: risk rises with score": tuning["risk rises with score"],
            "TUNING: within volatility cap": tuning["within volatility cap"],
            "TUNING: avg volatility surprise": tuning["avg volatility surprise"],
            "FINAL: risk rises with score": check["risk rises with score"],
            "FINAL: within volatility cap": check["within volatility cap"],
            "FINAL: avg volatility surprise": check["avg volatility surprise"],
            "all years: avg realised return": f"{valid['realised_return'].mean() * 100:.1f}%",
            "all years: beat the Nifty": f"{int((valid['realised_return'] > valid['nifty_return']).sum())}/{len(rows)}",
            f"all years: cleared {HURDLE:.0%}": f"{int((valid['realised_return'] >= HURDLE).sum())}/{len(rows)}",
            "portfolios not possible": f"{int(rows['realised_return'].isna().sum())}/{len(rows)}",
        }
    board = pd.DataFrame(scoreboard)
    print("\n=== Scoreboard ===")
    print(board.to_string())
    print("\nChoose a variant from the TUNING rows only. Then read its FINAL rows once.")
    print('"Volatility surprise" is realised minus expected volatility, both measured from daily returns.')

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    results.to_csv(os.path.join(OUTPUT_DIR, "walk_forward_results.csv"), index=False)
    bench.to_csv(os.path.join(OUTPUT_DIR, "walk_forward_benchmarks.csv"), index=False)
    board.to_csv(os.path.join(OUTPUT_DIR, "walk_forward_scoreboard.csv"))
    print(f"\nSaved three walk_forward_*.csv files to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()