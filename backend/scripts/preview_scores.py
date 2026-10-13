"""Prints the portfolio for a range of scores (long horizon), read-only."""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

from data import load_snapshot
from database import SessionLocal
from models import DataSnapshot
from optimizer.engine import InfeasiblePortfolioError, optimize_portfolio
from scoring.scoring import constraints_for_score

SCORES = (5, 22, 25, 28, 39, 55, 72, 95)


def main():
    db = SessionLocal()
    try:
        snap = db.query(DataSnapshot).order_by(DataSnapshot.created_at.desc()).first()
        if snap is None:
            sys.exit("No snapshot found. Run: python scripts/data.py")
        mu, cov = load_snapshot(db, snap.snapshot_id)
    finally:
        db.close()

    pd.set_option("display.width", 200)
    pd.set_option("display.float_format", lambda x: f"{x:7.2%}")

    weights, summary = {}, {}
    for score in SCORES:
        c = constraints_for_score(score, "long")
        try:
            r = optimize_portfolio(mu, cov, c)
        except InfeasiblePortfolioError as exc:
            print(f"score {score}: INFEASIBLE - {exc}")
            continue
        weights[score] = r.weights
        summary[score] = {"equity_min": c.min_equity, "equity_max": c.max_equity,
                          "return": r.expected_return, "volatility": r.volatility}

    print("--- Weights by score ---")
    print(pd.DataFrame(weights))
    print("\n--- Limits and results by score ---")
    print(pd.DataFrame(summary))


if __name__ == "__main__":
    main()